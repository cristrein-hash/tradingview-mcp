NAME = "L3-eqhl-liquidez"
LENS = ("EQH/EQL a escala SWING (topos~iguais & fundos~iguais = liquidez lateral, entre-tendencias), "
        "assimetrico p/ REJEITAR higher-high (bull) e lower-low (bear), agregado a CONFLUENCIA de "
        "bandas apertadas (bbw baixo = sem expansao de volatilidade = sem tendencia)")

# --- parametros internos (selados apos sweep auditado) ---
EQ_TOL  = 0.045   # tolerancia "igual" no lado equal/lower-high e equal/higher-low (|d|/mid)
HH_TOL  = 0.01    # tolerancia p/ NOVO extremo direcional: >1% acima do topo prev = higher-high (bull) => NAO e range
BBW_MAX = 5.2     # largura Bollinger (4sigma %) maxima = bandas apertadas (range med 4.6 vs bull 6.8 / bear 6.3)

def enter_range(c):
    """De BULL/BEAR -> RANGE. ESTRUTURA (escala swing m=13) + CONFLUENCIA (bandas apertadas)."""
    sh, sph = c["sw_high"], c["sw_prev_high"]
    sl, spl = c["sw_low"],  c["sw_prev_low"]
    if None in (sh, sph, sl, spl):
        return False
    midh = (sh + sph) / 2.0
    midl = (sl + spl) / 2.0
    if midh <= 0 or midl <= 0:
        return False
    # EQH assimetrico: o topo swing atual NAO pode ser um higher-high forte (isso e progressao bull);
    # aceita topo igual ou ligeiramente mais baixo (teto de liquidez) ate EQ_TOL.
    if (sh - sph) / midh > HH_TOL:  return False   # higher-high => uptrend, nao range
    if (sph - sh) / midh > EQ_TOL:  return False   # lower-high demasiado fundo => nao "equal"
    # EQL assimetrico: o fundo swing atual NAO pode ser um lower-low forte (isso e progressao bear);
    # aceita fundo igual ou ligeiramente mais alto (piso de liquidez) ate EQ_TOL.
    if (spl - sl) / midl > HH_TOL:  return False   # lower-low => downtrend, nao range
    if (sl - spl) / midl > EQ_TOL:  return False   # higher-low demasiado alto => nao "equal"
    # CONFLUENCIA de indicador: bandas de Bollinger apertadas (volatilidade contraida = lateral).
    return c["bbw"] <= BBW_MAX

def exit_range(c, rng_hi, rng_lo):
    """De RANGE -> tendencia: rompimento do extremo do range (banda expandida pelo harness) COM
    confluencia do gate ortogonal (dolar/drawdown/run-up). So rompe p/ o lado que o gate confirma."""
    if c["close"] > rng_hi and c["bull_gate"]:
        return "BULL"
    if c["close"] < rng_lo and c["bear_gate"]:
        return "BEAR"
    return None
