# XAU 4H L2/BPT — Teste: legpos × indicadores (e o residual real)

**Status:** `DIAGNOSTIC · NO_OUTCOME · HONEST_MIXED · RECALL_FIRST` · **Data:** 2026-06-18
Gabarito = rótulos visuais do Cris (E39 confirmado TRAP = reteste de polaridade de fundo dentro de bear leg iniciada).

---

## 1. O que esta rodada estabeleceu

**GANHO — 1 eixo causal validado: `legpos` (maturidade da perna, 60d).**
Separa o par decisivo: **E40 (win) legpos 56 · E39 (trap) legpos 89**. Isola os 4 top-traps (E15/E24/E34/E39 = legpos 89-95) no estrato HIGH. Primeira coisa que separou um par antes inseparável.

**NEGATIVO — indicadores condicionados ao legpos NÃO separam (testado de forma justa).**
Dentro de HIGH-legpos (4 top-traps vs 6 winners), com RSI-divergência real + climax-de-venda + NAS + volume:
- traps: só **E24** acende divergência; E15/E34/E39 = zero.
- winners: zero também.
- **E39 vs E40 idênticos nos indicadores** (rsi_div 0/0, sell_climax 1/1, rsi 46/45). Só legpos separa.
Regra ingênua `legpos>75 & exh>=2` **quebra recall** (flagou o winner E23). Descartada.

**NEGATIVO — direção de quebra estrutural (pivot 4H) não separa:** todos são reclaims → todos registram "quebra bull" local. Proxy local demais.

## 2. Tabela de eixos testados (acumulado)

| eixo | separa WIN×TRAP? | o que cobre |
|---|---|---|
| swing 4H (HL/HH/sweep) | ❌ | nada |
| slope 4H | ❌ | nada |
| **legpos 60d (maturidade)** | **parcial ✅** | isola top-traps (E15/24/34/39) no estrato HIGH; separou E39/E40 |
| **1D slope20d (tendência)** | **parcial ✅** | cluster bear (E6-E11/E36/E37, low legpos) — a reclamação mais alta do Cris |
| exaustão (RSI-div/bubbles/NAS/vol) cond. legpos | ❌ | só E24 |
| direção de quebra (pivot 4H) | ❌ | nada (tudo é reclaim) |

## 3. O residual preciso (o que falta)

Separar os **4 top-traps** (E15/E24/E34/E39) dos **6 winners high-legpos** (E5/E13/E21/E23/E27/E30). 5 famílias de features falharam. São gêmeos estruturais. Per anotação do Cris, a distinção é de **perna MACRO** (E39 = reteste de fundo dentro de bear leg 1D iniciada), não de pivot 4H nem indicador local.

## 4. Próximo teste correto (não mais indicador local)

**Decomposição de perna no 1D:** este reclaim é continuação de perna de alta 1D, ou repique contra-tendência dentro de perna de baixa 1D? (= "perna que mostra claramente início bear" do Cris, no timeframe certo.) + o gate **1D-trend** já utilizável para o cluster bear. Tudo com **recall-gate** contra os 9 winners antes de qualquer métrica.

## 5. DA appendix
- Não se deslumbrou? ✅ — hipótese dos indicadores REFUTADA com sinais corretos; reportado negativo.
- Não usou outcome/PnL? ✅. Não forçou positividade? ✅. Recall-gate aplicado (regra ingênua quebrou → descartada)? ✅.
- Ganho real isolado (legpos) sem inflar? ✅. Produção intacta? ✅.

**DA verdict: PASS — legpos validado como eixo causal; indicadores-cond-legpos refutados (E39≈E40 idênticos); residual = 4 top-traps vs 6 winners, hard; próximo eixo = decomposição de perna 1D, não indicador local; recall-first.**

---
*Outputs: este doc + `results/l2_bpt_legpos_exhaustion.csv`. Scripts: legpos_x_exhaustion.py, proper_exhaustion.py, structure_direction.py. Sem outcome/produção.*
