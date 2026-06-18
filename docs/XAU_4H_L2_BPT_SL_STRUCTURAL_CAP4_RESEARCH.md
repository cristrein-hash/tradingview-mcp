# XAU 4H L2/BPT — SL Estrutural CAP4 Operacional

**Status:** `RESEARCH · NO_PRODUCTION · NO_SLIM · NO_PROMOTION · EXIT_FIXED_partial50` · **Data:** 2026-06-18
Testa se um cap operacional ~4ATR torna o SL estrutural swing-origin prop-firm-operável sem destruir a cauda. CAP = filtro de viabilidade, NÃO otimização de PnL. DA dedicado. Não promove estratégia.

---

## 1. Executive summary

**CAP4 NÃO é boa decisão em nenhuma forma — e o bloco confirma que SL/CAP não é a alavanca.** O bucket >4ATR (97/276 = 35%) tem avgR **+0.064** (quase zero), 85/97 são UNKNOWN-label (ruído não classificado), 9/97 são BOM e 6 são topo/exaustão. **CAP4_REJECT** limita risco (maxDD 24→17, máx SL 3.97ATR) e preserva 89% do sumR (+56.2 vs +62.5) **MAS corta 2/8 must_preserve = E1 e E17** (as reversões em V exit-sensitive). **CAP4_REVIEW** roteia o bucket >4ATR pra revisão humana — mas com 82/97 sem label, "review" é promessa vazia (= REJECT disfarçado + latência) sem um compromisso de rotulagem. **CAP4_CLAMP** tem o maior sumR (+77.4) mas é **miragem** — força o stop num 4ATR mid-structure (nível sem order-flow, fill fictício); **diagnostic-only, FATAL se adotado**. E1/E17 sob partial50+SL gigante são **+0.64/+0.91R = near-scratch mutados** — "preservar monumentais" aqui é retoricamente inflado (o exit já neutralizou a cauda). **Recomendação:** nem REJECT nem REVIEW como resposta; manter **STRUCT_PURE como baseline honesto** e mover o trabalho pro **entry/exhaustion filter** (o bucket >4ATR = entrada-tarde/estrutura-larga = problema de ENTRADA). Nada em produção.

## 2. Why CAP4 is being tested

O SL estrutural swing-origin (=`SL_STRUCTURE_LOW` visual) recupera os bad_SL mas produz 97/276 trades com SL >4ATR (máx 15ATR) — inviável prop-firm (risco-$ escondido pela R-normalização). Hipótese: um cap ~4ATR torna operável sem destruir a cauda. Tratado como **filtro de viabilidade operacional, não otimização de lucro** (instrução do Cris).

## 3. Inputs and corrected labels

`pruned_base_v2.csv` (276 ep) · `reconciliation_labels.csv` (must_preserve 8) · `full_res_visual_episode_review.csv` · `sl_structural_trade_review.csv` · `sl_structural.py` (motor 76b38d4) · frozen 4H `/tmp/raw_features_2020_2026.jsonl`. Hard-stop: PASS. **Recall-gate corrigido (a02229c):** must_preserve(8) = E1,E5,E13,E17,E21,E27,E30,E40; E23 = should_not_long (não preservar).

## 4. CAP policy definitions

Base SL = swing-origin (Williams 5/5 causal j≤i-5, −0.1ATR, floor 0.3, **sem teto 1.5**). Exit FIXO partial50@2R+6R gap-aware, custo 0.10R.
- **CAP3_REJECT:** rejeita trade se SL estrutural >3ATR (sanity conservador).
- **CAP4_REJECT:** rejeita se >4ATR; senão SL estrutural.
- **CAP5_REJECT:** rejeita se >5ATR (sanity tolerante).
- **CAP4_REVIEW:** não rejeita; separa buckets SL≤4ATR e SL>4ATR, mede cada um.
- **CAP4_CLAMP_DIAGNOSTIC:** se >4ATR, força SL em 4ATR. **Diagnóstico apenas** (stop deixa de ser estrutural).

## 5. Full results (base 276, exit partial50, gap-aware)

| Política | n | rej | WR | avgR | sumR | medR | PF | maxDD | streak | SL máx | >4ATR |
|---|---|---|---|---|---|---|---|---|---|---|---|
| STRUCT_PURE (no cap) | 276 | 0 | 48.2 | +0.226 | +62.5 | −0.11 | 1.44 | 24.3 | 9 | **15.04** | 97 |
| CAP3_REJECT | 131 | 145 | 45.0 | +0.383 | +50.1 | −1.1 | 1.63 | **14.4** | 8 | 3.0 | 0 |
| **CAP4_REJECT** | 179 | 97 | 45.8 | +0.314 | +56.2 | −1.1 | 1.54 | 17.0 | 10 | 3.97 | 0 |
| CAP5_REJECT | 211 | 65 | 46.4 | +0.278 | +58.6 | −0.59 | 1.50 | 18.9 | 8 | 4.99 | 32 |
| CAP4_CLAMP_DIAG | 276 | 0 | 48.2 | +0.281 | **+77.4** | −0.18 | 1.53 | 24.7 | 9 | 4.0* | 0 |

\* clamp = stop não-estrutural (diagnóstico). **CAP4_REVIEW buckets:**

| Bucket | n | % | WR | avgR | sumR | PF | maxDD | BOM |
|---|---|---|---|---|---|---|---|---|
| SL_LE_4ATR (core operável) | 179 | 65% | 45.8 | **+0.314** | +56.2 | 1.54 | 17.0 | 6 |
| SL_GT_4ATR (revisar) | 97 | 35% | 52.6 | **+0.064** | +6.2 | 1.16 | 8.8 | 9 |

## 6. Recall-gate (must_preserve 8 + E23)

| Episódio | SL ATR | R | CAP4 | nota |
|---|---|---|---|---|
| E1 | 5.30 | +0.64 | **REJECTED** ❌ | exit-sensitive monumental cortado |
| E17 | 8.36 | +0.91 | **REJECTED** ❌ | exit-sensitive monumental cortado |
| E5 | 1.72 | +0.90 | kept | mutado |
| E13 | 2.87 | −1.10 | kept (stopa) | bad-pivot (SL real ~5.3ATR) |
| E21 | 2.90 | +3.90 | kept | runner ✓ |
| E27 | 3.07 | +2.34 | kept ✓ |
| E30 | 0.85 | +3.90 | kept | runner ✓ |
| E40 | 1.83 | +3.32 | kept ✓ |
| E23 | 4.83 | −1.10 | REJECTED | should_not_long → corte é POSITIVO (mas ideal = filtro exaustão, não CAP) |

**CAP4_REJECT corta 2/8 must_preserve = E1, E17.** Caveat (DA): E1/E17 já saem **mutados (+0.64/+0.91R)** sob partial50+SL gigante — "preservar monumentais" é inflado; o exit já neutralizou a cauda. Mas cortar a CAPACIDADE de pegar V-reversal é abrir mão da razão-de-existir do L2/BPT.

## 7. 4ATR trade review (`results/l2_bpt_sl_gt4atr_review.csv`, n=97)

- **Composição:** 85 UNKNOWN-label, 9 BOM, 3 NAO. Razões: **82 unknown-needs-visual**, 9 monumental (V-reversal larga), 6 top/exhaustion.
- **sumR do bucket:** estrutural **+6.2R** · clamp +21.2R · baseline-tight +18.1R.
- **DA relabel (honesto):** NÃO é "bucket que segura os monumentais" — é **bucket majoritariamente-desconhecido de stop-largo contendo 9 monumentais**; avgR +0.064 é o sinal honesto; chamar de "monumentais" cherry-pica 9 e lava 82.
- Top SL: idx6489 15.04ATR (UNKNOWN, +0.1R), idx5965 13.32ATR (BOM, +0.44R), E16 11.38ATR, idx6471 11.37ATR (−0.05R)...
- **Respostas:** 4ATR é net positivo? mal (+6.2R/97). Contém monumentais indispensáveis? 9/15 BOM, mas mutados. Contém muito ruído? SIM (82/97 unknown near-zero). Deveria virar REVIEW? só com **compromisso de rotulagem** dos 82 — senão REVIEW = REJECT disfarçado.

## 8. E13 / E23 / E1 / E17 treatment

- **E13** (SL 2.87ATR, kept, stopa −1.1R): CAP4 NÃO corta, mas stopa pelo bad-pivot (SL real defendido ~5.3ATR). Status `requires better entry / defended swing too deep` — não é falha do CAP. Se um cap rejeitasse o E13 com SL 5.3ATR, classificar como entrada-melhor-necessária, não falha.
- **E23** (SL 4.83ATR): CAP4 corta = positivo, mas o ideal é **filtro de exaustão/topo futuro**, não CAP (CAP corta por tamanho, não por ser topo — coincidência).
- **E1/E17** (5.3/8.36ATR): **cortados pelo CAP4_REJECT.** São cauda crítica — reportado explicitamente. Sob partial50 já mutados (+0.64/+0.91R). Conflito direto: CAP4_REJECT viola must_preserve.

## 9. Temporal split

| Política | 2020-2022 | 2023-2026 |
|---|---|---|
| STRUCT_PURE | +5.3R streak9 DD24 | +57.2R streak6 DD9.2 |
| CAP4_REJECT | +8.3R streak10 DD17 | +48.0R streak6 DD7.4 |
| CAP4_CLAMP | +9.2R streak9 DD24.7 | +68.2R streak6 DD9.1 |

Edge não-estacionária mantida (2020-22 pequeno). CAP4_REJECT reduz DD em ambas janelas. Único ano negativo: 2021 (−9 a −12R) em todos.

## 10. Operational risk

STRUCT_PURE: 97 trades >4ATR, máx 15ATR — inviável (risco-$ escondido). CAP4_REJECT: máx 3.97ATR, maxDD 30→17 — **operacionalmente limpo, mas corta E1/E17**. CAP4_CLAMP: maxSL "4ATR" mas o nível é **não-estrutural** (fill fictício) — maxDD nem é menor (24.7); **proibido como regra**. O ganho de sumR do CLAMP (+77.4) é miragem de R-normalização sobre stop irreal.

## 11. Recommendation (research-only)

**Nem REJECT nem REVIEW como resposta. CAP não é a alavanca.**
- **CAP4_REJECT** = viável operacionalmente (risco limpo, 89% do sumR) **só se o Cris aceitar perder E1/E17-tipo V-reversals** — o que contradiz must_preserve. Documentado como alternativa operável-mas-corta-franchise, não recomendada.
- **CAP4_REVIEW** = correto em espírito (core ≤4ATR operável + bucket >4ATR pra humano), **mas inválido sem compromisso de rotular os 82 unknown**; senão é deferral.
- **CAP4_CLAMP** = diagnostic-only, nunca regra (stop fictício).
- **Recomendado:** manter **STRUCT_PURE como baseline honesto de pesquisa**, **flag o set >4ATR pra rotulagem visual**, e **mover o esforço pro entry/exhaustion filter** — o bucket >4ATR é majoritariamente **entrada-tarde / estrutura-larga = problema de ENTRADA**, não de SL. Capar o stop trata o sintoma. Confirma (3º bloco seguido) que **SL não é onde mora a edge; entry-filter é**.

## 12. DA appendix

DA dedicado (5º DA da frente). Checklist:
- **Tunado por PnL?** NÃO — CAP4 é hipótese pré-especificada (~4ATR operacional); CAP3/5 sanity. Registrado: "4" não foi re-otimizado contra o grid (CLAMP coincidiu com melhor sumR — não influenciou escolha).
- **Teto 1.5ATR?** NÃO reintroduzido. **Clamp diagnostic-only?** SIM (FATAL se adotado — stop fictício).
- **Winners corrigidos usados?** SIM (must_preserve 8). **E23 fora do recall-gate como winner?** SIM (should_not_long). **E13 tratado certo?** SIM (bad-pivot, não falha). **E1/E17 auditados?** SIM (cortados pelo REJECT, reportado).
- **Risco SL>4ATR explicitado?** SIM (§10). **Exit alterado?** NÃO. **Produção?** Intacta. **SLIM?** Não. **Estratégia promovida?** NÃO.
- **Veredito DA (síntese):** "CAP4 é risco-bound cosmético que sobrevive só porque o partial50 fixo já muta os monumentais que ele alega pesar; SL capping é a alavanca errada, entry/exhaustion filtering é a certa." >4ATR bucket "segura monumentais" relabelado para "bucket majoritariamente-unknown contendo 9 monumentais". REVIEW sem rotulagem = deferral.

---

*Outputs: `results/l2_bpt_sl_cap4_policy_results.csv`, `l2_bpt_sl_cap4_trade_review.csv`, `l2_bpt_sl_gt4atr_review.csv`, `l2_bpt_sl_cap4_recall_gate.csv`. Script: `l2_bpt_cap4.py`. Sem produção, sem SLIM, sem chart.*
