# EXIT FAMILY LAB · RELATÓRIO FINAL (2026-07-04)

## 1. Executive verdict
**EXIT_VARIANT_MATERIAL_TRADEOFF** — o exit trail padrão da stack aprovada de fato suprime convexidade em amostra, mas nenhuma variante DOMINA: o ganho vem acoplado a piora material dos eixos FN e a fragilidades de robustez que o DA quantificou. **Nenhuma adoção recomendada pelo lab; decisão = Cris; árbitro limpo = dados virgens.**

## 2. Contexto e ledger
Descoberta = cruzamento entry×exit (1 look declarado; winner's curse do "melhor-de-4" DECLARADO — este lab confirma implementação/painel, não valida seleção). Família congelada: E0 trail (oficial) · E1 trail-pós-3R · E2 alvo 3R · E3 alvo 5R. Entradas fixas: BASE435 (primário) e SISTEMA_A_53 (secundário/EXPLORATORY). Baseline E0 reproduz a stack aprovada fail-loud.

## 3. Painéis (NET-SB; IC = bootstrap pareado por episódio)
**BASE435:** E0 +234,3 (WR 45,7 · stk −8/q95 13 · DD −14,2 · pior mês −4,7) · **E1 +316,7 (135%; Δ +82,3 IC [+25,9,+152,6]** MAS WR 38,4 · **stk −14/q95 19** · DD −18,8 · **pior mês −11,2** · Δ2024 −2,4 · conc. 2025-01 = 38%>gate; sem esse mês IC cruza 0) · E2 +185,7 (Δ −48,6, FAIL) · E3 +298,2 (IC cruza 0).
**SISTEMA_A_53:** E0 +25,9 (WR 60,4 · stk −3) · **E2 alvo-3R +47,1 (Δ +21,2 IC [+0,6,+43,1]; WR 49,1 · stk −4/q95 8 · todos anos +** · conc. 2024-09 45%>gate, sem ele IC cruza 0 · N53) · E1 +42,2 e E3 +42,0 (ICs cruzam 0).

## 4. Mecanismo (decomposição DA)
167/435 trades TOCAM 3R independentemente do exit; o Δ do E1 = +167,8 nos tocadores − 85,5 nos não-tocadores (o custo de segurar sem trail = a queda de WR/streak). O "run3 91" do E1 é bookkeeping, não runners novos. Exposição média sobe 29→51 barras (1,7-2,3×) — risco overnight/notícia não precificado.

## 5. Leitura FN honesta
E1 é **exit de convexidade para conta própria** — com trava de streak prop (q95 19; pior mês −11,2R), só operável a sizing reduzido que corta o ganho em $ pela metade. E2 no Sistema A preserva o perfil FN (stk q95 8, WR 49) com ganho modesto — o casamento estilo-exit faz sentido (entradas de resposta-rápida + alvo fixo), mas N=53 e concentração exigem dados virgens.

## 6. O que fica
- **Fato estabelecido (em amostra):** o trail +1R não é neutro — custa ~80R de convexidade na base em troca de WR/streak/DD melhores. É um DIAL, não um erro.
- **Registrado para arbitragem em dados virgens:** deltas de exit re-mediáveis sem winner's curse nas extensões futuras (o pipeline de extensão está pronto).
- **Nada muda na stack aprovada sem palavra do Cris.**
