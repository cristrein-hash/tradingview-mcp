# RAW 15M EXTENSION — COLLECT TO TODAY · RELATÓRIO FINAL (2026-07-04)

## 1. Executive verdict
**RAW_EXTENSION_COMPLETE_KILLCHECK_DONE** — 9º bloco coletado (run-2, após fix de visibilidade SMC/NAS pelo Cris), validado, promovido ao HD com manifest/roundtrip, derivados reconstruídos com prefixo byte-idêntico, e kill-check virgem do Sistema A executado com spec congelada → **VIRGIN_INCONCLUSIVE_N_LT_20 (N=0; janela 100% BEAR)**. DA independente: **CONFIRMA** tudo.
Histórico do bloco: run-1 (mesma sessão) foi **BLOCKED** por drift de indicadores (SMC/NAS invisíveis; relatório da falha preservado no git history deste mesmo arquivo, commit `feaae36`) — o fix foi manual do Cris.

## 2. Coverage before/after
- Antes: 8 blocos, 2024-05-25 → 2026-05-25.
- **Depois: 9 blocos, 2024-05-25 → 2026-07-03 16:30 UTC** (fim = último bar antes do fechamento de 4-jul). Gap remanescente: zero até a data da coleta.

## 3-5. Paths, checksums, counts
- **HD:** `TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz` (59M · sha256 `52e9d748a9c8be338147010bf65673290e966c648c5c937020411cbdb28ea705`) + manifest `TradingData/manifests/XAUUSD_15m_replay_2026-05-25_to_2026-07-04_manifest.txt`. Original local: `alert-bridge/logs/backtests/XAUUSD_15m_replay_2026-05-25_to_2026-07-04.normalized.jsonl` (547MB · sha256 `525931aa3c3cce6cc024da271faa8c59e88ae5d4bfe16750a284045580e28199`) — retido até aprovação de deleção. **Roundtrip triplo-verificado (DA recomputou).**
- 2710 snapshots reais (cauda pós-replay de 5290 registros aparada; **nota de risco residual do DA: o STAGE bruto não-trimado contém 1 barra realtime além do fim do replay — rebuilds futuros devem partir do gz do HD, nunca do STAGE bruto**) → 2714 barras curadas.
- Densidade de indicadores (DA): NAS 73,3/kbar · SMC 75,9 · OB 220,0 — ≥ 8º bloco (50,6/71,8/211,8); consistente com bear.

## 6. Gap/duplicate report
0 buracos · 0 INSPECT · 29 gaps legítimos (fds/sessão/Memorial Day) · barra final flat (convenção idêntica aos blocos históricos — o 8º também termina flat) · overlap 6 barras idênticas ao 8º exceto a barra final flat do PRÓPRIO 8º (8º permanece autoritativo via `setdefault` do engine). Cross-check run-1×run-2 na série curada: **0 mismatches em 2714 barras** (a investigação da "divergência de 197 barras" revelou que era artefato de convenção de identidade — corrida de captura auto-curada pelo last-write-wins do builder; validação v2 reescrita para a convenção correta, DA confirmou fidelidade ao builder).

## 7. Source guard
Cadeia de promoção PASS; 2 falso-positivos pré-existentes documentados (manifest §R4/R6); pendência de calibração registrada.

## 8-9. Promotion & derived rebuilds
- RAW: promovido após R4v2 PASS (protocolo sha→gz→sha→HD→gzip-t→roundtrip→manifest).
- Primitives 9º bloco: sandbox-first → validado (2714 bars · NAS 199 · SMC 206 · OB 597 · RSI 99%) → promovido (sha `92c50759...`). Bubbles 9º: sandbox → auditoria de mapping/causalidade OK (1017; BUY-up 70,7% >> SELL-up 27,8%; known_at≥t) → promovido (sha `4a095938...`). *(primitives/bubbles não são versionados no git — paths+sha aqui e no manifest.)*
- Candidates: backup → rebuild oficial → **PREFIX PASS: 4502 antigos byte-idênticos + 240 aditivos** (nos dois arquivos); universo Lab G: 4499 byte-idênticos + 240.

## 10. Validation of old prefix
Blocos antigos imutáveis por construção; candidates/universo byte-idênticos (acima); **baseline #4 reproduz na base estendida: N435 +291,5** (fail-loud + DA).

## 11. Kill-check
**VIRGIN_INCONCLUSIVE_N_LT_20 (N=0).** Janela 100% BEAR (v5h recomputado 240/240 pelo DA); Sistema A BULL-only ficou integralmente de fora (~−12% de queda sem nenhum LONG — stand-aside como desenhado). Bounds htf irrelevantes com N=0. Doc: `XAU_15M_SYSTEM_A_VIRGIN_KILLCHECK_20260704.md`.

## 12. What was not touched
Produção (receiver vivo; janela pausou/restaurou sozinha claude_recheck; daemon 4H permaneceu parado como antes) · blocos 1-8 e seus manifests · estratégias/gates/detector · Telegram · Supabase (delta pendente registrado) · SHORT.

## 13. Rollback instructions
RAW: remover `XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz` + manifest do HD (blocos 1-8 imunes). Primitives/bubbles: deletar os 2 ficheiros novos (aditivos). Candidates: restaurar backups (sha `f8debb6f.../47c24cb6...` em `scratchpad/derivados_sandbox/backup_candidates/`).

## 14. Next action (decisão Cris)
- O kill-check REAL do Sistema A precisa de janela virgem NÃO-BEAR → continuar a extensão em blocos futuros (mesmo pipeline, agora todo validado) quando o mercado der amostra.
- Pendências que este bloco deixou registradas: extensão htf_4H/1D (staleness) · calibração do source guard · Supabase delta seed · aprovação de deleção dos originais locais (run-1 forense + STAGE bruto) após confirmação.
