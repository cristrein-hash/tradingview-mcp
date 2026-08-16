# XAU SHORT 15M — Build Playbook (síntese das melhores práticas comprovadas + passo-a-passo)

> **Propósito.** Resgatar e organizar TODO o conhecimento comprovado da construção das estratégias XAU LONG
> (features, backtests, erros) e transformá-lo num **passo-a-passo simples, eficiente, sem invenções e sem erros**
> para construir uma estratégia **XAU SHORT 15M**. Objetivo: resultado real, auditável e rápido — sem alucinações,
> sem rabbit holes, sem curvas inúteis no thinking.
>
> **Estatuto.** Síntese de material já existente (nada inventado). NÃO é um lab; NÃO tocou produção/chart.
> Fontes: `04_STRATEGY_STATUS_MASTER.md`, `XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1.md`, `03_BACKTEST_VALIDATION_PROTOCOL.md`,
> `RECURRING_ERROR_CATALOG_AND_GUARD_PLAN_20260811.md`, `BOTTOM_ENGINE_LOGIC_REFERENCE_20260715.md`, e as memórias
> das estratégias aprovadas + feedback. Data: 2026-08-15.

---

## NÚCLEO 1 — Melhores práticas comprovadas (o que trouxe resultado positivo)

Oito padrões transversais que aparecem em ≥3 estratégias LONG vencedoras. **Estas são as regras de construção — não teoria.**

1. **ESTRUTURA-PRIMEIRO, indicadores DEPOIS.** Selecionar o evento estrutural (regime + perna + família/fundo) ANTES
   de olhar qualquer indicador. A entrada só funciona DENTRO de um evento estrutural verdadeiro; fora dele = null = a faca.
   O lift vem da ORDEM, não de um indicador isolado. *(Cp, N96, RWS, B, A1/A2.)*

2. **SL estrutural ancorado ao nível real ∓0,1ATR + alvo 3R fixo (SL-first).** A régua vencedora em TODAS as camadas:
   L1 `zona_OB_low−0,1ATR`, L2 `SL_CONTEXT` (demanda −0,1ATR, sem teto), Cp `flush−0,1ATR`, A1/A2 e B `low-real−0,1ATR`.
   **Trailing/let-run/chandelier foram testados e REJEITADOS** (L1 CHAND +123R era knife-edge k=5,0, 88-92% de 2025; L2 trailing todos negativos).

3. **Gate de REGIME que corta o streak-killer — não que gera alpha.** gate-bear (L2), intra-BEAR (N96 +13R = 13L/0W),
   crash-born SKIP (B, precisão 1,00), regime v5≠BEAR (RWS), macro-1D BULL (A1/A2). O ganho é **viabilidade/streak**, não expectância.

4. **Gate de POSIÇÃO — comprar o fundo/suporte, rejeitar o topo/esticado.** ≤40% do range (B, contribuição principal),
   zona-top vs esticada (L2 cap-bull), anti-extensão at-entry (L1), fundo-de-perna (Cp). "Entrar perto do topo/esticado" = os losers em toda a parte.

5. **CAUSALIDADE fanaticamente auditada — o edge quase sempre encolhe quando o lookahead é removido.** Âncora SL a espreitar
   futuro (A1/A2 14/14→13/14), zigzag r12 (RWS, confirmação usa futuro), zonas à mão (L2 6/6 refutado), supply_above (N96),
   DAYREG do próprio dia. Regra: features diárias recuam D-1; labels com `born_t`; NAS SHIFT1; **testar a versão causal ANTES de celebrar**.

6. **Distinguir EDGE de BETA long-gold com NULLS agressivos.** L2 provou (100-200 draws random) que +36R/+64R eram beta de
   exposição, não alpha. RWS swept null **p=0** (edge genuíno). A maioria das "vitórias" morre à multiplicidade (htf_demand_retest 0,647, Kaufman-ER 63,5%). Nunca aceitar sumR+ sem null que pague subset + feature-mining.

7. **Winners e losers COEXISTEM no espaço de features de ENTRADA (muro da irredutibilidade).** Confirmado em L2 (5 frentes = parede),
   N96 (poisoning ~1:1: cada feature que corta um loser mata um winner), RWS (Labs A-F não movem WR/streak), Cp (indicadores isolados não separam).
   **O lever real é gate estrutural + gestão/risco — NÃO seleção fina de entrada.** Confluência-de-indicadores sozinha ≠ edge (Engine 7 avgR 0,1).

8. **Validação = FORWARD, nunca OOS/cross-asset; painel COMPLETO sempre.** Todo desenho aprovado in-sample fica selado com
   prereg + coletor forward = árbitro. Painel obrigatório: N · WR · sumR · avgR · DD · return/DD · **STREAK** · por-ano.

**Evidência-âncora (in-sample, real — números verificados byte-exato 2026-08-15):** L1 N24·75%·+45,2R ·
**L2/BPT V2 N17·53%·+36,2R (exit +105,3R, ret/DD 26×) — ⚠️ o edge de ENTRADA é BETA long-gold, não alpha**
(teste pure-edge phase51: entradas estruturais NÃO batem 100 draws random em nenhum exit; a L2 vale pelo EXIT/gate/gestão,
não pela seleção de entrada) · Cp N21·43%·+12,6R·GT5/5 · B MB3+spring 3W/0L · A1 13/14·A2 16/18 · N96 52W/44L·+112R ·
RWS N435·47,6%·+291,5R (null p=0, o único com edge de sinal genuíno provado). **Regra de leitura desta linha: N e sumR
positivos NÃO são edge até o null pagar (Padrão 6) — L2 é o caso-escola de beta disfarçado.**

---

## NÚCLEO 2 — Workflow canónico de construção + validação (a via rápida)

Ordem OBRIGATÓRIA (fonte: `XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1`). **Regra-mãe: sem `macro_regime` + `leg_state` +
`family_label`, nenhum indicador vira evidência.** NUNCA `prompt → escolher ficheiros → medir → narrar`.

```
Manifest → Source-guard PASS → Bucket estrutural → Indicador DENTRO do balde →
Hipótese congelada → Script determinístico fail-loud → Null + DA real → Claim ledger → Painel completo → Lab-gate PASS
```

| Passo | Produz | Gate que o fecha |
|---|---|---|
| Manifest | direção/TF/gates/entry/SL/target/dedup + `raw_files`+`derived`(source_ref+checksum) + `structural_buckets` + grid prereg + splits | manifest ausente → lab **aborta** |
| RAW/source | RAW direto + checksum sha256 + stale-status; cada gate mapeado ao campo RAW | `check_xau_15m_raw_lineage.py` → `RAW_LINEAGE_PASS` |
| Structural-first | tabela `trade_id, macro_regime, leg_state, position_in_leg, family_label, causal_regime_source` ANTES de indicador | `check_xau_15m_structural_first.py` → `STRUCTURAL_FIRST_PASS` |
| Indicador no balde | SMC/OB/SVP/Bubbles/NAS/RSI/vol/ATR avaliados DENTRO de cada balde (global-scan-como-decisão = PROIBIDO) | mesmo blocker |
| Hipótese congelada | thresholds/grid no manifest ANTES do cálculo | grid prereg |
| Execução | script determinístico fail-loud, assert byte-parity, 1ª rodada read-only, outputs `/tmp` | asserts no script |
| Null + DA | null apropriado (permutação intra-bucket / feature-search / mining) + DA adversarial via **Agent tool real** | DA PASS + null P≤0,05 |
| Claim ledger | todo número → linha `claims_ledger.csv` (script/input/output/source_ref/checksum/status) | `check_xau_15m_claims_ledger.py` → `CLAIMS_LEDGER_PASS` |
| Report | só claims do ledger; painel completo; status com qualificador | mesmo blocker |
| Commit | só se o runner único passa | `run_xau_15m_lab_gate.py` → `XAU_15M_LAB_GATE_PASS` |

**Regras inegociáveis:** RAW-first (verificar `dataset_registry.json` antes de ler; nunca resamplear TF nativo; nunca SLIM) ·
close-only causal (SHIFT1 SMC/OB/bubbles, D-1 daily) · **unidade = EPISÓDIO não trade** (o leitor LLM julga; o código só monta
contexto e journala, NUNCA arbitra por score/voto/booleano) · convergência ≠ determinismo · **validação DENTRO dos dados**
(null/jackknife/sub-janela/robustez ±20%, NUNCA OOS/cross-asset) · calibração ≠ validação (GT/45-grupos = descobrir predicados,
não provar edge) · **objetivo = LUCRO (expectancy × frequência)**, capado/WR nunca árbitro, streak/viabilidade co-primário ·
status com qualificador (`VERIFIED_RAW`/`EXPLORATORY`/`REVIEW_LAYER`/`RISK_CONTROL`/`INVALID`) · subagents não committam.

**Baldes estruturais canónicos:** `BULL_impulse · BULL_pullback · BULL_excess_top · RANGE_neutral ·
RANGE_distribution_top_bear · RANGE_accumulation_bottom · BEAR_active · BEAR_shallow_bounce · BEAR_deep_capitulation ·
countertrend_bounce_in_bear · management_do_not_filter`. (Um SHORT vive sobretudo em `RANGE_distribution_top_bear`, `BEAR_active`, `BULL_excess_top`.)

---

## NÚCLEO 3 — Erros já cometidos a evitar (auditoria) + o que os trava

Fonte: `RECURRING_ERROR_CATALOG_AND_GUARD_PLAN_20260811.md`. 🟥=hook bloqueia · 🟨=advisory/manual · ⬜=sem guard.

| Erro | Sintoma / exemplo real | Trava |
|---|---|---|
| **SLIM/proxy vs RAW** | slim +185R vs RAW +18R (Caminho B revogado); recorrente 5-6× | 🟨 source_gate + 🟥 G3 só no commit |
| **Lookahead/repainting** | 3 OFICIAIS invalidados (A1' 88→46%, AMD 35→25%) | 🟥 pre_approval + 🟨 DA pós-facto |
| **Inventar zona/nível** | régua de pavio inventada rejeitou short real por 0,36pt (dia −4R 04/08) | 🟨 check_no_invented_zones + 🟥 contextual_read (só Bash/Write) |
| **Ligar LIVE antes de validar** | polaridade "validada"→refutada, 3× no dia 10/08 | 🟥 pre_golive_da (token DA_OK) |
| **Colapsar leitura em stats/votos/limiar** | reject-all E2 matou 4 winners E 6 losers; inside ≤0,5ATR zerou 17/17 | 🟥 myopia guard + G7 juiz Haiku |
| **Reconstruir reader paralelo** | mtf_cross desligou os monitores do E0; 4 regimes a flutuar | 🟥 consolidation + PARALLEL_CONTEXT_BUILD |
| **Calibração = validação** | precisão/lift dos 45 grupos como edge; 2965 "candidatos" = 276 episódios | 🟨 registry |
| **Otimizar seletor sobre substrato in-selecionável** | L2/BPT rabbit-hole (95 docs/85 scripts/292 CSV); window-cleaning removeu trades a avgR>base | ⬜ |
| **Overfit ao dia visível** | Caminho B promovido com canal seco 3+ dias | 🟨 Pre-Change 4-perguntas |
| **Veredicto em amostra pequena** | "0/7 catástrofe" virou +0,87R a n=11 | 🟨 sample-gate |
| **OOS/cross-asset** | violou instrução explícita ≥3× | 🟥 OOS_LOCK |
| **Supor sem verificar** | descartou polaridade porque a caixa OB sumiu (o nível não foi) | ⬜ |
| **Vetar a contra-tese** | quase-deploy de regime-veto silenciou o melhor LONG da noite | ⬜ |
| **Portar features 4H→15M** | gatilho markup/EMA21 4H declarado pronto p/ 15M | 🟨 memória |

**Insight-raiz (decisivo):** os guards que **funcionaram** no dia 10/08 foram os **hooks bloqueantes** (consolidation, myopia,
PARALLEL_CONTEXT_BUILD). Os que **falharam** foram normas de memória passiva (não-inventar, não-supor, DA-antes-commit).
**Conclusão: para o SHORT, o que protege é o guard que BLOQUEIA execução do lab — não o advisory.**

---

## NÚCLEO 4 — Conhecimento SHORT já decidido (a semente)

**Critério de aceitação (união das 3 formulações do Cris):** um SHORT qualifica quando há **(A)** quebra de estrutura
confirmada **1H+15M** + **retest ao nível rompido**, OU **(B)** **rejeição IMPRESSA no íman superior** — sweep de topo/PDH →
**failed-break** → retest, com **fecho no terço inferior** + **buyers presos/varridos** + **iniciativa sell** (idealmente CHoCH down),
tendo o preço **testado o íman superior (BB 15M + cluster SVP 15M + OB 15M não-testado acima) e rejeitado LÁ**. Gate de sinal
confirmado = **RR≥2 + conv≥60**. Recusar isto como "faca/manipulação/plano LONG intacto" = **erro de viés long**.
*(feedback_short_acceptance_break_retest, feedback_reader_short_symmetric_rejection, project_xau_short_engine_dev_20260720.)*

**Continuação = DEFAULT, não veto.** Ouro em alta = caso-base continuação; mas deixa de ser veto absoluto quando a rejeição
está impressa. Sistema = **sinalizador NEUTRO** (a contra-tese pode ser o melhor sinal; nunca vetar direção).

**Faca vs short:** faca = venda precipitada **abaixo do íman não-testado** (erro de sexta 17/07: shorts 4012/4015 → ambos SL).
**AVISO ESTRUTURAL:** **nenhum gate mecânico separa faca de dip na barra de entrada** (testado exaustivamente: convergência MTF,
estrutura, velocidade, swing-state, sweep-reject). O edge = leitura + contexto HTF como INFORMAÇÃO + gestão. **Não construir um
gate que prometa separá-los — construir o gate ESTRUTURAL de qualificação + gestão.**

**Semente concreta (GT#1, 13/08):** retest **4406,5** (05:15) → quebra **05:30** (O4406,5→L4386,6 C4387,9, −18,6, rompe 15M/1H)
→ caiu a **4356**. Short ~4405 no retest = win limpo ~50pt. O reader antigo recusou 3×; o recalibrado (14/08) tem as condições
para o ler. Prova = FORWARD (replay offline não é fiel).

**Espelhar do LONG — SIM (com âncoras próprias), NUNCA gate invertido:** teste-e-rejeição no íman (superior p/ short) ·
maturidade/exaustão da perna · leilão/iniciativa sell · SL estrutural (supply/nível-rompido **+0,1ATR**) · 3R fixo/RR≥2 · regime = contexto.
**NÃO espelhar cegamente:** ❌ inverter gates do LONG · ❌ shortar markup só porque o macro lento diz BEAR (a **perna imediata
1H manda** — 2 SHORT FORTE stopados 22/07 num markup +65pt; **alinhamento perna-1H = o #1 separador**, COM-perna 56% vs CONTRA 27%) ·
❌ tratar recuo grande em uptrend como short (recuo mediano 68%, fundo segura 14/15) · ❌ dogma do rótulo-de-perna que atrasa nas viragens.

**Estado do dev SHORT (arrancado 2026-07-20):** discriminador central definido (teste-e-rejeição no íman superior); reader
simetrizado + stack de contexto 14/08 LIVE (leitura). **Falta:** o AUTO-SINAL com âncora no íman + preço da rejeição (entrada
não-close-only, que chega tarde nos spikes — lição 4040), e o backtest sob o protocolo.

---

## NÚCLEO 5 — PASSO-A-PASSO de construção da estratégia XAU SHORT 15M

Recipe integrada. Cada passo diz **o que produz**, **o gate** e **o erro que evita**. Um passo por vez; verificar antes de avançar.

**Passo 0 — Bootstrap + Manifest.** `git status`, safety report. Escrever `manifest.json` do lab: `direction=SHORT`, `tf=15M`,
`raw_files` (HD externo + id no `dataset_registry.json`), `structural_buckets` alvo (`RANGE_distribution_top_bear`, `BEAR_active`,
`BULL_excess_top`), gates, entry/SL/target/dedup, grid prereg, splits calibração/holdout. → **Gate:** manifest presente.
→ *Evita:* correr sem plano, overfit ao dia.

**Passo 1 — RAW lineage.** Traçar RAW 15M/1H/4H/1D do HD + BB/SVP/OB 15M dos snapshots canónicos (nunca SLIM/primitives/resample).
Checksums sha256. → **Gate:** `check_xau_15m_raw_lineage.py` PASS. → *Evita:* SLIM/proxy, fonte não-verificada.

**Passo 2 — RECALL GATE (fazer PRIMEIRO, crítico).** Provar que o detetor SHORT recaptura os shorts-verdade conhecidos
(GT#1 13/08 4406,5→4356; caso 4040; e os SL 17/07 como negativos) com recall ≥ limiar prereg. Detetor que descarta os próprios
winners → backtest NULO (lição do censo L2/BPT −9,7R com recall 2/17). → **Gate:** `recall_report.json`. → *Evita:* recall-gate omitido, otimizar sobre substrato in-selecionável.

**Passo 3 — Structural-first labeling.** Para cada candidato: `macro_regime` + `leg_state` (**perna imediata 1H = driver de direção**,
macro só contexto) + `position_in_leg` + `family_label`, ANTES de qualquer indicador. → **Gate:** `check_xau_15m_structural_first.py`
PASS (colunas presentes; baldes canónicos). → *Evita:* colapsar em stats, calibração=validação, shortar markup por macro lento.

**Passo 4 — Núcleo SHORT NATIVO (não espelho).** Definir o qualificador: **teste-e-rejeição no íman SUPERIOR** (BB15M + cluster
SVP15M + OB15M não-testado acima) → rejeição impressa (fecho terço inferior + buyers presos + iniciativa sell, idealmente CHoCH down)
**OU** quebra estrutura 1H+15M + retest ao nível rompido. Reportar **distância-em-ATR + qualidade** (frescor/mitigação), **nunca flag
binária `inside`**. → *Evita:* espelho do LONG, zona binária/falso-nulo, inventar nível.

**Passo 5 — Indicadores DENTRO do balde.** OB/SMC/SVP/Bubbles/NAS/RSI como **convergência causal** (SHIFT1, close-only), lidos do
indicador REAL (nunca inventar/re-derivar de OHLC crua). Nunca eixo único. → *Evita:* invenção, re-derivação, miopia, SLIM.

**Passo 6 — Entry / SL / Exit (régua vencedora).** SL estrutural = **nível-rompido/supply +0,1ATR** (análogo próprio do flush−0,1ATR),
alvo **3R fixo / RR≥2**, SL-first. **NÃO trailing** (rejeitado em L1/L2). Entrada: close-only chega tarde nos spikes → considerar
âncora por toque-de-nível/intrabar (lição 4040). → *Evita:* SL-widening, trailing-hindsight, entrada tardia.

**Passo 7 — Congelar hipótese.** Thresholds/grid no manifest ANTES de calcular métricas. → *Evita:* overfit ao dia visível, calibração=validação.

**Passo 8 — Script determinístico + Claim ledger.** Fail-loud, assert byte-parity, 1ª rodada read-only, outputs `/tmp`. Todo número
→ linha em `claims_ledger.csv` (source_ref+checksum). → **Gate:** `check_xau_15m_claims_ledger.py` PASS. → *Evita:* números sem fonte, mining reportado.

**Passo 9 — Painel + Null + DA.** Painel COMPLETO (N·WR·sumR·avgR·DD·return/DD·**streak**·por-ano). Null/jackknife/sub-janela/robustez
±20% **DENTRO dos dados** (nunca OOS). DA adversarial via **Agent tool real**. **Expectancy×frequência = árbitro; capado/WR nunca.**
Streak/viabilidade co-primário. → **Gate:** DA PASS + null P≤0,05 + `run_xau_15m_lab_gate.py` PASS. → *Evita:* capado-árbitro, OOS, mining-antes-DA, veredicto n-pequeno.

**Passo 10 — Selar + Forward.** Status com qualificador. Prereg + coletor forward = árbitro real. **Alert-only.** Nunca go-live antes
do DA (commit com token `DA_OK`). Plotagem canónica; **review visual = Cris**. → *Evita:* go-live-antes-de-validar, winner's-curse.

---

## NÚCLEO 6 — Guards NOVOS propostos, específicos para a construção do SHORT

Padrão vigente: `decide()` puro + selftest, exit 2, escape auditável. **Prioridade aos que BLOQUEIAM execução do lab** (o insight do Núcleo 3). Nada implementado — lista antes de construir.

- **GS1 `pre_short_lab_manifest_guard`** 🟥 — bloqueia `.py` de lab SHORT sem manifesto co-localizado (raw_source + structural_bucket + claim_ledger). Fecha SLIM, overfit, verify-source, calibração. Escape `LAB_BOOTSTRAP:<razão>`.
- **GS2 `pre_short_source_gate_realtime`** 🟥 — corre o source-gate em cada execução do lab (não só no commit); bloqueia import de slim/primitives ou resample TF↑. Fecha o buraco "checkers só à mão". Escape `RAW_TRACED:<id>`.
- **GS3 `pre_short_recall_gate`** 🟥 — bloqueia o backtest se não houver `recall_report` provando recaptura do GT (4406,5→4356 etc.) ≥ limiar. Fecha recall-omitido, seletor sobre substrato in-selecionável. Escape `RECALL_WAIVED:<razão>`.
- **GS4 `pre_short_anti_mirror_guard`** 🟥 — bloqueia Write/Edit que porte feature LONG 4H (nomes/thresholds EMA21/markup) para ficheiro `*short*` sem tag `# SHORT_NATIVE:`. Fecha port-4H→15M, espelho.
- **GS5 `pre_short_binary_zone_guard`** 🟥 — bloqueia script que compute íman/supply como flag binária `inside/near ≤X·ATR` sem emitir distância-ATR + qualidade. Fecha o falso-nulo 0/17.
- **GS6 `pre_short_bias_veto_guard`** 🟥 — bloqueia introdução de veto duro de direção ("esquece shorts", "plano LONG intacto", "1º pullback nunca vende") no prompt/gate. O único veto sancionado = rejeição macro 4H/1D impressa (`DIRECTIONAL_VETO_OK:<razão>`). Fecha o veto que custou ~85pt em 13/08.
- **GS7 (opcional)** — endurecer a superfície MCP (verificar que o G4 dispara na 1ª ação MCP do lab); a invenção-por-MCP (`data_get_pine_boxes`, tab errada) é o buraco #1 da arquitetura e nenhum dos acima o cobre.

**ESTADO (2026-08-16): GS1, GS2, GS3 CONSTRUÍDOS E WIRED (bloqueantes, meta-runner 15/15).**
- GS2 = `raw_read_guard` + leitor canónico `raw_reader.py` (2 modos, paridade byte-a-byte; os 6+8 scripts migrados). commit 1bec4f3.
- GS1 = `pre_short_lab_manifest_guard` (no manifest = no lab); GS3 = `pre_short_recall_gate` (recall do GT#1 antes do backtest). commit 78ba2ba.
- Faltam GS4 (anti-mirror), GS5 (binary-zone), GS6 (bias-veto), GS7 (MCP) — a construir se/quando o lab lá chegar. **O lab SHORT nasce protegido contra os 3 erros mais caros: SLIM/parse-errado, correr-sem-estrutura, otimizar-sobre-substrato-in-selecionável.**

---

## Teto honesto + rabbit holes a evitar

- **O que este playbook garante:** um processo de construção **auditável, rápido e sem os erros já pagos**. NÃO garante que exista edge — isso decide-se pelos nulls, DA e forward.
- **O muro irredutível:** nenhum gate mecânico separa faca de dip na entrada. O edge do SHORT continua a ser **qualificação estrutural (teste-e-rejeição no íman + quebra/retest) + contexto HTF + gestão + forward** — não uma seleção fina de features nem uma promessa de discriminador perfeito.
- **Rabbit holes a NÃO repetir:** afinar features sobre outcome capado agregado (poisoning ~1:1); construir limpezas sobre substrato sem edge ex-ante (L2/BPT: 95 docs/85 scripts); resamplear TF em vez de ler RAW nativo; recomendar OOS; reportar precisão de calibração como edge; perseguir n-baixo/ultra-WR ignorando streak. **A via rápida é o pipeline do Núcleo 2 — saltar um passo é o que torna o lab lento (retrabalho) ou inválido (bloqueado no gate).**
