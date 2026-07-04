# MTF SIGNATURE GATE TEST · RELATÓRIO FINAL (2026-07-04)

## 1. Executive verdict
**SIGNATURE_GATE_FAIL** — e com diagnóstico definitivo: **a assinatura do discovery fica REFUTADA como artefato de fill-fiction**. No instante das operações do Cris mas com preço REAL de mercado, a cobertura cai de 60% para **6% ≈ controles (8%)**; o "lift 5,7-6,7×" era o desconto do preço-âncora retroativo (mediana 3,29 ATR abaixo do close) inflando as DUAS pernas simultaneamente — uma ilusão de confluência MTF contada duas vezes. Resultado negativo limpo, mecanismo quantificado, prereg cumprido sem re-tuning.

## 2-3. Discovery recap / frozen signature
`supply_far_3atr(15M) AND demand_near_1atr(1H)` — congelada, thresholds imutáveis, implementação verbatim do mapeamento (DA verificou 35/35 idêntico). Discovery doc anotado como REFUTADO.

## 4. Baseline reproduction
N435 · +291,5/+233,6 · 53 runners — fail-loud PASS; universo selado por sha.

## 5. Gated panels (bruto + NET-SB)
- **E1 BASE∩GATE:** N19 · NET +4,5 (**retenção 1,9%**) · **runner-kill 52/53** · nulls random/year/episode = pct 27,6/45,4/38,4 (indistinguível de seleção aleatória).
- **E2 UNIVERSE∩GATE standalone:** N358 (8,0% dos cobertos; 3,77/sem) · **NET −13,6** · DD −52,9 · stk −15 · células: BULL +5,0 (N155) / RANGE −14,7 (N115) / BEAR −3,9 (N88) — nenhuma viável.
- Cobertura de alvos no candidato: 3/35 manuais · **0/21 Sistema A**.
- 240 candidatos da extensão sem cobertura 1H (todos BEAR; excluídos e contados).

## 6-8. WR/streak/DD · runners · robustez
Nenhuma melhoria legítima em eixo algum. Runner-kill quase total não é anticorrelação específica: a preço real no cj, o close está mediana 1,86 ATR60 ACIMA da demanda 1H e o flush cria supply fresco ~0,96 ATR overhead → o gate reprova ~92% de tudo. Anos/células reportados integralmente (nada escondido).

## 9-10. Nulls / DA verdict
Nulls ≈ aleatório nas 3 famílias. DA independente reproduziu tudo do zero, adjudicou o mecanismo (tabela A/B/C/D no doc DA), declarou contaminadas as camadas sugestivas preço-dependentes do discovery e confirmou: **FAIL, sem REVIEW_LAYER** (não há melhoria de contexto/risco a preservar). O null de multiplicidade do discovery não podia capturar o defeito (randomizava rótulos, não preços) — lição metodológica registrada.

## 11. O que vira o quê
- **Nada vira gate ou review layer.**
- **Lição metodológica permanente:** alvos desenhados com âncora de preço retroativa NÃO podem ser comparados a controles a preço real — qualquer lente PREÇO-DEPENDENTE herda o artefato. Futuras leituras do HINDSIGHT_TARGET_SET: reprecificar os alvos ao close real ANTES de qualquer lift.
- **Sobrevive do episódio:** o perfil causal preço-INDEPENDENTE dos 35 (swept 43% vs 100%; entradas mediais; CHoCH recente; absorção/anti-iniciativa; dips quietos) — pistas nunca validadas, mas não refutadas por este teste.
- **Os 21 fora-da-base do Sistema A:** seguem substrato distinto pelo eixo swept/contexto (achado do Lab G), mas NÃO por esta assinatura (0/21, mesma geometria dos demais).

## 12. What remains unknown
Se existe assinatura estrutural real por trás do olho do Cris — o mapeamento precisa ser refeito com alvos reprecificados (close real no t0 dele) antes de qualquer nova lente; as lentes preço-independentes são o ponto de partida não-contaminado.

## 13. Recommendation (dados; decisão Cris)
DISCARD do gate e da assinatura como formulada · registrar a lição de reprecificação como regra de método · se o Cris quiser reatacar o alvo: refazer lifts com preço real (pipeline pronto — 1 variação do mapeamento) antes de desenhar qualquer lente nova.
