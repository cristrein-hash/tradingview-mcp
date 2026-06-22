# XAU 4H L2/BPT — BEAR-LEG REFINED LOSER-CUT (APROVADA por Cris, com limitações explícitas)

**2026-06-22.** Aprovada pelo Cris como feature de corte-de-loser, junto às demais aprovadas, COM suas limitações
implícitas reconhecidas. DIAGNÓSTICO→aprovada-com-caveats; base 276; realR uncapped (MFE). NÃO produção ainda.

## A regra
**Bloquear bear-leg EXCETO se sinal de exaustão.** Universo = `macro_reader_leg == MACRO_BEAR_LEG` (n=29 na 276).
- BLOQUEAR se NÃO houver exaustão: `NOT (rsi_min8<=35 OR drop20_atr>=2 OR clean_sky)`.
- PRESERVAR (não bloquear) se exaustão presente: `rsi_min8<=35 (oversold) OR drop20_atr>=2 (flush) OR clean_sky`.
Estruturalmente: bloqueia **bear-pullback em supply rejeitando sem capitulação** (o trap), preserva **bear-leg
exaurindo / capitulação / clean-sky** (a compra legítima).

## Resultado validado (base 276, uncapped)
- **RUNNERS preservados: 5/5** (o bear-leg CEGO cortava todos os 5).
- **MONUMENTAIS preservados: 2/2** ✓ (2023-03-08 +19.8R CLIMAX_RECLAIM; 2023-03-09 +18R).
- **LOSERS bloqueados: 8/19** (vitória real — corte limpo).
- **0 runners cortados** pela regra refinada.
- Os 8 bloqueados são **100% `supply_reject` + `fuel_low`** (supply overhead, sem espaço = inequivocamente ruins) —
  é daí que vem o lift 1.63 do bear-leg.

## Limitações IMPLÍCITAS (reconhecidas — DA FAIL_OVERFIT_TINY_N honrado)
1. **A preservação 5/5 é parcialmente tautológica** — a exceção foi calibrada sobre exatamente esses 5 runners (n=5).
2. **A assinatura de exceção (oversold/flush/clean-sky) NÃO generaliza fora do bear-leg** — no full 276 lift 1.01.
   Ela só é limpa CONDICIONADA ao contexto bear (o condicionamento bear é necessário; não é predicado global).
3. **`supply_reject + fuel_low` global é mais fraco (lift 1.30) e corta 33% dos runners** — confirma que o bear-leg
   não é proxy substituível; a edge mora na CONJUNÇÃO bear-context × supply-reject × low-fuel.
4. **Os 11 losers que vazam são AUCTION-IRREDUTÍVEIS dos 5 runners** — nenhuma feature atual os separa (idênticos no
   entry). A preservação dos runners é por NÃO-cortar o ambíguo, não por assinatura positiva. Trade-off: vazam 11.
5. **Calibração, não validação estatística** (Fisher p 0.13/0.61/0.62 a n=5). Escopo = universo bear-leg.

## Status e papel (evidência condicional)
- **APPROVED_AS_CONDITIONAL_LOSER_CUT** (Cris, 2026-06-22). Papel: cortar bear-pullback-trap preservando runners/
  monumentais no universo bear-leg. Junto às aprovadas: [[project_caminho_b_v_stair_exit_approved]] (exit), etc.
- **Sucessor honesto do `bear_leg_block` CEGO** (lift 1.63, cortava 19 losers + 5 runners): troca 11 losers a mais
  por 5 runners + 2 monumentais preservados. Cris assume o trade-off.
- **NÃO promover a produção** sem walk-forward; **NÃO usar fora do universo bear-leg** (não generaliza).

## Resíduo irredutível → aguarda MAIS DATA (Cris)
Os 11 leaked vs 5 runners não-separáveis com features atuais. Reconciliação só com **OHLC sub-4H contíguo** (aceitação
intra-barra real), inexistente hoje — integrar mais data adiante (conecta com coleta replay). Lever paralelo p/ os 2
monumentais: predicado GLOBAL `capit==CLIMAX_RECLAIM` (n=10, runner_rate 40%, lift 1.53, fraco mas estrutural).

Arquivos: `l2_bpt_bearleg_surgical.py` + `results/l2_bpt_bearleg_surgical.csv` (regra+grupos);
`l2_bpt_bearleg_leaked_vs_blocked.py` (leak vs blocked vs runner); `l2_bpt_supply_fuel_global.py` (generalização).
Commits 3125d21 / a48d725.
