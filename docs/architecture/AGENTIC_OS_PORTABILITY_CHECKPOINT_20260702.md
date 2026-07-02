# AGENTIC OS — PORTABILITY CHECKPOINT (2026-07-02)

**Natureza:** doc-only. Congela estado, decisões, commits, fronteiras e próximos passos da sessão de arquitetura/portabilidade. **Nenhum código alterado, nada movido/apagado, produção/runtime/RAW intocados.**
**Status:** `PORTABILITY_BASE_CONSOLIDATED` · `COLD_STORAGE_COMPLETE` · `PRODUCT_PRIVATE_SPLIT_DOCUMENTED`.

## 1. Estado final do repo
- **HEAD (após push):** `2d294c7` (origin/main sincronizado; ahead=0).
- **Tamanho:** 2,7G → **558M** (~2,2G movidos p/ cold storage).
- **Working tree esperado:** limpo, exceto `?? alert-bridge/logs/` (logs vivos do receiver, gitignored — NÃO tocar).
- **Cold storage:** `/Volumes/GUTS_ LACIE/trading_system_cold_storage/` (`alert-bridge-logs-backtests_20260702.tar.zst` 14M, `backups-dated_20260702.tar.zst` 16M, `SHA256SUMS.txt`).
- **Restore doc:** `docs/cleanup/COLD_STORAGE_MANIFEST_20260702.md`.
- **Commits da sessão (14, todos pushed):**
  `7da7337` arch memory v1 · `0bdbfd3` Fase 1 inventário · `6a1f48e` delete SLIM · `ff7c9bf` plano Fases 2-5 · `8dfb676` SLIM cluster historical · `2b4724e` EF venv regen doc · `bae85fe` Fase 2 config/env · `a803add` RTSE sample · `69cbc46` +research scripts · `310e3dd` high-value paths · `9fc9744` +read-only paths · `59dc35b` Fase 4A split · `e62d468` RAW extractors sandbox · `2d294c7` cold storage.

## 2. Decisões arquiteturais aprovadas
- **Produto vendável = engine** (MCP server + config/env + EF collectors/contratos + governança/safety + skills + validation contracts + docs de operação portável).
- **Alpha/edge do Cris = privado** (estratégias, rulers, RTSE, research, RAW/source, runtime, logs, daemons, plists, outputs). **O comprador leva o motor, nunca o edge.**
- **Supabase adiado** até definir boundary de memória (`DEFERRED_UNTIL_MEMORY_BOUNDARY_APPROVED`).
- **Move de `product_core/` (Fase 4C) adiado** (`DEFERRED_UNTIL_COMMERCIAL_PACKAGE_PREP`) — organizacional.
- **EF collectors** = already portable / no-op (module-relative; sem config import p/ isolar daemon).
- **venv EF v2** = mantido (`KEEP_RUNTIME_DEPENDENCY`; daemon vivo; regen documentado).
- **SLIM validation** = permanentemente proibido.
- **Cluster SLIM residual** = `HISTORICAL_COMPATIBILITY / RAW_IN_MEMORY_ALLOWED / SLIM_MODE_FORBIDDEN` (sustenta D1A/Breakout Continuation ACTIVE_CANDIDATE).
- **Migração file-by-file** = pausada após alto valor (`PAUSED_AFTER_HIGH_VALUE_PORTABILITY`).

## 3. Portabilidade entregue
- Ficheiros: `config/paths.py`, `config/__init__.py`, `.env.example`, `tests/test_paths_resolution.py`, `docs/architecture/CONFIG_ENV_CONTRACT.md`.
- **8 roots env-overridable:** `TRADING_SYSTEM_ROOT · DATA_ROOT · RAW_DATA_ROOT · OUTPUT_ROOT · PRIVATE_ROOT · EXTERNAL_FACTOR_ROOT · LOG_ROOT · TEMP_ROOT`.
- **Funções provadas:** `CP.repo()`, `CP.causal_segments()`, `CP.ruler()`, `CP.raw()`, `CP.private()`.
- **Defaults byte-idênticos** aos paths absolutos atuais → importar não muda comportamento; scripts não-migrados continuam a funcionar.
- Overrides de sandbox (só extractores, para teste seguro): `L2_OHLC_OUT_DIR`, `RTSE_30M_OUT_DIR` (default byte-idêntico).

## 4. Scripts migrados (13)
RTSE validation: `phase47_zone_entries.py`, `phase48_bear_deep_zone.py`, `phase70_best_entry.py`, `phase72_expand_n.py`, `phase75_combos.py`.
research/xau_15m_bb_nas_leonardo: `_inspect_raw_schema.py`, `_inspect_raw_schema2.py`, `_DA_raw_probe.py`, `_DA_contiguity_one.py`.
Extractores RAW (copy-sandbox): `my-strategy/research/revalidation/extract_raw_ohlc.py`, `regime_turnstate_engine/ground_truth/extract_30m_ohlc.py`.
(EF collectors NÃO migrados de propósito = já portáveis.)

## 5. Verificações realizadas
- **Byte-idêntico** (stdout re-run vs baseline) nos 9 scripts RTSE/research.
- **SHA256 idêntico** (sandbox vs vivo) nos 3 outputs dos extractores (4H 9880, 1H 11786, 30M 23554 bars).
- **mtime + SHA256 dos outputs vivos preservados** (raw_4h/1h/30m_ohlc.jsonl não sobrescritos).
- **Cold storage roundtrip** `diff -rq` conteúdo idêntico (backtests + backups).
- No production touched · No RAW/source modified · No daemon/plist/runtime touched.

## 6. Diretórios e status
| Dir | Status |
|---|---|
| `src/` | KEEP_PRODUCT |
| `config/` | KEEP_PRODUCT |
| `skills/`, `tests/`, `agents/` | KEEP_PRODUCT |
| `external_factors_v2/` | híbrido: collectors/config/agents = PRODUCT · runtime/plist/venv/snapshots = PRIVATE_RUNTIME |
| `my-strategy/` | PRIVATE_ALPHA/RESEARCH (rulers = SOURCE_OF_TRUTH/DO_NOT_TOUCH) |
| `regime_turnstate_engine/` | PRIVATE_ALPHA/RESEARCH |
| `research/` | PRIVATE_RESEARCH |
| RAW `/Volumes/GUTS_ LACIE/TradingData` | PRIVATE / DO_NOT_TOUCH |
| `alert-bridge/` (raiz + receiver) | PRIVATE_RUNTIME (LIVE) / DO_NOT_TOUCH |
| `alert-bridge/logs/` raiz | LIVE_LOGS / DO_NOT_TOUCH |
| `alert-bridge/logs/backtests/` | COLD_STORED |
| `backups/` | COLD_STORED |

## 7. Próximos blocos possíveis
- **A.** Fase 4C — `product_core/` skeleton/move (só p/ pacote comercial).
- **B.** Supabase memory mirror (só após boundary memória produto vs privada).
- **C.** Package / commercial-readiness audit.
- **D.** Migração de paths adicional (só se pertencer a produto ou for reativado).
- **E.** Restore drill opcional do cold storage.
- **F.** CI/hooks safety layer.

## 8. Recomendação de ordem
1. **Checkpoint agora** (este doc).
2. **Package/commercial-readiness audit** ou **hooks/CI safety layer** (C ou F).
3. Só depois **Fase 4C** (A).
4. Só depois **Supabase** (B).

## 9. Riscos pendentes
- Muitos scripts research mortos ainda têm hardcodes — não são alvo enquanto não forem produto/reativados.
- Supabase cedo demais persistiria sujeira histórica → esperar boundary.
- Mover `product_core/` antes da embalagem pode quebrar imports (49 refs ruler + 111 `/tmp`) → gated + harness.
- Daemons vivos (receiver, EF v2) devem permanecer no privado/local.
- Cold storage depende do HD externo + restore doc (verificar SHA256 antes de restaurar).

## 10. Critérios de aceitação do checkpoint
- Doc criado ✅ · nenhum código alterado ✅ · nenhum arquivo vivo tocado ✅ · estado final reproduzível (HEAD `2d294c7`, cold storage + SHA256 no HD) ✅ · próximos passos claros ✅.
