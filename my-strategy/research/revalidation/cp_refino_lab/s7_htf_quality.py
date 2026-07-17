#!/usr/bin/env python3
"""STAGE-7 HTF QUALITY RE-MEDIDA (critérios corretos, Cris 2026-07-17) — corrige os defeitos do s6:
emparelhamento de pivôs 4H por TEMPO DO EXTREMO (não confirmed_at) => retrace sem negativos; facetas que a
pesquisa apontou como qualidade-de-perna, medidas diretamente:
  demand_dist = dist ao swing-low 4H anterior mais próximo (ATR4H); below_all = fundo abaixo de TODOS = ar vazio
  h4_trend_up / hh_intact = últimos 2 highs e 2 lows 4H ascendentes? (correção de uptrend vs impulso de baixa)
  retr_clean = (high_4H - fundo)/(high_4H - low_que_iniciou_a_perna), MESMA perna, sem negativos
Causal (pivôs confirmados <= tp). Distribuições faca-vs-winner (apanha miragem). SEM gate. RAW-only."""
import sys, bisect, statistics as st, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent; REV = HERE.parent; LAB = REV / "a1a2_fundo_lab"
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(REV))
import cp_plot_window as CP
import cp_knife_diag as KD
import gt_pivot_structural_harness as R1
from gt_pivot_structural_harness_r2 import zigzag
T, O, H, L, C, N, ATR = CP.T, CP.O, CP.H, CP.L, CP.C, CP.N, CP.ATR
SLB, sz, BUYS, BT, SELLS, ST, M_FRAC = CP.SLB, CP.sz, CP.BUYS, CP.BT, CP.SELLS, CP.ST, CP.M_FRAC
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%m-%d %H:%M")
DUR4 = 14400
TS4, H4, L4 = R1.TS4, R1.H4, R1.L4

def ext_time(price, conf, arr):
    j = bisect.bisect_right(TS4, conf) - 1
    for k in range(j, max(0, j - 300), -1):
        if abs(arr[k] - price) < 1e-9: return TS4[k]
    return conf
HI6, LO6 = zigzag(6)
# (extreme_time, confirmed_at, price, type)
PIV = sorted([(ext_time(p, c, H4), c, p, "H") for c, p, _ in HI6] +
             [(ext_time(p, c, L4), c, p, "L") for c, p, _ in LO6])

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

def htf_quality(tp, Lp):
    j4 = bisect.bisect_right(TS4, tp - DUR4) - 1
    atr4 = R1.atr4(j4) or 10.0 if j4 >= 0 else 10.0
    seq = [x for x in PIV if x[1] <= tp]                 # pivôs CONFIRMADOS <= tp (causal)
    highs = [(et, p) for et, c, p, t in seq if t == "H"]
    lows = [(et, p) for et, c, p, t in seq if t == "L"]
    if len(highs) < 2 or len(lows) < 2: return None
    hh_intact = highs[-1][1] > highs[-2][1]             # último high mais alto
    hl = lows[-1][1] > lows[-2][1]                       # último low mais alto
    h4_trend_up = hh_intact and hl
    # demand: swing-low 4H anterior mais próximo do fundo
    lowP = [p for _, p in lows]
    demand_dist = round(min(abs(Lp - p) for p in lowP) / atr4, 2)
    below_all = Lp < min(lowP) - 0.05 * atr4            # fundo abaixo de TODOS = ar vazio
    # retrace da MESMA perna: último high (por tempo do extremo) e o low imediatamente ANTES dele
    lastH = highs[-1]; lo_before = [l for l in lows if l[0] < lastH[0]]
    if lo_before and lastH[1] > lo_before[-1][1] and Lp < lastH[1]:
        rng = lastH[1] - lo_before[-1][1]
        retr = round((lastH[1] - Lp) / rng, 2)
    else:
        retr = None                                     # sem perna up->down válida
    return dict(demand=demand_dist, air=below_all, trend_up=h4_trend_up, hh=hh_intact, retr=retr)

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
        q = htf_quality(T[p], L[p])
        if q is None: continue
        rows.append({"p": p, "cls": cls, "gt": is_gt(T[p]), "depth": depth, **q})
    return rows

def main():
    rows = build()
    FA = [r for r in rows if r["cls"] == "KNIFE"]
    WG = [r for r in rows if r["cls"] == "WIN" or r["gt"]]
    GTs = [r for r in rows if r["gt"]]
    GR = [r for r in rows if r["cls"] == "GRAB"]
    print(f"N={len(rows)} · HTF quality re-medida (critérios corretos)\n")
    print("=== TABELA por-trade (facas primeiro) ===")
    print(f"  {'fundo':<12}{'cls':<5}{'demand':>7}{'air':>5}{'trendUp':>8}{'hh':>4}{'retr':>7}{'GT':>3}")
    order = {"KNIFE": 0, "GRAB": 1, "OPEN": 2, "WIN": 3}
    for r in sorted(rows, key=lambda r: (order.get(r["cls"], 9), T[r["p"]])):
        print(f"  {ds(T[r['p']]):<12}{r['cls']:<5}{r['demand']:>7}{'Y' if r['air'] else '.':>5}"
              f"{'UP' if r['trend_up'] else 'dn':>8}{'Y' if r['hh'] else '.':>4}{str(r['retr']):>7}{'GT' if r['gt'] else '':>3}")

    def dist(rs, key): return sorted(r[key] for r in rs if r.get(key) is not None)
    print("\n=== DISTRIBUIÇÕES (faca vs WIN+GT) — sobreposição real? ===")
    for key in ("demand", "retr"):
        print(f"  {key:<8} FACA:  {dist(FA, key)}")
        print(f"  {key:<8} WIN+GT:{dist(WG, key)}")
    print("\n=== booleanos por grupo ===")
    for tag, rs in (("FACA", FA), ("WIN+GT", WG), ("GT", GTs), ("GRAB", GR)):
        n = len(rs) or 1
        air = sum(1 for r in rs if r["air"]); tu = sum(1 for r in rs if r["trend_up"]); hh = sum(1 for r in rs if r["hh"])
        print(f"  {tag:<7} n={len(rs):>2}  ar-vazio={air}/{len(rs)}  h4_trend_up={tu}/{len(rs)}  hh_intact={hh}/{len(rs)}")

    print("\n=== teste de separação (cada critério isolado — mata GT?) ===")
    for name, pred in (("ar-vazio (air)", lambda r: r["air"]),
                       ("NÃO trend_up (correção/down)", lambda r: not r["trend_up"]),
                       ("demand>2ATR (longe de estrutura)", lambda r: r["demand"] > 2.0),
                       ("retr<0.6 (retrace raso)", lambda r: r["retr"] is not None and r["retr"] < 0.6)):
        fk = sum(1 for r in FA if pred(r)); wk = sum(1 for r in WG if pred(r)); gk = sum(1 for r in GTs if pred(r))
        print(f"  {name:<34} facas={fk}/{len(FA)}  WIN+GT={wk}/{len(WG)}  GT-atingidos={gk}/{len(GTs)}")

if __name__ == "__main__":
    main()
