# XAU 4H L2/BPT — EPISODE READING 276 REPORT

**2026-06-23.** Primeira biblioteca de LEITURAS VIVAS dos 276 episódios, sob o canon episódico. Diagnóstico; sem
produção/promoção/OOS. Outcome NUNCA foi input da leitura (input stripado). Leitura NÃO virou score (canon).

## O que foi feito
- **Canon persistido** (`docs/XAU_4H_L2_BPT_EPISODE_READING_CANON.md` + memória): a unidade é o EPISÓDIO, não o trade.
- **Context Assembler** montou 276 pacotes vivos legíveis (sequência 4H real + path DSPA + 1D/weekly + regime_B +
  engine states + SVP + supply/demand + indicadores). Código montou, não julgou.
- **14 agentes-leitores** leram os 276 caso a caso (input SEM outcome), produzindo leitura narrativa: episode_type,
  papel do trade, narrativa da sequência, conditioning principal, fatores que mudaram de sentido, decisão provisória,
  convicção qualitativa, gatilhos de invalidação, incerteza. NÃO somaram flags; o canon (conditioning do timeframe
  superior) fez o trabalho discriminador em todos os lotes.

## Distribuição dos episode_types (276)
BULL_PULLBACK 85 · MARKUP_CONTINUATION 68 · **LEGITIMATE_BEAR_BUY 36 · BEAR_PULLBACK_TRAP 37** · REVERSAL_RUNNER 12 ·
SUPPLY_REJECTION 12 · RANGE_ABSORPTION 11 · UNKNOWN_CONFLICT 8 · DISTRIBUTION_TOP 7. Decisões: TAKE 140 · REVIEW 64 · SKIP 72.

## Auditoria pós-leitura (diagnóstico, base runner 26% / loser 61% / 30 monumentais)
**A leitura é ASSIMETRICAMENTE competente:**
| episode_type | n | runner% | rLift | loser% | mon |
|---|---|---|---|---|---|
| **BEAR_PULLBACK_TRAP** | 37 | 14 | **0.52** | 65 | 1 |
| **SUPPLY_REJECTION** | 12 | 8 | **0.32** | 92 | 1 |
| LEGITIMATE_BEAR_BUY | 36 | 28 | 1.06 | 61 | 4 |
| MARKUP_CONTINUATION | 68 | 28 | 1.07 | 54 | 11 |
| BULL_PULLBACK | 85 | 31 | 1.17 | 58 | 10 |
| RANGE_ABSORPTION | 11 | 45 | 1.74 | 45 | 1 |
| REVERSAL_RUNNER | 12 | 17 | 0.64 | 83 | 0 |
Por decisão: TAKE lift 1.10 · REVIEW 1.08 · **SKIP lift 0.75 (loser 69%)**.

## Os achados vivos principais
1. **A leitura é FORTE no lado SKIP/TRAP** — BEAR_PULLBACK_TRAP (0.52) e SUPPLY_REJECTION (0.32) são limpamente
   runner-pobres; o SKIP da leitura (0.75) evita runners e concentra losers. **A leitura sabe o que EVITAR.**
2. **A leitura é MAIS FRACA no lado TAKE/legítimo** — LEGITIMATE_BEAR_BUY 28% ≈ base; o rótulo "compra legítima" não
   concentra runners fortemente além do beta. RANGE_ABSORPTION surpreende (1.74) — a leitura pode estar sub-valorizando.
3. **Par central separa (28 vs 14, 2:1)** — mas o valor mora na identificação da ARMADILHA, não no resgate do runner.
4. **REVERSAL_RUNNER (12) falhou (0.64)** — os leitores rotularam 12 como reversal-runner mas não correram (o rótulo
   de runner antecipado errou; a convicção não bateu o desfecho).

## Mislabel vs engine — a leitura corrige?
- skip-winners RECUPERADOS (runner em SKIP-engine, leitura=TAKE): **9/37**.
- loser-takes CORTADOS (loser em TAKE-engine, leitura=SKIP): **9/86**.
- **MONUMENTAIS preservados (leitura TAKE/REVIEW): 25/30; PERDIDOS (leitura SKIP): 5/30.**
- **Leitura SUPERA o engine em 18 episódios.**

## Conflitos / erros da leitura (para PLOTAGEM, não pós-racionalização)
- **5 MONUMENTAIS SKIPADOS errados:** 391 (DISTRIBUTION_TOP, +10.4), **4926 (BEAR_PULLBACK_TRAP, +18.0 — a continuação
  do fundo 2023-03 que a leitura cortou)**, 4996 (BULL_PULLBACK, +15.4), 7232 (UNKNOWN_CONFLICT, +18.7), 9215
  (SUPPLY_REJECTION, +17.1). Estes são os erros mais caros da leitura.
- **14 SKIP-mas-RUNNER** (winners ainda perdidos) + **81 TAKE-mas-LOSER** (falsos positivos, parcialmente esperado num
  base de 61% loser). Lista completa em `l2_bpt_episode_reading_plot_list.csv` (32 casos críticos).

## Padrões reais vs pós-racionalização
- REAL: o conditioning do timeframe superior (weekly/cascade) separa trap de dip — confirmado nos 14 lotes
  independentemente; a leitura corta limpo bear-traps e supply-rejections.
- A REFINAR: o lado TAKE (legitimate-buy) é fraco; os 5 monumentais skipados mostram onde o conditioning falha — em
  continuações pós-fundo (4926), em conflitos rotulados UNKNOWN/SUPPLY_REJECTION que na verdade correram (7232, 9215).

## Próximos ajustes ANTES de Managed Agents
1. **Plotar os 32 casos críticos** (5 monumentais skipados + 14 skip-but-runner + high-conf-take-but-loser) — validar
   visualmente onde o conditioning da leitura falhou (especialmente 4926, 7232, 9215).
2. **Ajuste qualitativo do canon** (não threshold): refinar o lado LEGITIMATE_BEAR_BUY / continuação-pós-fundo, e
   reconciliar os SUPPLY_REJECTION/UNKNOWN que correram (o supply-as-lid foi lido como trap mas era markup).
3. Só DEPOIS dos ajustes + plotagem → Managed Agents (Context Assembler → Reader → Challenger → Journal).

NÃO automation-ready. NÃO regra matemática. NÃO feature-dead. A leitura viva é uma fundação real e auditável: forte em
evitar, a refinar em capturar. Outputs: `results/l2_bpt_episode_context_packets_276.jsonl`, `..._readings_276.jsonl`,
`..._reading_audit_276.csv`, `..._reading_plot_list.csv`.
