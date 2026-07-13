NAME = "L3-macro-prior-fine-confluence"
LENS = ("Macro 1D como PRIOR bayesiano assimetrico sobre confluencia fina: fd3(perna fina R=3) + "
        "sinal de momentum ret10 + ret5 tem de CONVERGIR na mesma direcao; o macro nao decide a "
        "direcao (a verdade fina R=3 e macro-independente e o drift-up domina), serve de prior que "
        "AFROUXA a barreira a favor do regime e a APERTA contra o regime — abstem em choppy/conflito")

# --- parametros internos (selados apos sweep na grelha de AC bars) ---
WITH_GATE    = 0.8   # |ret10|% minimo p/ resolver A FAVOR do regime macro (ou em RANGE, prior neutro)
AGAINST_GATE = 1.5   # |ret10|% minimo p/ resolver CONTRA o regime macro (prior exige momentum forte)

def _sgn(x):
    return "UP" if x > 0 else "DOWN"

def _prior(macro):
    # macro 1D como expectativa direcional; RANGE = sem prior direcional (neutro)
    return {"BULL": "UP", "BEAR": "DOWN"}.get(macro)

def resolve(c):
    """So chamado em barras ACUMULACAO. Confluencia estrutura-fina + momentum, arbitrada pelo
    prior macro. None = manter AC (choppy, ou leituras em conflito, ou momentum insuficiente)."""
    a = c["fd3"]                       # direcao da perna FINA em curso (R=3), causal
    b = _sgn(c["ret10"])               # momentum medio (10 barras 4H)
    d = _sgn(c["ret5"])                # momentum curto (5 barras) — confirma o timing
    # 1) CONFLUENCIA dura: estrutura fina e ambos os momentums tem de concordar. Sem consenso => AC.
    if not (a == b == d):
        return None
    # 2) PRIOR macro: gate assimetrico sobre a magnitude do momentum.
    p = _prior(c["macro"])
    m = abs(c["ret10"])
    gate = WITH_GATE if (p is None or a == p) else AGAINST_GATE
    if m < gate:
        return None                    # momentum insuficiente p/ o que o prior pede => AC genuino
    return a
