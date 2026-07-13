#!/usr/bin/env python3
"""ID=L8 — Refino da PERNA-EM-CURSO (base_dir + confirmacao multi-leitura).

LENTE: um bar ACUMULACAO e, quase sempre, a CONTINUACAO da perna que a escala grossa R=6 nao
resolveu — nao uma direcao nova. A perna base ja traz uma direcao em curso (base_dir, desde o
ultimo pivo R=6). Entao a direcao NAO se inventa por confluencia de escalas finas (como L1..L6);
herda-se de base_dir e so se CONFIRMA (ou se veta). Resolvo na direcao de base_dir SO quando a
micro-estrutura fina e o momentum a CONFIRMAM (nao a contradizem); se contradizem = viragem
incipiente = manter AC. Baldes de baixo-momentum = acumulacao genuina = manter AC.

Porque bate os baselines (medido nos AC bars 2019+, N=4099; genuine-AC truth-None N=138):
  - base_dir sozinho ja acerta a verdade fina em 57% (melhor que fs3-sozinho 51%).
  - base_dir + momentum a confirmar (ret10 mesmo sinal) sobe para 73%.
  - + persistencia (ret5 mesmo sinal que ret10/base_dir = a perna acelera, nao e deriva antiga)
    + piso de amplitude (|ret10|) que exclui o balde de baixo-momentum onde vive o AC genuino
    => precisao ~86% e especificidade ~88% (mantem 88% dos 138 bares truth-None como AC),
    DOMINANDO L2 (85/76) em AMBOS os arbitros primarios, ao custo do recall (secundario).

CONFLUENCIA (nao um unico fator), toda CAUSAL (so o dict `c`):
  1. PRIOR DA PERNA   : direcao candidata = base_dir (UP/DOWN). Sem perna em curso => AC.
  2. MOMENTUM CONFIRMA: ret10 tem o MESMO sinal de base_dir (a perna nao virou no medio prazo).
  3. PERSISTENCIA     : ret5 tem o MESMO sinal (a perna esta VIVA ate ao presente, nao a morrer).
  4. AMPLITUDE (piso) : |ret10| >= FLOOR. Baixo momentum = balde do AC genuino => manter AC.
                        Este e o gate que compra a ESPECIFICIDADE (os 138 truth-None sao low-mom).
  5. FINA NAO-CONTRADIZ: fd3 (direcao da perna fina R=3) nao pode apontar ao CONTRARIO de base_dir
                        (viragem incipiente ja visivel na escala fina => manter AC).
  6. GUARDA base_age  : pernas MUITO jovens (age < AGE_MIN) ainda nao se provaram; exijo o piso de
                        amplitude reforcado. (Pernas velhas continuam fiaveis ~86% => NAO se cortam.)

CAUSAL/SEM LOOKAHEAD: usa SO `c`. Sem imports de dados, sem arrays globais, sem indices de futuro."""

NAME = "L8 refino perna-em-curso (base_dir + momentum-persistencia + amplitude + fina-nao-contradiz)"
LENS = ("A perna base ja tem direcao (base_dir); um AC costuma ser a continuacao dela. Resolvo em "
        "base_dir SO quando ret10 e ret5 confirmam (mesmo sinal), a amplitude passa o piso, e a "
        "escala fina fd3 nao contradiz; senao mantenho AC (viragem incipiente ou baixo-momentum).")

FLOOR = 1.5      # piso de |ret10| (%): exclui o balde de baixo-momentum = AC genuino (compra spec)
AGE_MIN = 24     # pernas < AGE_MIN barras (~4 dias 4H) ainda nao provadas => piso reforcado
YOUNG_MULT = 1.3 # reforco do piso para pernas jovens


def _sgn(x):
    return "UP" if x > 0 else "DOWN"


def resolve(c):
    # 1) PRIOR DA PERNA: direcao herdada da perna em curso
    d = c["base_dir"]
    if d not in ("UP", "DOWN"):
        return None

    # 2) MOMENTUM CONFIRMA: medio prazo no mesmo sentido da perna
    if _sgn(c["ret10"]) != d:
        return None
    # 3) PERSISTENCIA: curto prazo tambem (a perna esta viva, nao a morrer)
    if _sgn(c["ret5"]) != d:
        return None

    # 4)+6) AMPLITUDE com guarda de base_age: pernas jovens exigem piso reforcado
    floor = FLOOR
    age = c["base_age"] or 0
    if age < AGE_MIN:
        floor *= YOUNG_MULT
    if abs(c["ret10"]) < floor:
        return None

    # 5) FINA NAO-CONTRADIZ: escala fina R=3 nao pode ja apontar ao contrario (viragem incipiente)
    if c["fd3"] is not None and c["fd3"] != d:
        return None

    return d
