# BEAR-LEG BLOCK GATE v3 — CORRECTIVE PULLBACK EXTENSION — RELATÓRIO DIAGNÓSTICO

**2026-06-22.** Bloco fechado. Diagnóstico/calibração nos **62 (ensino)** — NÃO 276/OOS, NÃO plotagem,
NÃO chart/MCP, NÃO produção/engine/decisions/registry/Telegram/SLIM. Determinístico, causal (D1 shift D-1),
sem outcome/realR/MFE/futuro como predicado, sem ID-fit, sem busca cega. Script: `bear_leg_block_gate_v3.py`.
**SMOKE PASS:** reconstrução do v2 bate **62/62** com o CSV v2 committado antes de aplicar as mudanças.

## Mudanças sobre o v2 (2, ambas principiadas)
1. **CARVE-OUT SCOPE FIX** (corrige misfire T17/T30): o carve-out bottom/turn só dispara **fora de
   MACRO_BULL_LEG**. Dentro de bull-leg estabelecida não há "fundo a virar" nem bloqueio do qual resgatar —
   o carve-out lá era rótulo falso. Efeito: **T17 e T30** perdem o rótulo `PRESERVE_BOTTOM_TURN` e caem em
   **ALLOW** (continuam **não bloqueados** — são micro-estrutura aberta, sem sinal causal; honesto). **S15
   (MACRO_RANGE) mantém o carve-out** (preservado).
2. **BLOCK_CORRECTIVE_PULLBACK** (novo): `leg==MACRO_CORRECTIVE_PULLBACK AND NOT bottom_turn AND
   drop20_atr < 1.0`. Mecanismo: comprar um corrective pullback só tem edge se for um **flush real** (queda
   significativa testando demanda); comprar **dip raso** dentro da correção = perseguir força sem capitulação
   = padrão dos losers.

### Por que drop20_atr separa (resposta à pergunta central) — sem ID-fit
Os 8 trades com `leg==MACRO_CORRECTIVE_PULLBACK` (descoberta importante: NÃO eram só os 4 alvos — incluem
**S3 e S27, ambos PROTECT, S27 anchor**; bloquear por leg sozinho mataria winners):

| | trades | drop20_atr | decisão v3 |
|---|---|---|---|
| BLOCK (dip raso) | T12, T25, T26, S28 (+ T33 REVIEW) | 0.00–0.32 | BLOCK_CORRECTIVE_PULLBACK |
| PRESERVE (flush real) | S3, S27 (+ S23 REVIEW) | 1.69, 4.28 (S23 2.05) | ALLOW |

Gap **0.32 → 1.69**; qualquer threshold em (0.32, 1.69) dá as MESMAS decisões → **robusto, não knife-edge**
(verificado thr ∈ {0.5, 0.8, 1.0, 1.2, 1.5} = idênticas). O carve-out (climax|oversold+reclaim+demanda) tem
precedência e preservaria um corrective que fosse genuíno bottom/turn — nenhum dos 8 o é, então drop20 é o
separador operante.

## Resultado v3 (62)
| set | blocked v3 | trades |
|---|---|---|
| A (winners) | **3/26** | S7, S8, S13 (bear-markdown — Cris confirmou corretos) |
| B (bad) | **7/18** | T9, T11, T15, T42 (bear) + **T12, T25, T26 (corrective NOVO)** |
| C (ambíguo) | 9/18 | S14, S19, T13, T14, T19, T27, T34 + **S28, T33 (corrective NOVO)** |

- **Preservação A: 23/26** (igual ao v2; as 3 perdas S7/S8/S13 são blocks corretos confirmados pelo Cris).
- Gate dist: ALLOW 42 · BLOCK_BEAR_MARKDOWN 14 · BLOCK_CORRECTIVE_PULLBACK 5 · PRESERVE_BOTTOM_TURN 1.

## Target check (Tarefa 2)
| trade | esperado | v3 | bloqueado | ok |
|---|---|---|---|---|
| T12 | BLOCK | BLOCK_CORRECTIVE_PULLBACK | YES | ✓ |
| T25 | BLOCK | BLOCK_CORRECTIVE_PULLBACK | YES | ✓ |
| T26 | BLOCK | BLOCK_CORRECTIVE_PULLBACK | YES | ✓ |
| S28 | BLOCK | BLOCK_CORRECTIVE_PULLBACK | YES | ✓ |
| S15 | PRESERVE | PRESERVE_BOTTOM_TURN | NO | ✓ |
| T17 | (misfire diag) | ALLOW (carve-out suprimido em bull-leg) | NO | diag — rótulo falso removido; não bloqueado (micro-estrutura aberta) |
| S7/S8/S13 | BLOCK | BLOCK_BEAR_MARKDOWN | YES | ✓ |
| T9/T11/T15/T42 | BLOCK | BLOCK_BEAR_MARKDOWN | YES | ✓ |

## Anchor check (Tarefa 3)
- **anchors NOVO-bloqueados por v3: NENHUM** (`[]`). A extensão CORRECTIVE não matou nenhum winner.
- **T34** aparece bloqueado, MAS é **pré-existente do v2** (BLOCK_BEAR_MARKDOWN, leg=MACRO_BEAR_LEG) — **NÃO
  introduzido pelo v3**. `cris=PROTECT_entry_fix_SL`: tensão conhecida do v2 (protect-com-fix em bear-leg),
  **fora do escopo deste bloco**. Flag para visibilidade, não é regressão da extensão.
- Fora dos 62: T35, T37, T39, T41 (nomeados na lista de anchors mas não no working-set).

## Limitações declaradas
- **T17/T20 permanecem não resolvidos** (micro-topo vs micro-fundo): v3 só removeu o **rótulo falso** de
  bottom/turn em T17; NÃO o bloqueia. Continuam micro-estrutura aberta, sem sinal causal. Não forçar regra.
- **T23** (classifier-error/hindsight) não tocado neste bloco.
- **62 = ensino/calibração, NÃO validação.** drop20_atr é separador plausível **nestes 8 corrective**; precisa
  de set independente (sub-janelas / RAW full-bar) antes de qualquer promoção. **Sem 276/OOS aqui.**
- S28/T33 são REVIEW (ambíguos): bloqueá-los é aceitável, não é ganho comprovado.

## Outputs
`results/l2_bpt_bear_leg_block_gate_v3_62.csv` · `..._v3_target_check.csv` · `..._v3_anchor_check.csv` ·
`..._v3_da.csv` · este relatório.

## Próxima recomendação
Cris avalia (por plotagem quando quiser, fora deste bloco). Frente aberta seguinte = **micro-estrutura de
liquidez** (T17/T20) com humildade, e **bear-as-of-entry** (T23). Sem promoção; tudo permanece diagnóstico.
