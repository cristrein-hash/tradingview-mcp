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

## 🔒 PROTOCOLO READER VIVO — etapas OBRIGATÓRIAS por cluster (lockado 2026-06-23)

Todo cluster do currículo de arquétipos roda 1-a-1, com pergunta viva clara, na sequência:

1. **Selecionar** coorte contrastiva (outcome usado SÓ p/ montar o par runner/trap, como hard-cluster).
2. **Blind plot** canônico no chart (long_position + SL estrutural real + TP 2:1 fixo + label azul; sem outcome/R/cor-de-resultado; pausar daemon L1 antes).
3. **Revisão visual humana** do plot (Cris valida antes de liberar a leitura).
4. **Pacote cego** — sem R/trap/runner/mfe/outcome/labels-de-resultado/nomes-de-lente; **leak-check estrito (para se falhar)**. Inclui o **causal indicator layer** como EVIDÊNCIA (perguntas, não decisão). **FONTE = RAW ORIGINAL replay** (NAS/SMC/bubbles/RSI/SVP); proibido derivado/frozen/slim/repro_recovery para indicador (incidente 2026-06-23).
   - **🔒 RAW SOURCE GATE (obrigatório):** rodar `source_gate/check_reader_sources.py` (exit 0) ANTES de montar o pacote. Todo campo declara `source_mapping_status` ∈ {RAW_ORIGINAL_OK · DERIVED_FROM_RAW_WITH_MAPPING · VISUAL_AUX_ONLY · HEURISTIC_ONLY_FLAGGED · UNKNOWN_BLOCKED · UNMAPPED_DERIVED_DISALLOWED · DERIVED_ARTIFACT_BUG}. Campos UNMAPPED_DERIVED_DISALLOWED / UNKNOWN_BLOCKED / DERIVED_ARTIFACT_BUG ficam **FORA** do pacote. `allowed_as_decision=NO` para todos. Política: `docs/RAW_SOURCE_GATE_POLICY.md`; manifest: `source_gate/reader_raw_source_manifest.yaml`; auditoria: `docs/XAU_4H_L2_BPT_READER_SOURCE_MAPPING_AUDIT.md`.
5. **Reader cego** — spawnar um subagente leitor REAL (via Agent tool), fresco, que nunca viu outcome → leitura por episódio + EXPECTATION auditável + contraste por par.
6. **Freeze** + **commit da leitura ANTES de abrir o outcome** (integridade anti-hindsight).
7. **Outcome audit** — spawnar um subagente auditor REAL (via Agent tool), fresco → leitura congelada vs realidade + EXPECTATIONS.
8. **🆕 VISUAL POST-AUDIT REVIEW (OBRIGATÓRIO) — contra prints/chart canônico, antes de propor o próximo cluster.**

> Nota anti-teatro: os leitores/auditores das etapas 5 e 7 são subagentes REAIS spawnados via Agent tool (cego = sem acesso ao outcome), nunca síntese escrita à mão rotulada de "agente".

### Etapa 8 — VISUAL POST-AUDIT REVIEW (checklist obrigatório)
Antes de propor o próximo cluster, revisar a leitura cega contra os prints/chart canônico e verificar:
1. a leitura cega bate com o chart?
2. NAS TOP/BOTTOM, RSI divergences, bubbles, SMC, BOS/CHoCH **reforçam ou contradizem** a leitura?
3. houve **indicador causal visível ausente** do pacote cego?
4. **alguma confiança foi alta demais?**
5. algum **"trap" era bottom-attempt-whipsaw**? (fundo macro perto, este entry falhou por timing)
6. algum **"supply wall" era compression/fuel**?
7. **quais lentes** devem ser refinadas?
8. **quais campos causais** devem entrar no próximo pacote cego?
9. 🆕 **source-mapping:** o causal indicator layer veio do RAW ORIGINAL (não derivado)? o timing dos eventos é causal as-of-bar? **qualquer divergência entre chart/print e RAW = INCIDENTE DE SOURCE-MAPPING** (auditar RAW, nunca concluir do derivado).

**Só depois desta revisão** se propõe o próximo arquétipo. Pular a etapa 8 = aceitar verdict sem olhar o chart (proibido — [[feedback_estatistica_aplicada_realidade]]).

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

## SEED lote 2 — 4 lentes do Cluster 2 (macro negativo; commit 9f7326f)

### OM4 · `indicator_confluence_as_reading` — o layer que faltava no pacote cego
- **family:** INDICATOR · **refines:** `bubble_polarity_context_dependent`(E2) · `overbought_in_bear`(C5) · `capitulation_climax`(A8) · `indicators_identify_macro_top_not_per_trade`(I4)
- **use_as:** `CONTRAST_LENS` + `CONDITIONAL_SUPPORT` (evidência que faz PERGUNTAS, NUNCA decide)
- **when_to_foreground:** sempre — o indicador (sell/buy bubbles, RSI bull/bear-div, NAS, SMC) pergunta: **capitulação? absorção? exaustão? mudança de caráter? whipsaw?** — NÃO classifica TAKE/SKIP.
- **what_it_can_invert:** confluência de indicador (sell-bubble climax no low + RSI bull-div + NAS-bottom) inverte uma leitura form-only de "range = wall" para "capitulação = fuel". É o fix do furo 5627 (form-only não viu o cluster de sell-bubbles m/L no low + rsi_min 26.6 + bull-div).
- **known_failure_mode:** indicador como gate per-trade afunda winners (I4); sell-bubble-no-low sozinho não decide (3929-trap e 3949-runner têm assinatura parecida → é o whipsaw OM6 que separa). **INCIDENTE 2026-06-23:** concluir disponibilidade de indicador a partir de DERIVADO (`raw_features_2020_2026`) é proibido — RAW-first sempre.
- **example_cases:** 5627 (capitulação no indicador — sell_mL15 + SHORT-supply acima; form-only leu wall); 3929 vs 3949 (mesma assinatura, separados por timing).
- **do_not_use_as:** gate per-trade; equal-veto; indicador isolado como verdade; **fonte derivada/frozen/slim para qualquer indicador**.
- **automation_note:** **FONTE = RAW ORIGINAL** (`raw_replay/XAUUSD/4H/*.jsonl.gz`): NAS/SMC=`pine_labels` (tail as-of-bar), bubbles=`pine_shapes_bubbles.activations_per_plot`, RSI+div=`study_values`. Extrator `l2_bpt_raw_indicator_extract.py` → `results/l2_bpt_raw_indicator_events.jsonl` (RAW_AUTHENTIC); layer `l2_bpt_causal_indicator_layer.py` com GUARD que recusa derivado. **Regra permanente: TODO indicador (NAS/SMC/bubbles/RSI/SVP) do RAW, nunca derivado.** Ver `docs/architecture/NAS_SMC_SOURCE_INCIDENT.md`.
- **provenance:** visual post-audit cluster 2 (prints) + audit 9f7326f + incidente de fonte corrigido (RAW).

### OM5 · `washout_runner_vs_compression_runner` — refina OM1
- **family:** MICRO/AUCTION · **refines:** `OM1`(supply momentum) · `capitulation_climax`(A8)
- **use_as:** `CONTRAST_LENS`
- **when_to_foreground:** ao decidir se um long em macro negativo vai se desenvolver — há DOIS arquétipos de runner, não um.
- **what_it_can_invert:** distingue **(A) washout-runner** = queda madura→capitulação→reabsorção→expansão **de (B) compression-runner** = range apertado sob supply→defesa lateral→coil→expansão. O furo 5627 veio de só ter o tipo A bem desenvolvido → tratou compressão-sob-supply como wall, era fuel (tipo B).
- **known_failure_mode:** 5627 (compression-runner lido como wall por falta do arquétipo B).
- **example_cases:** 5826/4401/1522/3949 (tipo A washout) vs 5627 (tipo B compression).
- **do_not_use_as:** gate; presumir que todo range-sob-supply é um dos dois (pode ser wall real).
- **automation_note:** discriminar A vs B por forma (clímax+reabsorção vs lateral-defendido+coil) + OM4 (capitulação no indicador). Leitura humana/agente.
- **provenance:** visual post-audit cluster 2, ep 5627.

### OM6 · `bottom_attempt_whipsaw_vs_trap` — nem todo loser é trap
- **family:** MICRO · **refines:** `leg_maturity`(D6) · `OM3`(timing)
- **use_as:** `CONTRAST_LENS` + `WARNING_ONLY`
- **when_to_foreground:** ao rotular um caso que falha em macro negativo perto de um possível fundo.
- **what_it_can_invert:** separa **bottom-attempt-whipsaw** (região perto de fundo macro real + sinais de tentativa de reversão, mas ESTE entry falha por timing/whipsaw) de **bear-pullback-trap limpo** (sem fundo perto, distribuição). Natureza diferente, mesmo que ambos falhem o trade.
- **known_failure_mode:** 1873 (lido "trap MED-ALTA"; era bottom-attempt-whipsaw — fundo macro perto, whipsaw); 3929 idem (tentativa 3 dias antes do 3949).
- **example_cases:** 1873, 3929 (whipsaw perto de fundo) vs trap de distribuição limpo.
- **do_not_use_as:** gate de TAKE (whipsaw ainda falha o entry); chamar todo loser-em-bear de trap.
- **automation_note:** proximidade de fundo macro + sinais de reversão tentada (OM4) + entry-timing; flag de natureza, não de trade.
- **provenance:** visual post-audit cluster 2, ep 1873/3929.

### OM7 · `confidence_calibration_ambiguous_zones`
- **family:** READING · **refines:** todas as lentes de natureza
- **use_as:** `WARNING_ONLY`
- **when_to_foreground:** sempre que a leitura cair em zona ambígua: **range-apertado-sob-supply · bottom-attempt · compressão-antes-da-expansão · entry-perto-de-zona-conflitante.**
- **what_it_can_invert:** baixa a confiança DECLARADA mesmo quando a DIREÇÃO parece clara — nessas zonas a NATUREZA é ambígua (o 5627 levou ALTA-confiança num caso difícil e errou).
- **known_failure_mode:** 5627 (ALTA-confiança em range-sob-supply, errado); 1873 (MED-ALTA em bottom-whipsaw).
- **example_cases:** 5627, 1873.
- **do_not_use_as:** desculpa para não ler; é calibração, não recusa.
- **automation_note:** rebaixar confiança a MÉDIA nessas 4 zonas por default; leitura humana/agente.
- **provenance:** visual post-audit cluster 2.

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

**Lote 2 migrado (2026-06-23) — 24 lentes WARNING/FAILURE_MODE + DO_NOT_USE_AS_GATE** (reshape fiel do inventário via `l2_bpt_migrate_lote2_warning_donotgate.py`, idempotente). WARNING → `use_as=WARNING_ONLY` (precedente de erro: `what_it_can_invert` = "previne repetir X"); DO_NOT_USE_AS_GATE → `use_as=DO_NOT_GATE` (vira de gate para contexto). **Manual agora = 39 lentes** (3 OM + 12 lote1 + 24 lote2).

**Pendente (lotes futuros, quando o uso pedir):** CORE_CONTEXT (17), CONDITIONAL_EVIDENCE, REQUIRES_CASE_READING, DEAD_AS_AUTHORITY. (Próximo passo combinado: ir ao próximo cluster, 1-a-1, com pergunta viva clara → aguardando autorização.)

**Artefato machine-readable:** `my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_reader_operating_manual.csv`.
