#!/usr/bin/env python3
"""L6 — Neutralidade de momentum GATED por estrutura swing.

RANGE = momentum neutro (rsi centrado ~50, dx baixo, volatilidade contraida) MAS so quando a 2a
escala de swing confirma ESTAGNACAO: preco DENTRO da banda swing (entre sw_low/sw_high) e o swing
ja nao imprime BOS ha um tempo (sw_since_bos moderado+). O gate estrutural evita apanhar pausas
curtas dentro de tendencia forte.

CONFLUENCIA (calibrada nas distribuicoes por regime do GT):
  RANGE  rsi_med~50 · dx_med 15-30 · bbw_med 3-5      (contracao)
  BEAR   rsi_med 41-45 · bbw ate 11 (2026)            (rsi baixo + expansao)
  BULL   rsi_med 62 · dx_med 39
Logo o nucleo do range exige: rsi in [48,58] (nem bull>58 nem bear<48) + bbw contraida (mata o
bear-2026 expansivo) + dx baixo. E estrutura (inside swing + estagnacao).

ASSIMETRIA POR ORIGEM (c['state']) — os 5 bears nascem de BULL e a reversao BULL->BEAR e tratada
pelo harness com PRIORIDADE:
  de BULL: conservador (nao em drawdown de escala bear; nao com dolar a subir) para nunca ficar em
           range no colo de um bear.
  de BEAR: so quando o momentum recuperou genuinamente (rsi>=48 + bbw contraida) => o bear pausou
           num range; se retomar (novo minimo) a saida responsiva reata o BEAR.

SAIDA ASSIMETRICA:
  DOWN->BEAR: rompimento do rng_lo (que ja absorveu os dips internos => sticky) + bear_gate,
              RESPONSIVO (sem margem) para nao atrasar onsets de reversao.
  UP->BULL:   rompimento do rng_hi + margem ATR (histerese) + bull_gate, para nao fragmentar."""

NAME = "L6 momentum-neutral gated-by-swing-structure"
LENS = "RANGE = rsi 48-58 + dx baixo + bbw contraida (estrutura de momentum neutro), SO com preco dentro da banda swing e sw_since_bos moderado+ (estagnacao da 2a escala); saida responsiva p/ baixo, histerese ATR p/ cima"

# --- parametros internos (calibrados nas distribuicoes por regime do GT) ---
RSI_LO, RSI_HI = 48.0, 58.0      # neutralidade de momentum centrada em 50
DX_MAX        = 32.0             # forca direcional baixa (ADX-like)
BBW_MAX       = 6.5             # contracao de volatilidade (mata bear-2026 expansivo bbw~11)
SINCE_BOS_MIN = 8              # 2a escala sem BOS ha >= N barras (estagnacao estrutural)
DD_GUARD_BULL = 6.0            # de BULL: nao demover a range em drawdown de escala bear (limite sup.)
SBOS_MATURE   = 100           # de BULL: 2a escala sem BOS ha muito (bull extendido/maduro)
DD_MATURE_TOP = 5.0           # ... E colado ao topo-252 => distribuicao pre-bear, NAO range
UP_MARGIN     = 0.0            # histerese de saida p/ cima em multiplos de ATR (0 = so estrutura+momentum)
UP_RU_MIN     = 15.0           # run-up minimo para confirmar breakout bull genuino


def _inside_swing(c):
    lo, hi = c["sw_low"], c["sw_high"]
    if lo is None or hi is None:
        return False
    return lo <= c["close"] <= hi


def enter_range(c):
    if c["crash"]:
        return False
    # --- GATE ESTRUTURAL (2a escala): estagnacao confirmada ---
    if not _inside_swing(c):
        return False
    if c["sw_since_bos"] < SINCE_BOS_MIN:
        return False
    # --- CONFLUENCIA DE MOMENTUM-NEUTRO (nucleo: rsi centrado + volatilidade contraida + dx baixo) ---
    if not (RSI_LO <= c["rsi"] <= RSI_HI):
        return False
    if c["bbw"] > BBW_MAX:            # expansao de volatilidade => NAO e range (ex.: bear-2026)
        return False
    if c["dx"] > DX_MAX:             # direcional forte => NAO e range
        return False
    # --- ASSIMETRIA POR ORIGEM ---
    if c["state"] == "BULL":
        if c["dd"] >= DD_GUARD_BULL:                       # perto de perna bear => nao entrar
            return False
        # topo-de-bull-maduro (2a escala sem BOS ha muito E colado ao topo-252) = distribuicao
        # pre-reversao, NAO um range entre-tendencias => nao demover (protege onset do bear).
        if c["sw_since_bos"] > SBOS_MATURE and c["dd"] < DD_MATURE_TOP:
            return False
        if c["rising"] and abs(c["dxy_slope"]) > 1.5:       # dolar a subir com forca => risco bear
            return False
    return True


def exit_range(c, rng_hi, rng_lo):
    # SAIDA ESTRUTURAL: o harness expande rng_lo=min(rng_lo,prot_low) a cada barra, logo o band
    # ABSORVE qualquer tendencia (close<rng_lo nunca dispara numa queda). Uso os EXTREMOS DA 2a
    # ESCALA DE SWING (sw_low/sw_high): preco fica DENTRO deles no range e ROMPE-os num trend real.
    lo = c["sw_low"] if c["sw_low"] is not None else rng_lo
    hi = c["sw_high"] if c["sw_high"] is not None else rng_hi
    # DOWN->BEAR: rompe o swing-low da 2a escala (breakdown estrutural) + confluencia bear
    if c["close"] < lo and c["bear_gate"]:
        return "BEAR"
    # UP->BULL: rompe o swing-high da 2a escala + histerese ATR + bull_gate + MOMENTUM genuino
    # (rsi saiu da banda neutra OU run-up forte) — pokes dentro de range nao qualificam, mas uma
    # retoma real da tendencia empurra rsi>58 / ru alto => nao fica preso em range dentro do bull.
    if (c["close"] > hi + UP_MARGIN * c["atr"] and c["bull_gate"]
            and (c["rsi"] > RSI_HI or c["ru"] >= UP_RU_MIN)):
        return "BULL"
    return None
