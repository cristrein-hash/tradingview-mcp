# XAU 4H L2/BPT — Swing-Structure Precision (o que REALMENTE separa, print a print)

**Status:** `DIAGNOSTIC · NO_OUTCOME · NOT_A_RULE · HONEST_NEGATIVE` · **Data:** 2026-06-18
**Sem outcome/PnL/backtest/filtro/produção/SLIM.** Gabarito = rótulos visuais do Cris (9 WIN / 12 SLFIX / 12 TRAP / 3 PREM). Features causais (pivots Williams SHIFT5 + 1D causal).

> Pedido do Cris: definir com precisão, print a print, o que distingue "HL após sweep" de "LH em perna bear" — para a definição não nascer genérica, e **sem deslumbre antes de resultado causal**. Este doc é o teste honesto da minha própria tese. **Ela NÃO sobreviveu na forma simples.**

---

## 1. Resultado central (honesto, negativo)

**Nenhum feature único separa os grupos.** Testei 4 famílias:

| feature | WIN | SLFIX | TRAP | separa? |
|---|--:|--:|--:|--:|
| low_seq HL (4H) | 6/9 | 6/12 | **8/12** | ❌ (trap tem mais) |
| high_seq HH (4H) | 4/9 | 5/12 | **8/12** | ❌ |
| sweep (4H) | 2/9 | 6/12 | 3/12 | ❌ |
| 4H slope20 (ATR) | 1.71 | 0.71 | 1.74 | ❌ (WIN≈TRAP) |
| 1D above_sma50 | 8/9 | 12/12 | 6/12 | parcial |
| **1D slope20d %** | **3.9** | **4.4** | **0.2** | **melhor sinal** |
| legpos 60d (0low-100high) | 85 | 92 | 51 | ❌ no agregado |

A tese "swing machine = HL-após-sweep" **não aparece** nas sequências de pivot. A discriminação é multi-dimensional e **mecanismo-específica**, não um gate escalar.

## 2. A verdade que emergiu: NÃO é 1 problema, são ≥2 mecanismos de TRAP e ≥2 de WIN

Decompondo os rótulos por estrutura real:

**Traps tipo A — EXAUSTÃO/TOPO** (E24, E34, E39): **alto na perna** (legpos 89-95, %above60low 11-21%, extended). Discriminador = **maturidade/extensão da perna**.
**Traps tipo B — RECLAIM EM PERNA BEAR** (cluster out20-mar21: E6-E11, E36, E37): reclaims dentro de downtrend 1D sustentado. Discriminador = **estrutura/slope 1D** (slope20d ~0, above_sma50 split).

**Winners tipo 1 — REVERSÃO DO FUNDO** (E27, E30, E40): legpos baixo/médio, sweep+bos_down+reclaim em contexto recém-virado.
**Winners tipo 2 — PULLBACK EM UPTREND** (E1, E5, E17, E21, E23): legpos variado, slope 1D positivo.

→ É um mapa **2×2+**, não um portão. Por isso minhas features (e os blocos anteriores de supply/demand/anatomy) **não separaram**: cada um media UMA dimensão de um problema multi-mecanismo.

## 3. O par decisivo resolvido com precisão: E39 (trap) × E40 (winner)

Eu tinha dito que eram "gêmeos". Em 4H-swing e 1D-slope, são (slope20d 3.45 vs 3.75). **Mas em maturidade-de-perna, separam de verdade:**

| | E40 (WIN) | E39 (TRAP) |
|---|--:|--:|
| legpos 60d (0low-100high) | **56** (meio, espaço acima) | **89** (perto do topo, sem espaço) |
| % acima do fundo 60d | 5.4% (cedo) | 11.8% (esticado) |
| dias desde fundo 60d | 39 | 48 |

E40 = reclaim **cedo** na recuperação do fundo de mar/2021 (espaço pra correr). E39 = reclaim **tarde**, perto do topo de um rally de 2 meses (exausto). **Distinção causal real e mensurável** — para o subtipo EXAUSTÃO. Idem E24 (legpos 95, +21% = topo extremo) e E34 (legpos 90).

## 4. O que ainda NÃO separa (e por quê)

- **legpos no agregado vira ao contrário** (WIN 85 > TRAP 51) porque os traps tipo B (cluster bear E6-E11) são **baixos na perna** (reclaim em downtrend), enquanto os winners tipo 2 (pullback) são altos. Ou seja: **um mesmo valor de legpos é bom (pullback) ou ruim (exaustão) dependendo do mecanismo.** Não há escalar único.
- O cluster bear (E6-E11) precisa do eixo **1D-trend**, não do eixo legpos.
- **Dúvida honesta sobre rótulo:** E39 por estrutura de reversão é parente de E40; só a maturidade o separa. Vale confirmar contigo se E39 é "trap estrutural" ou "setup válido que perdeu" (= pertenceria a SLFIX/understood-loser, não TRAP). O mesmo para a fronteira de alguns SLFIX vs TRAP.

## 5. Os 2 eixos causais que de fato emergiram (medir, não assumir)

1. **Eixo MATURIDADE/EXTENSÃO** (legpos 60d, %above60low): rejeita reclaims de **topo exausto** (E24, E34, E39). E40 sobrevive (meio da perna).
2. **Eixo TENDÊNCIA 1D** (slope20d: válidos ~4% vs traps ~0%): sinaliza os reclaims em **downtrend 1D** (cluster bear).

Nenhum dos dois sozinho é limpo. **Juntos, mecanismo-específicos**, podem cobrir mais — mas isso é **hipótese a validar por recall-gate**, não conclusão.

## 6. Próximo passo correto (recall-first, sem grande máquina)

NÃO construir uma "swing machine" monolítica (os dados mostram que conflataria os mecanismos e falharia, como minhas features falharam). Em vez disso:
1. Definir os 2 eixos (maturidade 60d + tendência 1D) como features causais explícitas.
2. **Recall-gate:** os 9 winners têm que sobreviver a ambos os eixos; os traps tipo A (extensão) e tipo B (1D) têm que cair nos eixos respectivos. Se um eixo cortar winner → reespecifica.
3. Resolver contigo os rótulos de fronteira (E39 trap vs valid-lost; alguns SLFIX vs TRAP) — porque a precisão da regra depende da precisão do gabarito.
4. Só então outcome (SL estrutural, por episódio, lift vs base rate).

**Expectativa calibrada (anti-deslumbre):** 4 famílias de features já falharam em separar limpo ao longo de vários blocos. Isso é evidência de que a edge é **seletiva, multi-condicional e parcialmente discricionária** — provavelmente baixa-frequência. O ganho virá de **composição mecanismo-específica + gabarito limpo**, não de um único feature mágico. Pode ser que parte da separação **não seja mecanizável** sem perder recall — e isso também é um resultado válido a aceitar.

## 7. DA appendix

- Não se deslumbrou? ✅ — tese simples REFUTADA nos dados; reportado negativo.
- Não usou outcome/PnL? ✅ (só estrutura + rótulos do Cris).
- Não fabricou separação? ✅ — mostrei onde NÃO separa (agregado legpos invertido).
- Resolveu o par difícil com dado? ✅ E39×E40 por maturidade (legpos 56 vs 89).
- Não construiu regra/máquina? ✅ — proposta de recall-gate, não implementação.
- Produção intacta? ✅.

**DA verdict: PASS — precisão print-a-print revela que NÃO há separador escalar; a estrutura real é 2 mecanismos de trap (exaustão/extensão vs downtrend-1D) e 2 de winner (reversão vs pullback); E39×E40 resolvido por maturidade-de-perna (causal); caminho = composição mecanismo-específica validada por recall-gate, com gabarito de fronteira a confirmar com o Cris. Sem deslumbre, sem outcome.**

---

*Read-only. Outputs: este doc + `results/l2_bpt_swing_anatomy.csv` (pivots/sequências/sweep/SL-origin por episódio). Scripts: `swing_anatomy.py`, `d1_context.py`, `leg_maturity.py`. Sem outcome/produção.*
