#!/usr/bin/env python3
"""FASE-DO-CICLO classifier: DISTRIBUTION-TOP (Fase C) detector -> CUT.

Ideia (causal, sequencial, snapshot-livre):
  Na barra de decisao j, olhar SO barras <= j numa janela W (48-96 barras).
  Fase C (DISTRIBUICAO-TOPO) = markup exausto:
    (a) preco a pairar perto do TETO  -> fracao de closes no terco superior do range da janela alta
    (b) EQH-like: varios toques do MESMO teto (highs dentro de tol*ATR do maximo da janela)
    (c) DESACELERACAO: os higher-highs (swings CAUSAIS) a encolher / sem novo HH recente
  Fase D (BEAR-ATIVO) = lower-highs / BOS-down nos swings causais.
  CUT = C uniao D. KEEP = resto.

CAUSAL: todas as features usam apenas barras com indice <= j e swings com conf_bar <= j
(via causal_swings_upto). Nenhuma usa e['out'] nem os n-alvo. Thresholds escolhidos por
PERCENTIL da propria feature (estrutura), nao por rotulo.
"""
import sys, itertools
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score,causal_swings_upto

# ---------- CAUSAL feature extractor ----------
def feats(e, W=96):
    j = e["j"]
    lo_i = max(0, j-W+1)
    win_hi = list(range(lo_i, j+1))
    hh = max(HI[k] for k in win_hi)
    ll = min(LO[k] for k in win_hi)
    rng = max(hh-ll, 1e-9)
    a = ATR[j] or 5.0
    # (a) fracao de closes no terco superior do range da janela
    thr_top = ll + (2.0/3.0)*rng
    frac_top = sum(1 for k in win_hi if CL[k] >= thr_top)/len(win_hi)
    # (b) EQH-like: toques do teto (highs dentro de tol*ATR do maximo)
    tol = 0.30*a
    ceil_touch = sum(1 for k in win_hi if HI[k] >= hh - tol)
    # posicao do close atual dentro do range (0=fundo,1=topo)
    pos = (CL[j]-ll)/rng
    # ---- swings causais (confirmados <= j) ----
    sw = causal_swings_upto(j)
    Hs = [(idx,pr,ci) for tp,idx,pr,ci in sw if tp=="H"]
    Ls = [(idx,pr,ci) for tp,idx,pr,ci in sw if tp=="L"]
    # (c) DESACELERACAO dos higher-highs: incrementos entre swing-highs a encolher
    decel = 0.0; hh_shrink = 0
    if len(Hs) >= 3:
        p3,p2,p1 = Hs[-3][1],Hs[-2][1],Hs[-1][1]
        inc_old = p2-p3; inc_new = p1-p2
        # normaliza por ATR
        inc_old_a = inc_old/a; inc_new_a = inc_new/a
        # desaceleracao: novo push menor que o anterior (mas ainda a subir = topo a abrandar)
        if inc_new_a < inc_old_a: decel = (inc_old_a - inc_new_a)
        if inc_new < inc_old: hh_shrink = 1
    # barras desde o ultimo swing-high confirmado (staleness do topo)
    bars_since_hh = j - Hs[-1][0] if Hs else 999
    # (D) BEAR: ultimo swing-high < swing-high anterior (lower-high) => estrutura de baixa
    lower_high = 0
    if len(Hs) >= 2 and Hs[-1][1] < Hs[-2][1]: lower_high = 1
    lower_low = 0
    if len(Ls) >= 2 and Ls[-1][1] < Ls[-2][1]: lower_low = 1
    # ultimo pivo confirmado foi H (topo) e ainda nao houve L novo = distribuicao/rollover
    last_is_H = 1 if (sw and sw[-1][0]=="H") else 0
    return dict(frac_top=frac_top, ceil_touch=ceil_touch, pos=pos, decel=decel,
                hh_shrink=hh_shrink, bars_since_hh=bars_since_hh,
                lower_high=lower_high, lower_low=lower_low, last_is_H=last_is_H)

def phase_cut(e, W, frac_thr, touch_thr, use_decel, use_bear):
    """True = CUT (Fase C ou D)."""
    f = feats(e, W)
    # ---- Fase C: distribuicao-topo ----
    isC = (f["frac_top"] >= frac_thr and f["ceil_touch"] >= touch_thr and f["pos"] >= 0.5)
    if use_decel:
        isC = isC and (f["hh_shrink"] == 1)
    # ---- Fase D: bear ativo ----
    isD = False
    if use_bear:
        isD = (f["lower_high"] == 1 and f["lower_low"] == 1)
    return isC or isD

def run_variant(W, frac_thr, touch_thr, use_decel, use_bear):
    keep = [e["n"] for e in ENTRIES if not phase_cut(e, W, frac_thr, touch_thr, use_decel, use_bear)]
    sc = score(keep)
    return keep, sc

# ========================================================================
# PIVOT EMPIRICO (diagnostico honesto):
# A hipotese Fase-C "preco a pairar perto do topo" NAO separa — MARKUP ATIVO
# (Fase A, WINNER) tambem senta perto do topo: frac_top/pos sao MAIORES nos
# winners (0.365/0.533) que nos losers (0.281/0.449). Logo o detector de
# terco-superior corta winners. O separador REAL e a Fase D (BEAR ATIVO):
# lower_low mediana = 1.0 nos losers vs 0.0 nos winners.
# CLASSIFICADOR FINAL = Fase D: estrutura de baixa causal (lower_low nos swings
# confirmados <=j) E preco NAO em markup (pos < thr no range da janela). CAUSAL.
# ========================================================================
def phaseD_cut(e, W, pos_thr):
    """True = CUT: Fase D (BEAR ATIVO) — lower-low causal + preco fora do markup."""
    f = feats(e, W)
    return f["lower_low"] == 1 and f["pos"] < pos_thr

def run_phaseD(W, pos_thr):
    keep = [e["n"] for e in ENTRIES if not phaseD_cut(e, W, pos_thr)]
    return keep, score(keep)

# ---------- feature distribution (for percentile-based thresholds; NO labels) ----------
if __name__ == "__main__":
    import statistics as st
    # inspect feature distribution to pick structural thresholds
    for W in (96,):
        fr = sorted(feats(e,W)["frac_top"] for e in ENTRIES)
        ct = sorted(feats(e,W)["ceil_touch"] for e in ENTRIES)
        print(f"[W={W}] frac_top quartiles", [round(fr[int(q*len(fr))],2) for q in (.25,.5,.75,.9)])
        print(f"[W={W}] ceil_touch quartiles", [ct[int(q*len(ct))] for q in (.25,.5,.75,.9)])

    print("\n=== VARIANT SWEEP (thresholds by feature structure, no labels) ===")
    best = None
    grid = []
    for W in (48, 72, 96):
        for frac_thr in (0.45, 0.55, 0.65):
            for touch_thr in (3, 5, 8):
                for use_decel in (False, True):
                    for use_bear in (False, True):
                        keep, sc = run_variant(W, frac_thr, touch_thr, use_decel, use_bear)
                        y25w,y25n = map(int, sc["y2025"].split("/"))
                        y26w,y26n = map(int, sc["y2026"].split("/"))
                        both_pos = (y25n>0 and y25w/y25n > 0.5) and (y26n>0 and y26w/y26n > 0.5)
                        ok = (sc["N_kept"]>=20 and sc["poison_ratio"]<0.9 and sc["poison_ratio"]>0
                              and both_pos and sc["losers_cut"]>0)
                        rec = dict(W=W,frac=frac_thr,touch=touch_thr,decel=use_decel,bear=use_bear,
                                   N=sc["N_kept"],hit=sc["hit3r_kept"],poison=sc["poison_ratio"],
                                   wc=sc["winners_cut"],lc=sc["losers_cut"],
                                   y25=sc["y2025"],y26=sc["y2026"],ok=ok)
                        grid.append(rec)
                        if ok:
                            key=(sc["hit3r_kept"], -sc["poison_ratio"], sc["N_kept"])
                            if best is None or key>best[0]:
                                best=(key, rec, keep, sc)
    # show qualifying variants sorted by hit
    q = [r for r in grid if r["ok"]]
    q.sort(key=lambda r:(-r["hit"], r["poison"], -r["N"]))
    print(f"\n{len(q)} qualifying variants (N>=20, 0<poison<0.9, both years >50%):")
    for r in q[:15]:
        print(f"  W{r['W']} frac{r['frac']} touch{r['touch']} decel{int(r['decel'])} bear{int(r['bear'])} "
              f"| N{r['N']} hit{r['hit']} poison{r['poison']} cut(w{r['wc']}/l{r['lc']}) "
              f"y25 {r['y25']} y26 {r['y26']}")

    # ---- PIVOT: Fase-D bear detector sweep (the real edge) ----
    print("\n=== FASE-D (BEAR) SWEEP — o separador real ===")
    Dgrid=[]
    for W in (72, 96, 120):
        for pos_thr in (0.40, 0.45, 0.50, 0.55):
            keep, sc = run_phaseD(W, pos_thr)
            y25w,y25n = map(int, sc["y2025"].split("/")); y26w,y26n = map(int, sc["y2026"].split("/"))
            bp = (y25n and y25w/y25n>0.5) and (y26n and y26w/y26n>0.5)
            ok = (sc["N_kept"]>=20 and 0<sc["poison_ratio"]<0.9 and bp)
            Dgrid.append((sc["hit3r_kept"], sc["poison_ratio"], sc["N_kept"], W, pos_thr, keep, sc, ok))
    for hit,pois,Nk,W,pt,keep,sc,ok in sorted(Dgrid, key=lambda r:(-r[0], r[1])):
        print(f"  {'OK' if ok else '  '} W{W} pos<{pt} | N{Nk} hit{hit:.3f} pois{pois} "
              f"cut(w{sc['winners_cut']}/l{sc['losers_cut']}) y25 {sc['y2025']} y26 {sc['y2026']}")
    bestD = max((r for r in Dgrid if r[7]), key=lambda r:(r[0], -r[1], r[2]))
    _,_,_,W,pt,keep,sc,_ = bestD
    best = (None, dict(W=W, pos_thr=pt), keep, sc)

    if best:
        _,rec,keep,sc = best
        print("\n=== BEST VARIANT (Fase-D bear detector) ===")
        print(rec)
        print(sc)
        # ---- POST-HOC sanity check (NOT used in logic) ----
        loser_targets = [21,23,31,49,50,55,56,57,59,60,65,66,67,68,69,79,83,84,85,89,93,94]
        winner_keys   = [1,11,12,13,14,26,28,29,30,44,45,61,62,63,71,72,73,74,75,82,95,96]
        keepset=set(keep)
        lt_cut = [n for n in loser_targets if n not in keepset]
        wk_kept= [n for n in winner_keys if n in keepset]
        print(f"\nSANITY (post-hoc): loser-targets CUT {len(lt_cut)}/{len(loser_targets)} -> {sorted(lt_cut)}")
        print(f"SANITY (post-hoc): winner-keys KEPT {len(wk_kept)}/{len(winner_keys)} -> {sorted(wk_kept)}")
        print("KEEP_NS =", sorted(keep))
    else:
        print("\nNO qualifying variant. Reporting honestly.")
