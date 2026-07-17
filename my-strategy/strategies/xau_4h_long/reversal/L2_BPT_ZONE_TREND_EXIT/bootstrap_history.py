#!/usr/bin/env python3
"""L2/BPT — BOOTSTRAP one-shot do ledger 4H (.runtime_state/l2_bars_4h.jsonl).

O FSM é path-dependent desde 2020 (EMA300/CUSUM/zigzag) — NUNCA recomeçar curto.
Seed canónico: my-strategy/research/revalidation/raw_4h_ohlc.jsonl (9880 barras, paridade V-1..V-4)
+ backfill do gap até hoje via MCP data_get_ohlcv paginado (from_time/to_time, count<=500)
na tab 4H PINADA (tab_pin.discover_tab("240"); ausente -> HARD_STOP, sem fallback).

Asserts:
  - grelha: t%3600==0, estritamente crescente, diffs>=14400 e %3600==0 (fins-de-semana/DST ok;
    diff>4d = gap descontínuo -> HARD_STOP)
  - sem duplicados conflituantes; paridade OHLC na janela de sobreposição seed<->MCP (tol 0.05)
  - barra em formação NUNCA entra (só t+14400 <= now)
  - QUIRK seed: a última barra do seed é degenerada (o=h=l=c, snapshot do open de 2026-05-24 22:00);
    é SUBSTITUÍDA pela barra real do MCP (registado no relatório). O research não a descartava
    (paridade do frozen), mas o ledger live deve ter a barra fechada REAL.

Também seeda:
  - l2_features.jsonl  (rsi+bubbles_recent por barra: frozen p/ t<=frozen_end; MCP p/ o gap)
  - l2_candidates.jsonl (pruned base V2 via scanner_l2.rebuild_candidates_journal — p/ episódio gap<=6)
  - l2_positions.json   (last_processed_bar_time = última barra do ledger; SEM sinais retroativos)

Uso: python3 bootstrap_history.py [--dry-run]   (dry-run: lê MCP mas não escreve estado)
py3.9 stdlib. Read-only no chart.
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scanner_l2 as SC          # noqa: E402
import position_state as PS      # noqa: E402
from l2_tv_read import L2Reader, bubbles_recent_for_bar, TF_SEC  # noqa: E402


def _repo(p):
    for d in [p] + list(p.parents):
        if (d / "my-strategy").is_dir() and (d / "alert-bridge").is_dir():
            return d
    return p.parents[5]


REPO = _repo(HERE)
SEED = REPO / "my-strategy/research/revalidation/raw_4h_ohlc.jsonl"
FROZEN = (REPO / "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/"
          "repro_recovery/raw_features_2020_2026.jsonl")
CORE = REPO / "my-strategy/core"
OVERLAP_BARS = 24          # janela de sobreposição seed<->MCP a verificar
OHLC_TOL = 0.05            # "tolerância cêntimos"
MAX_GAP_SEC = 4 * 86400    # diff>4d = gap descontínuo (weekend/holiday max observado ~3.3d)


def hard_stop(reason, detail=None):
    print(json.dumps({"bootstrap": "HARD_STOP", "reason": reason, "detail": detail},
                     ensure_ascii=False, indent=2))
    sys.exit(2)


def check_grid(bars, label):
    T = [b["t"] for b in bars]
    if len(T) != len(set(T)):
        hard_stop(f"{label}: timestamps duplicados")
    for i, t in enumerate(T):
        if t % 3600 != 0:
            hard_stop(f"{label}: t não múltiplo de 3600", {"i": i, "t": t})
    anomalies = []
    for i in range(1, len(T)):
        d = T[i] - T[i - 1]
        if d <= 0:
            hard_stop(f"{label}: t não crescente", {"i": i})
        if d % 3600 != 0 or d < TF_SEC:
            hard_stop(f"{label}: diff inválido na grelha 4H", {"i": i, "diff": d,
                                                              "t": T[i - 1]})
        if d > MAX_GAP_SEC:
            anomalies.append({"i": i, "t_prev": T[i - 1], "t": T[i], "diff_days": round(d / 86400, 2)})
    return anomalies


def main():
    ap = argparse.ArgumentParser(description="Bootstrap one-shot do ledger L2 4H (seed+MCP).")
    ap.add_argument("--dry-run", action="store_true", help="lê MCP mas não escreve estado")
    args = ap.parse_args()
    t0 = time.time()
    now = datetime.now(timezone.utc).timestamp()

    # ---- seed canónico ----
    if not SEED.exists():
        hard_stop("seed ausente", str(SEED))
    seed = [json.loads(l) for l in SEED.read_text().splitlines() if l.strip()]
    seed.sort(key=lambda b: b["t"])
    check_grid(seed, "seed")
    seed_last = seed[-1]
    seed_degenerate = (seed_last["o"] == seed_last["h"] == seed_last["l"] == seed_last["c"])

    # ---- tab 4H pinada (fail-closed, sem fallback) ----
    sys.path.insert(0, str(CORE))
    import tab_pin
    tid = tab_pin.discover_tab("240")
    if not tid:
        hard_stop("blocked_missing_tab_240", "tab XAUUSD 240 não encontrada (tab_pin)")

    gap_bars_n = None
    report = {"seed_bars": len(seed), "seed_last_t": seed_last["t"],
              "seed_degenerate_tail": seed_degenerate, "tab_240": tid[:8]}

    with L2Reader(target_id=tid) as rd:
        ok, info = rd.verify_chart()
        if not ok:
            hard_stop(info)
        report["chart"] = {"symbol": info["symbol"], "studies_n": len(info["studies"])}

        # ---- backfill paginado: desde OVERLAP_BARS antes do fim do seed até agora ----
        from_t = seed[-OVERLAP_BARS]["t"]
        ok, mcp_bars = rd.get_ohlcv_paginated(from_time=from_t, to_time=int(now))
        if not ok:
            hard_stop(mcp_bars)
        mcp_closed = [b for b in mcp_bars if b["t"] + TF_SEC <= now]   # forming NUNCA entra
        if not mcp_closed:
            hard_stop("MCP sem barras fechadas na janela pedida")
        report["mcp_window"] = {"n_closed": len(mcp_closed),
                               "first_t": mcp_closed[0]["t"], "last_t": mcp_closed[-1]["t"]}
        if mcp_closed[0]["t"] > seed_last["t"]:
            hard_stop("gap descontínuo: buffer MCP não alcança o fim do seed — "
                      "scroll o chart 4H para trás para carregar histórico",
                      {"mcp_first": mcp_closed[0]["t"], "seed_last": seed_last["t"]})

        # ---- paridade da sobreposição + substituição da barra degenerada ----
        seed_by_t = {b["t"]: b for b in seed}
        overlap_checked = 0
        max_diff = 0.0
        degenerate_replaced = False
        for b in mcp_closed:
            s = seed_by_t.get(b["t"])
            if s is None:
                continue
            if b["t"] == seed_last["t"] and seed_degenerate:
                seed_by_t[b["t"]] = {"t": b["t"], "o": b["o"], "h": b["h"],
                                     "l": b["l"], "c": b["c"]}
                degenerate_replaced = True
                continue
            overlap_checked += 1
            d = max(abs(s["o"] - b["o"]), abs(s["h"] - b["h"]),
                    abs(s["l"] - b["l"]), abs(s["c"] - b["c"]))
            max_diff = max(max_diff, d)
            if d > OHLC_TOL:
                hard_stop("paridade OHLC seed<->MCP falhou na sobreposição",
                          {"t": b["t"], "seed": s, "mcp": b, "tol": OHLC_TOL})
        if overlap_checked == 0:
            hard_stop("sobreposição seed<->MCP vazia — impossível validar continuidade")
        report["overlap"] = {"bars_checked": overlap_checked, "max_abs_diff": round(max_diff, 4),
                            "degenerate_replaced": degenerate_replaced}

        # ---- ledger final = seed (com substituição) + barras novas ----
        new_bars = [{"t": b["t"], "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]}
                    for b in mcp_closed if b["t"] > seed_last["t"]]
        ledger = [seed_by_t[t] for t in sorted(seed_by_t)] + new_bars
        anomalies = check_grid(ledger, "ledger")
        if anomalies:
            hard_stop("gap descontínuo no ledger final (diff>4d)", anomalies[:5])
        report["appended_bars"] = len(new_bars)
        report["ledger_bars"] = len(ledger)
        report["ledger_last_t"] = ledger[-1]["t"]
        report["ledger_last_iso"] = datetime.utcfromtimestamp(ledger[-1]["t"]).isoformat()

        # ---- features: frozen (verbatim) + gap via MCP (rsi por barra + bolhas) ----
        frozen = [json.loads(l) for l in FROZEN.read_text().splitlines() if l.strip()]
        feats = {}
        ledger_T = [b["t"] for b in ledger]
        tset = set(ledger_T)
        for r in frozen:
            if r["ts_epoch"] in tset:
                feats[r["ts_epoch"]] = {"t": r["ts_epoch"], "rsi": r.get("rsi"),
                                        "bubbles_recent": r.get("bubbles_recent") or [],
                                        "src": "frozen"}
        gap_ts = [t for t in ledger_T if t not in feats]
        gap_bars_n = len(gap_ts)
        rsi_cov = bub_acts_n = 0
        if gap_ts:
            need = len(gap_ts) + 20
            ok_r, rsi_by_t = rd.get_rsi_by_bar(count=min(need, 1000))
            rsi_by_t = rsi_by_t if ok_r else {}
            ok_b, acts = rd.get_bubble_activations(max_bars=min(need, 1000))
            acts = acts if ok_b else []
            acts_by_t = {}
            for t, plot in acts:
                acts_by_t.setdefault(t, []).append(plot)
            idx_by_t = {t: i for i, t in enumerate(ledger_T)}
            for t in gap_ts:
                i = idx_by_t[t]
                bub = bubbles_recent_for_bar(i, ledger_T, acts_by_t, window=10)
                feats[t] = {"t": t, "rsi": rsi_by_t.get(t),
                            "bubbles_recent": bub, "src": "mcp_backfill"}
                if rsi_by_t.get(t) is not None:
                    rsi_cov += 1
                bub_acts_n += sum(1 for x in bub if x["bars_ago"] == 0)
            report["features_gap"] = {"bars": len(gap_ts), "rsi_covered": rsi_cov,
                                      "rsi_missing": len(gap_ts) - rsi_cov,
                                      "bubble_acts_on_gap_bars": bub_acts_n,
                                      "rsi_source_ok": ok_r, "bubbles_source_ok": ok_b}

    if args.dry_run:
        report["dry_run"] = True
        print(json.dumps({"bootstrap": "DRY_RUN_OK", **report}, ensure_ascii=False, indent=2))
        return 0

    # ---- escrever estado (atómico) ----
    SC.STATE_DIR.mkdir(exist_ok=True)
    SC.save_ledger(ledger)
    SC.save_features(feats)

    # journal de candidatos (pruned base V2 sobre o ledger novo — research semantics, one-shot)
    idxs, _ = SC.rebuild_candidates_journal(ledger, feats)
    report["candidates_journal"] = {"n": len(idxs),
                                    "last_idx": idxs[-1] if idxs else None,
                                    "last_t": ledger[idxs[-1]]["t"] if idxs else None}

    # positions state: PRIMEIRO ciclo não procura sinais no passado
    st = PS.load_state()
    if st.get("last_processed_bar_time") is None:
        st["last_processed_bar_time"] = ledger[-1]["t"]
        PS.save_state(st)
        report["positions_state"] = {"initialized_last_processed": ledger[-1]["t"]}
    else:
        report["positions_state"] = {"kept_existing": st["last_processed_bar_time"]}

    # painel imediato (sanidade): regime atual + zona bear_deep
    fsm, reg, segs = SC.compute_regime(ledger)
    selector = SC.E.make_selector(segs, fsm["T"], fsm["H"], fsm["L"])
    report["panel"] = SC.zone_panel(ledger, reg, segs, selector)
    report["elapsed_s"] = round(time.time() - t0, 1)
    print(json.dumps({"bootstrap": "OK", **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
