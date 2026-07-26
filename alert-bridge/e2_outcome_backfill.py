#!/usr/bin/env python3
"""E2 OUTCOME BACKFILL — resolução CONTRAFACTUAL de TODOS os candidatos materiais (survivors E vetados)
para o painel forward hora×outcome. session_vacuum e chase foram REMOVIDOS do sistema (ordem Cris
2026-07-26) — o painel por hora Lisboa continua como leitura observacional, nunca gera veto. Lê
e2_verdicts.jsonl (levels entry/sl/target), resolve first-touch TP-vs-SL nas barras 15M do buffer Cp
(10 dias retenção), escreve logs/e2_outcomes.jsonl (idempotente por candidate_id; OPEN re-tentado).
Uso: python3 e2_outcome_backfill.py [--map]   (--map imprime o painel por hora acumulado)
Horas humanas em Lisboa (feedback_timezone_lisboa_always). py3.9 stdlib."""
import sys, json, bisect, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
BASE = Path(__file__).resolve().parent
LOGS = BASE / "logs"
VERD_F = LOGS / "e2_verdicts.jsonl"
OUT_F = LOGS / "e2_outcomes.jsonl"
BUF = Path("/Users/cristrein/tradingview-mcp/my-strategy/core/bar_store/store/bars_15m.jsonl")   # bar-store canónico (Fase 1)
LX = ZoneInfo("Europe/Lisbon")
HORIZON = 192          # 48h em barras 15M
BAR_S = 900


def _jl(f):
    try:
        return [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    except Exception:
        return []


def resolve(direction, entry, sl, tgt, bar_time, T, H, L):
    """First-touch TP vs SL a partir da barra seguinte ao bar_time. Devolve (outcome, barras)."""
    i0 = bisect.bisect_right(T, bar_time)
    if i0 >= len(T):
        return "OPEN", None
    for n, m in enumerate(range(i0, min(len(T), i0 + HORIZON)), 1):
        if direction == "SHORT":
            hit_sl = H[m] >= sl; hit_tp = L[m] <= tgt
        else:
            hit_sl = L[m] <= sl; hit_tp = H[m] >= tgt
        if hit_sl and hit_tp:
            return "AMBIGUOUS", n          # mesma barra tocou ambos — não decidir
        if hit_sl:
            return "SL", n
        if hit_tp:
            return "TP", n
    return ("EXPIRED", HORIZON) if len(T) - i0 >= HORIZON else ("OPEN", None)


def main():
    bars = _jl(BUF)
    if not bars:
        print("SEM buffer 15M"); return 1
    T = [b["t"] for b in bars]; H = [b["h"] for b in bars]; L = [b["l"] for b in bars]
    done = {r["candidate_id"]: r for r in _jl(OUT_F)}
    verd = _jl(VERD_F)
    n_new = n_re = 0
    with open(OUT_F, "a") as fh:
        for v in verd:
            cid = v.get("candidate_id"); lv = v.get("levels") or {}
            bt = v.get("bar_time")
            if not cid or bt is None or lv.get("entry") is None or lv.get("sl") is None or lv.get("target") is None:
                continue
            prev = done.get(cid)
            if prev and prev.get("outcome") not in (None, "OPEN"):
                continue                                   # já resolvido
            if bt < T[0]:
                continue                                   # antes do buffer — irresolúvel, não inventar
            oc, nb = resolve(v.get("direction"), lv["entry"], lv["sl"], lv["target"], bt, T, H, L)
            if prev and oc == "OPEN":
                continue                                   # ainda aberto, nada de novo
            lx = dt.datetime.fromtimestamp(bt, LX)
            rec = {"candidate_id": cid, "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
                   "outcome": oc, "bars_to": nb, "direction": v.get("direction"), "rule": v.get("rule"),
                   "tf": v.get("tf"), "grade": v.get("grade"), "veto": v.get("veto"),
                   "hour_lx": lx.hour, "date_lx": lx.strftime("%Y-%m-%d"),
                   "surfaced": v.get("surfaced"), "rr": lv.get("rr")}
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            done[cid] = rec
            n_new += 1 if not prev else 0; n_re += 1 if prev else 0
    print(f"outcomes: {n_new} novos, {n_re} re-resolvidos · total {len(done)}")
    if "--map" in sys.argv:
        rows = [r for r in done.values() if r.get("outcome") in ("TP", "SL")]
        from collections import defaultdict
        print(f"\n=== MAPA por hora Lisboa (decididos N={len(rows)}, observacional — nunca veto) ===")
        byh = defaultdict(lambda: [0, 0])
        for r in rows:
            byh[r["hour_lx"]][0] += 1 if r["outcome"] == "TP" else 0; byh[r["hour_lx"]][1] += 1
        for h in sorted(byh):
            tp, n = byh[h]
            print(f"  {h:02d}h  TP {tp}/{n}  ({100*tp/max(1,n):.0f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
