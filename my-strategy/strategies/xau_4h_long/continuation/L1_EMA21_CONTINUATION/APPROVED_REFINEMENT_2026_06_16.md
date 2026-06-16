# L1 EMA21 CONTINUATION — REFINAMENTO APROVADO (2026-06-16)

**Decisão do Cris:** APROVADO **sem OOS** — período 2020-01→2026-04 cobre todos os regimes e transições; sample suficiente; **risco assumido pelo Cris**. Validação por proxy + análise visual (Cris confirmou superior à versão anterior em todos os aspectos).

## Configuração aprovada (sobre a base-rule L1 já existente)
A base-rule L1 (regime BULL D-1 regime_l1_v4 + close>EMA21>SMA50 + slopes + BOS + zona Custom OB v11 + body≥0.35 + F5 vol≤1.0) **mais** as camadas refinadas:

1. **Filtro de regime/qualidade (stack v1, at-entry causal):**
   `ret5 ≤ 1.42% AND ext_ema ≤ 2.95·ATR AND zone_w ≥ 0.6·ATR AND dist_zone ≤ 1.81·ATR` (anti-extensão + zona de qualidade).
2. **Filtro NAS (causal, SHIFT1):** `NAS_DISTANCE_FROM_EMA_ATR(bar i-1) ≥ 1.31`.
3. **Exit aprovado:** **SL ESTRUTURAL = `max(zona_OB_low, swing6_low) − 0.1·ATR`** · **TARGET = +3R**.

## Métricas in-sample (63 candidatos → 34 após filtros, 2020-2026)
- **34 trades · winrate(target) 53% · sumR +41.0R · avgR +1.21 · PF 3.74.**
- Baseline sem filtros (63): WR 27%, +18.2R, PF 1.46. Stack v1 (49): +27.4R PF 1.94. C+SLv1 (34): +35.2R PF 3.20. **C+SL nova (34): +41.0R PF 3.74.**
- **5 monumentais (#48,#51,#52,#54,#61, MFE 6–18R) preservados (5/5 TARGET).** 1 winner curto perdido vs stack v1 (#3, +3R/MFE 4.04R).

## Natureza / caveats (registrados, aceitos pelo Cris)
- IN-SAMPLE optimization (não OOS). Ganho de WR parcialmente mecânico (SL mais apertado → alvo 3R mais perto). n=34. Exit-defined (3R fixo; a L1 produção usa V_stair).
- Causalidade: limpa (todas as features conhecidas no close do bar de entrada; NAS em SHIFT1).
- Fontes: `reports/l1_discriminator_filter_v1.md`, `_v2.md`/`.csv`, `l1_sl_structural_test.md`. Scripts: `discriminator_search*.py`, `sl_structural_test.py`.

## STATUS DE IMPLEMENTAÇÃO (atualizado 2026-06-16)
- **`scanner.py` (gate authority / research): IMPLEMENTADO.** Stack v1 + NAS SHIFT1≥1.31 + RSI gate + SL estrutural max(zona,swing6)−0.1ATR + target +3R. Estados: operational_candidate / blocked_exhaustion / **blocked_l1_refined_filter** / no_candidate. Saída inclui entry/stop/target + filter_trace. Causalidade validada (DA 10/10 PASS).
- **Validação histórica (full-scan 2020-2026):** **31 operacionais · 17 TARGET / 13 STOP / 1 TIME · +40.0R · PF 4.08 · 5/5 monumentais · #3 removido.** Difere dos 34 do estudo por 3 RSI-exhaustion-blocked (#26/#31/#47) que o gate de exaustão aprovado **corretamente exclui** (o estudo não os havia excluído). É a realização FIEL da config aprovada (gate de exaustão mantido).
- **Exit:** esta config aprovada usa **target +3R fixo** (substitui a menção a V_stair na base-rule, para ESTE refinamento). 
- **`runtime_xau.py` (LIVE): PARCIAL (2026-06-16 update).** NAS SHIFT1 resolvido via persistência por ciclo em `.runtime_state/l1_feature_history.jsonl` (fixture-provado causal) + reuso de `scanner.evaluate`. Guarda close-only-causal (bar-fechado) adicionada. **Ainda NÃO operacional:** no timing do scheduler o snapshot traz o bar em formação (`blocked_bar_not_closed`); operacional exige alinhar leitura ao bar fechado (bloco futuro). Detalhe: `reports/l1_runtime_nas_shift1.md`. [hist] HARD STOP anterior no NAS (regra #10): O snapshot MCP live só dá study_value corrente; **NAS_DISTANCE no bar i-1 NÃO é extraível causalmente** (sem histórico per-bar de study-value; recomputar = aproximar = proibido). Logo o runtime live **NÃO** emite operational sob a config completa — segue não-operacional (também depende de base-rule live). **scanner = gate autoritativo até o NAS-live ser resolvido** (bloco futuro: persistir NAS por ciclo em .runtime_state OU tool MCP de histórico de study-value).
