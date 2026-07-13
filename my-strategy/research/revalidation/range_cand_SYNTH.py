#!/usr/bin/env python3
"""SYNTH — síntese das melhores ideias dos candidatos que preservaram os turnos.

NÚCLEO ESTRUTURAL (de L5): RANGE = FALHA-DE-PROGRESSÃO da 2ª escala de swing (m=13). Em BULL o
swing-high mais recente falha novo high acima da tolerância EQH (sw_high<=sw_prev_high*(1+EQ)) sem
CHoCH-dn, CONFIRMADO na escala imediata (m=5, prot_high<=prev_high — protege os turnos); simétrico
em BEAR (EQL). Isto dá RECALL alto (a estrutura parou de estender é a assinatura mais fiável de
range) e false-bear-in-range baixo.

DISCRIMINADOR ESTRUTURAL ADICIONADO (de L4/L6): POSIÇÃO DO CLOSE NA BANDA DE SWING. O grande
leakage de range-em-bull não são ranges — são CONSOLIDAÇÕES-EM-TENDÊNCIA coladas ao topo do swing
(swpos med ~0.96, dd baixo, rsi ~61). Um range genuíno OSCILA no meio da banda (swpos med ~0.55).
Como o RANGE é PEGAJOSO no harness (uma vez dentro, só sai por exit_range), basta EXIGIR que a
ENTRADA aconteça quando o close está no meio/fundo da banda de swing: a consolidação-de-bull nunca
desce ao meio (rompe de volta para cima antes), o range genuíno desce (oscila) e dispara a entrada,
e a partir daí o exit sticky mantém a deteção. Aplico o teto de posição SÓ em origem BULL (onde
mora o range-in-bull); em origem BEAR mantenho o núcleo L5 (o false-range-in-bear não é métrica-
árbitro e mexer nele arrisca o recall de 2021/2024-11).

CONFLUÊNCIA DE INDICADORES (de L5): RSI de volta à banda média (momentum neutralizado). Mantenho a
banda 40-60; o teto de posição já remove o grosso do leak de rsi alto.

SAÍDA (de L5): a tendência VOLTA A ESTENDER — re-extensão ESTRUTURAL (novo swing-extremo além da
tolerância) OU rutura DECISIVA de preço (buffer), sempre com gate ortogonal. Os 5 bears fazem onset
via reversão-com-prioridade do harness (nunca via este exit), logo a banda pode ser pegajosa sem
risco para os turnos.

CAUSAL: só lê o dict `c` passado (sem imports de dados, sem arrays globais, sem índices de futuro).
"""

NAME = "SYNTH failure-of-progression + swing-position gate + RSI mid-band"
LENS = ("RANGE = falha estrutural de progressão do swing (EQH/EQL, confirmada no imediato) AGREGADA "
        "a (i) posição do close no meio/fundo da banda de swing [corta consolidação-de-bull colada "
        "ao topo] e (ii) RSI de volta à banda média. Saída = re-extensão estrutural ou rutura "
        "decisiva com gate.")

# --- núcleo estrutural (L5) ---
RSI_LO, RSI_HI = 40.0, 60.0
EQ = 0.008          # tolerância EQH/EQL: falha de progressão = novo extremo dentro de +-0.8%
EXIT_BUF = 0.02     # rutura DECISIVA da banda p/ sair de range

# --- discriminador de posição na banda de swing (L4/L6) — teto aplicado em origem BULL ---
POS_HI_BULL = 0.72  # close acima disto = consolidação colada ao topo do swing (pausa de bull, NÃO range)


def _swing_pos(c):
    hi, lo = c["sw_high"], c["sw_low"]
    if hi is None or lo is None or hi <= lo:
        return None
    return (c["close"] - lo) / (hi - lo)


def _stall_bull(c):
    sh, sph = c["sw_high"], c["sw_prev_high"]
    if sh is None or sph is None:
        return False
    struct_stall = sh <= sph * (1 + EQ)                 # swing nao faz higher-high MEANINGFUL
    imm_stall = (c["prot_high"] is not None and c["prev_high"] is not None
                 and c["prot_high"] <= c["prev_high"])  # confirmacao na escala imediata (protege turnos)
    return struct_stall and imm_stall and not c["choch_dn"]


def _stall_bear(c):
    sl, spl = c["sw_low"], c["sw_prev_low"]
    if sl is None or spl is None:
        return False
    struct_stall = sl >= spl * (1 - EQ)                 # swing nao faz lower-low MEANINGFUL
    imm_stall = (c["prot_low"] is not None and c["prev_low"] is not None
                 and c["prot_low"] >= c["prev_low"])
    return struct_stall and imm_stall and not c["choch_up"]


def enter_range(c):
    # confluencia de momentum: RSI de volta a banda media
    if not (RSI_LO <= c["rsi"] <= RSI_HI):
        return False
    st = c["state"]
    if st == "BULL":
        if not _stall_bull(c):
            return False
        # DISCRIMINADOR: entrar so quando o close ja esta no meio/fundo da banda de swing.
        # Consolidacao-de-bull vive colada ao topo (swpos>POS_HI) e rompe de volta para cima antes
        # de descer ao meio => nunca entra. Range genuino oscila e disponibiliza uma barra mid-band
        # => entra e o exit sticky mantem a detecao. Corta range-in-bull na raiz.
        pos = _swing_pos(c)
        if pos is not None and pos > POS_HI_BULL:
            return False
        return True
    if st == "BEAR":
        return _stall_bear(c)
    return False


def exit_range(c, rng_hi, rng_lo):
    new_hh = (c["sw_high"] is not None and c["sw_prev_high"] is not None
              and c["sw_high"] > c["sw_prev_high"] * (1 + EQ))
    new_ll = (c["sw_low"] is not None and c["sw_prev_low"] is not None
              and c["sw_low"] < c["sw_prev_low"] * (1 - EQ))
    if c["close"] > rng_hi and c["bull_gate"] and (new_hh or c["close"] > rng_hi * (1 + EXIT_BUF)):
        return "BULL"
    if c["close"] < rng_lo and c["bear_gate"] and (new_ll or c["close"] < rng_lo * (1 - EXIT_BUF)):
        return "BEAR"
    return None
