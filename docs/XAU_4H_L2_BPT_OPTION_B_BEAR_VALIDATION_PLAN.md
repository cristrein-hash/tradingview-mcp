# XAU 4H L2/BPT — Opção B: validação independente em regime BEAR (plano de coleta)

**Status:** `COLLECTED + ARCHIVED (2013-02→2016-05, 5100 bars, PASS) · VALIDATION PENDING USER GO` · **Data:** 2026-06-18

## ✅ COLETA CONCLUÍDA (2026-06-18)
Bloco **2013-02-01 → 2016-05-25**: 5100 bars (5076 ts únicos, 24 dup, 0 fora-de-ordem, 0 JSON inválido, 0 `_error`), 6/6 fontes RAW 5100/5100, indicadores OB+SMC+NAS+Bubbles+RSI+Volume todos 5100/5100. Local `alert-bridge/logs/backtests/XAUUSD_240m_replay_2013-02-01_to_2016-05-25.jsonl` (533M, RETIDO). Externo `…/raw_replay/XAUUSD/4H/XAUUSD_240m_replay_2013-02-01_to_2016-05-25.jsonl.gz` (65M, sha256 `6175e11f…`, roundtrip==original `349c2b69…`, gzip -t OK, manifest gravado). Produção restaurada (pause off, 0 orphan, `xau-l1-cycle` reativado). **Validação (§4) aguarda GO do Cris.**

Coleta/validação **independente** para responder a pergunta que a Opção A não pôde: o L2/BPT TAKE engine generaliza além do bull-beta, ou é bull/dip-scoped? Foundation: [[XAU_4H_L2_BPT_TRADE_QUALIFICATION_ENGINE_OOS_VALIDATION]].

## 1. Por que 2013 (bear do ouro)
A janela 2020-2026 tem **1 único bear real (2022, n=4, TAKE 0/4)** → Opção A é estruturalmente incapaz de testar regime não-bull. O **bear do ouro 2013-2015** (pico 2011 ~$1920 → fundo dez/2015 ~$1050; crash de abril/2013 de ~$200 em 2 dias) é o regime adverso sustentado canônico. **Não cross-asset** (regra do Cris) — é XAU, regime diferente. Não existe bloco 4H < 2016-05 ainda → genuinamente novo e independente.

## 2. Coleta (operacional)
- **Símbolo/TF:** `PEPPERSTONE:XAUUSD` 4H (`--timeframe 240`).
- **Janela:** start **2013-02** (máx que o chart 4H carrega, confirmado pelo Cris). End: a confirmar (ver §5).
- **Ferramenta canônica:** `safe_backtest_window.sh --replay-collect --timeframe 240 --start-date 2013-02-01 --end-date <END>` (cap 8000 bars). RAW completo: `ohlcv, study_values, pine_boxes, pine_labels, pine_shapes_bubbles, pine_lines`. **Sem reduzir payload (sem SLIM).**
- **Indicadores (baseline, Cris confirma manual):** Custom OB Detector, Smart Money Concepts [LuxAlgo], NAS TOP BOTTOM DETECTOR, Market Order Bubbles, RSI. (Session VP nativo = bônus; se ausente em 2013, esses fatores ficam null = aceitável.)
- **Preflight extra (gap do wrapper):** o wrapper pausa `xau-4h-monitor-daemon`/`-cron` (inexistentes); **pauso `xau-l1-cycle` manual** + limpo orphan `server.js` antes; restauro ambos no fim.
- **1 bloco por autorização.** Não auto-iniciar próximo.

## 3. Arquivamento (pós-coleta, skill replay-backtest-manager)
gz externo + SHA256 + `gzip -t` + roundtrip hash + manifest em `/Volumes/GUTS_ LACIE/TradingData/`. **Não deletar RAW local** sem validação externa + aprovação explícita.

## 4. Validação (após coleta — pré-registrada AGORA, sem retune)
1. Rodar o **detector L2/BPT** + **extrator de 84 fatores** (`qualification_extract.py`, mesmas defs causais) sobre o novo RAW 2013-2015.
2. Rodar o **mesmo raciocínio do engine** (rubrica `QUALIFICATION_RUBRIC.md` **inalterada**, subagentes cegos ao resultado) → TAKE/REVIEW/SKIP.
3. **Pré-registro do teste:** no bear 2013-2015, medir TAKE vs SKIP + TAKE vs random-casado-no-bear. 
   - **PASS regime-geral:** TAKE>SKIP **e** TAKE bate matched-random no bear (P alto, n suficiente).
   - **FAIL (confirma bull-scoped):** TAKE não bate SKIP/baseline no bear (espelha 2022 0/4). Resultado válido e honesto — fecha o escopo do engine.
4. **Sem retune, sem novo filtro, sem reclassificar.** A rubrica e os fatores são os de 2020-2026. Só medir generalização.

## 5. Confirmações pendentes (antes de disparar)
- **Janela end-date** (quanto de bear coletar).
- **Indicadores carregados** no chart 2013 (baseline §2).
- **Autorização** de 1 bloco.

---
*Plano. Coleta NÃO iniciada. Operacional via skill replay-backtest-manager + safe_backtest_window.sh. Produção restaurada em todo exit path. Nada promovido.*
