#!/usr/bin/env python3
"""FAMILIA FRACTAL HTF — FASE 4H (2026-07-07).
Constroi a fase de estrutura de mercado da escala 4H no momento de cada entry XAU 15M,
usando SO barras 4H FECHADAS antes do entry (htf_closed_upto -> end<=t; barra corrente EXCLUIDA).

Features (ESCALA RELATIVA A PROPRIA PERNA, nao direcao absoluta = calendario):
  h4_trend     : score continuo de tendencia 4H = tanh(EMA-slope/ATR) combinado com sequencia HH-HL / LH-LL robusta.
  h4_leg_age   : barras 4H desde a ORIGEM da perna corrente (ultimo pivo confirmado) / normalizado.
  h4_pos_in_leg: posicao do close corrente dentro do range da perna corrente (0=origem,1=extremo). RELATIVO A PERNA.
  h4_topping   : EQH/overlap 4H = compressao/igualdade de topos recentes (distribuicao/topping continuo 0..1).

Anti-lookahead PROVADO: para cada entry a ultima barra 4H usada tem end<=t (impresso no fim).
"""
import sys, json
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
import numpy as np
from mtf_kit import HTF, htf_closed_upto, htf_swings, ENTRIES, PHASE, oof_mining_null

def ema(vals, span):
    if not vals: return []
    a = 2.0/(span+1); out=[vals[0]]
    for v in vals[1:]: out.append(a*v+(1-a)*out[-1])
    return out

def atr_last(bars, k=14):
    H=[b["h"] for b in bars]; L=[b["l"] for b in bars]; C=[b["c"] for b in bars]
    tr=[]
    for i in range(len(bars)):
        if i==0: tr.append(H[i]-L[i])
        else: tr.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
    kk=min(k,len(tr));
    return sum(tr[-kk:])/kk if kk else 1.0

def h4_features(t):
    """features causais 4H no instante t (barras fechadas end<=t)."""
    bars = htf_closed_upto("4H", t)
    n = len(bars)
    if n < 20:
        return None, None  # sem contexto suficiente
    H=[b["h"] for b in bars]; L=[b["l"] for b in bars]; C=[b["c"] for b in bars]
    a = atr_last(bars, 14) or 1.0

    # --- EMA slope 4H (normalizado por ATR) ---
    e21 = ema(C, 21)
    look = min(6, n-1)
    ema_slope = (e21[-1]-e21[-1-look]) / (a*look)   # ATR por barra

    # --- sequencia de swings HH-HL / LH-LL robusta (score -1..1) ---
    piv,_,_,_,_ = htf_swings(bars, r=2.0)
    seq_score = 0.0
    if len(piv) >= 4:
        highs = [p[2] for p in piv if p[0]=="H"][-2:]
        lows  = [p[2] for p in piv if p[0]=="L"][-2:]
        s = 0
        if len(highs)==2: s += 1 if highs[-1] > highs[-2] else -1
        if len(lows)==2:  s += 1 if lows[-1]  > lows[-2]  else -1
        seq_score = s/2.0
    elif len(piv) >= 2:
        # com poucos pivos usa direcao do ultimo swing
        seq_score = 0.5 if piv[-1][0]=="H" else -0.5

    # trend continuo: combina slope (tanh) + sequencia. media -> variancia garantida.
    h4_trend = float(0.5*np.tanh(ema_slope) + 0.5*seq_score)

    # --- perna corrente: ultimo pivo confirmado = origem ---
    if piv:
        tp, pidx, pprice = piv[-1][0], piv[-1][1], piv[-1][2]
    else:
        # sem pivo: perna = toda a janela; origem = primeiro bar
        tp, pidx, pprice = ("L" if C[-1]>=C[0] else "H"), 0, (L[0] if C[-1]>=C[0] else H[0])

    leg_age_bars = (n-1) - pidx
    h4_leg_age = float(np.log1p(leg_age_bars))   # comprime cauda; variancia preservada

    # posicao no range da perna (RELATIVO). up-leg se origem foi um Low.
    seg = slice(pidx, n)
    seg_hi = max(H[pidx:]); seg_lo = min(L[pidx:])
    rng = seg_hi - seg_lo
    if rng < 1e-9:
        h4_pos_in_leg = 0.5
    elif tp == "L":   # up-leg desde a origem-low
        h4_pos_in_leg = float((C[-1]-seg_lo)/rng)
    else:             # down-leg desde a origem-high
        h4_pos_in_leg = float((seg_hi-C[-1])/rng)   # 0=perto do topo(origem),1=fundo. progresso da perna

    # --- topping/EQH: compressao & igualdade de topos nas ultimas K barras ---
    K = min(8, n)
    recentH = H[-K:]; recentL = L[-K:]; recentC = C[-K:]
    topH = max(recentH)
    # quantos topos dentro de 0.5 ATR do topo local -> EQH cluster
    eqh = sum(1 for h in recentH if topH-h <= 0.5*a)/K
    # compressao: media dos ranges recentes vs ATR (baixa = comprimido = topping/consolidacao)
    avg_rng = np.mean([recentH[k]-recentL[k] for k in range(K)])/a
    compress = float(np.clip(1.0 - avg_rng, 0, 1))   # 1=muito comprimido
    # progresso vertical parado: close perto do topo mas sem extensao
    near_top = float(np.clip((recentC[-1]-min(recentL))/(topH-min(recentL)+1e-9),0,1))
    h4_topping = float(0.5*eqh + 0.3*compress + 0.2*near_top)

    feats = {
        "h4_trend": round(h4_trend,4),
        "h4_leg_age": round(h4_leg_age,4),
        "h4_pos_in_leg": round(h4_pos_in_leg,4),
        "h4_topping": round(h4_topping,4),
    }
    return feats, bars[-1]["end"]

# ---- computa para todas as ENTRIES ----
FEAT_NAMES = ["h4_trend","h4_leg_age","h4_pos_in_leg","h4_topping"]
rows=[]; last_ends=[]; ok_causal=True
for e in ENTRIES:
    f, lend = h4_features(e["t"])
    if f is None:
        # fallback neutro (raro; so se <20 barras). marca.
        f = {k:0.0 for k in FEAT_NAMES}; lend = None
    if lend is not None and lend > e["t"]:
        ok_causal=False
    row = {"n": e["n"]}; row.update(f)
    rows.append(row)
    last_ends.append((e["n"], lend, e["t"]))

# ---- VERIFICA que as features disparam (variancia/min/max) ----
X = np.array([[r[k] for k in FEAT_NAMES] for r in rows], dtype=float)
print("="*70)
print("FEATURE FIRING CHECK (variancia/min/max) — N=%d entries"%len(rows))
print("="*70)
for j,k in enumerate(FEAT_NAMES):
    col=X[:,j]
    print(f"{k:16s} mean={col.mean():+.4f} std={col.std():.4f} min={col.min():+.4f} max={col.max():+.4f} nunique={len(np.unique(np.round(col,4)))}")
    if col.std() < 1e-6:
        print(f"  !!! WARNING {k} CONSTANTE — feature nao dispara")

# ---- prova de causalidade ----
viol = [(n,le,tt) for (n,le,tt) in last_ends if le is not None and le>tt]
print("\nCAUSALIDADE 4H: entries=%d · violacoes(end>t)=%d · ok=%s"%(len(last_ends),len(viol),ok_causal))
ex = last_ends[0]
print("exemplo n=%d: ultima_barra_4H_end=%s <= entry_t=%s  (gap=%ds)"%(ex[0],ex[1],ex[2],ex[2]-ex[1] if ex[1] else -1))

# ---- salva feature_file ----
FEAT_FILE="/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/results/mtf_feat_h4_phase.json"
import os; os.makedirs(os.path.dirname(FEAT_FILE),exist_ok=True)
json.dump(rows, open(FEAT_FILE,"w"), indent=1)
print("\nsaved feature_file:", FEAT_FILE)

# ---- OOF mining-null ----
print("\n"+"="*70); print("OOF MINING-NULL (X = 96 x %d)"%len(FEAT_NAMES)); print("="*70)
res = oof_mining_null(X)
for k,v in res.items(): print(f"  {k}: {v}")
print("\nRESULT_JSON:", json.dumps(res))
