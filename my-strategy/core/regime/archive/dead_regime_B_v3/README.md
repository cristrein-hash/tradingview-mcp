> 🗄️ **ARCHIVE — REFERÊNCIA HISTÓRICA, NÃO-OPERACIONAL (2026-06-16).**
> `regime_pipeline.py` aqui reproduz o **regime legacy morto** v2→v3 (`regime_B_v3`), declarado
> IRRECUPERÁVEL. **NÃO é usado pela L1** — o regime operacional é `core/regime_l1/regime_l1_v4.py`.
> Mantido só como diagnóstico/lição. O builder `build_daily_features.py` permanece **OPERACIONAL**
> em `core/regime/` (usado por regime_l1_v4) e NÃO foi arquivado.

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

## 🛑 v1 "B" — tentativa de recuperação (HARD STOP, 2026-06-16)
- **Script original NÃO encontrado** (repo, git history, backups, safety pack, /tmp) — irrecuperável.
- **Engenharia reversa contra o canônico:** o **agregador** do scoring reproduz 100% — `combined_score = cascade_score + vol_score`; `cascade_score = Σ(+1 break_bull / −1 break_bear por TF h4/d/w)`; `ma200_bull/bear = close ≷ ma_200`; `raw_state` = (BULL≥2 / BEAR≤−2 / TRANSITION). **Mas as ENTRADAS do agregador NÃO reproduzem:**
  - `vol_score`: **~93%**, sem regra limpa sobre `atr_expansion_ratio` (ranges vol=0/vol=1 se sobrepõem) — definição extra desconhecida.
  - **breaks `h4/d/w`**: não deriváveis dos dados disponíveis (h4 exige estrutura 4H ausente; d/w só ~97% de ma50). Lógica de break estrutural multi-TF desconhecida.
  - `state`/`stage_dir`/`stage_n`: máquina de estágio não documentada (79%).
- **Veredito:** reconstruir os breaks + vol_score exigiria **inventar** a lógica → vetado. **HARD STOP.** O `combined_score` (única entrada que o v2 consome) depende dessas peças irreprodutíveis, então **classificar dias novos NÃO é possível** a partir dos artefatos atuais.
- **Para o Bloco 2 (decisão do usuário):** (a) recuperar o script v1 B original de outra fonte (fora deste repo/backups), OU (b) re-derivar a detecção de breaks estruturais multi-TF a partir de uma especificação canônica (não improviso), OU (c) substituir o regime D-1 por uma fonte de regime nova explicitamente aprovada. Sem (a)/(b)/(c) + dado fresco, o `runtime_xau.py` permanece corretamente em `regime_feed_stale`.

## Validar
```bash
REG=my-strategy/strategies/candidates/regime_classifier_v3
python3 build_daily_features.py --ohlcv "$REG/xau_daily_with_features.jsonl" --validate-against "$REG/xau_daily_with_features.jsonl"
python3 regime_pipeline.py --v1b "$REG/regime_B_v3_classifications.jsonl" --daily "$REG/xau_daily_with_features.jsonl" --validate-against "$REG/regime_B_v3_classifications.jsonl"
```
Read-only, headless, sem MCP/rede/runtime change.
