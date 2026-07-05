# CASCATA-EXAUSTA v0.1 (XAU15M_CASCEX) — PRÉ-APROVADA · LAYER 1 ENTRY XAU LONG 15M

**Status:** `USER_PREAPPROVED_LAYER1_NOT_PRODUCTION` (Cris, 2026-07-05, após veredito visual dos 15 plotados ago/2025+: "primeira estratégia realmente mais madura"). Pré-aprovação ≠ validação ≠ produção.

## Config congelada (3 camadas, tudo causal ao close da barra de confirmação cj)

1. **ESTRUTURA (gatilho):** fundo local (fractal, universo lab_g) com **cascata ≥4 quebras estruturais bear consecutivas** (tokens BOS-/CHoCH- LuxAlgo, janela 48h; direção = close(t)>preço do evento; `t` = first-appearance/known_at, verificado em `build_causal_primitives.py:74`).
2. **INDICADORES em contexto:** `h1_rsi ≤ 42` E (`in_demand` OU `dist_demand_atr ≤ 0,5`) E `reclaim_atr ≥ 1,5`.
3. **VETO PERNADA-MACRO (risk-control, mecanismo nomeado pelo Cris):** SKIP se pernada macro (origem = high máximo 1920 barras/20d) em início/aceleração: `vel ≥ 0,10 ATR/barra` OU `recent_frac ≥ 0,5`.

**Execução:** entry = close@cj · SL = flush −0,1 ATR · exit fixo **3R first-touch** · custos SB $0,80 incluídos.

## Painel (2024-05 → 2026-07, RAW selado)

| | N | hit-3R/WR | sumR | avgR | DD | r/DD | streak | freq | 24/25/26 |
|---|---|---|---|---|---|---|---|---|---|
| **v0.1 (com veto)** | 34 | 55,9% | +39,6 | +1,17 | −4,8 | 8,2 | −4 (q95 6; P>5=0,19 episódico) | 0,31/sem | +6,7/+23,3/+9,6 |
| sem veto (ref.) | 56 | 44,6% | +41,4 | +0,74 | −5,5 | 7,5 | −5 (P>5=0,46) | 0,51/sem | +9,8/+19,0/+12,6 |

## Proveniência e DAs
- Descoberta: `smc_grammar_engine_20260705.py` (cascata) → pré-registo `cascade_context_indicators{,_v2}` (indicadores; v2 corrigido pós-desafio Cris) → `macro_leg_position_veto` + `macro_leg_kept_panels` (veto). Commits `211aa49` · `82a6746` · `bb62287`. Plot: `plot_cascex_34.py`.
- DA cascata: LEAD (multiplicidade sessão P efetivo 0,004-0,03; degrau no threshold; população disjunta dos 60 fundos GT do Cris 4/97; dependência do timing de labeling LuxAlgo — reproduzível ao vivo com o mesmo indicador).
- DA veto: RISK_CONTROL_CANDIDATE — enriquecimento loser 2,5-3:1 causal-limpo, null episódico P=0,009/0,020, replica em N228 e em CONTAGEM no período não-visto; **ganho de NET confinado à janela vista pelo Cris** (fora: NET-neutro; compra forma, não expectancy). M1 (age≤24h) refutado.
- Causalidade SMC known_at: PROVADA na fonte do builder (first-appearance por id em replay barra-a-barra).

## Buracos declarados / pendências para promoção
1. **Streak distribucional P(>5)=0,19** (episódico) — melhor perfil mecânico já achado no 15M, não imune a FN≤5.
2. Losers restantes = perfil "complexo BEAR envelhecido" (13/15) — inseparável com features atuais (#54 vs #55/56 idênticos na geometria macro).
3. Frequência 0,31/sem (~16/ano) — Layer 1, não engine única.
4. **Promoção exige:** pré-registo selado + dados virgens/forward + decisão Cris sobre o veto como camada shaping definitiva.
