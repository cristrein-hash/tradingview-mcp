# PROMPT PRONTO — XAU 15M OPÇÃO A: POST-CONFIRMATION TEST
TRADING SYSTEM — XAU 15M LONG MARKUP-DEMAND — EXECUTE OPTION A (ENTRIES PÓS-CONFIRMAÇÃO)
Objetivo: executar a Opção A completa conforme `XAU_15M_MARKUP_DEMAND_BASE_REPAIR_OPTION_A_PREREG.md`:
- universo: candidatos = pivôs L CONFIRMADOS (entries só após conf_i; janela reclaim 24 barras de conf_i);
- filtro Intra-Bear Capitulation inalterado (SKIP BEAR-v5-causal & 1D_px_vs_ema>=0, normalização /ATR_15M[j]);
- SL V1 (pivot_low − 0,1ATR[pivot]); exit 3R first-touch SL-first h1440;
- source guard (sem futuro; anti-survivorship); métricas painel completo + per-year/quarter/regime;
- robustez: nulls (exato+episódico), bootstrap semanal, slippage, delay, sobreposição;
- comparação justa vs Opção B (166→144, 31,9%, +40R marginal);
- DA adversarial via Agent real; claims ledger; report; commit/push.
PROIBIDO: produção, Telegram, broker, runtime, chart, tuning de thresholds, mudar filtro/SL/exit.
Verdicts: PASS_READY_FOR_VISUAL_REVIEW / PARTIAL / FAIL_EDGE_DOES_NOT_SURVIVE.
Gate: HEAD==origin, working tree limpo, safety baseline, protocolo 15M V1 ativo.
