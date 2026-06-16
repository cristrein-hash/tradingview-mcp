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

## STATUS DE IMPLEMENTAÇÃO: APROVADO — **PENDENTE WIRING NO SCANNER/RUNTIME LIVE**
O `scanner.py`/`runtime_xau.py` live **ainda NÃO implementam** o stack v1 + filtro NAS + SL novo. Implementar é mudança de código operacional (Pre-Change Discipline + confirmação do Cris). Até lá, esta config é o **alvo aprovado**, documentado, não-deployado.
