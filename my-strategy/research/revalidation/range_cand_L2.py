#!/usr/bin/env python3
"""L2 — Caixa de 2ª escala (swing box com toques múltiplos).

RANGE = preço contido na caixa de swing [sw_low, sw_high] com a caixa REVISITADA dos DOIS lados
(topo estável ~ topo anterior E fundo estável ~ fundo anterior no swing-scale m=13, dentro de uma
fração EQ_BOX da caixa = rejeição repetida em ambas as bordas, sem BOS-swing) — ESTRUTURA. Essa
contenção tem de PERSISTIR MIN_HOLD barras (uma caixa prova-se no tempo; um bear fresco pós-crash
ainda não teve toques repetidos). CONFLUÊNCIA no instante da entrada: força direccional fraca (dx
baixo) E volatilidade comprimida (atr% baixo) — atr% é o que separa um range genuíno (quieto) de um
bear em pausa (estruturalmente-caixa mas ainda VIOLENTO, atr%~3) e protege a coerência 2026.

SAÍDA assimétrica (os dois falsos têm causas opostas): BULL exit ATEMPADO (rompe a borda de swing
corrente sw_high => não derrama p/ a janela de bull seguinte); BEAR exit PEGAJOSO (rompe a caixa
ACUMULADA rng_lo => mini-dips não partem o range). Ambos confirmados pelo gate de significância.

CAUSAL: usa só o dict `c` + estado que acumula APENAS barras passadas (_streak, _last_i). Sem
imports de dados, sem arrays globais, sem índices de futuro. Estrutura = swing pivots m=13; 2
confluências = dx + atr%.
"""
NAME = "L2 swing-box multi-touch (dx + atr% confluence)"
LENS = "caixa 2ª escala [sw_low,sw_high] revisitada dos 2 lados (EQH+EQL swing, sem BOS) c/ persistência; confluência dx baixo + volatilidade comprimida (atr%); saída assimétrica (bull=borda swing atempada, bear=caixa acumulada pegajosa)+gate"

# ---- parâmetros internos (estruturais + confluência) ----
BOS_EXIT_ATR = 1.6   # SAÍDA por swing-BOS só se DECISIVO (grande margem) — mini-dips não contam
EQ_BOX      = 0.65   # borda "revisitada" = swing-extremo dentro desta fração da caixa vs o anterior
DX_MAX      = 24.0   # confluência #1: força direccional fraca => range
ATR_MAX     = 2.2    # confluência #2: VOLATILIDADE COMPRIMIDA (atr% baixo). Um range é quieto; um
                     #   bear pós-crash a fazer pausa continua VIOLENTO (atr% ~3) => separa 2026.
BREAK_ATR   = 0.5   # margem de rompimento sustentado da caixa (em ATR)
POS_LO      = 0.20   # preço tem de estar no MIOLO da caixa p/ entrar (não colado a um extremo)
POS_HI      = 0.80
MIN_HOLD    = 12     # PERSISTÊNCIA: a contenção estrutural tem de se aguentar tantas barras antes
                     #   de demover a tendência (uma caixa PROVA-SE no tempo; um bear FRESCO pós-
                     #   crash ainda não teve toques repetidos => não é range).

# estado causal (só conta barras passadas): streak de contenção estrutural enquanto em tendência
_streak = 0
_last_i = -999


def _structural(c):
    """ESTRUTURA pura (piecewise-constante c/ os swings lentos m=13). Base persistente do streak.
    NÃO inclui confluência (dx é ruidoso e partiria o streak) — a confluência entra no instante da
    decisão. Devolve (caixa_revisitada, pos_na_caixa)."""
    hi, lo = c["sw_high"], c["sw_low"]
    ph, pl = c["sw_prev_high"], c["sw_prev_low"]
    if None in (hi, lo, ph, pl):
        return False, 0.0
    box = hi - lo
    if box <= 0:
        return False, 0.0
    # caixa REVISITADA dos DOIS lados = toques repetidos. Range mantém topo E fundo estáveis; BEAR
    #   faz o topo COLAPSAR (hi<<ph), BULL faz o fundo SUBIR muito (lo>>pl) — ambos falham. (Subsume BOS.)
    top_stable = abs(hi - ph) <= EQ_BOX * box
    bot_stable = abs(lo - pl) <= EQ_BOX * box
    pos = (c["close"] - lo) / box
    return (top_stable and bot_stable and not c["crash"]), pos


def enter_range(c):
    global _streak, _last_i
    # reset do streak se houve interrupção (estivemos em RANGE entretanto => barras não-contíguas)
    if c["i"] != _last_i + 1:
        _streak = 0
    _last_i = c["i"]
    contained, pos = _structural(c)
    _streak = _streak + 1 if contained else 0
    # PERSISTÊNCIA (estrutura prova-se no tempo) + 2 CONFLUÊNCIAS no instante da decisão (força
    #   direccional fraca E volatilidade comprimida) + preço no MIOLO da caixa (a oscilar).
    #   A volatilidade comprimida (atr%) é o que separa um range genuíno de um bear pós-crash
    #   em pausa (que estruturalmente parece caixa mas continua VIOLENTO) — protege 2026.
    return (_streak >= MIN_HOLD
            and c["dx"] < DX_MAX
            and c["atr_pct"] < ATR_MAX
            and POS_LO < pos < POS_HI)


def exit_range(c, rng_hi, rng_lo):
    """Sai por (a) BOS ESTRUTURAL de swing — um novo swing-extremo rompe o anterior — confirmado
    pelo gate; independente da caixa que o harness ALARGA barra-a-barra (evita a armadilha do
    grind-em-tendência onde a caixa cresce e o close nunca "rompe"). (b) fast-path: close muito
    além da caixa corrente + gate."""
    atr = c["atr"] or (0.01 * c["close"])
    hi, lo = c["sw_high"], c["sw_low"]
    ph, pl = c["sw_prev_high"], c["sw_prev_low"]
    # SAÍDA ASSIMÉTRICA (os dois falsos têm causas opostas):
    #  - BULL exit ATEMPADO: false-range-in-bull vem de sair TARDE p/ bull => usa a BORDA DE SWING
    #    corrente (sw_high, segue a estrutura, não acumula) => rompe cedo na retoma de tendência.
    #  - BEAR exit PEGAJOSO: false-bear-in-range vem de sair CEDO (blips) em mini-dips => usa a
    #    caixa ACUMULADA (rng_lo, inclui todos os toques) => só sai num rompimento genuíno do fundo.
    #  Ambos + gate de significância.
    top = hi if hi is not None else rng_hi         # borda de swing corrente (atempada)
    if c["close"] > top + BREAK_ATR * atr and c["bull_gate"]:
        return "BULL"
    if c["close"] < rng_lo - BREAK_ATR * atr and c["bear_gate"]:   # fundo acumulado (pegajoso)
        return "BEAR"
    return None
