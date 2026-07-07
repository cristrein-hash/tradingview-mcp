#!/usr/bin/env python3
"""FASE-D DETECTOR (BEAR-ACTIVO) -> CUT, preservando INICIACAO intra-bear (Fase B).

Abordagem CAUSAL (so barras indice<=j via causal_swings_upto(j)):
  BEAR-ACTIVO := sequencia de LOWER-HIGHS (ultimos nlh H-swings confirmados descendentes)
                 E markdown em curso (BOS-down: CL[j] < ultimo L-swing confirmado, OU lower-lows).
  INICIACAO intra-bear (Fase B, MANTER apesar de bear) := CHoCH-up FRESCO
                 (algum close, em [j-choch_lb, j], acima do ultimo LOWER-HIGH confirmado).
  KEEP = (NAO bear-activo)  OU  (bear-activo E CHoCH-up fresco).
  CUT  = bear-activo E sem CHoCH-up fresco.

REGRAS: nenhuma feature usa e['out'] nem os n-alvo. Swings via causal_swings_upto (conf_bar<=j).
"""
import sys; sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score,causal_swings_upto

def classify(j, nlh=2, choch_lb=48, require_bos=True, require_ll=False):
    """Devolve (bear_active, choch_up). CAUSAL: so barras/ swings <= j."""
    sw = causal_swings_upto(j)
    Hs = [(idx,pr,ci) for tp,idx,pr,ci in sw if tp=="H"]
    Ls = [(idx,pr,ci) for tp,idx,pr,ci in sw if tp=="L"]
    if len(Hs) < nlh or len(Ls) < 1:
        return (False, False)  # sem estrutura suficiente -> nao bear
    lastH = Hs[-nlh:]
    lower_highs = all(lastH[k][1] < lastH[k-1][1] for k in range(1, len(lastH)))
    last_L_price = Ls[-1][1]
    bos_down = CL[j] < last_L_price
    lower_lows = (len(Ls) >= 2 and Ls[-1][1] < Ls[-2][1])
    markdown = ( (bos_down if require_bos else False) or lower_lows )
    if require_bos and require_ll:
        markdown = bos_down and lower_lows
    bear_active = lower_highs and markdown
    # CHoCH-up fresco: close acima do ULTIMO lower-high confirmado, dentro de choch_lb barras
    last_lh_price = Hs[-1][1]
    choch_up = False
    lo = max(0, j - choch_lb)
    for k in range(lo, j+1):
        if CL[k] > last_lh_price:
            choch_up = True; break
    return (bear_active, choch_up)

def keep_set(**kw):
    keep=set()
    for e in ENTRIES:
        bear, choch = classify(e["j"], **kw)
        if (not bear) or (bear and choch):
            keep.add(e["n"])
    return keep

LOSER_TARGETS = {21,23,31,49,50,55,56,57,59,60,65,66,67,68,69,79,83,84,85,89,93,94}
WINNER_KEYS   = {1,11,12,13,14,26,28,29,30,44,45,61,62,63,71,72,73,74,75,82,95,96}

def sanity(keep):
    cut = set(e["n"] for e in ENTRIES) - keep
    lt_cut = LOSER_TARGETS & cut
    wk_keep = WINNER_KEYS & keep
    return {
        "loser_targets_cut": len(lt_cut), "of": len(LOSER_TARGETS),
        "winner_keys_kept": len(wk_keep), "of_w": len(WINNER_KEYS),
        "lt_cut_ns": sorted(lt_cut), "wk_lost_ns": sorted(WINNER_KEYS - keep),
    }

VARIANTS = [
    ("V1 nlh2 lb48 bos",            dict(nlh=2, choch_lb=48, require_bos=True,  require_ll=False)),
    ("V2 nlh2 lb32 bos",            dict(nlh=2, choch_lb=32, require_bos=True,  require_ll=False)),
    ("V3 nlh2 lb64 bos",            dict(nlh=2, choch_lb=64, require_bos=True,  require_ll=False)),
    ("V4 nlh3 lb48 bos",            dict(nlh=3, choch_lb=48, require_bos=True,  require_ll=False)),
    ("V5 nlh2 lb48 bos|ll",         dict(nlh=2, choch_lb=48, require_bos=True,  require_ll=False)),  # dup control
    ("V6 nlh2 lb48 bos&ll",         dict(nlh=2, choch_lb=48, require_bos=True,  require_ll=True)),
    ("V7 nlh2 lb48 ll-only",        dict(nlh=2, choch_lb=48, require_bos=False, require_ll=False)),
    ("V8 nlh3 lb32 bos",           dict(nlh=3, choch_lb=32, require_bos=True,  require_ll=False)),
    ("V9 nlh2 lb24 bos",           dict(nlh=2, choch_lb=24, require_bos=True,  require_ll=False)),
    ("V10 nlh3 lb64 bos",          dict(nlh=3, choch_lb=64, require_bos=True,  require_ll=False)),
]

if __name__=="__main__":
    print(f"BASE: {score([e['n'] for e in ENTRIES])['base']}")
    print("="*118)
    best=None
    for name,kw in VARIANTS:
        keep = keep_set(**kw)
        sc = score(keep)
        sn = sanity(keep)
        y25=sc['y2025']; y26=sc['y2026']
        def pos(s):
            w,n=s.split('/'); return int(n)>0 and int(w)*2>int(n) # winners>losers -> >50%? use net R proxy: >50%
        # ambos anos POSITIVOS = hit-3R>1/4 (>25% breakeven a 3R). Report raw; flag>25%.
        def be(s):
            w,n=s.split('/'); w=int(w);n=int(n); return n>0 and w/n>0.25
        both_pos = be(y25) and be(y26)
        print(f"{name:26s} N={sc['N_kept']:3d} hit3r={sc['hit3r_kept']:.3f} "
              f"pois={sc['poison_ratio']:.2f} wc={sc['winners_cut']:2d} lc={sc['losers_cut']:2d} "
              f"y25={y25:7s} y26={y26:7s} {'BOTH+' if both_pos else '     '} "
              f"| LT_cut={sn['loser_targets_cut']:2d}/{sn['of']} WK_kept={sn['winner_keys_kept']:2d}/{sn['of_w']}")
        # criterio de escolha: hit3r alto & poison<0.9 & ambos anos+ & N>=20
        ok = sc['poison_ratio']<0.9 and both_pos and sc['N_kept']>=20 and sc['losers_cut']>0
        cand=(sc['hit3r_kept'], sc['losers_cut'], name, kw, sc, sn, keep)
        if ok and (best is None or cand[0]>best[0]):
            best=cand
    print("="*118)
    if best:
        _,_,name,kw,sc,sn,keep = best
        print(f"BEST: {name}  {kw}")
        print("  score:", sc)
        print("  sanity:", sn)
    else:
        print("NENHUMA variante passa o gate (poison<0.9 & ambos anos+ & N>=20 & losers_cut>0).")
