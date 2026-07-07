# XAU 15M LONG — Estudo de Filtragem Contextual dos Losers (visual + bateria de features)

**Data:** 2026-07-07 · **Estado:** leitura visual VALIDADA pelo Cris; filtragem contextual = MURO (poisoning) com features atuais.

## 1. Leitura visual (22 prints, #1-#96) — VALIDADA pelo Cris
**WINNERS** = pullback-à-demanda dentro de perna de markup impulsiva JOVEM/MÉDIA (tendência com combustível, estende a 3R): #1R, #11-14, #28-30, #44-45, #71-75, #82R, #95-96. Assinatura: higher-low genuíno + BOS/CHoCH-up + VELA DE FUNDO + reclaim rápido (R) + perna ainda não esticada ao topo macro.

**LOSERS** = 3 modos macro-contextuais (= as 3 marcas de inválido do Cris):
1. **Exaustão de topo macro** (última puxada de perna esticada → range/reverte): #21,#23,#31,#55,#65,#83,#85,#46R → "POLARIDADE TOPO".
2. **Range/chop** (sem tendência p/ 3R): #56-60, #5-8R.
3. **Perna bear macro ativa** (comprar contra estrutura descendente): #66,#69,#93,#94,#89R → "FUNDO NÃO VALIDO POIS PERNA BEAR CLARA ANTECEDE"; #49,#50R → "FUNDOS NÃO VALIDOS DE PEQUENA ACUMULAÇÃO".

Nota: #64R,#77R,#80R,#87R,#89R,#93R são R (reclaim rápido) e MESMO ASSIM vermelhos → reclaim-R só qualifica dentro de markup jovem; em topo/range/bear falha. **markup/correção = MASTER; R = seletor dentro dele.**

## 2. Correção honesta dos proxies anteriores
O estudo de caso numérico anterior disse "exaustão não separa" e "bear-leg refutado" — ERRADO por medir na escala errada (leg_pos micro-15M; EMA diária lenta). A leitura visual macro prova que exaustão-de-topo e perna-bear SÃO os grandes viveiros de losers. Mesma miopia macro→micro.

## 3. Alinhamento ground-truth
Os 96 entries recomputados = as trades #1-#96 do Cris, **32/32 outcomes alinhados** (winners/losers conhecidos). Base sólida para reverse-engineering.

## 4. Bateria de features (deixar os dados escolherem) — resultado
12 features macro/estruturais causais, ranking por AUC (winner vs loser, N96 52W/44L):
- `slope_emaD` AUC 0,393 (mais forte): losers com slope 20d-EMA MUITO íngreme (+38 vs +14) = exaustão. **MAS filtrar slope>30 corta 23 losers matando 22 winners** (#13,#14,#44,#45,#71… markup forte tem slope íngreme) = ENVENENA.
- `supply_above` AUC 0,584 (0,619 dentro de R): winners com room à supply acima; losers encaixotados. Mecânico (3R precisa espaço).
- `demand_near`/`pos_in_20d`/`ret_20d`: ~0,5 = não separam. **Range-demand-no-fundo REFUTADO p/ 3R** (pos_in_20d 0-0,33 = 14% hit-3R; bounce de fundo de range só vai ~1R até o topo do range).

## 5. Filtragem = MURO de poisoning (achado central)
Melhor filtro limpo = room: **R & supply_above≥0,35 = 72% hit-3R N25 (2025:73%/2026:71%)** — a exaustão na forma certa. MAS corta ~9 winners fortes (romperam supply próxima) para cortar ~10 losers = **~1:1 poisoning**. **NENHUMA feature corta losers sem matar winners na mesma proporção.** Winners e losers COEXISTEM no espaço de features — os winners de markup forte têm a MESMA assinatura macro (slope, supply, bear) que os losers, porque são os que ROMPERAM. A distinção visual do Cris ("esta perna tem momentum p/ romper?") não está nas features atuais. **Mesmo muro do PLT/DM: leitura visual > features disponíveis.**

## 6. Estado honesto / dial
- **Engine limpo:** markup master 54,2% → reclaim-R 61,4% (ambos anos+, Cris-validado). Não-envenenado.
- **Room = dial opcional de risco** (não filtro grátis): exigir room-à-supply sobe hit-3R (72%) trocando por menos winners; decisão do Cris sobre o trade-off. É a exaustão ex-ante defensável (não sabes ex-ante quem rompe).
- **Diferenciação fina** (bull-genuíno-em-bear, range-demand, exaustão-sem-poison) = precisa do read visual do Cris OU features que não temos (momentum de rutura da perna). Não mecanizável limpo com o set atual.

## 7. Artefatos
`entry_macro_context` / `entry_struct_state` / `feature_battery_20260707.py` + results/*.json (commit desta sessão). Bateria: `results/feature_battery_20260707.json` (96 × 12 features + outcome).
