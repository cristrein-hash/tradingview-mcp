# PREREG — Des-enviesamento E1 (admissão) + E2 (framing). Congelado 2026-07-18 (Cris aprovou).

Resolve a incoerência provada: E1 tinha score enviesado a regime (5/10 pontos de agreement HTF) a
decapitar reversões (104-105 contra-regime mortas por score<2 em 2 dias), "escondido" por limiar baixo.
Simulação provou: de-enviesar por *presença* = desdentado (86% admitido); de-enviesar por *auction
direction-specific* = re-enviesa (0 reversões). **Lever certo = filtro NEUTRO (agnóstico à direção):
atividade de order-flow + colapso de re-disparos.** Validação = FORWARD dia-a-dia (não fit ao visível).

## Camada 1 — E1 admissão (regime SAI do gate)
- **Remover do gate:** `score >= MIN_CONFLUENCE`. `mtf_align` (0-3) e `svp_htf` (0-2) eram os únicos
  eixos que variavam — e eram agreement de regime. Continuam a ser CALCULADOS mas viram CAMPO
  DESCRITIVO no dossiê/candidato (voz p/ E2), **nunca gate**.
- **Novo gate de admissão (tudo agnóstico à direção):**
  1. gatilho (regra estrutural) — como hoje.
  2. materialidade RR/SL band/frescura — como hoje.
  3. **`act_dens >= 0.3`** — atividade de order-flow na perna (mede ATIVIDADE, não lado). Corta fita
     morta. 0.3 ≈ mediana observada (0.27) = "acima do típico morto"; congelado por princípio, forward ajusta.
  4. **colapso de re-disparos** — 1 admissão por `(hora, direção, nível~=round(entry))`, agnóstico à
     regra (colapsa zone_reject + sweep_reclaim no mesmo nível/direção). Complementa cooldown/dedup.
- **Números (sim 2 dias, agnóstica):** act_dens≥0.3 preserva 38 reversões (vs 0 do filtro enviesado);
  act_dens≥0.3 + colapso ≈ **15/dia**, 7 reversões incluídas. Cabe no Max (CLI), **zero SDK/API/custo novo**.

## Camada 2 — E2 framing (F-B: equilíbrio, NÃO inverter viés)
Reescrever `READ_SYS` para tirar o **default de regime** (R1 "regime-como-veredito") SEM passar a
preferir reversões (aviso Cris). Núcleo do texto novo:
> O regime/trend HTF é UMA leitura entre várias, não um veredito. Pesa a CONVERGÊNCIA real: uma reversão
> em exaustão (clímax + absorção + íman não-testado + 1º-pullback maduro) pode ser ALTA-prob CONTRA o
> regime; uma continuação A FAVOR do regime mas sem iniciativa das velas / a subir para um íman contrário
> pode ser BAIXA-prob. Não há default direcional — descreve o que a fita converge.
Ambas as direções podem ser alta ou baixa prob consoante a convergência. Prompt-only; sem números.

## DA / disciplina
- act_dens e colapso = causais (act_dens é da perna fechada; colapso usa bar_time). Sem lookahead novo.
- **Congelado:** floor 0.3, colapso (hora×dir×nível). Mudança = novo prereg. **Árbitro = forward dia-a-dia:**
  o dossiê enriquecido + gate agnóstico alinham o read com o GT do Cris melhor que o viesado? Medido shadow.
- Selftest/âncoras E1+E2 têm de continuar PASS (Âncora A: short-de-hoje sobrevive; sem regressões).

## O que NÃO muda
E2 continua sem pesos numéricos (holístico). E1 continua permissivo por design (recall), mas agora
NEUTRO. Telegram continua alert-only/shadow. Nada de SDK/custo novo.
