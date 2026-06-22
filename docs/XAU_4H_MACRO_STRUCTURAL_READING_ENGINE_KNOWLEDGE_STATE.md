# MACRO STRUCTURAL READING ENGINE — KNOWLEDGE STATE

**2026-06-22.** Síntese curta e auditável do conhecimento adquirido. Documentação apenas — sem análise nova.
Ponto de retomada com clareza.

## 1. Escopo
- **Macro Structural Reading Engine** — camada de PERCEPÇÃO de estrutura macro/contextual, **strategy-agnostic**
  (reusável LONG/SHORT futuro).
- Nasceu da frente **XAU 4H L2/BPT / BOS-CHoCH / Trade Qualification Engine**, mas a leitura é strategy-agnostic.
- **Diagnóstico/calibração, NÃO produção.** Não é AGG_v2, não é regra oficial, não é Telegram.
- Conjunto de ensino: **62 trades** (A26 bull-cortado / B18 bear-aceito / C18 ambíguo), rotulados por revisão visual.

## 2. Linha de commits recentes
| commit | conteúdo |
|---|---|
| 9574c22 | design + censo (122 features, 6 fontes) |
| 7f3c852 | SVP causal as-of-bar (developing; sem shift) |
| d0e5566 | 9 especialistas determinísticos sobre 62 |
| c60bcab | confluence v2 (macro override + late-top) — REFUTADO (piorou) |
| 50db5de | entry-quality specialist — REFUTADO (não separa A/B) |
| 1937d82 | SMC BOS/CHoCH + pivots — causalidade verificada |
| 4770825 | TRAVA: prior failed layers as conditional evidence |
| 04eeb1b | leg-state 4H — REFUTADO por confound de escala |
| e54d87e | D1/weekly backbone determinístico + confluência por agentes |

## 3. Conclusões canônicas
- **macro_v1 / D1+agents preserva bull-run MELHOR que todas as tentativas anteriores** (anchor 12/14 → 13/14).
- **4H leg-state falha** por confundir pullback LOCAL (lower-high/lower-low) com macro-bear leg.
- **entry-quality local NÃO separa A/B** — bons e ruins são pullback-to-demand-perto-de-valor (idênticos).
- **late-top-in-bull é MAJORITARIAMENTE INDISTINGUÍVEL por design** (Auction Theory: o trap é feito idêntico à
  continuação para capturar liquidez). Provado: 4 agentes com toda a evidência sobre o backbone correto não os separam.
- **Perseguir detector perfeito de topo → overfit.**
- **Caminho realista:** preservar bull context + bloquear macro-bear-leg longs + ACEITAR resíduo late-top.

## 4. Knowledge locks
- **Não descartar camadas anteriores só porque falharam isoladamente** (failed primary rule = possível conditional evidence). [trava 4770825]
- **leg-state D1/weekly = backbone macro** (NÃO 4H fractal — confunde pullback local).
- **Prior layers entram como suporte/conflito condicionado** à leg-state, cruzamento interpretável (sem busca cega).
- **SVP causal as-of-bar** (developing; sem shift; só nota de maturidade no início de sessão).
- **SMC BOS/CHoCH + pivots causais** (first-appearance / lookforward capado em i), MAS SMC esparso ~41%.
- **sup_cat/pol_cat = inputs de primeira classe** (codificam CLEAN_SKY/no-overhead vs supply_colada).
- **tick-volume NÃO confiável** — usar Session VP nativo (volume real).
- **macro_leg/hour_utc/demand_age = mortas/proibidas.**

## 5. Resultados-chave (sobre os 62 de ensino)
| método | A-preserve | B-RISK | anchor preserve | anchor block |
|---|---|---|---|---|
| macro_v1 (det) | 20/26 | 5/18 | 12/14 | 0/1 |
| leg-state 4H (det) | 12/26 | 8/18 | 7/14 | 0/1 |
| **D1-backbone + agents** | **20/26** | 3/18 | **13/14** | 0/1 |

**Interpretação:** melhor preservação de bull-run de toda a jornada (13/14); o **B late-top residual continua**
não-bloqueável (auction-irredutível). Lado de preservação resolvido; lado de bloqueio late-top é irredutível.

## 6. Próximos passos possíveis (apenas fila — NÃO iniciar agora)
1. Reflexão estratégica profunda, determinada pelo Cris.
2. Depois, se aprovado: validação **276 + OOS** do princípio (preserva bull / bloqueia macro-bear no quadro completo).
3. Nada iniciado neste bloco.
