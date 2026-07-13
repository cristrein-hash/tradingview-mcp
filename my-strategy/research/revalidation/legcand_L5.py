NAME = "L5 high-precision conservative — momentum-pair + fine-dir consensus + structure non-opposition"
LENS = ("Resolve um bar AC em direcao SO com concordancia forte de >=3 leituras causais e magnitude "
        "clara: (1) momentum em DUAS janelas (ret5 E ret10) alem de +-0.8% no mesmo sentido "
        "[magnitude], (2) consenso da direcao da perna FINA (fd2==fd3) a favor, (3) estrutura fina "
        "(fs2/fs3) NAO oposta. Se qualquer condicao falhar -> mantem AC. Prioriza PRECISAO e "
        "ESPECIFICIDADE (AC-genuino preservado) sobre recall; aceita reducao-AC menor.")

MOM = 0.8   # magnitude minima (%) do retorno em ret5 E ret10 (duas janelas confluentes)


def _fine_dir_consensus(c):
    """direcao da perna fina so quando as escalas R=2 e R=3 concordam (consenso), senao None."""
    if c["fd2"] == c["fd3"] and c["fd2"] in ("UP", "DOWN"):
        return c["fd2"]
    return None


def resolve(c):
    r5, r10 = c["ret5"], c["ret10"]

    # (1) MAGNITUDE + confluencia de momentum: duas janelas (5 e 10 barras) alem do limiar, mesmo sentido
    if r5 > MOM and r10 > MOM:
        d = "UP"
    elif r5 < -MOM and r10 < -MOM:
        d = "DOWN"
    else:
        return None  # momentum fraco/misto -> provavel AC genuino, manter

    # (2) CONSENSO da perna fina (fd2==fd3) tem de existir e apontar no mesmo sentido
    if _fine_dir_consensus(c) != d:
        return None

    # (3) estrutura fina (fs2/fs3) NAO pode opor-se (guarda de precisao + AC-genuino)
    opp = "DOWN" if d == "UP" else "UP"
    if c["fs2"] == opp or c["fs3"] == opp:
        return None

    return d
