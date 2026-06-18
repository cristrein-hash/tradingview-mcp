# XAU 4H L2/BPT — F_STRICT × Regime: leitura comparativa (vs GPT)

**Status:** `RESEARCH · ANALYSIS · NO_PRODUCTION · NO_PROMOTION` · **Data:** 2026-06-18
Análise dos 12 prints full-res + dados causais + teste empírico de regime, comparada à leitura do GPT. DA dedicado. Sem plotagem nova, sem produção.

---

## 1. Tese do GPT (resumo)
F_STRICT discrimina late-entry/topo bem, mas corta 3-4 bons trades em bull (idx6453, idx8765, idx9368, idx9390) → deve ser regime-condicionado, não hard-block universal. Próximo bloco = F_STRICT × regime.

## 2. Onde concordo
F_STRICT = discriminador útil de topo/exaustão; NÃO hard-block universal; melhor uso = human-review/Telegram flag; não mexer no threshold.

## 3. Furos factuais no GPT (dados)
Outcomes reais (sim partial50@2R+6R + SL estrutural):
- **idx9390 (2026-01-28): R −1.10 = LOSER** (topo que rola, print 14.29.15). Corte é CORRETO, não falso-positivo. GPT pôs um loser na lista "preservar".
- **idx6453 (2024-03-05): R +0.13 ≈ breakeven** (breakout overbought saindo de range, print 14.31.45). Não é "bom trade".
- idx8765 (+1.95) e idx9368 (+0.90) = winners reais.
- **Custo real ≈ 2 winners (~+2.85R), não 4 trades.**

## 4. A tese central (regime separa) é FALSA empiricamente
Split por regime (sl200 = %Δ em 200 barras, causal):
| regime | n | W/L | avgR |
|---|---|---|---|
| STRONG BULL >+10% | 9 | 5/4 | +0.08 |
| BULL mod +3..+10% | 13 | 5/8 | −0.03 |
| RANGE −3..+3% | 7 | 4/3 | −0.02 |
| BEAR <−3% | 1 | 0/1 | −1.10 |

- **Strong bull = coin-flip 5W/4L**, não "corta bom".
- O **maior loser (idx9390, sl200 +25% / sl50 +15% = blow-off vertical) está no bull MAIS forte.**
- Winners e losers **interleaved dentro do mesmo regime**. "Ignorar F_STRICT em bull" re-admite ~4 bull-losers (idx9390, E23, idx9243, idx6597) pra salvar ~5 winners pequenos → net ~zero.

## 5. Verdade mais profunda
F_STRICT é near-breakeven em TODOS os regimes (+0.08/−0.03/−0.02; 14W/16L total; bootstrap confirma). Reslicing por regime (incl. Classifier v3) muda o eixo mas **não des-interleava** outcomes co-localizados → bloco "F_STRICT × regime" é EV-baixo (reconfirma o nulo). O conditioner certo NÃO é regime — é **leitura estrutural por-trade** (humano): pullback-continuação (idx8765/idx9368) vs blow-off vertical (idx9390). Proxy não vê; humano vê.

## 6. Fio aberto (oposto ao GPT)
O bull mais esticado dá os PIORES losers → sinal real provável = **intensidade de exaustão/stretch** (quão vertical), não "bull=bom". Feature-engineering com amostra séria (não n=3), NÃO regime-gate.

## 7. Recomendação
- **NÃO** abrir bloco "F_STRICT × regime" (dead-end como regra automática — DA + dados).
- **F_STRICT = Telegram/human-review flag**; regime = 1 input do humano, não gate.
- Casos = exemplos de julgamento (idx8765/idx9368 continuação limpa; idx9390 corte correto; idx6453 BE).
- Futuro eventual: stretch/exhaustion-intensity, com amostra.

## 8. DA appendix
DA: proxy sl200 é crude (magnitude, não estrutura) MAS a falha (pior loser no bull mais forte) é robusta a escolha de proxy; n por bucket pequeno (9/13/7/1) mas o padrão near-breakeven é robusto PORQUE win/loss estão interleaved, não por n; multiple-comparison sobre 4 buckets só FORTALECE o nulo (MC infla falso-positivo de separação, não nulo); idx9390 R−1.10 = piso de sim (stop antes de +2R) mas inequivocamente "stopou pré-2R" = corte correto; v3 re-slice = EV-baixo. Veredito: regime-conditioning F_STRICT NÃO merece bloco dedicado; ship como human-review-flag; único fio futuro = stretch-intensity (oposto da hipótese GPT). Causal: sl200/sl50 = closes passados ✓. Sem produção/SLIM/plot.

---

*Outputs: este doc. Sem produção, sem plotagem nova, sem promoção. Prints ref: zip FILTRO_ F_STRICT (12 full-res).*
