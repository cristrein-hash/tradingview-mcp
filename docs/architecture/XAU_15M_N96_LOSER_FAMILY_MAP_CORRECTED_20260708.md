# XAU 15M LONG · N96 · Corrected Loser Family Map

**Cris 2026-07-08.** Mapa dos 44 losers N96 com as correções do Cris incorporadas. Research-only. `results/n96_loser_family_map_corrected.csv`.

## Famílias (44 losers)
| família | n | trades | auction reading |
|---|---|---|---|
| **C** — distribuição de topo / topo de range bear | 22 | #17,18,20,21,23,25,31,36,42,46,48,55,56,57,58,59,60,65,79,83,84,85 | excess/prémio |
| **D** — bear ativo | 14 | #27,49,50,66,67,68,69,80,86,87,89,92,93,94 | downtrend imbalanced |
| **R** — range/chop neutro | 4 | #5,6,7,8 | balance |
| **MGMT** — recuperável por gestão (não filtrar) | 4 | #24,32,64,77 | BE/timing |

## Correções obrigatórias do Cris (validadas no script, assert PASS)
1. **#55,56,57,58,59,60 = C** — não são range neutro; são RANGE/CHOP de distribuição antes da queda, dentro de configuração bear (topo de range bear).
2. **#58 = C.**
3. **#64 = MGMT** — quase-winner recuperável por gestão humana; não filtrar como loser estrutural.
4. **#77 = MGMT** — quase-winner recuperável por gestão humana; não filtrar.
5. **#24 = MGMT** — BE em gestão humana; não filtrar.
6. **#32 = MGMT** — entrada antecipada (o certo era esperar demanda inferior, como no #33); timing/gestão, não filtrar como loser estrutural.
7. **#80 = D** — bear ativo.

## Cruzamento com regime causal v5 e filtro intra-BEAR
| família | BULL | BEAR | RANGE | cortados intra-BEAR |
|---|---|---|---|---|
| C (22) | 9 | 10 | 3 | 10 (os 10 BEAR-C são repiques rasos) |
| D (14) | 2 | 9 | 3 | 2 (#66,67) |
| R (4) | 0 | 0 | 4 | 0 |
| MGMT (4) | — | — | — | 1 (#24) |

Os losers cortados pelo filtro intra-BEAR (13) são o subconjunto BEAR & repique-raso. Os restantes losers de C/R em BULL/RANGE = alvo da rodada RANGE/distribuição (ver `..._RANGE_DISTRIBUTION_FILTER_ROUND_20260708.md`). D (bear ativo) = rodada própria, não misturar.

## Nota metodológica
Não misturar D-bear-ativo na análise de RANGE/distribuição. Os recuperáveis de gestão (#24,32,64,77) não são alvo de filtro estrutural.
