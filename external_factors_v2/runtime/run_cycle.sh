#!/bin/zsh
# Um ciclo de monitoração External Factors v2 (Tier-1 + Camada A consenso/direção + freeze).
# Keyless por padrão; se .env tiver ANTHROPIC_API_KEY, a frota Tier-2 também roda.
set -e
DIR="/Users/cristrein/tradingview-mcp/external_factors_v2"
cd "$DIR"
LOG="$DIR/snapshots/daemon.log"
echo "=== $(date -u +%FT%TZ) ===" >> "$LOG"
# 1) refresh Tier-1 (keyless) — só se coletor existir; tolera falha de rede
/usr/bin/python3 collectors/fred_collect.py >> "$LOG" 2>&1 || echo "[warn] fred_collect falhou" >> "$LOG"
# 2) calendário ForexFactory (keyless): datas/consenso/actual reais (substitui gerador+consenso+captura manual)
/usr/bin/python3 collectors/forexfactory_collect.py >> "$LOG" 2>&1 || echo "[warn] forexfactory_collect falhou" >> "$LOG"
# 2b) news/Fed (keyless): RSS oficial Fed -> abastece skills de texto (fed-tone/news/source-reliability)
/usr/bin/python3 collectors/fed_news_collect.py >> "$LOG" 2>&1 || echo "[warn] fed_news_collect falhou" >> "$LOG"
# 2c) market news (Alpha Vantage, key): rate-limited 90min -> geopolitical-impact + news ampla
/usr/bin/python3 collectors/av_news_collect.py >> "$LOG" 2>&1 || echo "[warn] av_news_collect falhou" >> "$LOG"
# 2d) ouro canônico (CME/COMEX preço FMP + COT CFTC keyless) -> gold-driver-analyzer
/usr/bin/python3 collectors/gold_collect.py >> "$LOG" 2>&1 || echo "[warn] gold_collect falhou" >> "$LOG"
# 2e) fed path (proxy CME FedWatch via slope da curva, keyless) -> macro-regime/gold-driver
/usr/bin/python3 collectors/fedwatch_collect.py >> "$LOG" 2>&1 || echo "[warn] fedwatch_collect falhou" >> "$LOG"
# 2f) teorias núcleo humano (não-dealer, RSS keyless) -> ledger + análise comparativa Tier-2
/usr/bin/python3 collectors/theory_sources_collect.py >> "$LOG" 2>&1 || echo "[warn] theory_sources_collect falhou" >> "$LOG"
# 2f2) extrai CLAIM falsificável (dir+horizonte) via claude -p (Max, cap 8/ciclo) -> popula ledger
if command -v claude >/dev/null 2>&1 || [ -x "$HOME/.local/bin/claude" ]; then
  PATH="$HOME/.local/bin:$PATH" /usr/bin/python3 runtime/theory_extract.py >> "$LOG" 2>&1 || echo "[warn] theory_extract falhou" >> "$LOG"
fi
# 2g) forward-scoring REAL (hit-rate/Brier vs preço real do ouro no horizonte; weight ativa scored>=10)
/usr/bin/python3 runtime/theory_score.py >> "$LOG" 2>&1 || echo "[warn] theory_score falhou" >> "$LOG"
# 3) ciclo do monitor (overlay consenso + freeze latest.json)
/usr/bin/python3 runtime/monitor_external_factors.py >> "$LOG" 2>&1
# 4) frota Tier-2 LLM via `claude -p` (DENTRO do plano Max — Opção B; sem billing de API).
#    Sem ANTHROPIC_API_KEY no ambiente -> claude usa auth da assinatura. Fallback keyless interno se CLI ausente.
if command -v claude >/dev/null 2>&1 || [ -x "$HOME/.local/bin/claude" ]; then
  PATH="$HOME/.local/bin:$PATH" /usr/bin/python3 agents/fleet.py >> "$LOG" 2>&1 || echo "[warn] fleet falhou" >> "$LOG"
else
  echo "[info] claude CLI ausente -> Tier-2 pulado (Camada A keyless segue)" >> "$LOG"
fi
# poda: manter só os 200 snapshots state_*.json mais recentes + cap do daemon.log em 5000 linhas
ls -1t "$DIR"/snapshots/state_*.json 2>/dev/null | tail -n +201 | xargs rm -f 2>/dev/null || true
if [ -f "$LOG" ] && [ "$(wc -l < "$LOG")" -gt 5000 ]; then tail -n 2000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"; fi
echo "ciclo ok $(date -u +%FT%TZ)" >> "$LOG"
