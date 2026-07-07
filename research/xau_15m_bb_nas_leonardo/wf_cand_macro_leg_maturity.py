#!/usr/bin/env python3
"""CANDIDATO: FILTRO MACRO-CONTEXTUAL CAUSAL — MATURIDADE DA PERNA MACRO (XAU 15M LONG 3R).

HIPOTESE ORIGINAL (exaustao): rejeitar a perna MUITO esticada (topo-exaustao).
  -> TESTADA E REFUTADA: manter perna curta (ext<=thr) ENVENENA (poison_ratio>1 em todo o sweep;
     winners tem extensao MEDIANA IGUAL/MAIOR e caudas mais longas -> pernas maduras CORREM ate 3R).

ACHADO REAL (mesma feature estrutural, direcao INVERSA): a IMATURIDADE e' que mata.
  Pernas FRESH (preco quase colado a origem do ultimo higher-low) sao os losers; pernas com
  extensao ja provada sao as que atingem 3R. Filtro = MANTER perna madura (ext >= thr).

FEATURE CAUSAL (so barras <= j, barra de decisao/entry):
  origin = base da cadeia corrente de higher-lows CONFIRMADOS ate j (causal_swings_upto(j),
           que so devolve pivos com conf_bar<=j -> zero confirmacao por movimento futuro).
  ext(j) = (CL[j] - origin_low) / ATR[j]   -> quantos ATRs a perna ja percorreu ate a decisao.
  KEEP se ext(j) >= THR (rejeita perna imatura/fresh). THR=6 (melhor: hit alto, poison<0.9, 2 anos+).

CAUSALIDADE: origin_low vem de pivos confirmados <= j; CL[j] e ATR[j] sao da propria barra j;
  nenhuma janela ultrapassa j; nao usa zone.last_t; nao usa e['out'] na decisao (so no score).
ESTRUTURAL: a origem e a cadeia de higher-lows sao trajetoria multi-barra (a perna que caminha),
  nao um snapshot isolado em j.
"""
import sys; sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import CL,ATR,ENTRIES,score,causal_swings_upto

THR = 6.0

def leg_origin_low(j):
    """Origem da perna de alta corrente = base da cadeia de higher-lows CONFIRMADOS ate j. CAUSAL."""
    sw = causal_swings_upto(j)                 # (tp,idx,price,conf_bar), todos conf_bar<=j
    lows = [(idx,pr) for tp,idx,pr,ci in sw if tp=="L"]
    if not lows: return None
    k = len(lows)-1
    while k-1>=0 and lows[k-1][1] < lows[k][1]: # recua enquanto os lows ascendem (higher-lows)
        k -= 1
    return lows[k][1]

def leg_ext(j):
    o = leg_origin_low(j)
    if o is None: return None
    return (CL[j]-o)/(ATR[j] or 5.0)

# decisao causal: manter perna madura, rejeitar fresh; None (sem historia) = manter (nao rejeitar por falta de dado)
keep_ns = [e["n"] for e in ENTRIES if (leg_ext(e["j"]) is None) or (leg_ext(e["j"]) >= THR)]

sc = score(keep_ns)
print("FILTRO = MATURIDADE DA PERNA MACRO (causal, keep se ext>=%.0f ATR)" % THR)
print("score:", sc)
print("keep_ns (n=%d):" % len(keep_ns), sorted(keep_ns))
