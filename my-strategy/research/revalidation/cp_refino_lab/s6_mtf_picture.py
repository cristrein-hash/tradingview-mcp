#!/usr/bin/env python3
"""STAGE-6 IMAGEM CONVERGENTE MULTI-TIMEFRAME (LEITURA, não gate) — a mesma imagem do flush, agora com a
QUALIDADE DA PERNA HTF (4H/1D). Por fundo Cp, causal (pivots 4H confirmados <= tp): leg 4H (leg_v3), macro
1D (Layer1), idade perna 4H, SUPORTE 4H abaixo (dist ao swing-low 4H mais próximo abaixo; VAZIO=sala p/
cair), posição no range 4H, retrace da perna 4H, extensão abaixo EMA-4H. 10 facas vs winners. SEM veto/score.
Vê se o gestalt separa no HTF o que o 15M não separou. RAW-only."""
import sys, bisect, statistics as st, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent; REV = HERE.parent; LAB = REV / "a1a2_fundo_lab"
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(REV))
import cp_plot_window as CP
import cp_knife_diag as KD
import gt_pivot_structural_harness as R1
from gt_pivot_structural_harness_r2 import zigzag
import leg_v3, leg_refine_harness as LH
T, O, H, L, C, N, ATR = CP.T, CP.O, CP.H, CP.L, CP.C, CP.N, CP.ATR
SLB, sz, BUYS, BT, SELLS, ST, M_FRAC = CP.SLB, CP.sz, CP.BUYS, CP.BT, CP.SELLS, CP.ST, CP.M_FRAC
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%m-%d %H:%M")
DUR4 = 14400

TS4, H4, L4, C4 = R1.TS4, R1.H4, R1.L4, R1.ENG.C4
V3 = leg_v3.build_leg_v3(); LEG4 = {r["t"]: r["leg"] for r in V3}
AGE4 = {r["t"]: LH.BASE_LEG.get(r["t"], {}).get("leg_age") for r in V3}
# EMA20 4H causal
E4 = [None] * len(TS4); af = 2 / 21
for i in range(len(TS4)):
    E4[i] = C4[i] if i == 0 else E4[i - 1] + af * (C4[i] - E4[i - 1])
# pivots 4H (zigzag R=6): highs/lows (confirmed_at, price)
HI6, LO6 = zigzag(6)
HIc = [(c, p) for c, p, _ in HI6]; LOc = [(c, p) for c, p, _ in LO6]
HIct = [x[0] for x in HIc]; LOct = [x[0] for x in LOc]

def j4_of(tp):
    return bisect.bisect_right(TS4, tp - DUR4) - 1        # última 4H fechada antes de tp

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

def htf(tp, Lp):
    j = j4_of(tp)
    if j < 0: return None
    atr4 = R1.atr4(j) or 10.0
    leg = LEG4.get(TS4[j]); mac1d = LH.macro_at(tp); age = AGE4.get(TS4[j])
    # suporte 4H abaixo (swing-low 4H confirmado <= tp, preço < Lp; o mais alto abaixo = 1º suporte)
    m = bisect.bisect_right(LOct, tp)
    below = [p for c, p in LOc[:m] if p < Lp]
    supp = None if not below else round((Lp - max(below)) / atr4, 2)
    # range 4H recente (últimas 60 barras 4H): posição do fundo
    a = max(0, j - 60)
    hh = max(H4[a:j + 1]); ll = min(L4[a:j + 1]); ll = min(ll, Lp)
    pos = round((Lp - ll) / (hh - ll), 2) if hh > ll else 0.0
    # retrace da perna 4H: último high 4H confirmado <= tp e último low antes desse high
    ih = bisect.bisect_right(HIct, tp)
    if ih > 0:
        hc, hp = HIc[ih - 1]
        il = bisect.bisect_right(LOct, hc)
        lp0 = LOc[il - 1][1] if il > 0 else ll
        rng = hp - lp0
        retr = round((hp - Lp) / rng, 2) if rng > 0 else None       # 0=no topo, 1=retrace total, >1 rompeu
    else:
        retr = None
    ext4 = round(((E4[j] or C4[j]) - Lp) / atr4, 2)                  # extensão abaixo EMA-4H
    return dict(leg4=leg, mac1d=mac1d, age4=age, supp4=supp, pos4=pos, retr4=retr, ext4=ext4)

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
        hh = htf(T[p], L[p])
        if hh is None: continue
        rows.append({"p": p, "cls": cls, "gt": is_gt(T[p]), "depth": depth, **hh})
    return rows

def med(rows, key):
    v = [r[key] for r in rows if r.get(key) is not None]
    return round(st.median(v), 2) if v else None

def main():
    rows = build()
    grp = {"FACA": [r for r in rows if r["cls"] == "KNIFE"],
           "WIN": [r for r in rows if r["cls"] == "WIN"],
           "GT": [r for r in rows if r["gt"]],
           "GRAB": [r for r in rows if r["cls"] == "GRAB"]}
    print(f"N={len(rows)} · imagem MTF (4H/1D) ancorada na entrada (causal)\n")
    print("=== MEDIANAS por grupo (o gestalt HTF, se existir) ===")
    print(f"  {'grupo':<6}{'n':>3}{'supp4(VAZ)':>12}{'pos4':>7}{'retr4':>7}{'ext4':>7}{'age4':>6}")
    for g, rs in grp.items():
        if not rs: continue
        nv = sum(1 for r in rs if r["supp4"] is None)
        s4 = med(rs, "supp4"); s4s = f"{s4}({nv}V)" if s4 is not None else f"-({nv}V)"
        print(f"  {g:<6}{len(rs):>3}{s4s:>12}{str(med(rs,'pos4')):>7}{str(med(rs,'retr4')):>7}"
              f"{str(med(rs,'ext4')):>7}{str(med(rs,'age4')):>6}")
    print("\n  leg4h × classe:")
    for leg in ("IMPULSO_DOWN", "PULLBACK_BEAR", "ACUMULACAO", "IMPULSO_UP", "PULLBACK_BULL"):
        d = {g: sum(1 for r in grp[g] if r["leg4"] == leg) for g in grp}
        if sum(d.values()): print(f"    {leg:<14} FACA={d['FACA']} WIN={d['WIN']} GT={d['GT']} GRAB={d['GRAB']}")
    print("\n=== TABELA por-trade (facas primeiro) — age4 incluído ===")
    print(f"  {'fundo':<12}{'cls':<5}{'leg4h':<13}{'age4':>5}{'retr4':>7}{'supp4':>7}{'1D':<6}{'GT':>3}")
    order = {"KNIFE": 0, "GRAB": 1, "OPEN": 2, "WIN": 3}
    for r in sorted(rows, key=lambda r: (order.get(r["cls"], 9), T[r["p"]])):
        s4 = "VAZIO" if r["supp4"] is None else f"{r['supp4']:.1f}"
        print(f"  {ds(T[r['p']]):<12}{r['cls']:<5}{str(r['leg4']):<13}{str(r['age4']):>5}{str(r['retr4']):>7}"
              f"{s4:>7} {str(r['mac1d']):<6}{'GT' if r['gt'] else '':>3}")

    # --- AUDIT age4: sobreposição real? ---
    print("\n=== AUDIT age4 (sobreposição faca vs winner) ===")
    fa = sorted(r["age4"] for r in grp["FACA"] if r["age4"] is not None)
    wg = sorted(r["age4"] for r in (grp["WIN"] + [x for x in grp["GT"] if x["cls"] != "WIN"]) if r["age4"] is not None)
    print(f"  FACA age4:      {fa}")
    print(f"  WIN+GT age4:    {wg}")
    for thr in (40, 50, 60, 70):
        fk = sum(1 for a in fa if a < thr); wk = sum(1 for a in wg if a < thr)
        print(f"  age4<{thr}: facas={fk}/{len(fa)}  winners={wk}/{len(wg)}")
    # --- imagem coerente: "HTF maduro/seguro" = IMPULSO_UP 4H OU perna madura ---
    print("\n=== imagem coerente 'HTF exausto/seguro' (LEITURA, não gate) ===")
    for thr in (50, 60, 70):
        safe = [r for r in rows if r["leg4"] == "IMPULSO_UP" or (r["age4"] or 0) >= thr]
        risk = [r for r in rows if r not in safe]
        def cnt(rs, k): return sum(1 for r in rs if (r["cls"] == k if k != "GT" else r["gt"]))
        print(f"  age4>={thr} ou IMPULSO_UP -> SEGURO: n={len(safe)} FACA={cnt(safe,'KNIFE')} WIN={cnt(safe,'WIN')} GT={cnt(safe,'GT')} GRAB={cnt(safe,'GRAB')}"
              f"  || RISCO: n={len(risk)} FACA={cnt(risk,'KNIFE')} WIN={cnt(risk,'WIN')} GT={cnt(risk,'GT')} GRAB={cnt(risk,'GRAB')}")

if __name__ == "__main__":
    main()
