# XAU 4H L2/BPT — Trade Qualification Engine (camada de decisão trade-a-trade)

**Status:** `RESEARCH · CAUSAL · RAW · OUTCOME-BLIND REASONING · LEAD VALIDADO (não promovido)` · **Data:** 2026-06-18
Camada de decisão **trade-a-trade** (não regra rígida): para cada episódio L2/BPT, 84 fatores causais → raciocínio multifatorial CEGO ao resultado → TAKE/REVIEW/SKIP + direção. Validado na base completa (276) vs 3 baselines + held-out. Importa TODOS os fatores que geraram positivo nas estratégias anteriores. Sem SLIM, sem look-ahead, sem plotagem, sem produção. Foundation: [[XAU_4H_L2_BPT_ENTRY_DEEP_REFLECTION]] · [[XAU_4H_L2_BPT_BOTTOM_REVERSAL_CONFLUENCE_PREREG]].

---

## 1. Arquitetura (o que torna real e não-circular)
1. **Extrator causal** (`qualification_extract.py`): 84 fatores/episódio, todos ≤ barra de entrada — regime/macro, capitulação/momentum, legpos 30/60/90, demanda 4H/1D, supply overhead/rejection, **Session VP nativo (volume REAL)**, NAS LONG/SHORT first-appearance + NAS numérico, bubbles BUY/SELL/POC (auction), **SMC LuxAlgo BOS/CHoCH**, RSI/estado/divergência (A7), reclaim quality, SL demand-anchored + tipo, anti-topo (F_STRICT), tempo/dead-hour. Cross-asset NÃO usado.
2. **Raciocínio CEGO ao resultado**: 14 subagentes independentes leram a [[QUALIFICATION_RUBRIC]] + um lote de packets (sem realR/exitype) e decidiram trade-a-trade. Decisão explicável (positive/negative_factors + decisive_reason), não score.
3. **Validação na base completa** (276) vs 3 baselines + bootstrap + held-out NON-GT. Decisão cega que ordena o R = edge; se só imita os 10 curados, falha no held-out.

**Auditoria de causalidade (DA ab5e8395):** VP, RSI diário, divergência, demanda, bubbles, NAS, momentum/legpos = CAUSAIS (sem repetir o A1' SUPERTREND). Único vazamento achado e **removido**: similaridade winner/loser-centroid (derivada de outcome) — tirada do packet, vai só p/ diagnóstico.

## 2. Resultado (demand-SL + partial50, unidade = episódio)
| decisão | n | WR | avgR | sumR | maxDD | maxLossStreak |
|---|---|---|---|---|---|---|
| **TAKE** | 32 | **53.1%** | **+0.912** | +29.2 | **4.4R** | 4 |
| REVIEW | 114 | 38.6% | +0.404 | +46.1 | 10.5R | 7 |
| SKIP | 130 | 20.8% | +0.068 | +8.9 | 15.8R | 11 |
| ALL_276 (base) | 276 | 31.9% | +0.305 | +84.2 | 18.7R | 7 |

Ordenação **monotônica** TAKE > REVIEW > SKIP em WR, avgR, DD e streak.

## 3. Testes de hipótese (bootstrap 5000, episódio)
- TAKE vs SKIP: delta **+0.844**, P=0.993, CI95 [+0.16,+1.56] (exclui 0).
- TAKE vs **legpos-random**: delta +0.787, **P=0.994**.
- TAKE vs **state-matched** (legpos+capitulação, mesma mecânica demand-SL): delta +0.794, **P=0.996**.
- TAKE vs **SL-matched** random (DA): **P=0.983** → não é só geometria do SL.
- TAKE vs base incondicional +0.305: P=0.963, CI95 lower +0.25 (**fino** — base já tem drift positivo).
- **Held-out NON-GT** (exclui os 10 curados): TAKE n=29, WR 51.7%, **avgR +0.73** → NÃO é imitação dos curados.
- Confidence calibrada: conf 70+ → avgR +1.545 (WR75%); 40-55 → +0.453.

## 4. Teste decisivo: engine vs regra trivial de 2-3 linhas
Regra `legpos30≤35 & dist_4h_demand≤2 & sl_atr≤2`: n=14, WR57%, avgR +0.890.
- Per-trade o engine **NÃO** bate a regra (delta +0.02, P0.51).
- **MAS** o engine: (a) **2.3× cobertura na mesma qualidade** (32 vs 14 → sumR +29 vs +12); (b) **discrimina dentro da regra** — os 10 TAKE-na-regra = **+1.49R WR70%**, os 4 que rejeitou = **−0.60R WR25%**; (c) acha **22 TAKE fora da regra** = +0.65R que nenhum threshold fixo pega.
→ O valor do raciocínio multifatorial é **generalização + filtragem**, não avgR-por-trade. A regra rígida deixa dinheiro na mesa e aceita losers que o contexto reprova.

## 5. Devil's Advocate (a1c384b6) — veredito equilibrado
Edge **real mas fino**, sobre 2 efeitos conhecidos. **Sobrevive** (bate SL/state/legpos-matched; held-out +0.73; não é tail-driven — mediana +0.90, 10/32 são >+2R; partial50 capa winners em +3.9R). **Limitações honestas:** (1) ~2/3 da seleção re-deriva legpos+demanda (o raciocínio agrega ~+0.27R sobre isso); (2) ~0.13R é geometria tight-SL; (3) n=32 subdimensionado (CI lower +0.25 ≈ base); (4) skew temporal (73% do sumR em 2023-26, beta long-gold); (5) fronteira TAKE/REVIEW fraca (p0.07).

## 6. Relatório final (perguntas do bloco)
- **Melhora a base?** SIM. TAKE WR53/avgR+0.91/DD4.4/streak4 vs base WR32/avgR+0.31/DD18.7; bate os 3 baselines P≥0.99. Monotônico.
- **Quais fatores pesaram?** Eixo dominante: legpos baixo + demanda colada/defendida + SL apertado (V_REVERSAL). Anti-topo (F_STRICT/TOP_EXHAUSTION) = principal driver de SKIP. Supply overhead bloqueando 2ATR = principal driver de REVIEW. Capitulação (drop20+rsi_min) + absorção SELL-bubble + CHoCH bullish = gatilho de TAKE. NAS/VP/SMC/div = confluência de desempate.
- **Quais decisões erradas?** 13/32 TAKE stoparam (−); fronteira TAKE/REVIEW fuzzy; episódio 521 não decidido (imputado SKIP). Acertos notáveis: rejeitou os 4 losers que passavam a regra mecânica; 0 GT-loser em TAKE; 0 GT-winner em SKIP.
- **Vale continuar?** SIM, com olhos abertos: confirmar fora-de-amostra (anos held-out), endurecer fronteira TAKE/REVIEW, e testar se os 22 TAKE-fora-da-regra (contribuição única do engine) seguram. **2 estratégias:** o engine deu 0 SHORT TAKE — a base L2/BPT é detector de reclaim LONG; SHORT exige outra fonte de candidatos (detector de topo/bounce), não esta base.
- **Nada promovido.**

---
## 7. Saídas
`results/l2_bpt_trade_qualification_matrix.csv` (84 fatores) · `..._outcomes.csv` (realR/exitype + similaridade diagnóstico) · `..._decisions_merged.csv` (decisão+razão+R). Scripts: `qualification_extract.py`, `validate_qualification.py`, rubrica `QUALIFICATION_RUBRIC.md`. DA: ab5e8395 (causalidade) + a1c384b6 (refutação). Sem SLIM/look-ahead/plot/produção. Unidade=episódio.
