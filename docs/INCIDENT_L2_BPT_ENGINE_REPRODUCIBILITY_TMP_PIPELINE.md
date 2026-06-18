# INCIDENT — L2/BPT TAKE Engine: pipeline depende de builders /tmp não versionados

**Status:** `INCIDENT · REPRODUCIBILITY BLOCKER · VALIDATION HARD-STOPPED · NO RECONSTRUCTION YET` · **Data:** 2026-06-18
**Severidade:** ALTA — invalida qualquer validação "sem retune" até o pipeline ser reproduzível.
Auditoria/explicação/plano. **Nada reconstruído.** Inventário: `results/l2_bpt_engine_pipeline_reproducibility_audit.csv`.

## 1. O que aconteceu
O pipeline do L2/BPT Trade Qualification Engine foi construído com vários **builders efêmeros em `/tmp`, nunca versionados**. Quando propus a validação Opção B (2013-2017) "sem retune", descobri que não consigo rodar o pipeline de forma reproduzível: builders-chave sumiram do `/tmp` e não estão no git. Logo, a frase "rodar o engine exatamente como está" não é garantível.

## 2. Por que aconteceu
Padrão de pesquisa rápida: scripts de detecção/extração escritos direto em `/tmp` (iteração veloz), artefatos cacheados em `/tmp`, e só os scripts **downstream/curados** foram promovidos ao repo `…/v1/`. Os elos de entrada (frozen builder, 1D-bars builder, detector, GT, d1_sig) nunca entraram no controle de versão. `/tmp` é volátil → perdidos na limpeza, exceto o que foi snapshotado no **safety pack 2026-06-09** e os artefatos que sobreviveram em `/tmp`.

## 3. Mapa do pipeline + status (resumo; detalhe no CSV)
`RAW gz → frozen raw_features → 1D bars → detector → candidate_matrix → pruned_base → demand/supply → macro/D1/SVP → 84 fatores → TAKE engine`

| etapa | gerador | versionado | status |
|---|---|---|---|
| frozen builder | `extract_raw_features.py` | ❌ | **MISSING → NEEDS_RECONSTRUCTION** |
| 1D bars builder | (writer de `XAU_1D_bars.jsonl`) | ❌ | **MISSING → NEEDS_RECONSTRUCTION** (low-risk) |
| 1D ohlc builder | `build_1d_ohlc.py` | ✅ | FOUND (gera `_ohlc`, não `_bars`) |
| detector | `L2_detector_v2_2.py` | ❌ (tmp+pack) | **TMP_ONLY → PROMOVER** |
| ground truth | `L2_ground_truth_v1.json` | ❌ (tmp+pack) | **TMP_ONLY → PROMOVER** |
| candidate_matrix | `l2_layer23_diag.py` | ✅ | FOUND (mas importa o detector tmp + lê GT tmp) |
| pruned_base | `build_pruned_base_v2.py` | ✅ | FOUND |
| demand/supply | `demand_supply_quality.py` | ✅ | FOUND |
| macro/D1 | `macro_context_enrich.py` | ✅ | FOUND |
| d1_sig (NAS 1D) | `extract_1d_v3.py` | ❌ (tmp) | **TMP_ONLY → PROMOVER** |
| SVP | `extract_svp.py` | ✅ | FOUND |
| 84 fatores | `qualification_extract.py` | ✅ | FOUND (commitado) |
| reasoning TAKE | `QUALIFICATION_RUBRIC.md` + 14 subagentes | ✅ rubrica | **FOUND mas ESTOCÁSTICO** (LLM; re-rodar ≠ byte-igual) |

## 4. Onde busquei (task 5)
repo ✅ · git history (incl. deletados) ✅ · branch `backup` ✅ · `./backups/` ✅ · docs/scripts ✅ · research folders ✅ · **safety pack `~/Desktop/TRADING/L2_REBOOT_SAFETY_PACK_2026-06-09`** ✅ · shell history ✅ · `/tmp` atual ✅.
- **Recuperados no safety pack:** detector `L2_detector_v2_2.py`, GT `L2_ground_truth_v1.json`, e o **artefato** `raw_features_2020_2026.jsonl` + `SHA256SUMS.txt`.
- **Builder `extract_raw_features.py`: NÃO encontrado em lugar nenhum.**

## 5. Integridade da referência do fidelity gate
`raw_features_2020_2026.jsonl` → SHA256 **`9fac96b9…`** idêntico em SHA256SUMS.txt = safety pack = `/tmp`. **Artefato de referência ÍNTEGRO** → qualquer reconstrução do frozen builder pode ser validada byte-exata contra ele.

## 6. Impacto na validação
- A validação Opção B (2013-2017) está **HARD-STOPPED**: 2 builders MISSING + 3 TMP_ONLY → pipeline não-reproduzível agora.
- A validação 2020-2026 já feita usou artefatos `/tmp` (válidos no momento), mas **não é re-executável** sem os builders. As decisões TAKE são de LLM (estocásticas) → segunda fonte de não-reprodutibilidade.
- **Conclusão: o pipeline NÃO é reproduzível no estado atual.**

## 7. Plano de correção (NÃO executar sem autorização)
1. **URGENTE — preservar artefatos `/tmp` voláteis** (referências do fidelity gate): `XAU_1D_bars.jsonl`, `d1_sig_v3.json`, `svp_bars.jsonl` (o `raw_features` já está no pack). Copiar para local versionado/externo + SHA. (raw_features já tem SHA 9fac96b9.)
2. **PROMOVER (sem reconstrução, só recuperar+versionar):** `L2_detector_v2_2.py` + `L2_ground_truth_v1.json` (do safety pack) e `extract_1d_v3.py` (do /tmp) para o repo `…/v1/`, com hash registrado.
3. **RECONSTRUIR só com autorização explícita** (fidelity-gate obrigatório):
   - `extract_raw_features.py` → reproduzir `raw_features_2020_2026.jsonl` **byte-igual** (SHA `9fac96b9`) a partir do gz 2020-2026. Campo difícil = `bubbles_recent`.
   - builder de `XAU_1D_bars.jsonl` → reproduzir o artefato (close diário) byte-igual.
4. **FIDELITY GATE obrigatório** antes de qualquer aplicação em 2013-2017: reconstruir → rodar no gz 2020-2026 → output idêntico (byte/field) ao artefato de referência. Sem gate verde, **não** aplicar em 2013-2017.
5. **Política permanente:** todo builder do pipeline vai para controle de versão; `/tmp` nunca é fonte-de-verdade. CI/check que falha se um script do pipeline importa de `/tmp`.

## 8. Próximo passo seguro
Aguardar autorização para (a) preservar artefatos voláteis e (b) promover os 3 scripts recuperáveis. Só depois, com autorização separada, reconstruir os 2 builders sob fidelity gate. **Nenhuma validação até o pipeline reproduzir 2020-2026 byte-exato.**

---
*Produção INTACTA (coleta parada, pause off, `xau-l1-cycle` ativo, 0 orphan). Sem SLIM, sem validação, sem reconstrução. Auditoria apenas.*
