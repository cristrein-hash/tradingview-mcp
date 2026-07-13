#!/usr/bin/env python3
"""L4 — Compressão de volatilidade (confluência de indicadores GATED por estrutura).

LENTE: RANGE = confluência de COMPRESSÃO de volatilidade, mas só CONTA se a ESTRUTURA de
swing (2ª escala, m=13) também estagnou. O núcleo é ESTRUTURAL (sem novo BOS de swing há
um tempo => a tendência parou de progredir); os indicadores de compressão (bbw apertado, dx
baixo=sem direção, atr_pct comprimido, dxy_slope plano, Donchian-60 estreito) são a
CONFLUÊNCIA que confirma que a estagnação estrutural é mesmo lateralização e não pausa
efémera. Não é um botão único de banda — é estrutura AGREGADA a >=K leituras de compressão.

Saída do range: rompimento SUSTENTADO do extremo da banda com significância (gate), na
direção do gate — mirrors a lógica de significância dos turnos (não inventa magnitude nova).
"""
NAME = "L4 compressão-vol (estrutura swing + confluência de compressão)"
LENS = ("RANGE = estagnação estrutural swing (sw_since_bos moderado+, sem novo BOS) AGREGADA a "
        "confluência de compressão (bbw baixo + dx baixo + atr_pct comprimido + dxy plano + "
        "Donchian60 estreito). Saída = rompimento sustentado da banda com gate de significância.")

# --- estrutura (TIMING/gate primário) ---
SW_STAG = 12          # nº mínimo de barras desde o último BOS de swing (estrutura parou)

# --- confluência de compressão (thresholds calibrados nas distribuições GT-RANGE) ---
BBW_MAX = 6.6         # largura Bollinger apertada (RANGE p75≈6.3; BULL/BEAR med≈6.8/6.3)
DX_MAX = 35.0         # força direcional baixa = sem direção (RANGE med≈23)
ATRP_MAX = 1.50       # atr% comprimido (RANGE p75≈1.46; BEAR med≈1.53 sobe)
DXYS_FLAT = 2.5       # inclinação do dólar plana (|slope| baixo)
DON60_MAX = 12.5      # Donchian-60 estreito (contenção; RANGE p75≈12.7) — 1 confluência entre várias
K_CONFL = 4           # nº mínimo de leituras de compressão que têm de concordar (de 5)

# --- ESTRUTURA #2: posição do close na banda de swing (2ª escala) ---
# Num RANGE genuíno o preço OSCILA no MEIO da banda de swing (pos med≈0.5). Numa PAUSA de BULL
# o preço fica COLADO ao topo de swing / acima (pos med≈0.9, p75>1.2 = acabou de fazer higher-high).
# Exigir pos em banda média = "entre-tendências" estrutural => corta range-in-bull na raiz.
POS_LO = 0.12         # nem colado ao fundo (potencial rompimento bear, não range)
POS_HI = 0.72         # nem colado/acima do topo de swing (pausa de bull a caminho de higher-high)

# --- gate de CONTEXTO bull (reforço; não demover CORPO de BULL a range) ---
RSI_HI = 62.0         # não entrar em range com momentum bull forte (BULL rsi med≈61.5)
RU_HI = 45.0          # nem com run-up muito forte de bull (mantém ranges near-highs 2024-11/2025)


def _compression_votes(c):
    v = 0
    if c["bbw"] and c["bbw"] <= BBW_MAX: v += 1
    if c["dx"] <= DX_MAX: v += 1
    if c["atr_pct"] and c["atr_pct"] <= ATRP_MAX: v += 1
    if abs(c["dxy_slope"]) <= DXYS_FLAT: v += 1
    if c["don_w60"] and c["don_w60"] <= DON60_MAX: v += 1
    return v


def _swing_pos(c):
    hi, lo = c["sw_high"], c["sw_low"]
    if hi is None or lo is None or hi <= lo:
        return None
    return (c["close"] - lo) / (hi - lo)


def enter_range(c):
    # ESTRUTURA #1: swing tem de ter estagnado (sem progressão de BOS há SW_STAG barras).
    if c["sw_since_bos"] < SW_STAG:
        return False
    # ESTRUTURA #2: close no MEIO da banda de swing (oscilação entre-tendências), não colado
    # ao topo (pausa de bull) nem ao fundo (rompimento bear).
    pos = _swing_pos(c)
    if pos is None or not (POS_LO <= pos <= POS_HI):
        return False
    # CONTEXTO: não demover corpo de BULL (momentum/run-up muito forte) a range.
    if c["rsi"] >= RSI_HI or c["ru"] >= RU_HI:
        return False
    # CONFLUÊNCIA de compressão: >=K das 5 leituras concordam.
    return _compression_votes(c) >= K_CONFL


# --- saída do range: rompimento DECISIVO (margem em ATR) + gate de significância ---
# Num range de drawdown (ex.: 2021) as down-legs picam o fundo da banda sem virar tendência;
# exigir margem = M*ATR além da banda evita marcar BEAR em cada perna interna (mata false-bear-
# in-range) sem perder os rompimentos reais (esses excedem a margem com folga).
EXIT_MARGIN_BULL = 0.60   # saída-BULL STICKY: falsos breakouts para cima (ex.: pop de mai-2021
                          # a 1899 acima do topo) reverteriam e viravam BEAR => fbr; margem larga
                          # mantém o range e evita o whipsaw range→BULL→BEAR.
EXIT_MARGIN_BEAR = 0.40   # saída-BEAR RESPONSIVA: o bear curto de 2024-11 (1 semana) precisa de
                          # um down-exit ágil; margem estreita preserva a deteção desse bear.


def exit_range(c, rng_hi, rng_lo):
    a = c["atr"] or 0.0
    # Referência ESTRUTURAL do rompimento = o extremo mais externo entre a banda rápida (m=5) e
    # o swing (m=13): o preço tem de bater o FUNDO/TOPO MAIS PROFUNDO conhecido do range. Assim
    # uma down-leg interna que pica a banda rápida mas fica acima do CHÃO de swing (ex.: dip
    # mid-2021 a ~1750 com chão ~1680) NÃO conta como saída => mata false-bear-in-range.
    sh, sl = c["sw_high"], c["sw_low"]
    ref_lo = min(rng_lo, sl) if sl is not None else rng_lo
    ref_hi = max(rng_hi, sh) if sh is not None else rng_hi
    # BULL exit (sticky): rompimento decisivo do topo estrutural com significância.
    if c["close"] > ref_hi + EXIT_MARGIN_BULL * a and c["bull_gate"]:
        return "BULL"
    # BEAR exit (responsivo): rompimento decisivo do CHÃO estrutural + EXPANSÃO de volatilidade
    # (a compressão quebrou = nasce tendência) ou crash. Mesmo detector que ENTRA guarda a SAÍDA.
    expanding = _compression_votes(c) < K_CONFL
    if c["close"] < ref_lo - EXIT_MARGIN_BEAR * a and c["bear_gate"] and (expanding or c["crash"]):
        return "BEAR"
    return None
