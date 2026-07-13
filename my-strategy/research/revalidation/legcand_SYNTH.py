#!/usr/bin/env python3
"""ID=SYNTH — Sintese das melhores lentes (L8 ancora + L7 aceleracao/dupla-fina + L5 conservadorismo).

Combina, medido no harness, as tres ideias que provaram valer nos candidatos:

  * L8  — ANCORA na PERNA-EM-CURSO: um bar ACUMULACAO e quase sempre a CONTINUACAO da perna que a
          escala grossa R=6 nao resolveu, NAO uma direcao nova. Logo a direcao NAO se inventa por
          confluencia de escalas finas (L1..L6 = ~51%, moeda-ao-ar); herda-se de base_dir (~57%
          sozinho) e so se CONFIRMA. Este e o esqueleto vencedor (87%/88%).
  * L7  — ACELERACAO PERSISTENTE em TRES horizontes (ret5/ret10/ret20 coerentes) + consenso da DUPLA
          escala fina (fd3 E fd4). A medicao de L7 mostrou que a rota momentum+estrutura-fina e a
          unica com substancia (~85-86%); momentum multi-horizonte que PERSISTE ate ao presente
          distingue perna viva de deriva antiga.
  * L5  — CONSERVADORISMO: preferir PRECISAO + ESPECIFICIDADE a recall; resolver so com magnitude
          clara e guardas de nao-oposicao, aceitando reducao-AC menor.

Medido nos AC bars 2019+ (N=4099; genuine-AC truth-None N=138): base_dir 57% -> +ret10 73% ->
config final 87%/93% (a ancora L8 + o gate de aceleracao ret20 de L7 empurra a especificidade de
88% para 93% ao mesmo pico de precisao 87%, com a MENOR fragmentacao de todos os candidatos, 260).

CONFLUENCIA (toda causal, so o dict `c`), por ordem de aplicacao:
  1. PRIOR DA PERNA    : direcao candidata = base_dir (UP/DOWN). Sem perna => manter AC.
  2. MOMENTUM CONFIRMA : ret10 mesmo sinal de base_dir (a perna nao virou no medio prazo).
  3. PERSISTENCIA      : ret5 mesmo sinal (a perna esta VIVA ate ao presente, nao deriva antiga).
  4. ACELERACAO (L7)   : ret20 mesmo sinal E |ret20| >= RET20_FLOOR. Exigir o TERCEIRO horizonte
                         longo com piso alto = a perna acelera de forma sustentada; e o gate que
                         empurra a ESPECIFICIDADE de 88% -> 93% (os 138 truth-None sao baixa-amplitude
                         e nao passam este piso) sem custar precisao.
  5. AMPLITUDE (piso)  : |ret10| >= FLOOR (age-ajustado). Segundo piso, no horizonte medio.
  6. FINA NAO-CONTRADIZ: nem fd3 nem fd4 (micro-pernas R=3/R=4) apontam ao CONTRARIO (viragem
                         incipiente ja visivel na dupla escala fina => manter AC). Exigir as DUAS
                         escalas (ideia L7) endurece a guarda sem inventar direcao. fd4 e "gratis":
                         baixa a fragmentacao sem custar precisao/especificidade (medido).
  7. GUARDA base_age   : pernas jovens (< AGE_MIN) exigem piso |ret10| reforcado (nao provadas).

NOTA de calibracao (Regra 3, confluencia nao um-so-fator): testei a guarda de ESTADO fs3==opp (ideia
L5); removida — media 87->85 precisao (removia resolucoes disproporcionalmente CORRETAS). Mantive so
as guardas de DIRECAO fina fd3/fd4, que sao neutras-a-boas. O gate ret20 e o unico que sobe a
especificidade sem tocar a precisao => e a alavanca escolhida do arbitro.

CAUSAL/SEM LOOKAHEAD: usa SO `c`. Sem imports de dados, sem arrays globais, sem indices de futuro."""

NAME = "SYNTH base_dir-core (L8) + aceleracao-3H ret20 & dupla-fina (L7) + conservadorismo (L5)"
LENS = ("Herda a direcao da perna em curso (base_dir) e resolve SO quando ret5, ret10 e ret20 a "
        "confirmam (mesmo sinal, aceleracao persistente com |ret20|>=2.5 e |ret10|>=piso) e as duas "
        "escalas finas fd3/fd4 nao a contradizem; senao mantem AC (viragem incipiente ou baixo-mom).")

FLOOR = 1.5        # piso de |ret10| (%): horizonte medio (age-ajustado)
RET20_FLOOR = 2.5  # piso de |ret20| (%): aceleracao sustentada no horizonte longo (compra spec 88->93)
AGE_MIN = 24       # pernas < AGE_MIN barras (~4 dias 4H) ainda nao provadas => piso |ret10| reforcado
YOUNG_MULT = 1.3   # reforco do piso |ret10| para pernas jovens


def _sgn(x):
    return "UP" if x > 0 else "DOWN"


def resolve(c):
    # 1) PRIOR DA PERNA: direcao herdada da perna em curso (nao inventada)
    d = c["base_dir"]
    if d not in ("UP", "DOWN"):
        return None
    opp = "DOWN" if d == "UP" else "UP"

    # 2) MOMENTUM CONFIRMA + 3) PERSISTENCIA: medio E curto prazo no sentido da perna
    if _sgn(c["ret10"]) != d or _sgn(c["ret5"]) != d:
        return None

    # 4) ACELERACAO (L7): terceiro horizonte longo coerente e com piso alto => empurra especificidade
    if _sgn(c["ret20"]) != d or abs(c["ret20"]) < RET20_FLOOR:
        return None

    # 5)+7) AMPLITUDE |ret10| com guarda de base_age (pernas jovens => piso reforcado)
    floor = FLOOR
    age = c["base_age"] or 0
    if age < AGE_MIN:
        floor *= YOUNG_MULT
    if abs(c["ret10"]) < floor:
        return None

    # 6) FINA NAO-CONTRADIZ (dupla escala R=3/R=4): nem fd3 nem fd4 apontam ao contrario
    if c["fd3"] == opp or c["fd4"] == opp:
        return None

    return d
