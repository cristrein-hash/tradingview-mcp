# ENGINE 5 — Transversal: ponto de entrada EXCLUSIVO aos fundos MONSTER+FORTE (PLANO)
*2026-06-28. Vira o problema: estudar SÓ os ~58 MON+FORTE (não varrer o universo). Achar a mecânica de entrada comum + exclusiva. Paradigma contextual por episódio (sequência de reação), multi-agente. Não executado ainda.*

## 0. Por que este é diferente dos 4 anteriores
- E1 descreveu fundos (rótulo forward). E2/E3 = seleção sobre 4502 mínimas → parede ~6% (label≠R). E4 = risk-shaping → beta-sentinel+2025.
- **NOVO ângulo:** não perguntar "qual mínima do universo é forte?" (parede), e sim **"o que os 50 fundos fortes TÊM EM COMUM no momento/sequência de entrada que os torna capturáveis — e que é RARO no resto?"**. Estudo transversal da MECÂNICA DE ENTRADA, não snapshot.

## 1. Objetivo
Encontrar 1+ **gatilho de entrada CAUSAL** que: (a) **capture** a maioria dos ~58 MON+FORTE (recall alto), (b) seja **ESPECÍFICO** (dispara raro no control-set = baixo falso-positivo), (c) renda em R (let-run). Como a perna MON+FORTE é grande, há folga: a entrada pode ser algumas barras após a mínima (confirmação/reteste) e ainda capturar a maior parte.

## 2. Universos
- **STUDY-SET:** 58 MON+FORTE (20 MONSTRO + 38 FORTE) de `reversal_power.csv`.
- **CONTROL-SET:** MED+FRACO (139) + NONE (mínimas fractais não-fundo) — para o teste de especificidade.

## 3. Régua causal
As-of/SHIFT1; HTF 4H/1D nativo (htf_primitives, born_t causal verificado); entry = close do bar de gatilho; SL=flush−0.1ATR; saída let-run (RCAP20/HMAX480). Sem OOS (cânon). Tier = label forward (só p/ definir study/control, nunca feature).

## 4. Fases (paradigma contextual, multi-managed-agents)
- **Fase 0 — Dossiê de mecânica de entrada por episódio** (determinístico): p/ cada um dos 58, reconstruir: perna de baixa (shape/velocidade/profundidade), a mínima, a **SEQUÊNCIA de reação barras +1..+12** (reclaim, sweep+reclaim, micro-HL, CHoCH 15M, retest da demanda, deslocamento), contexto multi-TF 4H/1D (regime/demanda/RSI), e o **melhor ponto de entrada causal** que captura ≥X% da perna com MAE tolerável (mapear ONDE realmente se entra).
- **Fase 1 — Leitores transversais (multi-agente):** cada especialista lê os 58 dossiês buscando a **assinatura de entrada COMUM** (ex.: "todos fizeram sweep+reclaim em ≤k barras", "todos tiveram CHoCH 15M dentro de N barras", "todos retestaram demanda 4H"). Convergência, lentes novas, NÃO contagem cega.
- **Fase 2 — Teste de ESPECIFICIDADE (o gate duro):** a assinatura comum dispara em quantos do CONTROL-SET? precisão = MON+FORTE/(todos que disparam) + R. Se larga (dispara em tudo) → parede confirmada (honesto). Se rara → regra candidata.
- **Fase 3 — Otimização do ponto de entrada:** dado o gatilho, qual barra exata entrar (reclaim vs reteste vs confirmação) maximiza R com MAE baixo; let-run.
- **Fase 4 — DA + R-outcome + plot canônico** (null-of-max, ex-2025, leave-block, concentração, look-ahead; recall+especificidade+R).

## 5. Lentes candidatas (a investigar, não pré-decididas)
Sequência de reação (reclaim_atr/velocidade, sweep+reclaim em ≤k, micro-HL, up-closes, CHoCH 15M, retest-da-demanda-e-segura), profundidade/limpeza da perna, contexto multi-TF 4H/1D (regime/demanda/RSI turning), absorção (bubble SELL + volume climax + reclaim), e COMBOS 2-3. Reuso de E1/E2/E4 como evidência condicional.

## 6. Travas / honestidade
- **Especificidade é o gate** — recall sem especificidade = parede (não vender como vitória).
- n=58 poder baixo: exigir per-ano + leave-block + null-of-max + sem concentração-em-poucos-trades.
- Não perseguir beta-clean-sky-sentinel (já refutado). Não grid cego.
- Se a conclusão honesta for "não há gatilho específico", reportar como dado (a perna grande pode ser entrável só por gestão/let-run amplo, não por gatilho exclusivo).
- Possível need de 5min RAW p/ ponto de entrada fino (reentry-CHoCH) — gate de proveniência ANTES (provável só 15M disponível; usar sequência 15M).

## 7. Decisão pendente (Cris)
Aprovar rodar (sugestão: Fase 0+1+2 primeiro — dossiê → leitores transversais → teste de especificidade — e parar p/ ler antes de otimização/plot).
