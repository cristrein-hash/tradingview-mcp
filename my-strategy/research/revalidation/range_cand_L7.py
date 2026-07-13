#!/usr/bin/env python3
"""L7 — Score hibrido ESTRUTURA x INDICADORES (>=1 estrutural E >=2 confluencias).

Desenho nomeado pelo Cris: o RANGE certo NAO e um botao unico. Exige uma ancora ESTRUTURAL
(2a escala de swing) E, por cima, confluencia de >=2 indicadores de "mercado sem direcao".
So entra em RANGE se AMBAS as camadas concordam.

CAMADA A — ESTRUTURA (2a escala swing m=13): NAO-PROGRESSAO "entre-tendencias".
  A escala swing NAO imprime higher-high (progressao bull) NEM lower-low (progressao bear) =>
  topos ~iguais e fundos ~iguais (liquidez lateral), E o preco esta CONTIDO na banda swing
  (+/- 0.25 ATR de folga). Esta ancora e o que separa RANGE de BULL (inside_swing 0.89 vs 0.37 no
  GT) e, com a guarda de lower-low, de BEAR — sem ela uma queda em grinding fica "dentro da banda"
  e vaza p/ range (foi o modo de falha das versoes so-inside-swing: false-range-in-bear ~22%).
  GUARDA DE PROGRESSAO BEAR (escala IMEDIATA m=5): se o low imediato ja e um lower-low > LL_GUARD
  vs o low anterior, o mercado esta a descer com estrutura => NAO e range (corta o bear-leak p/ ~11%).

CAMADA B — CONFLUENCIA de indicadores (>=2 de: dx baixo, bbw baixo, rsi neutro, atr_pct baixo,
  dxy plano, don60 contido). Mercado sem direcao. Calibrada nas distribuicoes por regime do GT 1D:
    RANGE  dx~23 · bbw~4.6 · rsi~51 · atr_pct~1.30 · don60~9.8
    BULL   dx~39 · bbw~6.8 · rsi~61 · atr_pct~1.37 · don60~12.3
    BEAR   dx~33 · bbw~6.3 · rsi~44 · atr_pct~1.53 · don60~11.6 · dd~11.5
  A confluencia refina a estrutura e, com a guarda-mae de drawdown profundo, protege os 5 bears +
  a coerencia macro-BEAR de 2026.

SAIDA: DOWN->BEAR responsiva (rompe swing-low + bear_gate, sem margem, p/ nao atrasar onsets);
UP->BULL com histerese ATR (rompe swing-high + margem + bull_gate) p/ nao fragmentar.

CAUSAL: usa so o dict 'c' (features com janelas que terminam em i; pivos confirmados em bar+m).
Sem lookahead, sem arrays globais de futuro.

VETOR AUDITADO (harness): PRESERVA=SIM (bears 5/5 · 2026 100%) · recall 72 · false-bear-in-range 7.1
· range-in-bull 14.5 · false-range-in-bear 10.9 · runs 59."""

NAME = "L7 hybrid structure(non-progression) x indicators (>=2 confluences)"
LENS = "RANGE = estrutura swing sem progressao (nem higher-high nem lower-low = liquidez lateral) + preco contido + guarda de lower-low imediato, E >=2 confluencias de indicadores (dx/bbw/rsi/atr_pct/dxy/don60); saida responsiva p/ BEAR, histerese ATR p/ BULL"

# --- CAMADA A: estrutura (2a escala swing) — tolerancias de NAO-PROGRESSAO ---
HH_TOL   = 0.050    # topo swing > 5% acima do topo prev = higher-high (bull) => NAO range
LL_TOL   = 0.035    # fundo swing > 3.5% abaixo do fundo prev = lower-low (bear) => NAO range
EQ_TOL   = 0.060    # o outro lado nao pode afastar-se mais que isto de "igual"
BAND_ATR = 0.25     # folga (em ATR) na contencao inside-swing (apanha ranges ligeiramente mais largas)
LL_GUARD = 0.03     # guarda de progressao BEAR na escala IMEDIATA (m=5): lower-low ativo >3% => NAO range

# --- CAMADA B: confluencia de indicadores (>=2) ---
DX_MAX     = 32.0   # forca direcional baixa (range med 23 vs bull 39)
BBW_MAX    = 6.0    # volatilidade contraida (range med 4.6 vs bull 6.8)
RSI_LO     = 44.0   # neutralidade de momentum (nem bull>61 nem bear<44)
RSI_HI     = 60.0
ATRP_MAX   = 1.48   # vol relativa baixa (range p75 1.46 vs bear med 1.53)
DXY_FLAT   = 1.6    # dolar sem inclinacao forte
DON_MAX    = 11.5   # contencao Donchian 60d (range med 9.8 vs bull 12.3)
N_CONFL    = 2      # >=2 confluencias de indicadores

# --- guardas anti-bear (preserva 5 bears + coerencia 2026) ---
DD_GUARD   = 14.0   # nao demover a range em drawdown MUITO profundo (regime bear real)
UP_MARGIN  = 1.00   # histerese de saida p/ cima (ATR)


def _inside_swing(c):
    lo, hi = c["sw_low"], c["sw_high"]
    if lo is None or hi is None:
        return False
    e = BAND_ATR * c["atr"]
    return (lo - e) <= c["close"] <= (hi + e)


def _structural(c):
    """NAO-PROGRESSAO na 2a escala + contido. Assimetrico: rejeita higher-high (bull) e
    lower-low (bear); aceita topos/fundos ~iguais (liquidez lateral, entre-tendencias)."""
    sh, sph = c["sw_high"], c["sw_prev_high"]
    sl, spl = c["sw_low"],  c["sw_prev_low"]
    if None in (sh, sph, sl, spl):
        return False
    midh = (sh + sph) / 2.0
    midl = (sl + spl) / 2.0
    if midh <= 0 or midl <= 0:
        return False
    if (sh - sph) / midh > HH_TOL:  return False   # higher-high => uptrend
    if (sph - sh) / midh > EQ_TOL:  return False   # topo demasiado fundo => nao "igual"
    if (spl - sl) / midl > LL_TOL:  return False   # lower-low => downtrend
    if (sl - spl) / midl > EQ_TOL:  return False   # fundo demasiado alto => nao "igual"
    return _inside_swing(c)


def _bear_progression(c):
    """escala IMEDIATA (m=5): o low imediato ja e um lower-low significativo => mercado a descer."""
    pl, ppl = c["prot_low"], c["prev_low"]
    if pl is None or ppl is None or ppl <= 0:
        return False
    return (ppl - pl) / ppl > LL_GUARD


def _confluences(c):
    n = 0
    n += c["dx"] <= DX_MAX
    n += c["bbw"] <= BBW_MAX
    n += RSI_LO <= c["rsi"] <= RSI_HI
    n += c["atr_pct"] <= ATRP_MAX
    n += abs(c["dxy_slope"]) <= DXY_FLAT
    n += c["don_w60"] <= DON_MAX
    return n


def enter_range(c):
    if c["crash"]:
        return False
    # guarda-mae anti-bear: drawdown MUITO profundo = regime bear, nunca range
    if c["dd"] >= DD_GUARD:
        return False
    # guarda de progressao bear na escala imediata (corta o bear-leak)
    if _bear_progression(c):
        return False
    # CAMADA A (estrutura: nao-progressao + contido) E CAMADA B (>=2 indicadores)
    if not _structural(c):
        return False
    if _confluences(c) < N_CONFL:
        return False
    # assimetria de origem: de BULL, extra-cauteloso com dolar a subir com forca (risco bear)
    if c["state"] == "BULL" and c["rising"] and c["dxy_slope"] > DXY_FLAT:
        return False
    return True


def exit_range(c, rng_hi, rng_lo):
    # extremos da 2a escala de swing (o rng_lo do harness absorve dips => uso sw_low/sw_high,
    # que respondem ao rompimento estrutural real).
    lo = c["sw_low"] if c["sw_low"] is not None else rng_lo
    hi = c["sw_high"] if c["sw_high"] is not None else rng_hi
    # DOWN->BEAR: rompe swing-low + confluencia bear. RESPONSIVO (sem margem) p/ nao atrasar onset.
    if c["close"] < lo and c["bear_gate"]:
        return "BEAR"
    # UP->BULL: rompe swing-high + histerese ATR + confluencia bull (evita fragmentar)
    if c["close"] > hi + UP_MARGIN * c["atr"] and c["bull_gate"]:
        return "BULL"
    return None
