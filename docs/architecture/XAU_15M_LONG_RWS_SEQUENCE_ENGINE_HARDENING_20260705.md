# RWS-15M — ENGINE SEQUENCIAL · HARDENING (2026-07-05)

## Origem
Crítica do Cris (prints Sistema A): entradas eram TOPO de range (box96 med 0,87; 0/53 no fundo), WR inflado por let-run pingando em pops esticados. Correção: leitura CONTEXTUAL/SEQUENCIAL (não snapshot). Portei o **V1.4g-RWS-A6** (4H reversal OFICIAL, WR67/streak4/DD4,4R) para 15M. Snapshot/estrutura/perna-HTF/indicadores todos capam em ~10% precisão / ~32% hit; **só o read SEQUENCIAL (acumulação de bubbles no tempo) tem edge.**

## Config CONGELADA (sha `b391f7bb...`)
`buy_recent(bubbles 0-4b, peso S1/M2/L3)>=2` · `(rsi_above_ma14 OU n_supply_overhead>20)` · anti-burst-fake(A6) · anti-RSI-bear-div-cluster≥2/20b(A7) · regime v5h≠BEAR · sem faca · entry=close@cj · SL=flush−0,1ATR · **exit=3R first-touch (árbitro).** Lista selada: `results/rws15m_signals_20260705.json`.

## Painel (N54)
| exit | hit3R | WR_liq | NET-SB | DD | streak-obs | anos (24/25/26) |
|---|---|---|---|---|---|---|
| **3R-fixo** | 44,4% | 46,3 | **+38,8** | −5,1 | 4 | 10,0 / 27,4 / 1,4 |
| let-run (alt) | 44,4% | 57,4 | +21,9 | −5,3 | 4 | 4,6 / 20,0 / −2,7 |
Frequência **26/ano** (mais que o V1.4g-4H, ~16/ano). Walk-forward por ano: 2024 40% · 2025 51,7% · 2026 30%.

## Nulls & robustez
- hit-3R obs 44,4% vs regime-matched 28,8% → **P=0,008** · year-matched P=0,006 · NET P<0,001.
- Multiplicidade (~5-8 looks familiares): NET sobrevive Bonferroni (P<0,008); **hit-rate fica MARGINAL** (P→0,040).
- Jackknife: pior mês = 23% do NET (< gate 35).
- **Causalidade PROVADA (DA):** recomputação independente 54/54 byte-idêntica; variante *leaky* (ignora bubble known_at) dá 131 sinais @ 33,6% — o filtro known_at é load-bearing e seleciona trades MELHORES, zero look-ahead.

## RESSALVA CENTRAL (DA — não enterrar): STREAK distribucional REPROVA FN
- streak-**obs 4**, mas bootstrap independente (block-episódio e iid): **q95=9-10, P(streak>5)≈0,45-0,50**; teórico (WR46%/N54) ≈ 5,2.
- **Sob exit 3R, ~50% de chance de estourar streak≤5 da FundedNext.** O obs-4 foi levemente sorte.
- **Trade-off de exit:** let-run tem WR 57,4% → P(streak>5)=0,16, q95=7 (FN-compatível) mas custa ~17R e 2026 negativo. **Segurança-FN e expectancy puxam em direções opostas.**

## Outras ressalvas
- **2026 = INCONCLUSIVO** (não refuta): majoritariamente BEAR (LONG fica fora corretamente); não-BEAR só Jan-Mar; N10 @ 30% = ruído (dentro do null); **dormente desde 2026-03 (4 meses sem sinal).**
- Fresta latente (inerte): NAS events sem `known_at` (0/54 usam o relaxamento anti-burst; fechar antes de forward).

## Veredito: **HARDENING_PASS_WITH_CAVEATS → PROMISSOR-NÃO-VALIDADO**
Metodologicamente limpo, causal, reprodutível/selado, NET significativo pós-multiplicidade. **NÃO vira "validado" limpo** por: (1) distribuição de streak incompatível com FN≤5 sob exit 3R (~50% violação); (2) 2026 sem confirmação viva; (3) hit-rate marginal sob desconto. **Promoção condicional exige:** mitigação de streak (exit maior-WR OU halt/sizing por streak), fechar NAS-known_at, e dados forward. Decisão de promoção = Cris.
