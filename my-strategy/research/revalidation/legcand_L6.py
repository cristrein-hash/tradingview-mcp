NAME = "L6 · velocidade/aceitacao direcional (corrida de closes)"
LENS = ("Direcao pela TRAJETORIA: corrida de closes na mesma direcao (ret5/ret10/ret20 mesmo sinal) "
        "com pace-por-barra que NAO desacelera (v5>=v20) = aceitacao; alterna/comprime = mantem AC.")

# --- L6: velocidade / aceitacao direcional ------------------------------------------------------
# Leitura DINAMICA (nao snapshot): a direcao emerge de uma corrida de closes que acelera, nao de um
# unico retorno. Resolve so quando CINCO leituras convergem; senao devolve None (mantem ACUMULACAO):
#
#   (1) MOMENTUM-RUN  : ret5, ret10 e ret20 todos do mesmo sinal (corrida coerente de closes).
#                       Sinais que alternam entre janelas = lateralizacao => mantem AC.
#   (2) ACEITACAO     : pace-por-barra recente nao desacelera vs o pace longo (v5 >= v20*0.6).
#                       Se o recente COMPRIME muito abaixo do antigo => a corrida esta a morrer => AC.
#   (3) MAGNITUDE     : piso de |ret10| macro-aware (RANGE exige corrida mais forte, pois e onde vive
#                       a acumulacao genuina; tendencia macro tolera um piso menor).
#   (4) ESTRUTURA FINA: a direcao da corrida nao pode CONFLITAR com a perna fina R=3 (fd3).
#   (5) PRIOR DA PERNA: a direcao alinha com a perna em curso (base_dir) — continuacao, nao contra-
#                       corrente isolada; alinhar reduz fragmentacao e sobe precisao/especificidade.

def resolve(c):
    r5, r10, r20 = c["ret5"], c["ret10"], c["ret20"]

    # (1) corrida direcional: os tres retornos partilham o sinal
    if not ((r5 > 0) == (r10 > 0) == (r20 > 0)):
        return None
    d = "UP" if r10 > 0 else "DOWN"

    # (3) magnitude minima da corrida (macro-aware)
    floor = 0.50 if c["macro"] == "RANGE" else 0.25
    if abs(r10) < floor:
        return None

    # (2) aceitacao: o pace-por-barra recente nao comprime muito abaixo do pace longo
    v5, v20 = abs(r5) / 5.0, abs(r20) / 20.0
    if v5 < v20 * 0.6:
        return None

    # (4) confluencia com a perna fina R=3 (sem conflito de direcao)
    if c["fd3"] is not None and c["fd3"] != d:
        return None

    # (5) alinhamento com a perna em curso (continuacao coerente)
    if c["base_dir"] is not None and c["base_dir"] != d:
        return None

    return d
