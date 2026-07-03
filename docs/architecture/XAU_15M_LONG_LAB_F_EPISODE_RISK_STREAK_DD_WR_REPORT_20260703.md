# LAB F — EPISODE RISK / STREAK / DD / WR · RELATÓRIO FINAL (2026-07-03)

## 1. Executive verdict
**NO_STREAK_DD_WR_SOLUTION** — nas 26 variantes (13 configs congeladas × 2 baselines), **nenhuma bate os nulls** (p 0,13-0,98; α Bonferroni 0,004), nenhuma atinge PASS_STRONG, e a única que atinge os eixos WR/streak do FundedNext (F2_max1c na linha P1: WR 50,0 · stk −5) o faz **destruindo a estratégia** (retention 33,8%, mata 70% dos runners) = FAIL pelo critério duro. Sub-veredito positivo único: **F4 sizing = RISK_CONTROL_FOUND_NOT_EDGE** (retention 93-94%, DD −12 a −18%, pior mês melhora, zero runner-kill — mas não toca WR nem streak).

## 2. Baseline reproduction
Fail-loud OK nas duas linhas: BASE +233,6 NET-SB (WR 46,0 · DD −14,2 · stk −8 · run 53) e BASE+P1 +257,1 (46,7 · −13,5 · −8 · 56). Exit materializado com R==R0 em 435/435 (D1). Concorrência declarada (D11): máx 4 posições abertas; 108/100 entries com posição aberta — streak/DD de conta ≠ sequência de R.

## 3. Streak anatomy (insumo comum)
97% da dor concentrada (15 intra-episódio + 20 ≤2 semanas de 36 loss-runs≥3). **Achado estrutural do discovery: loss-clusters e runner-bursts são os MESMOS clusters (fail-then-fire; ex. 2024-07-31: 3 runners ~+24R disparam DEPOIS de losses no mesmo cluster/semana)** — qualquer regra chaveada em "losses recentes" taxa exatamente os trades que pagam o sistema. Este é o mecanismo unificador dos negativos abaixo.

## 4. Variants tested (ledger integral; nulls D9 + calendar-shuffle; regra causal exit-realizado D2)
Painel NET-SB, linha BASE | linha P1 (retention da própria linha):

| Config | NET B | ret | stk | run | NET P1 | ret | stk | run | nulls |
|---|---|---|---|---|---|---|---|---|---|
| BASELINE | 233,6 | 100 | −8 | 53 | 257,1 | 100 | −8 | 56 | — |
| F1_cd8/24/96 | 193/189/161 | 83/81/69 | −7/−8/−7 | 46/44/35 | 216/207/169 | 84/80/66 | −8/−8/−6 | 50/47/38 | p≥0,13 |
| F2_max1c | 78,5 | 34 | **−5** | 15 | 87,0 | 34 | **−5** | 17 | p≥0,24 |
| F2_max2c | 121,4 | 52 | −5 | 25 | 128,8 | 50 | −5 | 28 | p≥0,30 |
| F2_max2day | 171,1 | 73 | −7 | 42 | 191,5 | 74 | −7 | 46 | p≥0,76 |
| F3_br2 (regra prereg) | 180,0 | 77 | −7 | 41 | 199,3 | 77 | −6* | 44 | p≥0,46 |
| F3_br3 | 202,7 | 87 | −9 | 46 | 227,6 | 88 | −7 | 49 | p≥0,60 |
| F5_daily3 | 230,7 | 99 | −7 | 52 | 254,4 | 99 | −7 | 55 | p≥0,38 (+shuffle 0,48) |
| F5_wk5 | 198,3 | 85 | −8 | 48 | 216,5 | 84 | −8 | 50 | p≥0,88 (+shuffle 0,96) |
| **F4_sz 1/0,5/0,25** | **219,6** | **94** | −8 | 51† | **238,3** | **93** | −8 | 52† | sizing (sem null de seleção) |
| F8a/b_abort8 | 203,5/203,3 | 87 | **−13** | 48 | 228,3/229,0 | 89 | **−13** | 51/52 | p≥0,85 |

\*lente exit-order: −7 · †threshold ponderado, zero runner morto de fato.

## 5. WR/DD/streak panel — leitura por eixo FundedNext
- **WR:** NENHUMA config passa de 50% sem destruir o sistema (max1c 49,2/50,0 com 34% retention). F8 DERRUBA WR (46→42,5; converte 13-17 winners em pequenas losses).
- **Streak:** melhoras chegam a −5 só via amputação (max1c/max2c); F8 piora para −13; o resto fica em −6/−9. Na lente de conta (exit-order) vários pioram 1.
- **DD:** F4 é o único ganho limpo (−14,2→−12,4 · −13,5→−11,3; q95 bootstrap 19,9→18,5 na P1); F2_max2c chega a −7,9 mas com 50% do lucro.

## 6. SB-net retention
F5_daily3 99% (cosmético, Δ−2,9R) · F4 93-94% · F3_br3 87-88% · F8 87-89% · F5_wk5 84-85% (delta negativo em qualquer atribuição, shuffle p 0,96-0,98) · F1 66-84% · F2 34-75%. **Nenhuma config compra melhora material de WR/streak com ≤25% do lucro.**

## 7. Runner preservation
Runner-kill: F2_max1c 38-39 (7 do top-10, ~215R) · F2_max2c 28 · F1_cd96 18 · F3_br2 12 · F2_max2day 10-11 (incl. o dia 2024-07-31 inteiro) · F8 4-5 (claim "intocados por construção" do prereg era FALSO — corrigido pelo DA) · F5_daily3 1 · **F4 zero**.

## 8. FundedNext proxy impact
A base já falha WR≥50 e stk≤6 (4/6). Nenhuma variante melhora o score FN de forma legítima; F4 e F5_daily3 mantêm 4/6 com DD/pior-mês mais suaves (F4: pior mês −5,0→−4,1 / −4,7→−4,1). Limitações declaradas: floating não modelado; consistency-rule (best day +23,7R vs 2024 +13,6R) = risco operacional registrado, fora do escopo das famílias.

## 9. Null/DA verdict
DA independente (não commitou; verificado): **1 bug material** (término da pausa do F3 — corrigido: br2 BASE DD −20,0→−16,9; "br2 piora DD" era parcialmente artefato) + **2 desvios de prereg no F5** (calendar-shuffle e bounds entry-time — adicionados). Réplicas independentes: F1 kept-sets idênticos, F4 causal 0 violações, F8 0 mismatches, 3 painéis recomputados dígito a dígito, determinismo byte-idêntico. Vereditos: F4 CONFIRMA_POSITIVO (só risk-control) · demais CONFIRMA_NEGATIVO. Global do DA: NO_STREAK_DD_WR_SOLUTION. Doc: `..._DA_20260703.md`.

## 10. What changes for Lab B/C/D
- **Ponte F6 (tier):** exige contexto estrutural → Lab B rodada estrutural (box-pos/banda do regime anterior) segue sendo a via para tier de qualidade.
- **Ponte F7/Lab D (re-entry):** dados do discovery: fail-then-retry carrega +259R NET (mais que o NET total) e retry rápido ≤8b é o MELHOR subgrupo pós-loss (WR 46,9) — disciplina de re-entry NÃO pode banir retry rápido; candidata natural deferida: **exposure-overlap** (nova entry com posição do cluster ainda aberta: WR 6,2%, 1/16 — n minúsculo, precisa mais dados).
- **Lab C (SL_CONTEXT):** herda a lente de conta (exit-order) e o aviso de custo.
- **Defers registrados:** dor de 2-semanas (nenhuma família alcança) · consistency-rule FN · floating no proxy · RAW estendido re-run.

## 11. Recommendation (dados; decisão = Cris)
- **Preserve:** base #4 intacta (nenhum controle de exposição melhora o painel de forma legítima); **F4 sizing 1,0/0,5/0,25 por chain_pos causal como CANDIDATO de camada de conta prop** (RISK_CONTROL_FOUND_NOT_EDGE: −12/−18% DD, 93-94% retention, zero kill) — se adotado, é regra de SIZING operacional, não mudança de estratégia; requer decisão explícita do Cris.
- **Discard:** F1 cooldown · F2 max-trades (incl. max1c: ótica FN por amputação) · F3 breaker · F5 weekly · F8 abort (piora os dois eixos FN).
- **Sem efeito:** F5 daily-3R (cinto de segurança cosmético; manter como higiene operacional é decisão de conforto, não de painel).
- **O eixo WR/streak permanece NÃO-RESOLVIDO** após Lab A (trigger/execução) e Lab F (exposição/episódio/calendário/sizing/abort). O que os dois labs estabelecem em conjunto: a dor é estrutural do perfil swept-runner (WR ~46-47 com convexidade fail-then-fire); os caminhos restantes não testados: contexto estrutural profundo (Lab B r2), SL_CONTEXT (Lab C), re-entry disciplinada (Lab D), e RAW estendido. Continuidade = decisão Cris.
