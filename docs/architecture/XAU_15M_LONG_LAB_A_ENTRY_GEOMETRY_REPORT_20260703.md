# LAB A — ENTRY GEOMETRY · RELATÓRIO FINAL (2026-07-03)

## 1. Executive verdict

**TRIGGER_GEOMETRY_FAILS** — **escopo obrigatório (DA):** o que falhou é a **EXECUÇÃO PÓS-SINAL** (limit/retest/cap/reclaim depois do sinal completo). O gatilho no NÍVEL DO SINAL (confirmação k3, altura, CHoCH — famílias A1/A3/A4) permanece **NÃO-TESTADO** (BLOCKED por exigir builder re-scan; rodada futura). Dentro do espaço testado: **market no close de cj é a melhor execução — resultado negativo limpo, mecanismo quantificado.**

## 2. Baseline reproduction

S0 market@cj: **bruto +291,5 / líquido-SB +233,6** — reproduzido (fail-loud + verificação independente do DA).

## 3. Variants tested (17 execuções, todas pré-registradas/A6 aceitas; nenhuma omitida)

Grid δ (0,3/0,5/0,8 ATR × W8/16) · mid-risk · pHigh · **4 propostas dos agentes** (CAP20 condicional + vizinhança 1,8/2,2 · RECLAIM fill-on-hold · HLDEF higher-low · CR2 depth c/ piso de custo) · nulls delay cj+2/cj+4 · regime THROUGH (fill exige low ≤ L−$0,40) nas 5 principais. Engine multi-agentes real: 4 perspectivas (mecânica/estrutura/custo-risco/DA-pré), 9 propostas, 4 aceitas por desenho pré-resultado, não-aceitas registradas (SPLIT/CJLOW/MS1/MS3/CR1).

## 4. Gross vs SB-net panel (números pós-correção DA)

| Variante | miss% | bruto | **NET** | DD | r/DD | runners |
|---|---|---|---|---|---|---|
| **BASE market@cj** | 0 | **291,5** | **233,6** | −14,2 | **16,4** | 51 |
| A6_CR2 (melhor alt.) | 11,0 | 269,8 | 207,6 | −17,8 | 11,7 | 49 |
| LIM_0.3ATR_W16 | 10,1 | 264,5 | 198,2 | −22,5 | 8,8 | 46 |
| A6_CAP20 | 17,0 | 238,0 | 179,1 | −26,2 | 6,8 | 47 |
| LIM_pHigh_W16 | 23,4 | 245,8 | 178,1 | −25,7 | 6,9 | 45 |
| NULL_delay_cj2 | 0 | 260,0 | 173,0 | −38,9 | 4,5 | 51 |
| A6_HLDEF | 17,7 | 231,7 | 162,0 | −26,1 | 6,2 | 40 |
| NULL_delay_cj4 | 0 | 244,2 | 153,5 | −43,4 | 3,5 | 44 |
| A6_RECLAIM | 43,9 | 152,7 | 102,6 | −29,4 | 3,5 | 35 |
| LIM_mid_risk | 36,8 | 160,1 | 80,8 | −48,0 | 1,7 | 34 |

THROUGH (anti-otimismo de touch): todas pioram mais 15-50R — o negativo é robusto ao regime de fill.

## 5. risk_usd impact

Limits reduzem risk_usd mediano ($8,2 → $3,7-7,2) e ganham R nos fills (delta pareado +27 a +91R), **mas nunca compensam os winners perdidos**.

## 6. Runner preservation — o mecanismo da falha

**Seleção adversa medida (não presumida):** em TODAS as variantes limit, o base-avgR dos MISSES é 1,4-2,7 vs 0,23-0,55 dos filled — **quem não retesta é justamente o runner** (8-36 runners perdidos por variante). Todo loser atravessa o limit por definição (caminho ao SL passa por L); o winner só enche se voltar. Fill-rate null corrigido: p=0,506 — a melhor variante é **indistinguível de jogar fora 11% da base ao acaso** (a melhora de preço é cancelada 1:1 pela seleção adversa). Delay nulls: atrasar sem profundidade também perde (−60/−80R NET).

## 7. Annual/episode robustness

A6_CR2 perde nos **três anos** (9,8<13,6 · 173,0<183,4 · 24,8<36,6) — 2025 não carrega o veredito. Jackknife-episódio (398 eps): sem dependência de episódio único. **17/17 negativas com o mesmo mecanismo = multiplicidade a FAVOR do negativo** (com esse nº de tentativas, um vencedor espúrio era o esperado; zero apareceu).

## 8. DA verdict

DA independente (real; script `_DA_lab_a_geometry_attack.py`; **não commitou**): achou **2 bugs materiais nos números publicados** — same-bar-stop indevido em entradas at-close (corrompia delay-nulls e RECLAIM; corrigidos: 173,0/153,5/102,6 — "RECLAIM pior de todas" era FALSO, pior é mid-risk) e fill-rate null com custo fixo (p 0,806→0,506). Ataques dissolvidos: horizonte ancorado (Δ=0,0), same-bar em limit fills (física correta), custo SB (física do Lab E; déficit de CR2 é 21,7R bruto + só 4,3R de custo). Script corrigido e re-executado; números do relatório = pós-correção, batem com a verificação independente. Veredito DA: **FAILS escopado a pós-sinal**.

## 9. What changes for Lab B/C/D

- **Lab B (próximo):** intocado e REFORÇADO — se a execução não melhora o painel, o lever restante do formato conhecido é **eliminação por contexto** (cortar losers sem tocar runners). Pontes dos agentes registradas: fills sob banda de supply = pior seleção adversa (leitura para B).
- **Lab C:** SL_CONTEXT herda o aviso — SL mais largo interage com custo (Lab E) e com o trail; avaliar líquido-SB.
- **Lab D:** re-entry paga round-trip por tentativa + herda a física da seleção adversa aqui medida (o retest que enche tende a ser o ruim).
- **Rodada futura (fora de B/C/D):** redesenho no NÍVEL DO SINAL (A1/A3/A4 via builder re-scan) — única via restante para atacar o custo de confirmação; requer bloco próprio.

## 10. Recommendation

- **PRESERVE:** entrada market no close de cj como execução canônica da base #4 (validada contra 17 alternativas).
- **DISCARD:** família limit/retest/cap/reclaim pós-sinal (forbidden path novo — não re-testar sem dados de fill reais que mudem a física).
- **Needs visual review:** NÃO (negativo limpo; nada a inspecionar).
- **Next lab: B — context elimination** (posição-no-regime + supply + room_above como leitura convergente assimétrica).
