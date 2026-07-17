#!/usr/bin/env python3
"""Runtime L2/BPT XAU 4H trend-exit — orquestração (FASE 2, alert-only, NASCE TRAVADO).

Por ciclo (tab 4H pinada via TVMCP_TARGET_CHART_ID; sem trocar chart, sem pausa):
  1. Seleção da última barra 4H FECHADA (close-only, mesma lógica do runtime_xau.py:221-243).
  2. Append de barras fechadas novas ao ledger (.runtime_state/l2_bars_4h.jsonl) com
     cross-check de sobreposição (tol 0.05) e grelha (gap>4d -> HARD_STOP).
  3. Features das barras novas (RSI por barra + bolhas Market Order) — fail-closed.
  4. scanner_l2.run_cycle: FSM história inteira + GUARD prefix-stability + candidato no frontier.
  5. Transições de posição (position_state, STOP-FIRST) intercaladas por barra com aberturas.
  6. Dedup por signal_hash + notify (telegram_notify_l2.py).

HARD-LOCK: envio real exige env L2_PRODUCTION_AUTHORIZED=1 — sem ele, dry-run FORÇADO
(mesmo padrão runtime_xau.py:311-337). Estados blocked_* fail-closed: missing_tab,
missing_study, gap, prefix_instability -> SEM alertas.

PRIMEIRO ciclo: last_processed_bar_time inicializado à última barra do ledger SEM procurar
sinais no passado (sem alertas retroativos). py3.9 stdlib.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scanner_l2 as SC          # noqa: E402
import position_state as PS      # noqa: E402
from l2_tv_read import L2Reader, bubbles_recent_for_bar, TF_SEC  # noqa: E402

CONSUMER = "L2_BPT_ZONE_TREND_EXIT"
GROUP = "XAU_240"            # registo do consumer no core/group_model_xau.py = destrava de go-live
SYMBOL = "PEPPERSTONE:XAUUSD"
TF = "240"
STATE_DIR = SC.STATE_DIR
DEDUP_DEFAULT = STATE_DIR / "l2_dedup.txt"
OHLC_TOL = 0.05
MAX_GAP_SEC = 4 * 86400
NOTIFIER = HERE / "telegram_notify_l2.py"


def signal_hash(ts_iso):
    key = f"{ts_iso}|XAUUSD|{TF}|{CONSUMER}|reversal"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def already_sent(dedup_path, sh):
    p = Path(dedup_path)
    if not p.exists():
        return False
    return any(line.strip() == sh for line in p.read_text().splitlines())


def mark_sent(dedup_path, sh):
    with open(dedup_path, "a") as f:
        f.write(sh + "\n")


def _production_authorized():
    """HARD-LOCK de código: envio real exige env L2_PRODUCTION_AUTHORIZED=1. Default = NÃO.
    Telegram disabled until Cris explicitly authorizes production. Só PREVINE envio, nunca ativa."""
    return os.environ.get("L2_PRODUCTION_AUTHORIZED", "") == "1"


def notify(payload, send, dedup_path, dedup_key):
    """Dispara alerta via telegram_notify_l2.py (advisory). Hard-lock + dedup + allowlist local."""
    if send and not _production_authorized():
        return {"sent": False, "dry_run": True,
                "skip": "PRODUCTION_NOT_AUTHORIZED — Telegram hard-locked (env L2_PRODUCTION_AUTHORIZED!=1)"}
    if payload.get("strategy_route") != CONSUMER:
        return {"sent": False, "skip": "route fora da allowlist L2"}
    if already_sent(dedup_path, dedup_key):
        return {"sent": False, "skip": f"dedup: {dedup_key} já enviado"}
    args = [sys.executable, str(NOTIFIER)] + (["--send"] if send else [])
    r = subprocess.run(args, input=json.dumps(payload), capture_output=True, text=True)
    sent = send and "SENT=True" in r.stdout
    if sent:
        mark_sent(dedup_path, dedup_key)
    return {"sent": sent, "dry_run": not send, "stdout": r.stdout.strip()[-400:]}


def blocked(state, reason, extra=None):
    return {"runtime": "BLOCKED", "state": state, "reason": reason,
            "consumer": CONSUMER, "group": GROUP, **(extra or {})}


def cycle(send_telegram=False, dedup_path=DEDUP_DEFAULT, ohlcv_count=400):
    now = datetime.now(timezone.utc).timestamp()
    out = {"runtime": "OK", "consumer": CONSUMER, "group": GROUP,
           "ts": datetime.now(timezone.utc).isoformat(), "telegram_real": bool(send_telegram),
           "production_authorized": _production_authorized()}

    if not os.environ.get("TVMCP_TARGET_CHART_ID"):
        return blocked("blocked_missing_tab_240", "env TVMCP_TARGET_CHART_ID ausente "
                       "(run_l2_cycle faz o pin; SEM fallback manage-chart no L2)")

    ledger = SC.load_ledger()
    if len(ledger) < 1000:
        return blocked("blocked_missing_ledger",
                       f"ledger ausente/curto ({len(ledger)} barras) — corre bootstrap_history.py")

    with L2Reader() as rd:
        ok, info = rd.verify_chart()
        if not ok:
            return blocked(info.split(":")[0] if isinstance(info, str) else "blocked_chart",
                           info)
        out["chart"] = {"symbol": info["symbol"], "timeframe": info["timeframe"]}

        # ---- (1) OHLCV + seleção da última barra FECHADA (close-only, padrão runtime_xau) ----
        ok, bars = rd.get_ohlcv(count=ohlcv_count)
        if not ok:
            return blocked("blocked_ohlcv", bars)
        closed = [b for b in bars if b["t"] + TF_SEC <= now]     # forming NUNCA entra
        if not closed:
            return blocked("blocked_bar_not_closed",
                           f"nenhuma barra fechada (last={bars[-1]['t'] if bars else None})")
        forming_excluded = len(bars) - len(closed)
        eval_bar_time = closed[-1]["t"]
        out["bar_diagnostics"] = {"returned_last_bar_time": bars[-1]["t"],
                                  "eval_bar_time": eval_bar_time,
                                  "forming_bars_excluded": forming_excluded}

        # ---- (2) cross-check sobreposição MCP<->ledger + append de barras novas ----
        ledger_by_t = {b["t"]: b for b in ledger}
        ledger_last_t = ledger[-1]["t"]
        overlap = [b for b in closed if b["t"] in ledger_by_t]
        if not overlap:
            return blocked("blocked_gap", "janela MCP não sobrepõe o ledger — gap descontínuo; "
                           "re-corre bootstrap_history.py")
        max_diff = 0.0
        for b in overlap[-12:]:
            s = ledger_by_t[b["t"]]
            d = max(abs(s["o"] - b["o"]), abs(s["h"] - b["h"]),
                    abs(s["l"] - b["l"]), abs(s["c"] - b["c"]))
            max_diff = max(max_diff, d)
            if d > OHLC_TOL:
                return blocked("blocked_ledger_mismatch",
                               f"OHLC diverge do ledger em t={b['t']} (diff={d:.2f}>{OHLC_TOL})")
        out["overlap_check"] = {"bars": len(overlap[-12:]), "max_abs_diff": round(max_diff, 4)}
        new_bars = [{"t": b["t"], "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]}
                    for b in closed if b["t"] > ledger_last_t]
        prev_t = ledger_last_t
        for b in new_bars:
            d = b["t"] - prev_t
            if d % 3600 != 0 or d < TF_SEC:
                return blocked("blocked_gap", f"grelha inválida no append (diff={d}s em t={b['t']})")
            if d > MAX_GAP_SEC:
                return blocked("blocked_gap", f"gap descontínuo no append ({d/86400:.1f}d) — "
                               "re-corre bootstrap_history.py")
            prev_t = b["t"]
        if new_bars:
            ledger = ledger + new_bars
            SC.save_ledger(ledger)
        out["new_bars"] = [b["t"] for b in new_bars]

        # ---- (3) features das barras novas (fail-closed) ----
        feats = SC.load_features()
        ledger_T = [b["t"] for b in ledger]
        if new_bars:
            need = len(new_bars) + 15
            ok_r, rsi_by_t = rd.get_rsi_by_bar(count=need)
            if not ok_r:
                return blocked("blocked_missing_study:rsi", rsi_by_t)
            ok_b, acts = rd.get_bubble_activations(max_bars=need)
            if not ok_b:
                return blocked("blocked_missing_study:bubbles", acts)
            acts_by_t = {}
            for t, plot in acts:
                acts_by_t.setdefault(t, []).append(plot)
            idx_by_t = {t: i for i, t in enumerate(ledger_T)}
            for b in new_bars:
                i = idx_by_t[b["t"]]
                rsi = rsi_by_t.get(b["t"])
                if rsi is None:
                    return blocked("blocked_missing_study:rsi",
                                   f"RSI ausente p/ barra fechada t={b['t']}")
                feats[b["t"]] = {"t": b["t"], "rsi": rsi,
                                 "bubbles_recent": bubbles_recent_for_bar(i, ledger_T, acts_by_t),
                                 "src": "live"}
            SC.save_features(feats)

        # ---- (4) zonas DEMAND (context_sl) ----
        ok_d, ds = rd.get_demand_supply()
        if not ok_d:
            return blocked("blocked_missing_study:ob_boxes", ds)
        out["boxes"] = {"demand": len(ds["demand"]), "supply": len(ds["supply"])}

    # ---- (5) posição/continuidade + barras novas a processar ----
    st = PS.load_state()
    okc, why = PS.check_continuity(st, ledger_T)
    if not okc:
        return blocked("blocked_gap", why)
    first_cycle = st.get("last_processed_bar_time") is None
    if first_cycle:
        # SEM sinais retroativos: inicializa no fim do ledger e não varre o passado
        st["last_processed_bar_time"] = ledger[-1]["t"]
        PS.save_state(st)
        out["initialized_first_cycle"] = ledger[-1]["t"]
        new_idxs = []
    else:
        lp = st["last_processed_bar_time"]
        new_idxs = [i for i, t in enumerate(ledger_T) if t > lp]

    # ---- (6) scanner: FSM + guard + candidatos + rótulos ----
    sc = SC.run_cycle(ledger, feats if new_bars or True else {}, ds["demand"], new_idxs)
    if sc["status"] != "ok":
        return blocked(sc["status"], sc.get("guard"))
    out["guard"] = sc["guard"]
    out["panel"] = sc["panel"]

    # ---- (7) transições + aberturas intercaladas por barra (ordem do ledger) ----
    latest = len(ledger) - 1
    results_by_idx = {r["ledger_idx"]: r for r in sc["bar_results"]}
    alerts = []
    for j in new_idxs:
        r = results_by_idx[j]
        # fechos primeiro (posições existentes avaliam a barra j)
        for ev in PS.process_closed_bar(st, j, ledger[j], r["regime_label"], latest):
            alerts.append({"kind": "exit", "event": ev})
        # abertura (posição advisory nasce em j; avaliada a partir de j+1)
        ec = r.get("entry_candidate")
        if ec:
            ts_iso = datetime.utcfromtimestamp(ec["bar_time"]).isoformat()
            ec["signal_hash"] = signal_hash(ts_iso)
            ec["candidate_timestamp"] = ts_iso
            pos, ev = PS.open_position(st, ec)
            if pos is not None:
                alerts.append({"kind": "entry", "candidate": ec})
        st["last_processed_bar_time"] = ledger[j]["t"]
    if new_idxs:
        PS.save_state(st)
    out["open_positions"] = len(PS.open_positions(st))
    out["bar_results"] = [{k: r.get(k) for k in ("bar_time", "stage", "regime_label",
                                                 "late_bars", "no_trade_reason")}
                          for r in sc["bar_results"]]

    # ---- (8) alertas (dedup + hard-lock) ----
    notif = []
    for a in alerts:
        if a["kind"] == "entry":
            ec = a["candidate"]
            payload = {"kind": "entry", "strategy_route": CONSUMER, "operational": True,
                       "symbol": SYMBOL, "timeframe": TF,
                       "candidate_timestamp": ec["candidate_timestamp"],
                       "signal_hash": ec["signal_hash"], "entry": ec["entry"], "sl": ec["sl"],
                       "risk_pts": ec["risk"], "wide_stop": ec["wide_stop"],
                       "regime": ec["regime"], "zona": ec["zona"], "sl_type": ec["sl_type"],
                       "late_bars": ec.get("late_bars", 0)}
            res = notify(payload, send_telegram, dedup_path, ec["signal_hash"])
        else:
            ev = a["event"]
            key = f"{ev['signal_hash']}:EXIT:{ev['bar_time']}"
            payload = {"kind": "exit", "strategy_route": CONSUMER, "operational": True,
                       "symbol": SYMBOL, "timeframe": TF, "mot": ev["mot"], "R": ev["R"],
                       "bar_time_iso": datetime.utcfromtimestamp(ev["bar_time"]).isoformat(),
                       "entry_signal_hash": ev["signal_hash"], "late_bars": ev["late_bars"]}
            res = notify(payload, send_telegram, dedup_path, key)
        notif.append({"kind": a["kind"], "payload_hash": payload.get("signal_hash")
                      or payload.get("entry_signal_hash"), "notify": res})
    out["alerts"] = notif
    out["alerts_n"] = len(notif)
    return out


def main():
    ap = argparse.ArgumentParser(description="Runtime L2/BPT XAU 4H (tab-pinned, alert-only).")
    ap.add_argument("--once", action="store_true", help="executa 1 ciclo e sai (default já é 1)")
    ap.add_argument("--send-telegram", action="store_true",
                    help="envio real (opt-in; hard-lock L2_PRODUCTION_AUTHORIZED=1 continua a mandar)")
    ap.add_argument("--dedup-path", default=str(DEDUP_DEFAULT))
    args = ap.parse_args()
    try:
        res = cycle(send_telegram=args.send_telegram, dedup_path=args.dedup_path)
    except Exception as e:
        res = {"runtime": "HARD_STOP", "state": "exception",
               "reason": f"{type(e).__name__}: {e}"}
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res.get("runtime") == "OK" else 2


if __name__ == "__main__":
    sys.exit(main())
