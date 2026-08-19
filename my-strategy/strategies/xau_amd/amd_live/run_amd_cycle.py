#!/usr/bin/env python3
"""AMD LIVE F1 — detetor H4 sweep+reclaim, Ping-1 "SETUP ARMADO" (Cris 2026-07-19, LIVE alert-only).
Store-first (raw_4h via store_reader, zero CDP). Reusa o detetor DA-limpo amd_lab/amd_v2.signals_v2 (bias
EMA20-D1 = paridade backtest; Layer1 logado como CONTEXTO). Triplo gate anti-flood: once-per-level (no
detetor) × dedup persistido (ledger) × frescura ≤1 barra H4. 1º run marca TODA a história stale SEM alertar;
só o setup da última barra H4 fechada dispara Telegram. Gated AMD_PRODUCTION_AUTHORIZED=1 (senão dry).
NUNCA negoceia, NUNCA toca o chart, complementa (não gateia) estratégias. Lisboa nas horas humanas. py3.9."""
import os, sys, json, time, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "alert-bridge"))
sys.path.insert(0, str(REPO / "my-strategy/research/revalidation/amd_lab"))
import store_reader as SR
import amd_v2 as V
HERE = Path(__file__).resolve().parent
STATE = HERE / ".amd_state"; STATE.mkdir(exist_ok=True)
LEDGER = STATE / "amd_setups.jsonl"
LOG = STATE / "amd_cycle.log"
LAYER1 = REPO / "my-strategy/core/layer1_service/.layer1_state/current_layer1.json"
FRESH_H4_S = 14400                 # 1 barra H4 (só o setup acabado de fechar arma+alerta)
LX = ZoneInfo("Europe/Lisbon"); UTC = dt.timezone.utc
lx = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%Y-%m-%d %H:%M")
KZ = {6: "London", 10: "London/NY", 14: "NY"}


def _log(o):
    with open(LOG, "a") as fh: fh.write(json.dumps(o, ensure_ascii=False) + "\n")


def _jl(f):
    try: return [json.loads(x) for x in Path(f).read_text().splitlines() if x.strip()]
    except Exception: return []


def _setup_id(s):
    u = dt.datetime.fromtimestamp(s["t"], UTC)
    return f"amd_{u.strftime('%Y%m%dT%H%M')}_{s['dir'][0].upper()}_{int(round(s['level']))}"


def _layer1():
    try: return json.loads(LAYER1.read_text()).get("regime")
    except Exception: return None


# formato único notify.py (Cris 2026-08-19; reclass 2ª ordem): AMD é ESTRATÉGIA — ping1 = 🎯 ENTRADA
# fase 1 (setup sem entry ainda: busca do FVG inferior SEMPRE no 1H); ping2 = 🎯 ENTRADA fase 2 (candidato
# com entry/SL/alvo). Detalhe (bias/killzone/ids) fica no ledger.
def _ping1(s, sid, l1):
    kind = "PDL/PWL" if s["dir"] == "long" else "PDH/PWH"
    side = "🟢 LONG" if s["dir"] == "long" else "🔴 SHORT"
    return "\n".join([
        "🎯 ENTRADA · AMD (fase 1: setup) · 4H",
        "──────────────",
        f"{side} XAUUSD — varreu {kind} {s['level']} · reclaim {s['h4c']}",
        "sem entry ainda — busca o FVG inferior no 1H (fase 2 traz entry/SL/alvo)",
        "──────────────",
        f"{lx(s['t'])} Lisboa · decisão humana · #N",
    ])


def _send(msg):
    try:
        sys.path.insert(0, str(REPO / "alert-bridge"))
        import notify as NF
        r = NF._send(msg, "group"); return bool(r) if not isinstance(r, str) else r
    except Exception as e:
        return f"ERR {str(e)[:60]}"


def _ping2(rec, cands):
    side = "🟢 LONG" if rec["dir"] == "long" else "🔴 SHORT"
    lines = ["🎯 ENTRADA · AMD · 1H", "──────────────",
             f"{side} XAUUSD — {len(cands)} candidato(s) até {lx(rec['window_expires_epoch'])} Lisboa"]
    for i, c in enumerate(cands, 1):
        lines += [f"[{i}] FVG {c['fvg'][0]}-{c['fvg'][1]} · {c['status']}",
                  f"entry   {c['ent']}",
                  f"SL      {c['sl']}",
                  f"alvo    {c['tgt']}  (2R)"]
    lines += ["──────────────", "decisão humana · #N (ex: #7 amd fvgN)"]
    return "\n".join(lines)


def main():
    send = os.environ.get("AMD_PRODUCTION_AUTHORIZED") == "1"
    now = int(time.time()); ts = dt.datetime.now(UTC).isoformat()
    out = {"ts": ts, "mode": "LIVE" if send else "DRY"}
    if not SR.fresh("240", mult=2):
        out["status"] = "NO-OP: 4H store stale"; _log(out); print(json.dumps(out)); return
    h4 = SR.bars("240")
    if not h4 or len(h4) < 120:
        out["status"] = f"NO-OP: 4H insuficiente (n={len(h4) if h4 else 0})"; _log(out); print(json.dumps(out)); return
    sigs = V.signals_v2(h4, use_bias=True)
    last_t = h4[-1]["t"]; l1 = _layer1()
    rows = _jl(LEDGER); by_id = {r["setup_id"]: r for r in rows}
    armed = 0; new_stale = 0
    # --- F1: novos setups H4 ---
    for s in sigs:
        sid = _setup_id(s)
        existing = by_id.get(sid)
        if existing and (existing.get("ping1_sent") or existing.get("state") == "STALE"):
            continue                                       # já tratado: ping ENTREGUE, ou stale (sem ping)
        stale = (last_t - s["t"]) > FRESH_H4_S
        if existing:
            rec = existing                                 # ARMED cujo ping1 falhou -> re-tentar (não re-dedup)
        else:
            hu = dt.datetime.fromtimestamp(s["t"], UTC)
            rec = {"setup_id": sid, "dir": s["dir"], "level": s["level"], "bias": s["bias"], "bias_layer1": l1,
                   "killzone": KZ.get(hu.hour), "h4_bar_t": s["t"], "h4_bar_ts": lx(s["t"]), "sweep_wick": s["wick"],
                   "h4_close": s["h4c"], "close_pos": s["close_pos"], "window_expires_epoch": s["t"] + 16 * 3600,
                   "armed_ts": lx(now), "state": "STALE" if stale else "ARMED", "ping1_sent": False, "tg_ok": None,
                   "candidates_pinged": []}
            armed += 0 if stale else 1
            new_stale += 1 if stale else 0
        if not stale and send:
            ok = _send(_ping1(s, sid, l1))
            rec["ping1_sent"] = (ok is True); rec["tg_ok"] = str(ok)   # entregue SÓ se sucesso -> senão re-tenta
        if not existing:
            by_id[sid] = rec; rows.append(rec)
    # --- F2: candidatos 1H p/ setups ARMED dentro da janela ---
    h1 = SR.bars("60"); ping2 = 0
    for rec in rows:
        if rec.get("state") != "ARMED":
            continue
        if now >= rec.get("window_expires_epoch", 0):
            rec["state"] = "EXPIRED"; continue
        cands = V.list_candidates({"t": rec["h4_bar_t"], "dir": rec["dir"], "setup_id": rec["setup_id"]}, h1)
        rec["candidates_latest"] = cands                     # lista completa p/ o E0 ler (F3)
        pinged = set(rec.get("candidates_pinged", []))
        new = [c for c in cands if c["candidate_id"] + ":" + c["status"] not in pinged]
        if new:
            ok = _send(_ping2(rec, new)) if send else None
            # AUDIT-FIX 19/08 (C4): só marca pinged com envio CONFIRMADO (ok True) ou em dry-run;
            # antes um envio falhado marcava os candidatos e o sinal perdia-se sem re-tentativa.
            if (ok is True) or not send:
                for c in new: rec.setdefault("candidates_pinged", []).append(c["candidate_id"] + ":" + c["status"])
            ping2 += 1
    # reescreve o ledger inteiro (F1 append + F2 update)
    tmp = LEDGER.with_suffix(".jsonl.tmp"); tmp.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else "")); os.replace(tmp, LEDGER)
    out.update({"n_signals": len(sigs), "armed_fresh": armed, "new_stale": new_stale, "ping2_setups": ping2,
                "active": sum(1 for r in rows if r.get("state") == "ARMED"), "last_h4": lx(last_t), "status": "OK"})
    _log(out); print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
