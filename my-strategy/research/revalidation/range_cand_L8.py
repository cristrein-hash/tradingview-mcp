#!/usr/bin/env python3
"""L8 — Reversao na banda swing (mean-reversion por TOQUES).

LENTE: RANGE = o preco reverte REPETIDAMENTE dos extremos da 2a escala de swing — falha em
romper para cima a partir de sw_high (rejeicao no topo) E falha em romper para baixo a partir de
sw_low (o fundo aguenta). Isto e mean-reversion DENTRO de uma banda estruturalmente estavel, sem
BOS. O discriminador nao e um botao unico: e a ESTRUTURA (banda swing estavel + nao-progressao,
via sw_since_bos alto) AGREGADA a CONTAGEM DE TOQUES em ambos os lados (evidencia de oscilacao,
nao de drift) e a CONFLUENCIA de indicadores (dx baixo = sem forca direcional; bbw baixo =
volatilidade contraida).

Porque toques + estrutura, e nao so estrutura: 'sw_since_bos alto' sozinho tambem marca um
grinding lento (que e BEAR/BULL fraco). Exigir toques DOS DOIS LADOS separa a caixa oscilante
(range verdadeiro) do drift silencioso. Os toques sao contados com ESTADO INTERNO acumulado APENAS
de barras passadas (a barra i so ve dados <=i) — 100% causal, sem lookahead, sem arrays globais.

ESTADO (modulo): banda corrente (sw_hi/sw_lo). Enquanto a banda swing se mantem estavel, acumulo
rejeicoes-no-topo e aguentos-no-fundo. Quando a banda muda materialmente (nova pernada/BOS), os
contadores RESETAM — logo, durante uma tendencia (banda a expandir com novos extremos) os toques
NAO se acumulam e o range NAO dispara; so numa caixa estavel e que a evidencia de oscilacao cresce.

SAIDA: a banda so 'rompe' quando um lado e finalmente quebrado COM gate — para baixo (swing-low +
bear_gate, responsivo p/ nao atrasar onsets de bear) ou para cima (swing-high + histerese ATR +
bull_gate, para nao fragmentar).

CAUSAL: usa so o dict 'c'. Sem lookahead, sem import de dados."""

NAME = "L8 mean-reversion por toques na banda swing (estrutura + dx/bbw)"
LENS = ("RANGE = preco reverte repetidamente de sw_high (rejeicao) e de sw_low (aguenta) dentro de "
        "banda swing estavel sem BOS (contagem de toques dos 2 lados) + confluencia dx baixo/bbw "
        "baixo; sai quando um lado rompe com gate (swing-low+bear_gate=BEAR, swing-high+ATR+bull_gate=BULL)")

# --- estrutura / banda ---
# A banda swing e a referencia estrutural, mas NAO resetamos os toques a cada micro-update do pivo
# (isso impedia acumular evidencia dos 2 lados numa caixa real). So uma mudanca GRANDE (nova
# pernada / rompimento) reseta. Assim os toques acumulam dentro da caixa estavel.
BAND_RESET = 0.006   # >3% de shift em sw_hi ou sw_lo = nova pernada => reset contadores de toque
SB_MIN     = 55      # sw_since_bos: so evita disparar imediatamente apos um BOS fresco (nao e o gate)
CONT_MARG  = 0.005   # containment tolera fecho ate 3% acima do sw_high (pivo swing e retardado)
TOUCH_TOL  = 0.18    # 'toque' = a <=18% da largura da banda do extremo
BODY_TOL   = 0.02    # rejeicao/aguento = fecho recua >=2% da largura do extremo (falha o rompimento)
REJ_HI_MIN = 1       # >=1 rejeicao no topo (falhou romper p/ cima)
HOLD_LO_MIN= 1       # >=1 aguento no fundo (falhou romper p/ baixo)

# --- confluencia de indicadores (mercado sem direcao) ---
DX_MAX     = 30.0    # forca direcional baixa (range med 23 vs bull 39 vs bear 33)
BBW_MAX    = 6.0     # volatilidade contraida (range med 4.6)
N_CONFL    = 2       # >=2 confluencias (dx, bbw, |dxy_slope|)
DXY_FLAT   = 1.6

# --- guardas anti-bear (preserva 5 bears + coerencia 2026) ---
DD_GUARD   = 12.0    # drawdown MUITO profundo = regime bear real, nunca range
UP_MARGIN  = 1.00    # histerese de saida p/ BULL (ATR)
DOWN_MARGIN= 1.00    # histerese de saida p/ BEAR (ATR): evita bear-whipsaw num dip do range,
                     # sem atrasar onset real (rompimento estrutural verdadeiro passa a margem)

# --- estado interno CAUSAL (acumulado so de barras passadas) ---
_band_hi = None
_band_lo = None
_rej_hi  = 0         # rejeicoes cumulativas no topo desta banda
_hold_lo = 0         # aguentos cumulativos no fundo desta banda


def _update(c):
    """Atualiza contadores de toques desta banda. Chamado no topo de enter/exit (uma das duas e
    invocada em cada barra ativa) => cobre todas as barras causalmente."""
    global _band_hi, _band_lo, _rej_hi, _hold_lo
    sh, sl = c["sw_high"], c["sw_low"]
    if sh is None or sl is None or sh <= sl:
        return
    # nova banda? (pernada nova / BOS) => reset evidencia de oscilacao
    if (_band_hi is None or _band_lo is None
            or abs(sh - _band_hi) / sh > BAND_RESET
            or abs(sl - _band_lo) / sl > BAND_RESET):
        _band_hi, _band_lo = sh, sl
        _rej_hi = _hold_lo = 0
    rng = sh - sl
    if rng <= 0:
        return
    tol = TOUCH_TOL * rng
    body = BODY_TOL * rng
    # rejeicao no topo: testou sw_high mas fechou de volta p/ dentro (falhou o rompimento)
    if c["high"] >= sh - tol and c["close"] < sh - body:
        _rej_hi += 1
    # aguento no fundo: testou sw_low mas fechou de volta p/ dentro (fundo defendido)
    if c["low"] <= sl + tol and c["close"] > sl + body:
        _hold_lo += 1


def _confluences(c):
    n = 0
    n += c["dx"] <= DX_MAX
    n += c["bbw"] <= BBW_MAX
    n += abs(c["dxy_slope"]) <= DXY_FLAT
    return n


def _contained(c):
    sh, sl = c["sw_high"], c["sw_low"]
    if sh is None or sl is None:
        return False
    # tolera fecho ligeiramente acima do sw_high (pivo swing e retardado; range forma-se sob topos)
    return sl <= c["close"] <= sh * (1.0 + CONT_MARG)


def enter_range(c):
    _update(c)
    if c["crash"]:
        return False
    # guarda-mae anti-bear: drawdown profundo = bear real, nunca demover a range
    if c["dd"] >= DD_GUARD:
        return False
    # ESTRUTURA: banda swing estavel + nao-progressao + preco contido
    if not _contained(c):
        return False
    if c["sw_since_bos"] < SB_MIN:
        return False
    # TOQUES: evidencia de oscilacao dos DOIS lados (mean-reversion, nao drift)
    if _rej_hi < REJ_HI_MIN or _hold_lo < HOLD_LO_MIN:
        return False
    # CONFLUENCIA de indicadores (>=2 sinais de mercado sem direcao)
    if _confluences(c) < N_CONFL:
        return False
    # de BULL: extra-cauteloso com dolar a subir com forca (risco de virar bear, nao range)
    if c["state"] == "BULL" and c["rising"] and c["dxy_slope"] > DXY_FLAT:
        return False
    return True


def exit_range(c, rng_hi, rng_lo):
    _update(c)
    # extremos da 2a escala swing respondem ao rompimento ESTRUTURAL (rng_lo do harness absorve dips)
    lo = c["sw_low"] if c["sw_low"] is not None else rng_lo
    hi = c["sw_high"] if c["sw_high"] is not None else rng_hi
    # DOWN -> BEAR: rompe swing-low (com histerese ATR leve) + gate bear. A margem corta o
    # bear-whipsaw num dip do range; um rompimento estrutural real ultrapassa-a e o onset segura.
    if c["close"] < lo - DOWN_MARGIN * c["atr"] and c["bear_gate"]:
        return "BEAR"
    # UP -> BULL: rompe swing-high + histerese ATR + gate bull (evita fragmentar)
    if c["close"] > hi + UP_MARGIN * c["atr"] and c["bull_gate"]:
        return "BULL"
    return None
