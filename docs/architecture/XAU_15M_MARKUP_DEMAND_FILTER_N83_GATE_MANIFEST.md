# XAU 15M — LAB GATE MANIFEST · MARKUP-DEMAND + FILTER N83

**Data:** 2026-07-09 · **Protocolo:** `XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1 = ACTIVE` · **Stage:** 1 (Gate manifest)
**Status:** **`BLOCKED_MISSING_N83`** — manifest aberto, **lab NÃO autorizado a correr** (nenhum backtest).

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
- **Filter N83 ❌ NÃO LOCALIZADO** (0 matches literais; `#83` = índice de trade loser).

## Blocker que impede o gate
🚫 **N83 sem definição.** Stage 5 (hypothesis-freeze) proíbe inventar predicado. Candidatos (Cris escolhe): `n96_range_distribution_filter` (N82, near-miss) · `n96_d_bear_active_filter` · Kaufman-ER `impulse_efficiency_prior_leg` (N52) · N96 base · trade #83. **Não vincular automaticamente.**

## Pendências antes de autorização de teste
1. **Cris define "N83"** (predicado real + campos).
2. Completar RAW/source mapping de N83 + **family_label cobertura completa (96/96)**.
3. Materializar claims ledger (`docs/templates/XAU_15M_CLAIMS_LEDGER_TEMPLATE.csv`).
4. Passar blockers: `check_xau_15m_raw_lineage.py` · `check_xau_15m_structural_first.py` · `check_xau_15m_claims_ledger.py` · `run_xau_15m_lab_gate.py` = `XAU_15M_LAB_GATE_PASS`.
5. DA adversarial via Agent tool (Stage 7).

## Confirmação negativa
Nenhum backtest · nenhuma produção · nenhum Telegram · nenhum broker · nenhum runtime/strategy_rules/monitor · nenhum chart/plot/screenshot.

**GATE: NÃO PASSA (BLOCKED_MISSING_N83). Aguarda definição de N83 pelo Cris.**
