# XAU 4H L2/BPT — READER OPERATING MANUAL (overlay funcional da Camada 2)

> **Evolução da [Camada 2 Knowledge Library](XAU_4H_L2_BPT_READER_LAYER2_EVIDENCE_LIBRARY.md).** A biblioteca preserva
> *o que* foi descoberto (status + reader_use). O Operating Manual diz *COMO o Reader usa cada lente na leitura viva* —
> a lente deixa de ser "mais uma feature" e ganha **PAPEL DE LEITURA**.
> Aditivo: NÃO substitui a biblioteca nem o assembler. Migração das 93 lentes é incremental.
> Data: 2026-06-23. Seed: 3 lentes vindas de ERROS REAIS do audit fase-3 do cluster 4918 (commit c3839b8).

---

## ⚠️ Trava — Operating Manual NÃO é tabela de decisão

Os campos funcionais descrevem COMO ler com a lente, NUNCA uma regra TAKE/SKIP/score. O campo `use_as` inclui
`DO_NOT_GATE` e `WARNING_ONLY` exatamente para impedir que "papel de leitura" vire gate. Toda lente carrega
`automation_note` declarando o que ainda NÃO pode ser automatizado. **A leitura continua narrativa e condicional.**

---

## Schema funcional (por lente)

| campo | significado |
|---|---|
| `lens_id` | id estável (OM# para lentes nativas do manual; ou o nome da lente da biblioteca quando migrada) |
| `name` | nome legível |
| `family` | família de origem (MACRO/MICRO/REGIME/INDICATOR/RISK/READING/DSPA/BEARLEG/FOUNDATION) |
| `refines` | lentes EXISTENTES da biblioteca que esta condiciona/refina (não as substitui) |
| **`use_as`** | papel de leitura — enum: `BACKBONE_CONTEXT` · `CONTRAST_LENS` · `INVALIDATION_PROBE` · `WARNING_ONLY` · `CONDITIONAL_SUPPORT` · `REFERENCE_ONLY` · `DO_NOT_GATE` |
| `when_to_foreground` | em que contexto a lente deve entrar na leitura (gatilho de relevância, não de decisão) |
| `what_it_can_invert` | que leitura ingênua ela pode INVERTER (o valor contrastivo) |
| `known_failure_mode` | onde ela já enganou / o precedente de erro (caso-âncora) |
| `example_cases` | episódios concretos (bar_idx) que ilustram |
| `do_not_use_as` | usos proibidos (anti-gate, anti-threshold) |
| `automation_note` | o que falta para automatizar; o que NÃO promover |
| `provenance` | de onde veio (audit/commit/script) |

---

## SEED — 3 lentes do audit fase-3 (cluster 4918)

As 3 vieram dos 2 erros + 1 lean-errado da leitura cega (5/9 limpa, 2/9 ambíguo, 2/9 erro). São **condicionantes de
polaridade/timing**, não eixos novos — refinam lentes existentes.

### OM1 · `supply_proximity_momentum_conditioned` — ⭐ o maior ponto cego
- **family:** MICRO/AUCTION · **refines:** `supply_sup_cat_pol_cat` (A3) · `demand_supply_distance_quality` (E6) · `overhead_supply_awareness` (E7) · `ob_micro_vs_macro` (D12)
- **use_as:** `CONTRAST_LENS` + `INVALIDATION_PROBE` (pode inverter a leitura de "supply = freio")
- **when_to_foreground:** sempre que houver supply overhead próximo (dist_supply ≲ 2 ATR) E a leitura ingênua trataria a proximidade como rejeição/risco-topo.
- **what_it_can_invert:** a MESMA distância de supply inverte de sentido pelo **momentum**: supply perto é **PAREDE** quando o momentum está fraco/esticado (fade), mas é **ALVO A SER CONSUMIDO** num impulso fresco e forte. Refuta o veto de supply.
- **known_failure_mode:** **4926** (2023-03-09) — dist_supply 1.61 ATR foi lido como freio (leitura "continuação testando supply, risco rejeição"); o impulso fresco ABSORVEU o supply → monumental +18R. A leitura tinha o backbone certo mas a lente de supply pesou para o lado errado.
- **example_cases:** 4926 (impulso forte → supply consumido, monumental). Contraponto: episódios de momentum esticado onde supply perto de fato rejeita (a lente NÃO inverte cegamente — é condicional ao momentum).
- **do_not_use_as:** NUNCA dist_supply como gate/veto binário (corta markup-through-supply e o 4926); NUNCA threshold ATR fixo isolado.
- **automation_note:** exige feature de momentum/impulso (slope recente, range-expansion, consec_up) cruzada com dist_supply. Sem isso = leitura humana. NÃO promover a gate.
- **provenance:** audit fase-3 cluster 4918, ep 4926 (commit c3839b8).

### OM2 · `bottom_turn_regime_conditioned`
- **family:** REGIME/MACRO · **refines:** `capitulation_climax` (A8) · `capitulation_carrier` (F6) · `D1_weekly_leg_state_backbone` (A1)
- **use_as:** `CONDITIONAL_SUPPORT` (modificador do backbone; não decide sozinho)
- **when_to_foreground:** sempre que `bottom_turn=True` aparecer — checar o **weekly_slope** ANTES de promover a leitura a absorção/fundo-legítimo.
- **what_it_can_invert:** `bottom_turn=True` só faz UPGRADE de trap→absorção/fundo quando o **weekly concorda** (≥0 ou virando). Sob weekly negativo, `bottom_turn` NÃO promove — segue trap / range-bottom.
- **known_failure_mode:** **5701** (2023-09-07) — `bottom_turn=True` sob weekly −0.22 induziu um lean de absorção; era trap (loser). O Reader declarou baixa confiança (ambiguidade honesta), mas o tie-breaker recuperável era: bottom_turn sob weekly negativo NÃO upgrada.
- **example_cases:** **4918** (bottom_turn + weekly +0.54 → fundo legítimo, monumental ✓) **vs** 5701 (bottom_turn + weekly −0.22 → trap ✗). Mesma flag, regimes opostos.
- **do_not_use_as:** NUNCA `bottom_turn` isolado como sinal de fundo; NUNCA ignorar o weekly.
- **automation_note:** `bottom_turn × sign(weekly_slope)` como condicional de LEITURA (não de trade). NÃO promover a gate.
- **provenance:** audit fase-3 cluster 4918, ep 5701 vs 4918 (commit c3839b8).

### OM3 · `recovery_apex_timing_penalty_cascade_neg`
- **family:** MICRO/timing · **refines:** `momentum_exhaustion_legpos` (A7) · `risk_structural_sl_T34` (A10) · `entry_bos_choch_no_isolated_edge` (I1)
- **use_as:** `WARNING_ONLY` (penalidade de TIMING, não da natureza)
- **when_to_foreground:** quando a entry cai no **APEX de uma barra de recuperação** (reclaim forte) com regime ainda frágil (cascade ≈ −1).
- **what_it_can_invert:** NÃO inverte a natureza — penaliza o TIMING. Distingue "leitura certa, entry cedo demais": comprar o **reteste de higher-low**, não o apex da recuperação.
- **known_failure_mode:** **6887** (2024-06-14) — pullback-continuação lido certo na natureza (weekly +0.90), mas a entry no apex de recuperação em cascade −1 falhou (o apex virou lower-high), loser por timing, não por leitura.
- **example_cases:** 6887 (apex falhou; o reteste teria sido a entry).
- **do_not_use_as:** NUNCA virar gate de SKIP (a natureza pode estar certa) — é flag de timing/risk-review: roteia entrada-boa-mal-temporizada para melhor entry, não para descarte.
- **automation_note:** detectar apex-de-recuperação (entry ≈ high recente pós-reclaim) × cascade negativo; flag de timing ligada ao eixo risco/exit (Família G). NÃO promover a SKIP.
- **provenance:** audit fase-3 cluster 4918, ep 6887 (commit c3839b8).

---

## Como o Reader usa o Operating Manual (fecho)

1. Fixe a Camada 1 → leia a forma (Camada 0).
2. Ao puxar uma lente da Camada 2, consulte seu registro no Manual: **`when_to_foreground`** (entra agora?), **`what_it_can_invert`** (qual leitura ingênua ela derruba?), **`known_failure_mode`** (onde ela já enganou?), **`do_not_use_as`** (o que não fazer).
3. As lentes `INVALIDATION_PROBE`/`CONTRAST_LENS` são obrigatórias quando há sósia conflitante (hard cluster).
4. `use_as=DO_NOT_GATE`/`WARNING_ONLY` nunca produzem TAKE/SKIP — só mudam a profundidade/cautela da leitura.

## Migração (incremental)
As lentes da biblioteca migram para este schema aos poucos, priorizando POLARITY/CONTRAST (maior valor de inversão).
Cada migração herda status+reader_use da biblioteca e acrescenta os campos funcionais. **Nada é apagado** — overlay.

**Lote 1 migrado (2026-06-23) — 12 lentes POLARITY + CONTRAST** (além das 3 OM seed = 15 no Manual):
- POLARITY (6): `supply_sup_cat_pol_cat` · `overbought_in_bear` · `leg_maturity` · `bubble_polarity_context_dependent` · `capitulation_carrier` · `indicators_identify_macro_top_not_per_trade`.
- CONTRAST (6): `fuel_convexity_cleansky` · `capitulation_reversal_lens_dspa` · `SMC_BOS_CHoCH` · `acceptance_rejection` · `learned_context_vs_convexity` · `sosia_surface_clustering_3a`.

São as lentes de maior poder de **inversão** (polaridade/contraste) — onde o `what_it_can_invert` mais importa para o Reader. Cross-link via campo `refines`/`related` liga cada uma às OM e às lentes vizinhas.

**Pendente (lotes futuros):** CORE_CONTEXT (17), CONDITIONAL_EVIDENCE, REQUIRES_CASE_READING, DO_NOT_USE_AS_GATE, WARNING_FAILURE_MODE, DEAD_AS_AUTHORITY — migrar quando o uso pedir. (Próximo passo combinado: ir ao próximo cluster — aguardando instrução.)

**Artefato machine-readable:** `my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_reader_operating_manual.csv`.
