# FULL 276 — ADENDO DE AUTO-AUDITORIA (retração do veredicto BASELINE_WEAK)

**2026-06-22.** O Cris apontou que a conclusão `BASELINE_WEAK / NO_PROMOTABLE_CONFLUENCE` era absurda após
todo o trabalho de engine. Investiguei a fundo e encontrei **2 bugs internos reais** — ambos confirmados por
re-run independente e por DA. **O veredicto anterior está RETRATADO** (foi driven por bugs). Diagnóstico apenas.

## Bug 1 — o EXIT do eval é CAPADO em +3.9R → métrica cega à convexidade
realR (276): min −1.11, **max exatamente +3.9R (17 winners pinados no teto)**; 128 stops −1.1R. A edge desta
estratégia é **CONVEXIDADE** (monumentais +15-20R via V_stair). Um realR capado em +3.9 torna o **sumR
estruturalmente cego à própria coisa que justifica a estratégia**. ⇒ a comparação "baseline sumR +84.2 vs gate
+75.5" é um **yardstick INVÁLIDO**. Métricas certas (cap-imunes / fair): **contagem de monumentais** e
**maxDD sobre equity capado** (lower bound). PF fica contaminado pelo teto (numerador truncado) — rebaixar.

## Bug 2 — o BEAR-MARKDOWN dispara DENTRO de MACRO_BULL_LEG (over-fire)
Regra v3: `BLOCK_BEAR_MARKDOWN = leg==MACRO_BEAR_LEG OR (macro_broken AND combined<0)`. Nos 276: 62 blocks, mas
**só 26 em MACRO_BEAR_LEG**; **36 disparam FORA de bear-leg** (10 BULL / 17 RANGE / 9 TRANSITION), **18 são
winners (+27.3R)**. Ex.: bar2053 (2021-05, +3.32R, **leg=MACRO_BULL_LEG daily HH+HL**, mb=True combined=−1).
Um escalar regimeB lagging sobrepõe o **leg-state backbone** (que é a verdade macro estabelecida — trava
"leg-state = backbone"). Isso **inverte a hierarquia documentada** = bug estrutural.

**FIX (principiado, derivado da trava existente — NÃO outcome-tuning):** bear-markdown nunca em MACRO_BULL_LEG:
`leg==MACRO_BEAR_LEG OR (leg ∈ {RANGE,TRANSITION} AND macro_broken AND combined<0)`. Smoke vs 62: só **T19**
muda (era bear-blocked, vira ALLOW — é MACRO_BULL_LEG, un-block consistente). 10 trades un-blocked (4 winners).

## Re-medição (lente cap-imune; ler com a ressalva do Bug 1)
| config | allow | WR | sumR(capado) | PF | maxDD | monumentais |
|---|---|---|---|---|---|---|
| baseline no-gate | 276 | 49.3 | 84.2 | 1.58 | 18.7 | **17** |
| v3 (over-fire) | 195 | 50.3 | 75.5 | 1.75 | 15.2 | 14 |
| **v3 FIXED** | 205 | 49.8 | 77.1 | 1.72 | **11.3** | 14 |

## Veredicto honesto e equilibrado (anti over-correção, per DA)
- O veredicto **`BASELINE_WEAK` está RETRATADO** — era artefato dos 2 bugs (métrica capada + over-fire). O gate
  **NÃO é value-destroying**; o bug bull-leg é que o fazia parecer ruim.
- **MAS o caso positivo NÃO está ganho.** O fixo é **≈ NEUTRO** em métricas capadas: a queda maxDD 18.7→11.3 é
  **parcialmente sample-thinning** (remove 34W+37L, net −7.1R; mesma vala 2021-05→2022-01) — dentro do ruído a
  n=205. E na métrica **cap-imune (monumentais), o fixo ainda perde 3/17** → favorece no-gate nesse eixo.
- A camada **CORRECTIVE-shallow** agora é a mais agressiva (bloqueia bar6954, +3.9R em corrective com combined>0
  = contexto bullish) — merece a mesma auditoria que o bear-markdown levou.
- **Candidato confluência = OVERFIT_REJECT mantido (razão melhor):** 22/26 fires têm `bub_ratio==0` → colapsa
  num único termo tick-volume; os outros 2 (BULL, supply_blocks) são inertes. NÃO são sinais ortogonais (≠
  precedente capit+rsi). "Fraqueza isolada≠inútil" protege ortogonais genuínos, não hull com 2/3 termos mortos.
  Re-descobre volume×1D-bear + legbear (RETRATADOS). SHIFT1 de bub não-confirmado.
- **Analogia A1' SUPERTREND era BACKWARDS p/ o gate** (A1' inflado POR look-ahead; aqui o fix é causal e CORTA
  viés). A1' aplica-se só ao candidato (tick-volume não-auditado).

## O TESTE DECISIVO real (próximo bloco, não re-leitura)
A conclusão só fecha com o **EXIT V_stair REAL / não-capado** wired no 276 — é onde a convexidade fica visível e
a perda de 3 monumentais do gate vira "sobrevivível" ou "fatal". Tudo acima usa realR capado (lower bound).
Outputs: `results/l2_bpt_full276_bear_markdown_FIX_decisions.csv`.
