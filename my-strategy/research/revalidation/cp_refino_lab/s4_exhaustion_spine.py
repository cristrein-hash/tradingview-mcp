#!/usr/bin/env python3
"""STAGE-4 espinha da exaustão — mede o reclaim-que-SEGURA (entry_postgrab, SL abaixo do flush) vs o
baseline (entry_first, 1º-reclaim) no MESMO universo dos 26 fundos Cp, mesmo exit 3R-fixo. Pergunta:
quantas facas corta sem perder WIN/GT? Espinha comportamental da exaustão — leg-independente. NÃO é
feature isolada nem veto: é o próprio evento (o flush exauriu e o reclaim segurou, ou continuou=faca).
entry_postgrab portado VERBATIM de cp_refined.py. Classe via cp_knife_diag. RAW-only, causal."""
import sys, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent; REV = HERE.parent; LAB = REV / "a1a2_fundo_lab"
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(REV))
import cp_plot_window as CP
import cp_knife_diag as KD
T, O, H, L, C, N, ATR = CP.T, CP.O, CP.H, CP.L, CP.C, CP.N, CP.ATR
SLB, is_sl, sz, BUYS, BT, SELLS, ST = CP.SLB, CP.is_sl, CP.sz, CP.BUYS, CP.BT, CP.SELLS, CP.ST
M_FRAC = CP.M_FRAC
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")

# GT (5 janelas Cris, bear2026) — verbatim
GT_WIN = [(1770015600, 1770210000), (1770339600, 1771448400), (1774242000, 1774270800),
          (1781128800, 1781128800), (1782781200, 1782907200)]
GT = []
for a, b in GT_WIN:
    aa = bisect.bisect_left(T, min(a, b) - 12*3600); bb = bisect.bisect_right(T, max(a, b) + 12*3600)
    GT.append(T[min(range(aa, bb), key=lambda k: L[k])])
is_gt = lambda tp: any(abs(tp - g) < 6*3600 for g in GT)

def entry_first(j):     # baseline (verbatim cp_plot_window)
    atr = ATR[j] or 5.0; sl = round(L[j] - 0.1 * atr, 2)
    for k in range(j + M_FRAC, min(N, j + 96)):
        if L[k] <= sl: return None
        if C[k] > H[k - 1] and C[k] > O[k]:
            ent = round(C[k], 2); r = ent - sl
            if r > 0.05 * atr: return {"k": k, "ent": ent, "sl": sl}
    return None

def entry_postgrab(j):  # espinha: higher-low acima do grab + reclaim que segura; SL abaixo do flush (verbatim cp_refined)
    atr0 = ATR[j] or 5.0; lowest = L[j]; hl = False
    for k in range(j + 1, min(N, j + 96)):
        if L[k] < lowest: lowest = L[k]; hl = False
        p = k - M_FRAC
        if p > j and is_sl(p) and L[p] > lowest + 0.05 * atr0: hl = True
        if hl and C[k] > H[k - 1] and C[k] > O[k]:
            ent = round(C[k], 2); sl = round(lowest - 0.1 * atr0, 2); r = ent - sl
            if r > 0.05 * atr0: return {"k": k, "ent": ent, "sl": sl}
    return None

def fundos():
    out = []
    for p in SLB:
        if not (CP.T_LO <= T[p] <= CP.T_HI): continue
        hb = max(range(max(0, p - CP.LEGWIN), p + 1), key=lambda k: H[k]); atr = ATR[p] or 5.0; dur = max(1, p - hb)
        if (H[hb] - L[p]) / atr < CP.LEGMIN or not (L[p] <= min(L[max(0, p - 192):p + 1]) + 1e-9): continue
        if not (sz(BUYS, BT, T[hb], T[p]) / dur >= 0.25 or sz(SELLS, ST, T[hb], T[p]) >= 180): continue
        out.append(p)
    return out

def run(entry_fn):
    rows = []
    for p in fundos():
        e = entry_fn(p)
        if not e: continue
        tgt = round(e["ent"] + 3 * (e["ent"] - e["sl"]), 2)
        cls, depth = KD.classify(int(T[e["k"]]), e["ent"], e["sl"], tgt)
        R = 3.0 if cls == "WIN" else (-1.0 if cls == "KNIFE" else (3.0 if cls == "GRAB" else None))
        rows.append({"p": p, "etime": int(T[e["k"]]), "cls": cls, "depth": depth, "gt": is_gt(T[p]),
                     "R": R, "ent": e["ent"], "sl": e["sl"]})
    return rows

def panel(name, rows):
    n = len(rows)
    kn = [r for r in rows if r["cls"] == "KNIFE"]; win = [r for r in rows if r["cls"] == "WIN"]
    grab = [r for r in rows if r["cls"] == "GRAB"]; opn = [r for r in rows if r["cls"] == "OPEN"]
    gts = sorted({round(T[r["p"]]) for r in rows if r["gt"]})
    # P&L 3R-fixo: WIN/GRAB=+3, KNIFE=-1, OPEN=neutro(ignora)
    seq = [(3.0 if r["cls"] in ("WIN", "GRAB") else -1.0) for r in rows if r["cls"] != "OPEN"]
    net = sum(seq); w = sum(1 for x in seq if x > 0)
    eq = pk = dd = strk = mx = 0
    for x in seq:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk); strk = strk + 1 if x < 0 else 0; mx = min(mx, -strk)
    wr = 100 * w / max(1, len(seq))
    ngt = sum(1 for r in rows if r["gt"])
    print(f"  {name:<26} N={n:>2} facas={len(kn):>2} WIN={len(win)} GRAB={len(grab)} OPEN={len(opn)} "
          f"| decid N={len(seq)} WR{wr:>3.0f}% NET{net:>+5.1f}R DD{dd:>+5.1f} stk{mx:>3} | GT {ngt}/5")
    return rows

def main():
    print(f"universo: {len(fundos())} fundos Cp (mesmos gates do baseline)\n")
    b = panel("BASELINE (entry_first)", run(entry_first))
    pg = panel("ESPINHA (entry_postgrab)", run(entry_postgrab))
    # o que aconteceu a CADA faca do baseline sob a espinha
    print("\n=== o que a espinha faz a cada FACA do baseline ===")
    bmap = {r["p"]: r for r in b}; pmap = {r["p"]: r for r in pg}
    for p, r in sorted(bmap.items(), key=lambda kv: T[kv[0]]):
        if r["cls"] != "KNIFE": continue
        pr = pmap.get(p)
        if pr is None: verdict = "NÃO dispara (reclaim nunca segura) = faca EVITADA"
        elif pr["cls"] == "KNIFE": verdict = f"ainda faca (fura −{pr['depth']:.1f}R) = SL profundo não aguenta"
        else: verdict = f"vira {pr['cls']}"
        print(f"  fundo {ds(T[p])}  baseline faca −{r['depth']:.1f}R  ->  {verdict}")
    # e os WIN/GT do baseline sobrevivem?
    print("\n=== WIN/GT do baseline sob a espinha (não pode perder) ===")
    for p, r in sorted(bmap.items(), key=lambda kv: T[kv[0]]):
        if not (r["cls"] == "WIN" or r["gt"]): continue
        pr = pmap.get(p); tag = "GT" if r["gt"] else "WIN"
        if pr is None: verdict = "PERDIDO (espinha não dispara)"
        else: verdict = f"mantém ({pr['cls']})"
        print(f"  [{tag}] fundo {ds(T[p])}  baseline {r['cls']}  ->  {verdict}")

if __name__ == "__main__":
    main()
