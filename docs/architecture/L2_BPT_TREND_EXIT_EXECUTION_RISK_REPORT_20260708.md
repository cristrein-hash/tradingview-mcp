# L2/BPT Trend-Exit — Execution/Risk Layer · Report

**Cris 2026-07-08.** Bloco `L2_BPT_TREND_EXIT_EXECUTION_RISK_LAYER`. Research-only, não produção. Prereg: `..._PREREG_20260708.md`. DA: `..._DA_20260708.md`.

## 1. Executive verdict
**Classificação: `FULL_UNIVERSE_STRESS_RISK_IDENTIFIED` + `SELECTIVE_STRATEGY_REQUIRES_CAUSAL_ENTRY_FORMALIZATION_BEFORE_PRODUCTION`.**

> **CORREÇÃO DE ENQUADRAMENTO (Cris 2026-07-08):** a estratégia oficial L2/BPT trend-exit **é seletiva** (SELECT-17 + novo exit), **NÃO** pretende acionar os 245. **FULL-245 = stress test / controle adversarial, não o universo de produção.** O DD−72R/streak22 pertence ao **universo amplo**, não à estratégia seletiva aprovada — operar 245 seria **outra estratégia**, não a aprovada. Portanto: (a) a estratégia oficial **NÃO está invalidada**; (b) a produção **NÃO está bloqueada pelo DD dos 245**; (c) a produção segue **pendente** porque falta **formalizar/validar a regra causal de seleção dos 17 em tempo real** (os parâmetros da seleção foram calibrados in-sample) **+ parâmetros de execução/risco sobre essa seleção**.

A camada exec/risco é uma caracterização honesta de controlos de cauda — **toda variante custa R, nenhuma é edge**. Status `USER_APPROVED_OFFICIAL_NOT_PRODUCTION` inalterado (só o Cris muda).

## 2. Baseline reproduction (fail-loud PASS)
SELECT-17: let-run120 +36.2 · hold500 +90.3 · **trend-exit +105.3R** (DD−4.1, streak3, retDD 26). FULL-245: let-run120 +52.5 · hold500 +257.6 · **trend-exit +399.2R** (DD−71.8, streak22). #6 mecânico +1.15R.

## 3. Risk anatomy (17-selecção, `l2_bpt_risk_profile.py`)
Mediana hold 54d, máx 83d; 6 trades ao CAP-500; saídas STOP=7/BEAR=4/CAP=6 (só 4/17 por regime-flip); **até 3 posições concorrentes**; 805 trade-days. Risco em pontos: mediana 26, máx 173.

## 4. DD/streak drivers
Tame DD−4.1/streak3 = **100% da seleção retrospetiva de entrada** (`keep()` afinado a mão para excluir os bears 2023). A MESMA lógica no full-base = **DD−72/streak22**. Os winners são os holds longos (+9 a +21R); os losers são os STOP curtos em clusters (o que gera o streak no full-base).

## 5. Gap / stops-largos risk
4 stops largos 2025: #13(97pt STOP), #14(82pt +19.77), #16(173pt STOP), #17(124pt +10.89). Gap-buffer −0.5/−1R nos STOP>80pt: SELECT-17 +104.3/+103.3 (worst −1.85/−2.35). **Real mas sub-modelado** (não cobre gaps durante holds de 83d; 173pt pode gapar >2R num choque). **2ª ordem — não bloqueia sozinho.** stop-width≤80 remove os wide MAS mata 2 big winners (#14,#17) → +77.4R.

## 6. Sizing/caps testados (SELECT-17 / FULL-245 · todas reportadas, sem cherry-pick)
| variante | 17 sumR | 17 DD | 17 stk | full sumR | full DD | full stk |
|---|---|---|---|---|---|---|
| BASELINE | +105.3 | −4.1 | 3 | +399.2 | −71.8 | 22 |
| hold-cap 360 | +76.3 | −4.1 | 3 | +282.8 | −65.9 | 22 |
| hold-cap 240 | +65.8 | −4.1 | 3 | +225.1 | −53.1 | 14 |
| stop-width ≤100 | +95.8 | −4.1 | 3 | +360.4 | −69.7 | 20 |
| stop-width ≤80 | +77.4 | −2.7 | 2 | +319.8 | −68.3 | 19 |
| gap-buffer −0.5R | +104.3 | −4.6 | 3 | +392.7 | −72.8 | 22 |
| partial 50%@+2R+BE | +56.0 | −2.1 | 1 | +170.5 | −50.0 | 12 |
| DD-guard @−15R | +105.3 | −4.1 | 3 | **+41.7** | −15.6 | 12 |
| max-concurrent 2 | +98.5 | −4.1 | 3 | **+119.1** | −18.4 | 12 |
| max-concurrent 1 | +60.0 | −2.7 | 2 | +68.9 | −9.7 | 12 |
**Toda redução de DD custa R.** Melhor retDD (17): stop-width≤80 (28.7) e partial (27.3). Melhor controlo full-base: concurrent-2 (DD−18, retDD 6.5) ou DD-guard (−15) — a grande custo de R.

## 7. SELECT-17 vs FULL-base (a distinção que importa)
- **SELECT-17 = a ESTRATÉGIA APROVADA / alvo de produção futura** — seleção causal por posição-em-zona (prior-segment hi/lo, sem look-ahead) + trend-exit. Perfil in-sample +105.3R / DD−4.1 / streak3. 2.8/ano (extremamente seletiva, por design).
- **FULL-245 = STRESS UNIVERSE, não plano de execução** — o que aconteceria se se acionasse TODOS os sinais L2/BPT (outra estratégia). DD−72/streak22. Serve de controlo adversarial amplo, **não** de critério para bloquear a estratégia seletiva.
- **A questão real:** os parâmetros da seleção (`amp/3`, `≥15`bar, `180`d) foram **calibrados in-sample**. O gate pré-produção é **provar que essa seleção causal reproduz forward** (janela virgem / próximas ops live), não o DD de um universo que a estratégia nunca vai operar.

## 8. #6 result
hold-cap 240-360 → #6 +2.0-2.55R (vs +1.15 baseline). Mas o cap custa 29-39R à carteira e o #6 ainda fica aquém dos **+3R discricionários** do Cris. **Cosmético/fitting, não melhoria mecânica.**

## 9. DA verdict (com a correção de enquadramento aplicada)
O DA mantém a crítica ao **universo 245** (DD−72/streak22; nenhuma variante mecânica passa FundedNext streak≤5 no universo amplo). **MAS isso é STRESS TEST, não critério de rejeição da estratégia seletiva aprovada.** O ponto substantivo que fica de pé: a tameness dos 17 vem da **seleção de entrada calibrada in-sample** → antes de produção é preciso **validar essa seleção forward** (não é look-ahead — a lógica é causal; são os parâmetros que precisam de robustez forward). Toda camada de risco custa R (confirmado).

## 10. O que a estratégia oficial NÃO é e o que fica pendente
- **NÃO invalidada.** **NÃO bloqueada pelo DD dos 245** (universo que não vai operar).
- **Pendente de produção por 2 coisas, sobre a SELEÇÃO (não sobre o exit):**
  1. **Formalizar/validar a regra causal de seleção dos 17 em tempo real** (parâmetros in-sample → forward-validar em janela virgem / ops live do Cris).
  2. **Parâmetros de execução/risco sobre essa seleção:** gap-handling nos 4 stops largos 2025 (2ª ordem) + exposição (até 3 concorrentes, holds de meses).

## 11. O que está pronto para review do Cris
- **Caracterização honesta** dos controlos de cauda sobre a estratégia seletiva (todos custam R; nenhum é edge).
- **Stress test do universo amplo** (245) documentado como controlo adversarial (não como plano de execução).
- O perfil in-sample da estratégia aprovada (SELECT-17) = +105.3R / DD−4.1 / streak3 — **cuja validade forward depende de validar a seleção** (o gate real).

## 12. Próximo passo requerido antes de produção (NÃO iniciado)
**Formalizar + forward-validar a camada causal de seleção dos 17** (regra de entrada causal com parâmetros robustos forward) **+ definir os parâmetros de execução/risco sobre essa seleção** (gap, exposição). Só então a estratégia seletiva aprovada é deployável. Produção segue pendente dessa formalização — **não por DD do universo amplo**. Decisão de rumo = Cris.
