# RAW 15M EXTENSION — COLLECT TO TODAY · RELATÓRIO (2026-07-04)

## 1. Executive verdict
**RAW_EXTENSION_BLOCKED** — coleta executada com janela segura e produção restaurada, MAS o bloco coletado **não tem paridade de layout com o baseline dos 8 blocos**: `Smart Money Concepts [LuxAlgo]` e `NAS TOP BOTTOM DETECTOR` **não reportaram payload em nenhum dos 2709 registros** (presentes no `chart_get_state` pré-coleta, ausentes no export). Hard stop do protocolo ("cobertura coletada não bate") acionado ANTES de qualquer escrita no HD. **RAW vivo 100% intocado. Zero promoção. Zero rollback necessário.** Kill-check do Sistema A NÃO executado (R10 exige RAW/derivados validados).

## 2. Coverage before/after
Antes: 8 blocos, 2024-05-25 → 2026-05-25 (intactos). Depois: **INALTERADO** (bloco novo rejeitado em staging).

## 3-6. Paths, checksums, counts, gaps
- Staging (retido para forense, LOCAL apenas): `alert-bridge/logs/backtests/XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl` (8000 registros brutos) · `.normalized.jsonl` (**2709 barras reais**, sha256 `0a9d87cf...b25ac0` → correção pós-dedupe `0a9d87cf0ed0f4a0f693fb0ea271a2aa618226f21c4932273e7fc10fb33a96bd`) · `.normalized.jsonl.gz` (594K — o tamanho anômalo vs ~130M históricos foi o gatilho da inspeção; sha256 `4e9c1a70...`, roundtrip YES) · `.checkpoint.json` (**deletar antes de re-coleta** — senão o coletor resume do bar 7999).
- Qualidade de série (R4 PASS): junção contígua com o 8º bloco (1ª nova 00:15; overlap 2 por design) · 0 dup (1 soluço consecutivo deduplicado keep-first) · 0 não-monotônico · 30 gaps legítimos (fds/sessão/Memorial Day) · range real 2026-05-24 23:45 → **2026-07-03 16:30 UTC** (fim = early close de sexta pré-feriado). CSV: `results/raw_15m_extension_gap_report_20260704.csv` · JSON: `results/raw_15m_extension_validation_20260704.json`.

## 7. Source guard
Cadeia de promoção PASS (builder/bubbles/engine/engine3). 2 falso-positivos pré-existentes documentados no manifest (token `macro_bear` = atribuição de campo; allowed-token não vê leitura via exec do engine) — **pendência: calibração do guard** (classe GUARDRAIL_CARD).

## 8-9. Promotion / derived rebuilds
**NÃO executados** (bloqueados pelo veredito). Nada no HD; primitives/bubbles/candidates oficiais intocados.

## 10. Validation of old prefix
Intocado por construção (blocos independentes; nenhuma escrita).

## 11. Kill-check
**NÃO executado** (pré-condição falhou). Preparação preservada: dependência do Sistema A de `htf_demand_any` medida = **0/53 picks históricos** (bound sólido para quando a coleta válida existir); htf_4H termina 2026-06-09 e htf_1D 2026-05-24 (staleness declarada; extensão HTF = pendência separada).

## 12. What was NOT touched
RAW vivo (8 blocos) · manifests · primitives/bubbles/htf oficiais · produção (receiver vivo o tempo todo; pause flag criada e removida pela própria janela com trap; daemon 4H permaneceu parado como estava antes) · estratégias/gates/detector · Telegram · Supabase.

## 13. Diagnóstico técnico (para o fix)
- Capturados em 2709/2709: **Custom OB Detector v11 — Alert ✓ · Market Order Bubbles ✓ · RSI ✓** (+ HTF Power of Three°, extra).
- Ausentes em 2709/2709 (desde o registro 0): **LuxAlgo SMC · NAS TOP BOTTOM** — exatamente os dois estudos com 500+ objetos de desenho.
- `chart_get_state` lista estudos EXISTENTES; o leitor pine só lê estudos **VISÍVEIS** (contrato conhecido do MCP). Hipótese principal: os dois estão **ocultos (olhinho) ou em estado de erro** no chart desde as sessões de plotting — verificação/correção é ação MANUAL no TradingView (fora do protocolo da janela).
- Probe reproduzível: `research/xau_15m_bb_nas_leonardo/_probe_extension_indicator_drift_20260704.py`.

## 14. Rollback instructions
Nada a reverter (nada promovido). Forense local pode ser apagada com autorização após re-coleta válida.

## 15. Next recommended action (aguarda Cris)
1. **Cris confere no chart** (10s): LuxAlgo SMC e NAS TOP BOTTOM visíveis (olhinho aberto) e sem erro; se em erro, re-adicionar/recarregar.
2. Apagar `checkpoint.json` + staging antigo.
3. **Re-autorizar a re-coleta do MESMO bloco** (re-run do período, não é 2º bloco) — pipeline inteiro daqui em diante já está pronto e validado (R4-R10 re-executam sem mudanças).
4. (Opcional junto) reconectar o MCP da sessão (`/mcp`) para eu verificar visibilidade dos estudos antes da nova janela.
