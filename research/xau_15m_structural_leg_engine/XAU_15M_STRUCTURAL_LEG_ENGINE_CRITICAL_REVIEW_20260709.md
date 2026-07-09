# CRITICAL REVIEW PRÉ-CÓDIGO — XAU 15M STRUCTURAL LEG ENGINE (2026-07-09)

> Ordem do Cris: buscar incongruências/erros na spec+manifest ANTES de codar. Sem código, sem
> backtest, sem lab, sem produção/Telegram/broker/chart. Autoridades lidas: PROTOCOL_V1,
> 02_DATA_SOURCE_POLICY_RAW_FIRST, 03_BACKTEST_VALIDATION_PROTOCOL, 10_DO_NOT_DO_RULES,
> memória `feedback_no_primitives_raw_hd_only` + `feedback_15m_needs_own_structural_engine`.

## 0. Bootstrap
- HEAD `62101bc` == origin/main ✅ · working tree: só `?? research/xau_15m_structural_leg_engine/` (docs PRE-CODE) ✅
- Safety: BLOCKER=3 **pré-existentes** (scanner marca scripts do lab leonardo que escreveram o
  catálogo em 2026-07-07 como "write op em target catalog") + WARNING=1 (SLIM em candidato 4H
  dormant) — fora do escopo deste lab, nada introduzido pelos docs novos.
- `RAW_LINEAGE_PASS` com `--strict-existence` (9 RAW no HD + checksum GT verificados) ✅

## 1. VERDICT: `APPROVE_WITH_REQUIRED_SPEC_EDITS`
O desenho central é são (máquina de estados causal ≠ zigzag; RAW-only; calibração com looks
contados; gates duros). MAS a auditoria encontrou **1 não-conformidade com o protocolo, 3 riscos
conceituais reais e 5 lacunas de doc** que têm de ser corrigidos ANTES de codar. Nenhuma falha fatal.

## 2. TOP RISKS (ordenados)

**R1 — Histerese vira zigzag estatístico se mal calibrada (conceito).** A diferença REAL vs zigzag:
(i) estados têm semântica de invalidação (ACTIVE/SHALLOW_BOUNCE) que pivôs não têm; (ii) extremos
são running extremes conhecíveis em t; (iii) nada é confirmado por excursão futura. MAS se a
calibração empurrar K/D_flush para baixo, o flip-flop de leg_dir reproduz pivôs de facto.
→ EDIT E1: triagem de plausibilidade ANTES do matcher PLT/DM (nº pernas/mês, duração mediana,
% tempo por estado — métricas que NÃO olham o GT), elimina configs degeneradas; só top-≤20 configs
vão ao PLT/DM; contagem de flips proibida como feature de seleção.

**R2 — Latência da camada 1H pode chegar tarde ao pullback (d_vale=0, reação 1,5h).** leg_dir com
histerese K em buckets 1H = atraso de horas. Aceitável para DIREÇÃO (muda raramente); fatal se
leg_phase depender dela barra-a-barra.
→ EDIT E2: explicitar que leg_phase/eventos/pb_min/d_vale operam em **barras 15M nativas** sobre o
running extreme da perna; só leg_dir e macro_regime usam agregação 1H. Latency_known_at já é métrica
com stop_condition — mantida.

**R3 — "BULL continuação sem toque de âncora" pode virar licença para comprar topo (repetir A-BULL).**
→ EDIT E3 (salvaguarda estrutural na DETECÇÃO): evento só pode ser emitido em leg_phase ∈
{PULLBACK, PULLBACK_FLOOR_FORMING, DEEP, TERMINATING, BASE_BOTTOM} — **NUNCA em IMPULSE nem
DISTRIBUTION_TOP**. A "continuação sem toque" é regra de ENTRY (Fase 2), continua a exigir pullback
≥ pb_min (a isenção é do TOQUE DE ÂNCORA, nunca do pullback) e só nasce com revisão visual do Cris.

**R4 — 162 combos da camada de pernas vs 21 marcas PLT/DM = mining risk.** → coberto por E1
(triagem 2 estágios) + mining-null estendido ao F1.5 (recall do melhor config sob marcas deslocadas
cluster-aware) + 162 looks TODOS no ledger.

**R5 — recall ≥36/42 sem gate de FP = detector que marca tudo.** Recall alto com precisão nula não
resolve nada; sem FP/dia o detector é inútil operacionalmente. → EDIT E4: report obrigatório com
curva recall×FP/dia completa + razão eventos/janela-GT + null-de-detector (ocupação de estado
aleatória) com P≤0,05 como gate mínimo; teto estrutural de precisão (densidade sósia 28-108:1)
DECLARADO no report; ponto de operação = decisão do Cris.

**R6 — Holdout BEAR 6+6 dentro do MESMO episódio bear 2026 = validação fraca por autocorrelação.**
→ EDIT E5: rebaixar formalmente a leitura BEAR para **CALIBRAÇÃO, não validação** (regra do Cris:
grupos dentro do mesmo regime = calibração); validação BEAR real só com bear futuro/forward.

**R7 — Gate PLT/DM (≥9/10, ≥10/11) foi calibrado na representação zigzag antiga** — exigir
equivalência cega pode forçar a máquina nova a imitar o zigzag morto. → EDIT E6: gate mantido; se
falhar por ≤1 marca com pernas visualmente plausíveis, STOP + arbitragem visual do Cris (em vez de
expandir grid às cegas).

**R8 — Indicador dentro da detecção (cascata SMC em DEEP, CHoCH+ em TERMINATING) viola a ordem
estrutura→indicador do protocolo §C.** BOS/CHoCH são eventos estruturais, mas por pureza do
protocolo: → EDIT E7: na v1 a EMISSÃO é 100% price-only; SMC/CHoCH viram **colunas anotadas** no
evento (com known_at), avaliadas como evidência SÓ na Fase 3 dentro dos baldes; se discriminarem,
entram na v2 como reforço, com looks contados.

**R9 — Critério do Cris (losers ≤10) e painel final AUSENTES da spec/manifest.** → EDIT E8:
manifest ganha `success_criteria_final` (winners de continuidade válidos SÓ se losers ≤10 na
estratégia downstream; painel completo: winners preservados, losers restantes/cortados, maxDD,
streak, FP/dia, trades concorrentes, clusters, R com SL V1 + exit 3R, **visual review do Cris
obrigatória antes de qualquer upgrade de status**).

**R10 — Manifest no dir errado.** Protocolo Stage 1 exige `docs/architecture/XAU_15M_<LAB>_GATE_MANIFEST.md`.
→ EDIT E9: mover manifest para docs/architecture/ (pointer no dir do lab).

## 3. AUDITORIA POR FASE (respostas diretas)

**F2 Conceito:** (1) não é smoothing disfarçado SE E1/E2 aplicados — a semântica de estados
(invalidação ACTIVE, SHALLOW_BOUNCE≠DEEP) é o que o zigzag não tem; (2) agregação 1H price-only =
aceitável e canónica, risco confinado por E2; (3) definições observáveis em tempo real ✅, exceto
"banda inferior do range" que estava vaga → EDIT E10: banda = running-min do run FLAT ± tol_anchor
(0,7 ATR congelado; sem parâmetro novo); (4) camadas separadas ✅ com 1 mistura: "gatilho de reação"
dentro do evento BULL → EDIT E11: evento em 2 known_at (`region_known_at` quando o estado qualifica
a REGIÃO; `floor_known_at` na confirmação mínima do floor) — confirmação de floor ≠ entry trigger,
proibido reutilizar como entry na Fase 2 sem re-medição; (5) região vs entry corretamente separados
(F4 hand-off) ✅; (6) risco real → E3; (7) losers ≤10 ausente → E8.

**F3 RAW:** inputs = 9 `.jsonl.gz` + GT com checksum ✅; zero primitives ✅; `raw_features_2020_2026.jsonl`
NÃO é usado (é o RAW-features do 4H L2/BPT) — mas para blindar → EDIT E12: ban explícito no manifest
de `raw_features_*.jsonl`, `*.primitives.json` e qualquer CSV regenerado como FONTE; HD desmontado =
BLOCKED sem fallback ✅ (stop_condition); extração por barra descrita (study_values RAW; ATR/EMA
recalculados de OHLC = "derivada simples verificável" da política 02 §4, fórmulas declaradas) ✅.
`RAW_FEATURES_IS_NOT_RAW_INDICATOR_SOURCE`: registado — qualquer uso futuro desse ficheiro em 15M
= violação.

**F4 Lookahead:** extremos = running ✅; âncora só de perna FECHADA com t_known = fecho da perna
(usável só para t ≥ t_known) ✅ → explicitado (E13); retr_fam usa H1 running, não posição final ✅;
family_label não usa outcome ✅; range bottom detectado DURANTE o range ✅; capitulação definida por
drop+flip PASSADOS, nunca pelo rally posterior ✅; 1D agregado = só dias FECHADOS (D-1) → explicitado
(E13); eventos IMUTÁVEIS: append-only, snapshot congelado no known_at, truncation test com zero
tolerância, "se mudar = provisional e nunca usável" → explicitado (E13).

**F5 GT:** catalog existe (sha256 verificado no manifest) ✅; 42 primário / 50 secundário /
4 INVALIDO negativos / 65 trades FORA (21 timestamps corrompidos) ✅ tudo no manifest; PLT/DM gate
entendido, risco de overfit à representação antiga → E6; split BULL 13(2025)+13(2026) ✅; BEAR → E5
(calibração, não validação); RANGE n=4 = sempre EXPLORATORY (n mínimo) → nota adicionada; nunca
calibra e valida nos mesmos 42 ✅.

**F6 Overfit:** 6 constantes novas, grids ≤3 ✅ mas produto = 162 (pernas) + 27/família (eventos)
→ E1 + mining-null + ledger completo; holdout real ✅ (BULL 2026 lido 1×); null episódico ✅ (3 tipos);
ajuste pós-losers proibido (hipóteses congeladas no manifest antes de correr) ✅; recall como único
alvo → E4 (FP/dia + null-de-detector como gates de report).

**F7 Métrica final:** → E8 (painel completo + losers ≤10 + visual review no manifest).

**F8 Indicadores:** ordem regiões→entry→indicadores respeitada nas fases ✅ com a exceção R8 → E7
(emissão v1 price-only; SMC/NAS/OB/Bubbles/SVP SÓ na Fase 3, dentro de baldes, com source mapping
da política 02; nenhum indicador acha fundo antes da estrutura).

## 4. O QUE ESTÁ BOM (fica)
- Máquina de 3 camadas transposta com semântica de invalidação como ESTADO (é a matematização
  direta das notas INVALIDO do Cris).
- RAW-only com lineage PASS estrito; stitch de fronteiras com carry de estado + eventos suprimidos
  em warmup + GT `UNSCORABLE` explícito.
- Herança v5 congelada (eff_thr/slope_thr/tol_anchor) — reduz superfície de fit.
- F1.5 gate duro PLT/DM antes de eventos; truncation test zero-tolerância; grep-assert anti conf_i;
  paridade macro obrigatória.
- Split por família com holdout 1×; nulls episódicos; R uncapped; claims ledger; stop_conditions
  executáveis; fora-de-escopo explícito (entry/produção/SHORT).

## 5. O QUE TEM DE SER REMOVIDO/MUDADO (antes de codar)
1. E7 — SMC/CHoCH fora da CONDIÇÃO de emissão v1 (viram anotação; evidência só na Fase 3).
2. E3 — proibição de evento em IMPULSE/DISTRIBUTION_TOP (anti-A-BULL) escrita na spec.
3. E11 — "gatilho de reação" reclassificado: confirmação de floor com known_at próprio, não entry.
4. E9 — manifest movido para docs/architecture/.
5. E8/E12/E13/E10/E5/E6/E4/E1/E2 — edits de doc listados acima.
Nenhuma medição infantil escondida encontrada além de R1 (mitigada por E1); nenhum uso de
primitives; nenhum lookahead de desenho (riscos são de IMPLEMENTAÇÃO, cobertos pelos DA-checks).

## 6. GO/NO-GO
**GO para codar F0→F1.5 APÓS aplicação dos edits E1-E13 na spec/manifest** (só docs) e DA desta
auditoria. Paragem obrigatória no gate F1.5 com apresentação ao Cris.
