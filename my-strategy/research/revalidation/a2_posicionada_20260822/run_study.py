#!/usr/bin/env python3
"""A2 POSICIONADA — execução do prereg ff2caf2. Limite no topo de FVG 15M causal durante pullback raso;
SL sob o gap; 3R SL-first. RAW canónico. py3.9 stdlib."""
import json
import random
import sys
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "my-strategy/core"))
import raw_reader as RR  # noqa: E402

OUT = Path(__file__).resolve().parent
SEED = 20260822
HH_WIN, HH_GAP = 96, 8
FVG_FRESH, DIST_ATR, VALID, HORIZON = 32, 1.5, 16, 480
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
    """DA-FIX 22/08: a barra do FILL conta — se o low da MESMA barra fura o sl, e LOSS (o preco passou
    pela entry a caminho do stop). Original comecava em k+1: 31% dos fills ficavam vivos indevidamente."""
    tgt = ent + 3 * (ent - sl)
    if S["L"][k] <= sl:
        return -1.0
    for m in range(k + 1, min(S["N"], k + HORIZON)):
        if S["L"][m] <= sl: return -1.0
        if S["H"][m] >= tgt: return 3.0
    return 0.0


def main():
    rnd = random.Random(SEED)
    bars = RR.series_flat(RR.resolve_gz("XAUUSD", "15M"))
    rows = [dict(t=t, o=v[0], h=v[1], l=v[2], c=v[3]) for t, v in sorted(bars.items())]
    S = build(rows)
    T, H, L, C, ATR = S["T"], S["H"], S["L"], S["C"], S["ATR"]
    half = lambda i: dt.datetime.fromtimestamp(T[i], dt.timezone.utc).strftime(
        "%Y-H1" if dt.datetime.fromtimestamp(T[i], dt.timezone.utc).month <= 6 else "%Y-H2")

    # varrimento causal: em cada barra i, setups armáveis
    setups = []
    last_ep_by_gap = {}
    for i in range(200, S["N"]):
        atr = ATR[i] or 5.0
        hw = range(max(0, i - HH_WIN), i - HH_GAP)
        hh_i = max(hw, key=lambda z: H[z]); hh = H[hh_i]
        low_so_far = min(L[hh_i + 1:i + 1]) if hh_i + 1 <= i else L[i]
        depth = (hh - low_so_far) / atr
        if not (hh > C[i] and depth <= 2.0):            # s1: pullback raso EM CURSO
            continue
        # s2: FVG fresco não-preenchido abaixo do preço
        best = None
        for k in range(max(2, i - FVG_FRESH), i + 1):
            gap_bot, gap_top = H[k - 2], L[k]
            if gap_top <= gap_bot:                       # sem FVG
                continue
            if any(L[m] <= gap_bot for m in range(k + 1, i + 1)):   # já preenchido
                continue
            if gap_top >= C[i]:                          # tem de estar ABAIXO do preço
                continue
            if (C[i] - gap_top) > DIST_ATR * atr:        # longe demais
                continue
            if best is None or gap_top > best[1]:        # o mais próximo do preço
                best = (k, gap_top, gap_bot)
        if best is None:
            continue
        kf, gtop, gbot = best
        ent = gtop; sl = gbot - 0.1 * atr; risk = ent - sl
        if risk <= 0.05 * atr or risk > 2.5 * atr:       # s3 guarda de escala
            continue
        ep_key = kf                                       # s6 dedup por FVG
        if ep_key in last_ep_by_gap and i - last_ep_by_gap[ep_key] <= EP_GAP:
            last_ep_by_gap[ep_key] = i
            continue
        if ep_key in last_ep_by_gap:
            continue                                      # FVG já armado uma vez = 1 episódio
        last_ep_by_gap[ep_key] = i
        # s4: fill dentro da validade
        fill_k = None
        for k2 in range(i + 1, min(S["N"], i + VALID + 1)):
            if L[k2] <= ent:
                fill_k = k2
                break
        rec = dict(i=i, kf=kf, ent=round(ent, 2), sl=round(sl, 2), risk=round(risk, 2),
                   half=half(i), fill_k=fill_k)
        if fill_k is not None:
            rec["R"] = outcome(S, fill_k, ent, sl)
            hh_ref = hh
            bounce_at_entry = (ent - low_so_far) / (hh_ref - low_so_far) * 100 if hh_ref > low_so_far else None
            rec["bpct"] = round(bounce_at_entry) if bounce_at_entry is not None else None
        setups.append(rec)

    fills = [s for s in setups if s["fill_k"] is not None]
    nofill = len(setups) - len(fills)
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

    print(f"setups {len(setups)} · fills {len(fills)} ({round(100*len(fills)/max(1,len(setups)))}%) · no-fill {nofill}")
    for c in (0.0, 0.2, 0.35):
        print(f"  custo {c}: {panel(rs, c)}")
    bp = sorted([s["bpct"] for s in fills if s.get("bpct") is not None])
    print(f"  bounce% mediano na ENTRADA: {bp[len(bp)//2] if bp else None} (tese: estruturalmente baixo)")
    halves = {}
    for s in fills:
        halves[s["half"]] = round(halves.get(s["half"], 0) + s["R"] - 0.35, 1)
    print(f"  por-semestre (c0.35): {dict(sorted(halves.items()))}")
    # jackknife
    jk = {}
    for hx in sorted(halves):
        sub = [s["R"] - 0.35 for s in fills if s["half"] != hx]
        jk[hx] = round(sum(sub), 1)
    print(f"  jackknife (sumR c0.35 sem o semestre): {jk}")

    # null: 300 entradas aleatórias/episódio na MESMA janela de validade, mesma regra de SL (fvg do episódio)
    nw = nn = 0
    for s in fills:
        for _ in range(300):
            ei = rnd.randint(s["i"] + 1, min(S["N"] - 2, s["i"] + VALID))
            ent = C[ei]; atr = ATR[ei] or 5.0
            sl = s["sl"]                                  # mesma âncora estrutural (fundo do gap)
            r = ent - sl
            if r <= 0.05 * atr or r > 2.5 * atr:
                continue
            nn += 1
            if outcome(S, ei, ent, sl) > 0: nw += 1
    null_wr = round(100 * nw / nn, 1) if nn else None
    wr = round(100 * sum(1 for r in rs if r > 0) / len(rs), 1) if rs else None
    print(f"  null (300/ep, mesma âncora SL): WR {null_wr}% vs estratégia {wr}%")

    (OUT / "results_summary.json").write_text(json.dumps(dict(
        setups=len(setups), fills=len(fills), nofill=nofill,
        panels={str(c): panel(rs, c) for c in (0.0, 0.2, 0.35)},
        bounce_med=bp[len(bp) // 2] if bp else None, halves=halves, jackknife=jk,
        null_wr=null_wr, wr=wr), indent=1))
    print("gravado results_summary.json")


if __name__ == "__main__":
    main()
