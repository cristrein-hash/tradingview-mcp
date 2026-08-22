#!/usr/bin/env python3
"""A2 POSICIONADA V2 — adenda 39d6638: confluência FVG 15M∩1H + gate regime Layer1 BULL/RANGE.
Resto idêntico ao run_study.py pós-DA-fix (fill-bar-SL conta). py3.9 stdlib."""
import json
import random
import sys
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "my-strategy/core"))
sys.path.insert(0, str(REPO / "my-strategy/core/layer1_service"))
sys.path.insert(0, str(REPO / "my-strategy/research/revalidation"))
import raw_reader as RR  # noqa: E402

OUT = Path(__file__).resolve().parent
SEED = 20260822
HH_WIN, HH_GAP = 96, 8
FVG_FRESH, DIST_ATR, VALID, HORIZON = 32, 1.5, 16, 480
FVG1H_FRESH = 32
EP_GAP = 8


def build(rows):
    T = [r["t"] for r in rows]; O = [r["o"] for r in rows]; H = [r["h"] for r in rows]
    L = [r["l"] for r in rows]; C = [r["c"] for r in rows]
    N = len(rows); ATR = [None] * N; trs = []
    for i in range(N):
        if i > 0: trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
        ATR[i] = sum(trs[-14:]) / 14 if len(trs) >= 14 else None
    return dict(T=T, O=O, H=H, L=L, C=C, ATR=ATR, N=N)


def outcome(S, k, ent, sl):
    """fill-bar SL conta (DA-fix)."""
    tgt = ent + 3 * (ent - sl)
    if S["L"][k] <= sl:
        return -1.0
    for m in range(k + 1, min(S["N"], k + HORIZON)):
        if S["L"][m] <= sl: return -1.0
        if S["H"][m] >= tgt: return 3.0
    return 0.0


def h1_canonical():
    """1H do RAW canónico (raw_1h_ohlc.jsonl, dono bar_store) — NUNCA resamplear do 15M (trava dura)."""
    rows = [json.loads(l) for l in open(REPO / "my-strategy/research/revalidation/raw_1h_ohlc.jsonl") if l.strip()]
    rows.sort(key=lambda x: x["t"])
    return rows


def regime_labels():
    """Labels Layer1 1D causais (motor real, mesma fusão do serviço). Devolve (T1d, labels)."""
    import layer1_cycle as LC
    import macro_structural_v3 as M
    xau = LC._merge_xau_1d()
    M.T = [b["t"] for b in xau]; M.O = [b["o"] for b in xau]; M.H = [b["h"] for b in xau]
    M.L = [b["l"] for b in xau]; M.C = [b["c"] for b in xau]; M.N = len(xau)
    dxy = [json.loads(l) for l in open(REPO / "my-strategy/research/revalidation/raw_dxy_1d.jsonl") if l.strip()]
    M.DXY_K = [b["t"] + 86400 for b in dxy]; M.DXY_C = [b["c"] for b in dxy]
    return M.T, M.build_layer1()


def main():
    rnd = random.Random(SEED)
    bars = RR.series_flat(RR.resolve_gz("XAUUSD", "15M"))
    rows = [dict(t=t, o=v[0], h=v[1], l=v[2], c=v[3]) for t, v in sorted(bars.items())]
    S = build(rows)
    T, H, L, C, ATR = S["T"], S["H"], S["L"], S["C"], S["ATR"]
    H1 = h1_canonical()
    T1h = [b["t"] for b in H1]
    import bisect
    T1d, lab1d = regime_labels()

    def regime_at(t):
        """label D-1 causal: última barra 1D cujo t é < início do dia de t."""
        day0 = t - (t % 86400)
        i = bisect.bisect_left(T1d, day0) - 1
        return lab1d[i] if 0 <= i < len(lab1d) else None

    def fvg1h_fresh(t_now, price):
        """Existe FVG 1H bullish fresco não-preenchido com zona abaixo do preço? Devolve (bot,top) ou None."""
        j = bisect.bisect_right(T1h, t_now) - 1          # última 1H FECHADA <= agora: exige t+3600<=t_now
        while j >= 0 and T1h[j] + 3600 > t_now:
            j -= 1
        out = []
        for k in range(max(2, j - FVG1H_FRESH), j + 1):
            gb, gt = H1[k - 2]["h"], H1[k]["l"]
            if gt <= gb:
                continue
            if any(H1[m]["l"] <= gb for m in range(k + 1, j + 1)):
                continue
            if gt < price:
                out.append((gb, gt))
        return out

    half = lambda i: dt.datetime.fromtimestamp(T[i], dt.timezone.utc).strftime(
        "%Y-H1" if dt.datetime.fromtimestamp(T[i], dt.timezone.utc).month <= 6 else "%Y-H2")

    setups = []
    seen_gap = set()
    n_regime_block = n_no_conf = 0
    for i in range(200, S["N"]):
        atr = ATR[i] or 5.0
        hw = range(max(0, i - HH_WIN), i - HH_GAP)
        hh_i = max(hw, key=lambda z: H[z]); hh = H[hh_i]
        low_so_far = min(L[hh_i + 1:i + 1]) if hh_i + 1 <= i else L[i]
        depth = (hh - low_so_far) / atr
        if not (hh > C[i] and depth <= 2.0):
            continue
        reg = regime_at(T[i])
        if reg not in ("BULL", "RANGE"):                 # ADENDA B: gate como o live
            n_regime_block += 1
            continue
        best = None
        for k in range(max(2, i - FVG_FRESH), i + 1):
            gap_bot, gap_top = H[k - 2], L[k]
            if gap_top <= gap_bot: continue
            if any(L[m] <= gap_bot for m in range(k + 1, i + 1)): continue
            if gap_top >= C[i]: continue
            if (C[i] - gap_top) > DIST_ATR * atr: continue
            if best is None or gap_top > best[1]:
                best = (k, gap_top, gap_bot)
        if best is None:
            continue
        kf, gtop, gbot = best
        # ADENDA A: confluência — FVG 15M tem de sobrepor um FVG 1H fresco
        h1list = fvg1h_fresh(T[i], C[i])
        if not any(not (gtop < b or gbot > t) for b, t in h1list):
            n_no_conf += 1
            continue
        ent = gtop; sl = gbot - 0.1 * atr; risk = ent - sl
        if risk <= 0.05 * atr or risk > 2.5 * atr:
            continue
        if kf in seen_gap:
            continue
        seen_gap.add(kf)
        fill_k = None
        for k2 in range(i + 1, min(S["N"], i + VALID + 1)):
            if L[k2] <= ent:
                fill_k = k2; break
        rec = dict(i=i, kf=kf, ent=round(ent, 2), sl=round(sl, 2), risk=round(risk, 2),
                   half=half(i), fill_k=fill_k, regime=reg)
        if fill_k is not None:
            rec["R"] = outcome(S, fill_k, ent, sl)
            b = (ent - low_so_far) / (hh - low_so_far) * 100 if hh > low_so_far else None
            rec["bpct"] = round(b) if b is not None else None
        setups.append(rec)

    fills = [s for s in setups if s["fill_k"] is not None]
    rs = [s["R"] for s in fills]

    def panel(rlist, cost):
        n = len(rlist); w = sum(1 for r in rlist if r > 0)
        s = sum(r - cost for r in rlist)
        cum = peak = dd = 0.0; stk = mx = 0
        for r in rlist:
            cum += r - cost; peak = max(peak, cum); dd = min(dd, cum - peak)
            stk = stk + 1 if r <= 0 else 0; mx = max(mx, stk)
        return dict(N=n, W=w, WR=round(100 * w / n) if n else None, sumR=round(s, 1),
                    avgR=round(s / n, 2) if n else None, maxDD=round(dd, 1), streak=mx)

    print(f"setups {len(setups)} · fills {len(fills)} · no-fill {len(setups)-len(fills)} · "
          f"bloqueados-regime {n_regime_block} · sem-confluência-1H {n_no_conf}")
    for c in (0.0, 0.2, 0.35):
        print(f"  custo {c}: {panel(rs, c)}")
    bp = sorted([s["bpct"] for s in fills if s.get("bpct") is not None])
    print(f"  bounce% mediano: {bp[len(bp)//2] if bp else None}")
    halves = {}
    for s in fills:
        halves[s["half"]] = round(halves.get(s["half"], 0) + s["R"] - 0.35, 1)
    print(f"  por-semestre (c0.35): {dict(sorted(halves.items()))}")
    jk = {hx: round(sum(s["R"] - 0.35 for s in fills if s["half"] != hx), 1) for hx in sorted(halves)}
    print(f"  jackknife: {jk}")

    nw = nn = 0
    for s in fills:
        for _ in range(300):
            ei = rnd.randint(s["i"] + 1, min(S["N"] - 2, s["i"] + VALID))
            ent = C[ei]; atr = ATR[ei] or 5.0
            sl = s["sl"]; r = ent - sl
            if r <= 0.05 * atr or r > 2.5 * atr: continue
            nn += 1
            if outcome(S, ei, ent, sl) > 0: nw += 1
    null_wr = round(100 * nw / nn, 1) if nn else None
    wr = round(100 * sum(1 for r in rs if r > 0) / len(rs), 1) if rs else None
    print(f"  null: WR {null_wr}% vs estratégia {wr}%")

    (OUT / "results_v2_summary.json").write_text(json.dumps(dict(
        setups=len(setups), fills=len(fills), regime_block=n_regime_block, no_conf=n_no_conf,
        panels={str(c): panel(rs, c) for c in (0.0, 0.2, 0.35)},
        bounce_med=bp[len(bp) // 2] if bp else None, halves=halves, jackknife=jk,
        null_wr=null_wr, wr=wr), indent=1))
    print("gravado results_v2_summary.json")


if __name__ == "__main__":
    main()
