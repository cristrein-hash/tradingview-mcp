NAME = "L5 failure-of-progression (EQH/EQL) + RSI mid-band"
LENS = ("RANGE = a tendencia deixa de estender MEANINGFULLY o seu extremo estrutural: em BULL o "
        "swing-high mais recente falha novo high acima de tolerancia EQH (sw_high<=sw_prev_high*"
        "(1+EQ)) sem CHoCH-dn; simetrico em BEAR (EQL). Confluencia = RSI de volta a banda media "
        "(40-60). Sai quando rompe a banda com gate (nova extensao sustentada) para BULL/BEAR.")

RSI_LO, RSI_HI = 40.0, 60.0
EQ = 0.008          # tolerancia EQH/EQL: falha de progressao = novo extremo dentro de +-0.8%
EXIT_BUF = 0.02     # rutura DECISIVA da banda p/ sair de range (evita pokes intra-range flipar)


def _stall_bull(c):
    sh, sph = c["sw_high"], c["sw_prev_high"]
    if sh is None or sph is None:
        return False
    # swing-scale nao faz higher-high MEANINGFUL (EQH ou lower-high)
    struct_stall = sh <= sph * (1 + EQ)
    # confirmacao na escala imediata: pivo imediato tambem estanca (protege os turnos)
    imm_stall = (c["prot_high"] is not None and c["prev_high"] is not None
                 and c["prot_high"] <= c["prev_high"])
    return struct_stall and imm_stall and not c["choch_dn"]


def _stall_bear(c):
    sl, spl = c["sw_low"], c["sw_prev_low"]
    if sl is None or spl is None:
        return False
    # swing-scale nao faz lower-low MEANINGFUL (EQL ou higher-low)
    struct_stall = sl >= spl * (1 - EQ)
    imm_stall = (c["prot_low"] is not None and c["prev_low"] is not None
                 and c["prot_low"] >= c["prev_low"])
    return struct_stall and imm_stall and not c["choch_up"]


def enter_range(c):
    # confluencia: momentum neutralizado (RSI volta a banda media)
    if not (RSI_LO <= c["rsi"] <= RSI_HI):
        return False
    st = c["state"]
    if st == "BULL":
        return _stall_bull(c)
    if st == "BEAR":
        return _stall_bear(c)
    return False


def exit_range(c, rng_hi, rng_lo):
    # Saida = a tendencia VOLTA A ESTENDER: (a) re-extensao ESTRUTURAL (novo swing-extremo
    # significativo alem da banda) OU (b) rutura DECISIVA de preco (buffer) — sempre com gate
    # ortogonal. Os 5 bears fazem onset a partir de BULL/crash (reversao com prioridade), nunca
    # via este exit, logo a banda pode ser "pegajosa" sem por em risco os turnos.
    new_hh = (c["sw_high"] is not None and c["sw_prev_high"] is not None
              and c["sw_high"] > c["sw_prev_high"] * (1 + EQ))
    new_ll = (c["sw_low"] is not None and c["sw_prev_low"] is not None
              and c["sw_low"] < c["sw_prev_low"] * (1 - EQ))
    if c["close"] > rng_hi and c["bull_gate"] and (new_hh or c["close"] > rng_hi * (1 + EXIT_BUF)):
        return "BULL"
    if c["close"] < rng_lo and c["bear_gate"] and (new_ll or c["close"] < rng_lo * (1 - EXIT_BUF)):
        return "BEAR"
    return None
