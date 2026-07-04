# EXIT FAMILY LAB — DA ADVERSARIAL (2026-07-04)

DA pós-resultado independente (subagent real; `_DA_exitlab_{1,2,3}*.py`, não commitou). **Nenhum bug material**: reimplementação do zero (fractais+engines reescritos) bate os 8 painéis a ±0,1R; E1 intrabar correto (stop antes do trail-update; SL original antes de armar; same-bar 3R+SL→SL, 1×/435); E2/E3 ambíguo-conservador ocorre 1× cada (upper-bound +4/+6R — irrelevante); pareamento/custos/fail-loud ✓; 5 trades traçados bar-a-bar.

## Confirmado (bootstrap independente seed 777, 2000×)
E1−E0/BASE +82,3, IC [+23,8, +147,5] exclui 0 ✓ · E2−E0/SISTEMA_A +21,2, IC [+0,5, +43,0] exclui 0 por um fio ✓ · E2/BASE e E3/BASE cruzam 0 ✓.

## Fragilidades NOVAS (obrigatórias no report)
1. **E1 falha 2 gates do PRÓPRIO prereg:** concentração 2025-01 = 38% do Δ (> gate 35) — sem esse mês Δ=+51,3 com IC 10000× **[−1,2, +107,4] cruzando 0** (P(Δ≤0)=2,9%, borderline genuíno); e Δ2024 = −2,4 (consistência por ano exigida FALHA). 5/22 meses com delta negativo.
2. **E2/SISTEMA_A igualmente concentrado:** 2024-09 = 45% do Δ; sem ele +11,7, IC cruza 0. N=53 exploratório — sugestivo, não confirmável.
3. **run3 91 do E1 é MECÂNICO:** 167 trades TOCAM 3R independentemente do exit; E1 fecha ≥3R em 91 mas devolve <3R em 76 tocadores; decomposição do Δ: tocadores +167,8 / **não-tocadores −85,5** (custo de segurar sem trail = a queda de WR/streak). Não vender como "mais runners".
4. **Exposição:** duração média 29→51 barras (Sistema A 43→80-140) — 1,7-2,3× mais tempo em mercado (overnight/notícias não precificados).
5. **FN:** E1 com stk q95 19 e pior mês −11,2R (a 0,5%/trade: −5,6% mês, streak q95 −9,5%) colide com travas prop — **exit de convexidade para conta própria, não para prop com trava de streak**; operável só a 0,25%, cortando o ganho em $ pela metade.
6. **Winner's curse declarado:** os 4 exits foram vistos no cross (mesmos dados) e E1 = melhor-de-4 implícito; este lab = confirmação formal de implementação/painel, NÃO validação nova; IC não corrige seleção.

## Veredito DA: **EXIT_VARIANT_MATERIAL_TRADEOFF** — efeito real em amostra; E1 não domina (paga +82,3 com WR −7,3pp, stk q95 13→19, DD −18,8, pior mês −11,2, IC marginal sem o melhor mês); E2/SISTEMA_A é o único fixo que vence o trail todos os anos, mas frágil (N53, 45% num mês). **Nenhum exit recomendado pelo DA; adoção = decisão do Cris**; árbitro limpo = dados virgens (extensões futuras / janela não-BEAR), onde os deltas de exit podem ser re-medidos sem winner's curse.
