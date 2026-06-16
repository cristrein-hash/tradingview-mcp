# L1 — Comparação exata OLD (regime_B_v3) vs NEW (regime_l1_v4)

**2026-06-16 · research / `NOT_VALIDATION`.** Diferença ÚNICA entre OLD e NEW = a fonte de regime. Mesmo ativo/TF/direção (PEPPERSTONE:XAUUSD/4H/LONG), mesmo gate-base, mesmo RSI gate (`round(rsi_vs_ma,2)<=-9.35`), **sem vol_entry_z**. R antigo de `rebuild_v3/trades.jsonl` (não inventado). CSV: `l1_old_vs_new_regime_comparison.csv`.

## B — Comparação (perguntas 1–18)
| | valor |
|---|---|
| 1. OLD (regime_B_v3) | **38** candidatos |
| 2. NEW (regime_l1_v4) | **63** candidatos (59 operational, 4 blocked_exhaustion) |
| 3. BOTH | **38** |
| 4. OLD_ONLY | **0** |
| 5. NEW_ONLY | **25** |
| 6. Winners antigos perdidos | **0** (nenhum) |
| 7. Losers antigos removidos | **0** (nenhum) |
| 8. Candidatos novos com R conhecido | **0** — não há backtest dos 25; **R não inventado** |
| 9. Novos são winners/losers/unknown | **25 = NEW_UNKNOWN** |
| 10. R total OLD vs NEW | OLD **+14.87R** (in-sample, FULL-38) · NEW **UNKNOWN** (38 conhecidos + 25 sem R) |
| 11. Média R OLD | +0.39R/trade (in-sample) · NEW UNKNOWN |
| 12. WR OLD | 31.6% (12W/26L) · NEW UNKNOWN |
| 13. PF OLD | 1.76 · NEW UNKNOWN |
| 14. Max DD OLD | ~7.9R (rebuild_v3) · NEW UNKNOWN |
| 15. #1/#11/#36/#38 | **preservados — `operational_candidate`** |
| 16. #3/#15/#18/#32 | **seguem `blocked_exhaustion`** (RSI gate é regime-independente) |
| 17. Perfil dos +25 | sob regime_B_v3: **18 TRANSITION, 2 BEAR, 2 BULL, 3 sem entrada daily**. Maioria = bars que o regime antigo NÃO chamava BULL. **Outcome desconhecido.** |
| 18. Tese antiga | **PRESERVADA** (38/38). O regime_l1_v4 **não destrói** a tese — ele a **amplia** (+25 candidatos não-provados). |

**Veredito B:** o universo NEW é **estritamente um superset** do OLD (38 ⊂ 63). Nada do approved thesis foi perdido. Mas regime_l1_v4 é **mais permissivo (+66%)**, adicionando 25 candidatos de outcome **UNKNOWN** — incluindo **2 bars que o regime_B_v3 classificava como BEAR** (long-continuation em regime de baixa = risco real a investigar). **Não dá para chamar edge no set de 63 sem RAW OOS.**

## C — Regime antigo: recuperável ou não?
**Artefatos encontrados (agora versionados):** `candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl` (**estático COMPLETO 2016-05-24 → 2026-05-25**, com `combined_score`/`vol_score`/`h4|d|w_break_*`/`cascade_score`/`v2_state`/`v3_state` por dia), `regime_classifier_B_v2.py`, `regime_classifier_B_v3.py`, `xau_daily_with_features.jsonl` (2016→2026-05-25).

- **1. Reproduzir o regime_B_v3 histórico?** **SIM** — o arquivo estático tem o `v3_state` (e todos os scores intermediários) de cada dia até 2026-05-25. Para datas históricas é exato.
- **2. Estender para dias novos?** **NÃO.** v3 consome v2, que consome o **output do v1 B** (`/tmp/regime_B_classifications.jsonl`, `combined_score`/breaks/vol_score). O **script v1 B que computa breaks h4/d/w + vol_score do multi-timeframe raw NÃO existe no repo** (grep confirmou ausência). v2/v3 só **re-processam** os valores do v1; não os recalculam do raw.
- **3. Inputs faltantes:** o gerador v1 B (detector de breaks h4/d/w + vol_score). Sem ele, não há como produzir `combined_score`/breaks para 2026-05-26+.
- **4. Os artefatos novos resolvem o v1 B ausente?** **NÃO** — preservam o **output** histórico (útil para backtest), não o **gerador** (necessário para live).
- **5. Pode voltar como fonte operacional live?** **NÃO** (não classifica o dia de hoje).
- **6. Impossibilidade objetiva:** gerador v1 B perdido; breaks/vol_score não reconstruíveis do raw com fidelidade.
- **7/8. Alternativa simples para preservar o comportamento antigo sem regime_l1_v4 permissivo?** Para **backtest/validação**: usar o **regime_B_v3 estático** (≤2026-05-25) como gate — reproduz exatamente os 38 e exclui os 25 (que são por definição não-BULL no regime antigo). **Não há filtro forward mínimo "mágico"** que remova os 25 sem reintroduzir a definição de regime — a diferença **É** a definição de regime. Derivar um regime forward-computável que aproxime as decisões BULL do regime_B_v3 é tarefa de modelagem futura (sem overfit, fora deste bloco).

**Recomendação C:** regime_B_v3 = **KEEP_REFERENCE recuperável só para histórico**; **NÃO** reativar live. Para validar a tese, rodar o RAW OOS **sob regime_B_v3 estático** (preserva a tese exata).

## D — Decisão de risco
**CASE 3 + CASE 4 (híbrido).**
- **CASE 4 (regime antigo recuperável p/ histórico):** a tese aprovada pode ser validada **exatamente** sob regime_B_v3 estático — **não precisamos trocar a tese por erro nosso.**
- **CASE 3 (os +25 são UNKNOWN):** o regime live (regime_l1_v4) adiciona 25 candidatos sem outcome conhecido (2 deles em regime BEAR antigo). **Não chamar edge.** A L1 já é human-discretionary → candidatos live passam por revisão humana; isso é o guard conservador correto (mecânico de seleção + decisão humana), sem overfit.

**Recomendação operacional para a L1 live:**
1. **Validação/backtest:** usar **regime_B_v3 estático** (≤2026-05-25) — preserva a tese (38). É o teste honesto da estratégia aprovada.
2. **Live forward:** manter **regime_l1_v4** (única fonte forward-computável) **MAS** tratar candidatos como **human-review** (já são) e **não** declarar os 25 extras como edge. Opcional futuro: derivar um regime forward que aproxime o BULL do regime_B_v3 (remove a permissividade) — modelagem, com autorização.
3. **Não mascarar:** o set de 63 não tem R; qualquer número de performance da L1 hoje é in-sample sob a tese antiga (regime_B_v3). Edge só com RAW OOS + gate manifest.

_Read-only. Nenhum backtest OOS rodado, R não inventado, regime_B_v3 não reativado live, vol_entry_z não voltou._
