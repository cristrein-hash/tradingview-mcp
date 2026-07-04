# RAW 15M EXTENSION — POST-CLOSE CHECKPOINT (2026-07-04)

## Estado final registrado (Decisão 2 Cris)
- **RAW_15M_EXTENSION_20260704 = COMPLETE**
- **RAW_15M_COVERAGE = 2024-05-25_TO_2026-07-03_16:30_UTC** (9 blocos contíguos, manifests+sha+roundtrip)
- **SYSTEM_A_VIRGIN_KILLCHECK = INCONCLUSIVE_N0**
- **SYSTEM_A_STAND_ASIDE_IN_BEAR = PASS_BEHAVIORAL_OBSERVATION_NOT_VALIDATION**
- Sistema A NÃO validado, NÃO refutado, NÃO produção. SHORT não aberto. Estratégia/gates/detector inalterados.
- Push feito: `feaae36` + `43a870c` → origin/main (`7c5253d..43a870c`).

## Cobertura/paths/checksums (9º bloco)
- HD gz: `raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz` — sha256 `52e9d748a9c8be338147010bf65673290e966c648c5c937020411cbdb28ea705` (re-verificado no fechamento) · manifest `TradingData/manifests/XAUUSD_15m_replay_2026-05-25_to_2026-07-04_manifest.txt` · original sha256 `525931aa3c3cce6cc024da271faa8c59e88ae5d4bfe16750a284045580e28199` · roundtrip YES.
- Derivados promovidos: primitives 9º (`92c50759...`) · bubbles 9º (`4a095938...`) · candidates 4502→4742 (prefix byte-idêntico) · universo Lab G 4499→4739.
- Kill-check: `XAU_15M_SYSTEM_A_VIRGIN_KILLCHECK_20260704.md` (N=0; janela 100% BEAR).

## Higiene forense (H5) — classificação e execução
| Item | Classe | Ação/Restore |
|---|---|---|
| run-2 STAGE bruto (1,5G; cauda pós-replay c/ 1 barra realtime = risco DA) | DELETE_SAFE | DELETADO. Conteúdo real preservado byte-a-byte no normalized (HD gz); cauda = lixo por construção, documentado. Elimina o risco de rebuild contaminado. |
| run-2 normalized local (528M) | DELETE_SAFE | DELETADO. Restore: `gunzip -c <HD gz>` (roundtrip triplo-verificado). |
| run-2 checkpoint.json (estado de resume perigoso) | DELETE_SAFE | DELETADO. |
| run-2 normalized.gz local (59M, espelho do HD) | KEEP | cópia de segurança local do 9º bloco. |
| run-1 RAW bruto (único, evidência do incidente de drift SMC/NAS) | COLD_STORAGE local | comprimido → `forensics_20260704_run1/...jsonl.gz` (866K) · sha256 `f72d933c01656a470293a59720401ca4ac03f8bb0320a64ef37111b9c72187d0` · roundtrip YES; uncompressed deletado. |
| run-1 normalized + v1-gz + checkpoint | DELETE_SAFE | DELETADOS (deriváveis do raw gz com script no git history; superseded). |
~2GB liberados. Nenhum dado não-regenerável perdido (únicos preservados comprimidos com sha).

## Pendências (estado final)
- **HTF 4H/1D staleness = DEFERRED** (htf_4H até 2026-06-09 via coleta 4H SVP_LUX; htf_1D até 2026-05-24; estender = novas coletas de chart 4H/1D, bloco futuro próprio; impacto atual nulo — Sistema A htf-dependência 0/53, janela N=0; lookups asof-stale causais).
- **Source guard = CALIBRADO** (PASS 7/7; ver hygiene report §4).
- **Supabase delta = CRIADO, NÃO APLICADO** (`supabase/seeds/memory_delta_raw_15m_extension_20260704.sql`, 5 rows; review em `SUPABASE_DELTA_RAW_15M_EXTENSION_REVIEW_20260704.md`).
- Kill-check real do Sistema A: aguarda janela virgem NÃO-BEAR (extensão futura; pipeline pronto).

## Rollback
9º bloco: remover gz+manifest do HD; primitives/bubbles: deletar os 2 ficheiros aditivos; candidates: `git checkout 43a870c~1 -- entry_candidates*.jsonl` (ou backups sha `f8debb6f/47c24cb6` enquanto o scratchpad viver). Guard: `git diff` reversível.

## Fora do commit (política do repo; paths+sha aqui)
primitives/bubbles do 9º bloco · gz do HD · espelho local 59M · forense run-1 gz · `results/lab_g_candidates.jsonl` (regenerável).
