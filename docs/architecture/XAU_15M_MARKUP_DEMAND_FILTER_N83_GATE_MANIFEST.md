# XAU 15M — LAB GATE MANIFEST · MARKUP-DEMAND + FILTER N83

**Data:** 2026-07-09 · **Protocolo:** `XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1 = ACTIVE` · **Stage:** 1 (Gate manifest)
**Status:** **`PASS_READY_FOR_TEST_AUTHORIZATION`** (recovery 2026-07-09; era `BLOCKED_MISSING_N83`) — **lab ainda NÃO autorizado a correr** (aguarda autorização explícita do Cris; nenhum backtest corrido).

> **RECOVERY 2026-07-09:** o Cris corrigiu — o PDF `~/Desktop/Sistema_Agentico_Trading_XAU_LONG_PT.pdf` (2026-07-08) reporta "Markup-Demanda + Filtro Capitulação · 96 → 83 · 62,7% · +125". Usado **só como ponte de proveniência**, levou à fonte real: **"Filter N83" = INTRA-BEAR CAPITULATION FILTER** (`SKIP se BEAR-v5-causal & 1D_px_vs_ema≥0`; 13L/0W cortados; ids 24,25,55-59,66,67,79,83-85). Verificação mecânica das 3 métricas a partir do repo: `research/xau_15m_bb_nas_leonardo/reports/n83_source_recovery_verify.py` = **SOURCE_RECOVERED** (52W/31L=62,7% · +125R@3R). Proveniência: `n96_fase1_fase2_maps.py` → `results/n96_intra_bear_cut_{list.json,trades.csv}` → doc `XAU_15M_N96_INTRA_BEAR_CAPITULATION_FILTER_20260708.md` → commit `a32b25a`. Status do filtro: `USER_APPROVED_NOT_PRODUCTION` · `PROFITABLE_BUT_FRAGILE` (+4…+13R conforme detector).

Prereg completo: `research/xau_15m_bb_nas_leonardo/reports/XAU_15M_MARKUP_DEMAND_FILTER_N83_PREREG.md`.
DA: `research/xau_15m_bb_nas_leonardo/reports/XAU_15M_MARKUP_DEMAND_FILTER_N83_PREREG_DA.md`.

## Bootstrap (Stage 0)
- HEAD == origin/main == `630b806` · working tree limpo · safety BLOCKER=3/W=1/INFO=50 (baseline).

## Lab
- **Nome:** XAU 15M LONG — Markup-Demand + Filter N83.
- **Unidade (congelada):** episódio markup-demand → entrada causal reclaim EMA21 (engine N96).
- **Universo:** PEPPERSTONE:XAUUSD · 15M · ago-2025→2026-07-03 · RAW `research/xau_15m_bb_nas_leonardo/`.
- **Base:** N96 (`entry_engine_master_20260707.json`, 96 markup/52W) = `RESEARCH_BASE` (swept-runner `RESEARCH_BASE_NOT_OFFICIAL`; N96 `USER_APPROVED_NOT_PRODUCTION`).

## Source guard (Stage 2) — estado
- macro_regime ✅ (`n96_causal_regime.json`, 96/96) · leg_state ✅ (leg-walk r=6) · **family_label ⚠️ PARCIAL (loser-only 44/96)** · markup-demand primitives ✅ · entry/SL/target ✅ (V1, 3R, outcome forward-only, sem leak/SLIM — DA-confirmado).
- **Filter N83 ✅ RECUPERADO** = intra-BEAR capitulation (`macro_regime BEAR-v5-causal` + `1D_px_vs_ema≥0` → SKIP). Campos causais, RAW-mapeados.

## Pendências antes de execução de teste (o gate técnico está pronto; falta autorização)
1. **Autorização explícita do Cris** para o estudo que usar esta base+filtro.
2. family_label cobertura 96/96 **se** o estudo a usar como gate (hoje loser-only).
3. Materializar claims ledger do lab (`docs/templates/XAU_15M_CLAIMS_LEDGER_TEMPLATE.csv`).
4. Passar blockers na execução: `check_xau_15m_raw_lineage.py` · `check_xau_15m_structural_first.py` · `check_xau_15m_claims_ledger.py` · `run_xau_15m_lab_gate.py` = `XAU_15M_LAB_GATE_PASS`.
5. DA adversarial via Agent tool (Stage 7).

## Confirmação negativa
Nenhum backtest · nenhuma produção · nenhum Telegram · nenhum broker · nenhum runtime/strategy_rules/monitor · nenhum chart/plot/screenshot.

**GATE: PRONTO PARA AUTORIZAÇÃO (PASS_READY_FOR_TEST_AUTHORIZATION). Nenhum teste corre sem autorização explícita do Cris.**
