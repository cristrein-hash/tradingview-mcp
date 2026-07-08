# L2/BPT Trend-Exit — Execution/Risk Layer · Devil's Advocate

**2026-07-08.** Checagem adversarial da camada exec/risco. Read-only. Ambos os scripts reproduzem byte-level; baseline fail-loud PASSOU (SELECT-17 +105.3R/DD−4.1/stk3; FULL-245 +399.2R/DD−71.8/stk22). Sem look-ahead no exit-sim.

> **CORREÇÃO DE ENQUADRAMENTO (Cris 2026-07-08):** a estratégia oficial é **seletiva (SELECT-17 + trend-exit)** e **NÃO** pretende acionar os 245. **FULL-245 = STRESS TEST / controle adversarial, NÃO critério de rejeição da estratégia seletiva.** A crítica do DA ao universo 245 mantém-se **como stress test**; o DD−72/streak22 pertence ao universo amplo, não à estratégia aprovada. O ponto substantivo que fica: a tameness dos 17 vem da **seleção calibrada in-sample** → gate pré-produção = **validar essa seleção forward** (não é look-ahead; são os parâmetros que precisam de robustez). Veredito reformulado: `FULL_UNIVERSE_STRESS_RISK_IDENTIFIED` + `SELECTIVE_STRATEGY_REQUIRES_CAUSAL_ENTRY_FORMALIZATION_BEFORE_PRODUCTION`. Estratégia oficial **NÃO invalidada**; produção **NÃO bloqueada por DD do universo amplo**.

## Veredito (universo amplo, stress): `RISK_CONTROL_ONLY` — nenhuma variante mecânica torna o **universo 245** prop-compatível. **Aplicado à estratégia seletiva aprovada, isto é stress test, não bloqueio** (ver correção acima).

## Ataques
**A. Sizing como maquiagem = CONFIRMADO (no free lunch).** Toda camada custa sumR ou é neutra; nenhuma adiciona edge. SELECT-17: hold-cap360 −29R, hold-cap240 −39R, partial −49R, sw≤60 −50R. FULL-245: DD-guard corta DD −72→−16 mas custa **−357R** (399→+41.7); concurrent-2 −280R (→+119). As "neutras" (DD-guard/streak-pause nos 17) só são neutras porque a seleção-17 nunca as dispara. **Nenhuma é alfa.** O script é auto-honesto ("SEM veredito").

**B. DD/streak escondido = CONFIRMADO — a segurança é a SELEÇÃO DE ENTRADA, não a camada de risco.** Achado central: a MESMA lógica de exit/risco no full-base dá **DD −71.8 / streak 22**. O −4.1/streak-3 é 100% propriedade do pick retrospetivo dos 17 (`keep()` = regra de posição-em-zona com thresholds `amp/3`/`≥15`bar/`180`d **afinados a mão neste dado** para excluir os bears 2023 "prematuros"). **O DD honesto da estratégia mecânica é −72R / streak 22, não −4.1R / streak 3.** O −4.1 é sobrevivente-de-hindsight, não frequência-sobrevivível.

**C. Gap risk = real mas sub-modelado; secundário.** Buffer −0.5/−1R nos STOP>80pt quase não mexe (worst −2.35R). Mas o modelo é fino: só penaliza o gap do stop de entrada, não gaps adversos durante os holds de 83d; num stop de 173pt (2025-10-21) um gap de 2R (~346pt) é fisicamente possível num choque macro do ouro → real pode passar de −2.35R. **Real e sub-modelado nos 4 stops largos 2025, mas 2ª ordem — não bloqueia sozinho.**

**D. Hold exposure = CONFIRMADO pesado.** Mediana 54d, máx 83d, **805 trade-days em 17 trades, até 3 posições concorrentes**. Os winners SÃO os holds longos (todos os 6 CAP-500 + 4 BEAR = os +9 a +21R; os 7 STOP são holds curtos). **~78% do ganho = horizonte/exposição.** Para conta FundedNext (daily-loss, margem única) sentar 3 golds concorrentes de meses = marginal-a-inoperável.

**E. Seleção-17 = CONFIRMADO showcase.** 17 trades / 6 anos = **2.8/ano**. Rumo ao universo deployável (245) as MESMAS regras dão DD −72 / streak 22. Nem a de-concentração mais suave (concurrent-2) baixa streak abaixo de 12. **Não há interpolação suave entre "17 escolhidos" e "mecanicamente deployável" — frequência e DD/streak explodem juntos.**

**F. Prop/FundedNext = NENHUMA variante passa streak≤5 no base deployável.** Worst-streak full-base em TODAS as 13 variantes: min **12**, max 22. **Nenhuma ≤5.** DD-guard@−15 (+41.7R) tem streak 12; concurrent-2 (+119R) tem streak 12/DD−18.4. Só o pick-17 tem streak 3 (não é regra tradeável forward). **Sob streak≤5, não há variante mecânica prop-compatível.**

**G. #6 = cap ajustado ao #6, ainda ≠ +3R discricionário.** hold-cap leva #6 1.15→2.55 (cap360)/2.01 (cap240), MAS o cap que ajuda o #6 custa 29-39R à carteira e o #6 ainda fica aquém dos +3R. **Cosmético/fitting, não melhoria mecânica.**

**H. Produção — pendente (reformulado).** O que o stress test do **universo 245** mostra: DD/streak explodem e nenhuma camada os leva a streak≤5 sem destruir ~80-90% do R (F). **MAS a estratégia aprovada é seletiva (17), não o universo 245** — logo o gate real não é "DD dos 245", é: (1) **validar forward a seleção calibrada in-sample** (B/E — o filtro de entrada é causal mas os parâmetros foram afinados neste dado); (2) definir **execução/risco sobre a seleção** — exposição (D, 3-concorrentes/meses) e gap nos 4 stops largos 2025 (C, 2ª ordem). Frequência 2.8/ano é **por design** (estratégia extremamente seletiva), não defeito.

## Nota
Objeção não é ao código (limpo, determinístico, auto-honesto — imprime "SEM veredito"). É a qualquer narrativa que leia −4.1R/streak-3 como o perfil de risco da estratégia. Não é. O perfil real é **−72R / streak 22**, e a camada só o troca por menos a um custo de R íngreme, sem atingir compatibilidade prop. Status `USER_APPROVED_OFFICIAL_NOT_PRODUCTION` está correto e **não deve avançar**.
