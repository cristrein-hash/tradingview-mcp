#!/usr/bin/env python3
"""STAGE-5 IMAGEM CONVERGENTE (LEITURA, não gate) — por fundo Cp, ancorada no ponto de decisão (entrada
entry_first), monta as facetas do flush como UM todo e põe as 10 facas lado a lado com WIN/GT/GRAB para
ver se emerge um GESTALT. TUDO causal (<= barra de entrada k). SEM mecanização, SEM veto/score. RAW-only.
Facetas: inclinação da descida · wick de rejeição · extensão abaixo EMA20 · suporte real abaixo (VAZIO=sala)
· absorção pós-mínimo [p->k] · força do reclaim. Grupos + medianas + tabela por-trade."""
import sys, bisect, statistics as st, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent; REV = HERE.parent; LAB = REV / "a1a2_fundo_lab"
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(REV))
import cp_plot_window as CP
import cp_knife_diag as KD
T, O, H, L, C, N, ATR = CP.T, CP.O, CP.H, CP.L, CP.C, CP.N, CP.ATR
SLB, sz, BUYS, BT, SELLS, ST, M_FRAC = CP.SLB, CP.sz, CP.BUYS, CP.BT, CP.SELLS, CP.ST, CP.M_FRAC
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%m-%d %H:%M")

# EMA20 causal (15M)
EMA = [None] * N; a = 2 / 21
for i in range(N):
    EMA[i] = C[i] if i == 0 or EMA[i - 1] is None else EMA[i - 1] + a * (C[i] - EMA[i - 1])

GT_WIN = [(1770015600, 1770210000), (1770339600, 1771448400), (1774242000, 1774270800),
          (1781128800, 1781128800), (1782781200, 1782907200)]
GT = []
for aa, bb in GT_WIN:
    lo = bisect.bisect_left(T, min(aa, bb) - 12*3600); hi = bisect.bisect_right(T, max(aa, bb) + 12*3600)
    GT.append(T[min(range(lo, hi), key=lambda k: L[k])])
is_gt = lambda tp: any(abs(tp - g) < 6*3600 for g in GT)

def entry_first(j):
    atr = ATR[j] or 5.0; sl = round(L[j] - 0.1 * atr, 2)
    for k in range(j + M_FRAC, min(N, j + 96)):
        if L[k] <= sl: return None
        if C[k] > H[k - 1] and C[k] > O[k]:
            ent = round(C[k], 2)
            if ent - sl > 0.05 * atr: return {"k": k, "ent": ent, "sl": sl}
    return None

def supp_below(p, atr):
    """swing-low histórico mais próximo ABAIXO do mínimo (o 1º suporte se cair mais). VAZIO=nada abaixo."""
    best = None
    for q in SLB:
        if q >= p: break
        if L[q] < L[p] and (best is None or L[q] > L[best]): best = q
    return None if best is None else round((L[p] - L[best]) / atr, 2)

def facets(p, k):
    atr = ATR[p] or 5.0
    hb = max(range(max(0, p - CP.LEGWIN), p + 1), key=lambda i: H[i]); dur = max(1, p - hb)
    slope = round((H[hb] - L[p]) / atr / dur, 2)                       # ATR/barra na descida
    wick = round((min(O[p], C[p]) - L[p]) / atr, 2)                    # rejeição no fundo
    ext = round(((EMA[p] or C[p]) - L[p]) / atr, 2)                    # extensão abaixo EMA20
    sb = supp_below(p, atr)                                            # suporte real abaixo
    absorb = sz(BUYS, BT, T[p], T[k]) - sz(SELLS, ST, T[p], T[k])      # absorção pós-mínimo [p->k]
    reclaim = round((C[k] - L[p]) / atr, 2)                            # força do reclaim
    return dict(slope=slope, wick=wick, ext=ext, sb=sb, absorb=absorb, reclaim=reclaim, dur=dur)

def build():
    rows = []
    for p in SLB:
        if not (CP.T_LO <= T[p] <= CP.T_HI): continue
        hb = max(range(max(0, p - CP.LEGWIN), p + 1), key=lambda i: H[i]); atr = ATR[p] or 5.0; dur = max(1, p - hb)
        if (H[hb] - L[p]) / atr < CP.LEGMIN or not (L[p] <= min(L[max(0, p - 192):p + 1]) + 1e-9): continue
        if not (sz(BUYS, BT, T[hb], T[p]) / dur >= 0.25 or sz(SELLS, ST, T[hb], T[p]) >= 180): continue
        e = entry_first(p)
        if not e: continue
        tgt = round(e["ent"] + 3 * (e["ent"] - e["sl"]), 2)
        cls, depth = KD.classify(int(T[e["k"]]), e["ent"], e["sl"], tgt)
        f = facets(p, e["k"])
        rows.append({"p": p, "k": e["k"], "cls": cls, "gt": is_gt(T[p]), "depth": depth, **f})
    return rows

def med(rows, key):
    vals = [r[key] for r in rows if r[key] is not None]
    return round(st.median(vals), 2) if vals else None

def main():
    rows = build()
    grp = {"FACA": [r for r in rows if r["cls"] == "KNIFE"],
           "WIN": [r for r in rows if r["cls"] == "WIN"],
           "GT": [r for r in rows if r["gt"]],
           "GRAB": [r for r in rows if r["cls"] == "GRAB"]}
    print(f"N={len(rows)} · imagem convergente ancorada na entrada (causal)\n")
    print("=== MEDIANAS por grupo (o gestalt, se existir) ===")
    print(f"  {'grupo':<6}{'n':>3} {'slope':>7}{'wick':>6}{'ext':>6}{'supB':>7}{'absorb':>8}{'reclaim':>9}")
    for g, rs in grp.items():
        if not rs: continue
        sbv = [r['sb'] for r in rs if r['sb'] is not None]; nvaz = sum(1 for r in rs if r['sb'] is None)
        sbm = f"{st.median(sbv):.1f}" if sbv else "-"
        print(f"  {g:<6}{len(rs):>3} {med(rs,'slope'):>7}{med(rs,'wick'):>6}{med(rs,'ext'):>6}"
              f"{sbm:>5}({nvaz}V){med(rs,'absorb'):>7}{med(rs,'reclaim'):>9}")
    print("\n=== TABELA por-trade (facas primeiro) ===")
    hdr = f"  {'fundo':<12}{'cls':<5}{'slope':>6}{'wick':>6}{'ext':>6}{'supB':>7}{'absorb':>7}{'reclaim':>8}{'GT':>3}"
    print(hdr)
    order = {"KNIFE": 0, "GRAB": 1, "OPEN": 2, "WIN": 3}
    for r in sorted(rows, key=lambda r: (order.get(r["cls"], 9), T[r["p"]])):
        sb = "VAZIO" if r["sb"] is None else f"{r['sb']:.1f}"
        print(f"  {ds(T[r['p']]):<12}{r['cls']:<5}{r['slope']:>6}{r['wick']:>6}{r['ext']:>6}{sb:>7}"
              f"{r['absorb']:>7}{r['reclaim']:>8}{'GT' if r['gt'] else '':>3}")

if __name__ == "__main__":
    main()
