#!/bin/zsh
# Wrapper da NEWS LANE rápida (InvestingLive) — corrido pela LaunchAgent com.cristrein.external-factors-news
# (~4min). Passo 1: coleta determinística (sempre). Passo 2: escalada Telegram (dedup+cooldown; só envia
# se NEWS_ALERTS_AUTHORIZED=1, senão dry-run). NÃO toca no ciclo macro nem em latest.json (single-writer).
set -u
DIR="/Users/cristrein/tradingview-mcp/external_factors_v2"
LOG="$DIR/snapshots/news_daemon.log"
cd "$DIR" || exit 1
set -a; source /Users/cristrein/tradingview-mcp/.env 2>/dev/null || true; set +a   # keys (FINNHUB/FMP) duráveis a restart

echo "=== $(date -u +%FT%TZ) news cycle ===" >> "$LOG"
python3 collectors/investinglive_news_collect.py >> "$LOG" 2>&1 || echo "[warn] investinglive falhou" >> "$LOG"
python3 collectors/finnhub_news_collect.py >> "$LOG" 2>&1 || echo "[warn] finnhub_news falhou" >> "$LOG"
python3 collectors/geopolitical_news_collect.py >> "$LOG" 2>&1 || echo "[warn] geopolitical falhou" >> "$LOG"
python3 collectors/oil_collect.py >> "$LOG" 2>&1 || echo "[warn] oil falhou" >> "$LOG"
python3 collectors/polymarket_collect.py >> "$LOG" 2>&1 || echo "[warn] polymarket falhou" >> "$LOG"
python3 runtime/news_escalate.py >> "$LOG" 2>&1 || echo "[warn] escalate falhou" >> "$LOG"

# poda o log (mantém ~400 linhas)
tail -n 400 "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG"
