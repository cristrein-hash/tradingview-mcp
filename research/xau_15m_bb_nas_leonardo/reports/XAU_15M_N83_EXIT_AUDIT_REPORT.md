# N83 EXIT AUDIT (F4) — relatório
**2026-07-09.** Exit = FIXED_3R first-touch SL-first, horizon 1440; **52 TGT / 31 SL / 0 TIME; 0 both-touch** → +3/−1 = modelo executável ao nível do trade; time-in-trade mediana 61 barras (JSON: `xau_15m_n83_exit_audit_result.json`).
**⚠️ CORREÇÃO (FINAL DA):** `executable_live: SIM` vale **condicional-à-população**; a população N96 tem event-selection lookahead (94/96 pré-confirmação) → o conjunto não é alcançável por executor causal. Verdict corrigido: `EXIT_CAUSAL_CONDITIONAL_ON_LEAKED_POPULATION`.
