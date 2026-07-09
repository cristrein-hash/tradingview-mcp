# PROMPT PRONTO — XAU 15M BULL BUCKET LAB
TRADING SYSTEM — XAU 15M LONG — BULL BUCKET LAB (base causal live-fireable)
Objetivo: investigar o BULL bucket (44,4%/PF~2,4/n45 na base causal Option B) como possível estratégia própria, sob protocolo 15M COMPLETO:
- manifest/gate (`docs/architecture/XAU_15M_BULL_BUCKET_GATE_MANIFEST.md`) ANTES de qualquer scan;
- universo: `xau_15m_live_fireable_candidates.csv` filtrado regime==BULL (v5 hour-causal) — congelar unidade;
- structural-first: macro_regime + leg_state + baldes canónicos ANTES de indicadores;
- hypothesis freeze; indicadores só DENTRO de baldes; claims ledger; nulls (mining-aware); DA real;
- SL V1 + 3R como base; capitulation N/A em BULL (declarar);
- NÃO assumir edge; NÃO tuning livre; NÃO produção/Telegram/chart.
Verdicts: PASS_RESEARCH_CANDIDATE / PARTIAL / FAIL.
Gate: HEAD==origin, tree limpo, safety baseline, blockers 15M (raw_lineage/structural_first/claims_ledger/lab_gate).
