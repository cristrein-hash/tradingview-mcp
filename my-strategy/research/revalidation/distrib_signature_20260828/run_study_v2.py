#!/usr/bin/env python3
"""DISTRIB v2 — correções do DA (ac996eaf), hipótese e params INALTERADOS:
(1) V1H com ATR14 1H REAL do raw_1h_ohlc (era proxy 2×ATR15 inventado);
(2) null block-shuffle (shift circular das flags reais) sobre gap de WR E de avgR (lucro=doutrina);
(3) descritivo semana 24-28/08 via store bars_15m (RAW canónico termina 25/05 — declarado, não pontua).
py3.9 stdlib. SANITY_PROBE: read-only."""
import bisect
import json
import random
import sys
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "my-strategy/core"))
sys.path.insert(0, str(REPO / "my-strategy/research/revalidation"))
sys.path.insert(0, str(REPO / "my-strategy/strategies/xau_15m_long/continuation_A1A2"))
import raw_reader as RR  # noqa: E402
from run_study import build, distrib_flag, outcome, panel, K15, K1H, EP_GAP  # noqa: E402

OUT = Path(__file__).resolve().parent
SEED = 20260828
NULL_REPS = 300


def atr14(H, L, C):
    out = [None] * len(H); trs = []
    for i in range(len(H)):
        if i > 0: trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
        out[i] = sum(trs[-14:]) / 14 if len(trs) >= 14 else None
    return out


def main():
    rnd = random.Random(SEED)
    bars = RR.series_flat(RR.resolve_gz("XAUUSD", "15M"))
    rows = [dict(t=t, o=v[0], h=v[1], l=v[2], c=v[3]) for t, v in sorted(bars.items())]
    S = build(rows)
    T, H, C, ATR = S["T"], S["H"], S["C"], S["ATR"]
    h1 = [json.loads(l) for l in open(REPO / "my-strategy/research/revalidation/raw_1h_ohlc.jsonl") if l.strip()]
    h1.sort(key=lambda x: x["t"])
    T1, H1, L1, C1 = [b["t"] for b in h1], [b["h"] for b in h1], [b["l"] for b in h1], [b["c"] for b in h1]
    ATR1 = atr14(H1, L1, C1)

    import a1a2_runtime as RT
    sigs = []; last_i = -10**9
    for i in range(200, S["N"]):
        Sw = {k: (v[:i + 1] if isinstance(v, list) else v) for k, v in S.items()}
        Sw["N"] = i + 1
        r, why = RT.detect(Sw)
        if not r or i - last_i < EP_GAP:
            continue
        last_i = i
        R = outcome(S, i, r["ent"], r["sl"])
        v15 = distrib_flag(H, C, ATR[i], i, K15)
        j = bisect.bisect_right(T1, T[i]) - 1
        while j >= 0 and T1[j] + 3600 > T[i]:
            j -= 1
        v1h = distrib_flag(H1, C1, ATR1[j], j, K1H) if j > 0 and ATR1[j] else False
        sigs.append(dict(R=R, v15=v15, v1h=v1h))
    print(f"censo: {len(sigs)} episódios (idêntico v1 por construção)")

    out = dict(n_sigs=len(sigs), variants={})
    for vn in ("v15", "v1h"):
        flags = [s[vn] for s in sigs]
        on = [s["R"] for s, f in zip(sigs, flags) if f]
        off = [s["R"] for s, f in zip(sigs, flags) if not f]
        p_on, p_off = panel(on, 0.0), panel(off, 0.0)
        gap_wr = (p_off["WR"] or 0) - (p_on["WR"] or 0)
        gap_avg = round((p_off["avgR"] or 0) - (p_on["avgR"] or 0), 3)
        # block-null: shift circular da sequência REAL de flags (preserva autocorrelação)
        ge_wr = ge_avg = 0
        for _ in range(NULL_REPS):
            k = rnd.randint(1, len(flags) - 1)
            fl = flags[k:] + flags[:k]
            ron = [s["R"] for s, f in zip(sigs, fl) if f]
            roff = [s["R"] for s, f in zip(sigs, fl) if not f]
            qo, qf = panel(ron, 0.0), panel(roff, 0.0)
            if ((qf["WR"] or 0) - (qo["WR"] or 0)) >= gap_wr: ge_wr += 1
            if ((qf["avgR"] or 0) - (qo["avgR"] or 0)) >= gap_avg: ge_avg += 1
        blk = dict(on=p_on, off=p_off, gap_wr=gap_wr, gap_avgR=gap_avg,
                   p_blocknull_wr=round(ge_wr / NULL_REPS, 3),
                   p_blocknull_avgR=round(ge_avg / NULL_REPS, 3))
        out["variants"][vn] = blk
        print(f"{vn.upper()}: ON {p_on} · OFF {p_off}")
        print(f"  gap WR {gap_wr}pp p={blk['p_blocknull_wr']} · gap avgR {gap_avg}R p={blk['p_blocknull_avgR']}")

    # descritivo semana via STORE (fora do censo, não pontua — RAW canónico termina 25/05, declarado)
    st = [json.loads(l) for l in open(REPO / "my-strategy/core/bar_store/store/bars_15m.jsonl") if l.strip()]
    st.sort(key=lambda x: x["t"])
    Ts, Hs, Ls, Cs = [b["t"] for b in st], [b["h"] for b in st], [b["l"] for b in st], [b["c"] for b in st]
    ATRs = atr14(Hs, Ls, Cs)
    wk = [json.loads(l) for l in open(REPO / "my-strategy/strategies/xau_15m_long/continuation_A1A2/.a1a2_state/alerted.jsonl") if l.strip()]
    wk0 = dt.datetime(2026, 8, 24, tzinfo=dt.timezone.utc).timestamp()
    desc = []
    for r in wk:
        t = r.get("entry_t")
        if not t or t < wk0: continue
        i = bisect.bisect_left(Ts, t)
        if i >= len(Ts) or Ts[i] != t:
            desc.append(dict(when=str(t), err="sem match no store")); continue
        v15 = distrib_flag(Hs, Cs, ATRs[i], i, K15)
        j = bisect.bisect_right(T1, t) - 1
        while j >= 0 and T1[j] + 3600 > t: j -= 1
        v1h = distrib_flag(H1, C1, ATR1[j], j, K1H) if j > 0 and ATR1[j] else False
        desc.append(dict(when=dt.datetime.fromtimestamp(t, dt.timezone(dt.timedelta(hours=1))).strftime("%a %d/%m %H:%M"),
                         v15=v15, v1h=v1h))
    out["week_descriptive_store"] = desc
    print("DESCRITIVO semana (store, não pontua):")
    for d in desc:
        print(f"  {d}")

    (OUT / "results_v2_summary.json").write_text(json.dumps(out, indent=1))
    print("gravado results_v2_summary.json")


if __name__ == "__main__":
    main()
