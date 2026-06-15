# Regime pipeline (Production v2) — reconstrução offline canônica

Reconstrução **offline, repo-local e validada** do pipeline de regime XAU usado como
pré-condição da L1 (`runtime_xau.py`). **Bloco 1: sem dado fresco, sem MCP, sem runtime change.**

## Cadeia canônica
```
OHLCV diário → build_daily_features.py → features diárias
features + v1 "B" classifications → regime_pipeline.py (v2 + v3) → v3_state (BULL/TRANSITION/BEAR)
```

## `build_daily_features.py` — features (engenharia reversa validada, diff=0)
Definições inferidas contra `candidates/regime_classifier_v3/xau_daily_with_features.jsonl` e validadas:
- `ma_50` = SMA(close,50) · `ma_200` = SMA(close,200) — **diff=0**
- `rsi_14` = RSI Wilder(14) · `rsi_ma_14` = SMA(rsi_14,14) — **diff=0**
- `slope_20_pct` = linreg_slope(close[-20:]) / mean(close[-20:]) × 100 — **diff=0**
- `atr_14` = ATR Wilder(14) — **exato de 2016-09-01 em diante (2509/2509)**; os 59 bars iniciais de 2016 (`n_bars=6` incompletos) divergem só por seeding Wilder (decai e some até 2016-09-01) — irrelevante p/ regime recente/futuro.

## `regime_pipeline.py` — v2→v3 (port fiel, repo-local)
Port fiel de `regime_classifier_B_v2.py` + `_v3.py` lendo paths do repo. Validado:
**`v3_state` reproduz o canônico 2582/2582 (100%)** até 2026-05-25. `dist_alarm`=100% False no canônico → eventos de distribuição ausentes não afetam.

## 🔴 Gap conhecido (Bloco 2) — classificador v1 "B" AUSENTE
O classificador v1 "B" (cascade/stage/breaks que gera `combined_score`/`state`) **não está no repo**.
Este bloco **sourceia a saída do v1 B do registro canônico** (offline, até 2026-05-25) — NÃO reconstrói a lógica do v1 B.
**Estender o regime para dias novos (live) exige o v1 B** (reconstruir a lógica cascade/stage, ou recuperar o script) **+ dado diário fresco** (re-coleta 1D RAW ou leitura D live). Decisão do Bloco 2.

## Validar
```bash
REG=my-strategy/strategies/candidates/regime_classifier_v3
python3 build_daily_features.py --ohlcv "$REG/xau_daily_with_features.jsonl" --validate-against "$REG/xau_daily_with_features.jsonl"
python3 regime_pipeline.py --v1b "$REG/regime_B_v3_classifications.jsonl" --daily "$REG/xau_daily_with_features.jsonl" --validate-against "$REG/regime_B_v3_classifications.jsonl"
```
Read-only, headless, sem MCP/rede/runtime change.
