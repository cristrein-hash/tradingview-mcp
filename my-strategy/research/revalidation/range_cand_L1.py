#!/usr/bin/env python3
"""ID=L1 — Entre-tendencias: swing-CHoCH sem BOS de confirmacao.

NUCLEO ESTRUTURAL (2a escala de pivo, m=13): a estrutura PAROU de progredir. Duas assinaturas:
  (A) preco OSCILA CONTIDO entre o ultimo swing-low e o ultimo swing-high (sw_low<close<sw_high) E
      nao esta a romper nenhum pivo imediato (nao choch_dn/up) -> nao ha BOS novo -> consolidacao.
  (B) sw_since_bos ENORME (centenas de barras sem novo extremo de escala) = tendencia morta ha muito,
      mesmo que a banda esteja larga (caso 2021: range longo pos-bear, dx ainda ~32).
CONFLUENCIA DE INDICADORES (porteiro obrigatorio, nunca um botao unico de banda):
  - dx (forca direcional ADX-like) BAIXO = ausencia de tendencia.
  - bbw (largura Bollinger) COMPRIMIDO = baixa energia.
  - dd (drawdown 252) MODERADO = nao e markdown de bear ativo (protege os bears).
  - ru (run-up 252) BAIXO na clausula-B = consolidacao morta, nao pausa de bull vivo.

SAIDA (rompe um lado do swing COM gate): um breakout REAL reacende a forca direcional (dx). O chop
  interno de um range rompe mini-pivos mas mantem dx BAIXO -> nao liberta (range preservado). Assim
  recupera-se o bear-onset que uma banda alargada engoliria, sem fragmentar o range. A reversao ja
  tem prioridade no FSM (protege os onsets); aqui so tratamos a saida do estado RANGE.

HISTERESE (anti-fragmentacao, licao do whack-a-mole): dwell minimo em RANGE e em TENDENCIA elimina o
  flip-flop RANGE<->tendencia dentro do mesmo regime. Um breakout FORTE (dx alto) pode furar o dwell
  de range para nao derramar range no bull seguinte (controla range-in-bull). Contadores causais
  derivados SO da progressao do indice de barra c['i'] (passado-apenas; reset se a serie recomeca).

CAUSAL: usa SO o dict 'c' e contadores do proprio passado. Sem imports de dados, sem arrays globais,
sem indices de futuro. (crash continua a ser override BEAR no proprio harness.)"""

NAME = "L1 entre-tendencias (swing-CHoCH sem BOS) + confluencia dx/bbw/dd + histerese"
LENS = "estrutura parou de progredir a escala swing (contido em sw_low/sw_high sem choch, OU sw_since_bos enorme) agregado a dx/bbw/dd baixos; saida por rompimento com dx a reacender; dwell anti-fragmentacao"

# --- clausula A: range de baixa energia (contido + sem tendencia) ---
SB_A   = 8       # floor estrutural: alguma estagnacao de escala
DX_A   = 24.0    # forca direcional baixa
BBW_A  = 6.0     # Bollinger comprimido
DD_A   = 12.0    # nao em markdown profundo (protege bear ativo: 2022 dd15, 2026 dd17 ficam de fora)
# --- clausula B: consolidacao longa morta (caso 2021) ---
SB_B   = 150     # centenas de barras sem novo extremo de escala
DX_B   = 33.0    # tolera dx maior porque a estrutura esta MORTA ha muito
RU_B   = 12.0    # run-up baixo = nao e pausa de bull vivo
DD_B   = 12.0
# --- saida ---
DX_EXIT   = 28.0  # forca direcional que RETORNA = tendencia voltou
DX_STRONG = 33.0  # breakout FORTE: pode furar o dwell de range (evita derramar range no bull)
# --- histerese ---
DWELL_RANGE = 20  # barras minimas em RANGE antes de sair (excepto breakout forte / crash-no-harness)
DWELL_TREND = 10  # barras minimas em tendencia antes de poder re-entrar em RANGE

# contadores causais (SO passado). _last_i deteta reinicio da serie -> reset limpo.
_S = {"last_i": -1, "in_range": 0, "since_exit": 10 ** 9}


def _tick(c):
    if c["i"] <= _S["last_i"]:
        _S["last_i"] = -1
        _S["in_range"] = 0
        _S["since_exit"] = 10 ** 9
    _S["last_i"] = c["i"]


def _contained(c):
    lo, hi = c["sw_low"], c["sw_high"]
    return lo is not None and hi is not None and lo < c["close"] < hi


def _range_signature(c):
    contained = _contained(c)
    no_break = not c["choch_dn"] and not c["choch_up"]
    sb = c["sw_since_bos"]
    # Clausula A — range de baixa energia, estruturalmente contido e sem rompimento imediato
    if (contained and no_break and sb >= SB_A
            and c["dx"] < DX_A and c["bbw"] < BBW_A and c["dd"] < DD_A):
        return True
    # Clausula B — tendencia morta ha centenas de barras (range longo pos-tendencia, ex-2021)
    if (contained and sb >= SB_B
            and c["dx"] < DX_B and c["ru"] < RU_B and c["dd"] < DD_B):
        return True
    return False


def enter_range(c) -> bool:
    _tick(c)
    _S["in_range"] = 0
    _S["since_exit"] += 1
    if _range_signature(c) and _S["since_exit"] >= DWELL_TREND:
        return True
    return False


def exit_range(c, rng_hi, rng_lo):
    _tick(c)
    _S["in_range"] += 1
    _S["since_exit"] = 0
    down = (c["close"] < rng_lo) or c["choch_dn"]
    up = (c["close"] > rng_hi) or c["choch_up"]
    band_up = c["close"] > rng_hi and c["bull_gate"]
    band_dn = c["close"] < rng_lo and c["bear_gate"]
    # breakout FORTE (dx alto + furou a banda com gate) pode sair mesmo dentro do dwell de range
    strong_break = c["dx"] >= DX_STRONG and (band_up or band_dn)
    if _S["in_range"] < DWELL_RANGE and not strong_break:
        return None
    strong = c["dx"] >= DX_EXIT
    d = None
    if up and c["bull_gate"] and strong:
        d = "BULL"
    elif down and c["bear_gate"] and strong:
        d = "BEAR"
    elif band_up:                       # fallback: rompimento sustentado da banda real
        d = "BULL"
    elif band_dn:
        d = "BEAR"
    if d is not None:
        _S["in_range"] = 0
    return d
