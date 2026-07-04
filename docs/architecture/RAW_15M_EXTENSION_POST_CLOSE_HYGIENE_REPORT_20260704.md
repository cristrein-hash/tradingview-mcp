# RAW 15M EXTENSION — POST-CLOSE HYGIENE · RELATÓRIO (2026-07-04)

## 1. Executive verdict
**POST_CLOSE_COMPLETE_WITH_DEFERRED_ITEMS** — push feito, docs/manifests conferidos, source guard calibrado (PASS 7/7), Supabase delta criado sem aplicar, forense classificada e higienizada (~2GB, únicos preservados com sha/roundtrip), baselines revalidados intactos. Único DEFERRED: extensão htf_4H/1D (exige coletas de chart fora do escopo).

## 2. Push status
`feaae36` + `43a870c` → origin/main (`7c5253d..43a870c`); working tree limpo pós-push (untracked = vivos declarados).

## 3. HTF 4H/1D staleness
**DEFERRED com auditoria completa:** htf_4H.primitives ← coleta 4H `XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz` (10-jun; cobre até 2026-06-09); htf_1D ← coleta 1D até 2026-05-25 (primitives até 05-24). Rebuild sem nova coleta é impossível (fonte sancionada esgota aí); coleta = chart = proibido neste bloco. Impacto atual nulo (Sistema A htf-dependência 0/53; janela virgem N=0; lookups asof-stale são causais). Bloco futuro próprio quando houver janela não-BEAR para o kill-check real.

## 4. Source guard calibration
**CALIBRADO, política intacta:** (a) token proibido como NOME DE CAMPO em atribuição (`f["macro_bear"]=`) não flagra mais — só uso como FONTE; (b) allowed tokens ganharam `engine_substrate4_v5_hourcausal` (exec do engine sancionado) e `lab_g_candidates.jsonl` (intermediário determinístico de cadeia guard-PASS; comentário no código deixa claro: nunca fonte de verdade). Nenhum check removido; SLIM/proxy continuam banidos. **PASS 7/7** na cadeia (builder, bubbles, candidates, engine3, engine, inventário, kill-check).

## 5. Supabase delta seed
**CRIADO, NÃO APLICADO:** `supabase/seeds/memory_delta_raw_15m_extension_20260704.sql` (5 rows, idempotente, batch tag, rollback comentado, zero secrets/RAW). Review: `SUPABASE_DELTA_RAW_15M_EXTENSION_REVIEW_20260704.md` (inclui count pós-Run esperado = 5 e lembrete pbcopy). MCP permanece read-only.

## 6. Forensic cleanup
Tabela completa no checkpoint. Resumo: run-2 STAGE bruto (risco DA) + normalized local + checkpoints + superseded run-1 = **DELETADOS (DELETE_SAFE, restore documentado)**; run-1 RAW (único; evidência do incidente de drift) = **COLD local comprimido** (866K, sha `f72d933c...`, roundtrip YES); espelho local do 9º bloco (59M gz) = KEEP. ~2GB liberados; zero dado não-regenerável perdido.

## 7. Baseline validation (pós-higiene)
Source guard PASS 7/7 · candidates 4742 · universo Lab G 4739 com prefixo 4499 byte-idêntico · **base #4 N435 +291,5R reproduz** · kill-check virgem re-executado: **N=0 inalterado** (240/240 BEAR) · DA desta sessão cobre estes resultados (re-execução byte-idêntica).

## 8. Safety baseline
BLOCKER=0 · WARNING=1 (Caminho B TRUE_RISK, esperado) · INFO=50.

## 9. Files changed (commit deste bloco)
Checkpoint + este report + review Supabase + seed SQL + `_source_guard.py` (calibração validada).

## 10. Intentionally not committed
primitives/bubbles do 9º bloco, gz do HD, espelho local, forense (política do repo — paths+sha no checkpoint/manifest) · `results/lab_g_candidates.jsonl` (regenerável).

## 11. Next recommended action (decisão Cris)
(a) aplicar o delta Supabase quando conveniente (count esperado 5); (b) push do commit de fechamento; (c) próximo bloco lógico do programa: o eixo WR/streak e o Sistema A aguardam **janela virgem não-BEAR** — extensões futuras curtas com o pipeline agora maduro, ou retomar as lanes deferidas (Lab B r2 estrutural · exposure-overlap/Lab D · F4 sizing como camada de conta) — sem auto-recomendação de ordem.
