import os
NAME = "L4-confluencia-estrutura-momentum"
LENS = ("Cruzamento lagging(estrutura fina fs3/fs4) x leading(momentum ret10/ret20): resolve so quando "
        "a estrutura fina aponta uma direcao (fs3 ou fs4 direcional, nenhuma escala em oposicao) E o "
        "momentum (ret10 E ret20) confirma a mesma direcao. Discordancia = incerteza = manter AC.")

MOM_THR = float(os.environ.get("MOM_THR", "1.3"))  # joelho da fronteira: max precisao+especificidade com cobertura util

def _struct_dir(c):
    s3, s4 = c["fs3"], c["fs4"]
    up = (s3 == "UP") or (s4 == "UP")
    dn = (s3 == "DOWN") or (s4 == "DOWN")
    if up and not dn: return "UP"
    if dn and not up: return "DOWN"
    return None

def _mom_dir(c):
    r10, r20 = c["ret10"], c["ret20"]
    if r10 > MOM_THR and r20 > MOM_THR:  return "UP"
    if r10 < -MOM_THR and r20 < -MOM_THR: return "DOWN"
    return None

def resolve(c):
    sd = _struct_dir(c)
    if sd is not None and sd == _mom_dir(c):
        return sd
    return None
