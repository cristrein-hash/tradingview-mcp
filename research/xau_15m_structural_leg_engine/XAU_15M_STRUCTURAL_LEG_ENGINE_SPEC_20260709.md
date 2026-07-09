# SPEC CONGELADA — XAU 15M STRUCTURAL LEG ENGINE v1.2 (2026-07-09, pós critical review + DA)

> PRE-CODE. Nenhum módulo será escrito até aprovação do Cris sobre este doc.
> v1.1 aplica os edits E1-E13 do `XAU_15M_STRUCTURAL_LEG_ENGINE_CRITICAL_REVIEW_20260709.md`.
> v1.2 aplica as correções C1-C8 do DA (`..._CRITICAL_REVIEW_DA_20260709.md`, verdito
> PARTIAL_REVIEW_INCOMPLETE) — ver §12.
> Manifest canónico: `docs/architecture/XAU_15M_STRUCTURAL_LEG_ENGINE_GATE_MANIFEST.md` (E9).
> Plano-mãe: Plan agent 2026-07-09.
> Ordem de origem (Cris): replicar a máquina do regime detector com cada leg 15M — legs de alta e
> pullbacks em BULL, bottoms de RANGE, capitulações em BEAR — sem medições infantis, RAW do HD,
> calibrado no mapeamento manual dele.

## 1. Tese
As 3 camadas do detector 4H v5 (estável por histerese · override de flush · leitura causal ao fecho),
transpostas da escala regime-diário para a escala perna-15M. Pernas = runs de estado (nunca pivôs
zigzag). Fundos = transições de estado. Âncoras = extremos de pernas/regimes fechados. As 3 famílias
do GT saem por construção de `macro_regime × leg_state × retr_fam`.

## 2. Estado por barra 15M — tupla `(macro_regime, leg_dir, leg_phase, retr_fam)`

### 2.1 `macro_regime` ∈ {BULL, RANGE, BEAR}
Reuso VERBATIM de `regime_hourcausal()` (`engine_substrate4_v5_hourcausal.py`), alimentado pelo
raw_loader novo. Contexto, nunca detector de fundo. **(C1) Paridade = paridade de LÓGICA: funções
portadas verbatim + fixtures sintéticas determinísticas. PROIBIDO correr/comparar contra série
primitives-derived (o engine canónico lê primitives — fonte banida). Divergência em dados reais =
investigar FONTE antes de declarar defeito de porte.**

### 2.2 `leg_dir` ∈ {LEG_UP, LEG_DOWN, LEG_FLAT} — camada estável
**(E2) Divisão de escalas explícita: SÓ `leg_dir` e `macro_regime` usam agregação 1H/1D price-only
(1D = dias FECHADOS D-1). `leg_phase`, eventos, pb_min, d_vale e running extremes operam SEMPRE em
barras 15M nativas.**
Sobre buckets 1H agregados dos closes 15M (price-only, cláusula no manifest):
- eficiência `eff = |close_t − close_{t−M}| / Σ|Δclose|` sobre M buckets 1H
- slope EMA_fast(1H)/ATR_1H; posição no range local
- classificador raw por bucket → histerese K (K_up/K_down assimétricos) para flip de estado
- **flush override 15M nativo**: `dd_atr = (running_peak − close)/ATR15 ≥ D_flush` E `close < close[−mom]`
  → força LEG_DOWN imediato (fura histerese); recovery por quiet-count.

### 2.3 `leg_phase` — sub-fase do run corrente (deriva de medições causais do run, sem histerese própria)
- LEG_UP: `IMPULSE` · `PULLBACK` (dd do running-max ≥ pb_min·ATR — mata "pequena acumulação" 0,8 ATR)
  · `PULLBACK_FLOOR_FORMING` (pullback + toque de âncora/demanda)
- LEG_DOWN: `ACTIVE` (perna de baixa NÃO terminou = **regra de invalidação do Cris como estado**)
  · `SHALLOW_BOUNCE` (repique dentro de ACTIVE = os 3 INVALIDO de março, d_vale 27-36)
  · `DEEP` (drop ≥ deep_thr·ATR do topo da perna — **(E7) price-only; cascata SMC = coluna ANOTADA,
  nunca condição na v1**)
  · `TERMINATING` (momentum flip multi-barra + reclaim price-only; **(E7) CHoCH+ = anotação com
  known_at, nunca condição na v1** — indicadores só viram evidência na Fase 3, dentro de baldes)
- LEG_FLAT: `NEUTRAL` · `BASE_BOTTOM` (pos_R < banda inferior por ≥ base_min barras → d_vale grande
  por construção; **(E10) banda inferior = running-min do run FLAT ± tol_anchor·ATR (0,7 congelado,
  sem parâmetro novo)**) · `DISTRIBUTION_TOP`

### 2.4 `retr_fam` ∈ {RASO <0,5 · BANDA 0,5-1,3 · FUNDO >1,3}
Retração da perna macro corrente; L0/H1 vêm da MÁQUINA (running extremes de runs), não de zigzag.
Camada VIVA herdada (recall 100% nos 50 círculos, P=0,004).

### 2.5 Mapeamento para baldes canónicos §C
LEG_UP/IMPULSE→BULL_impulse · LEG_UP/PULLBACK*→BULL_pullback · LEG_DOWN/ACTIVE→BEAR_active ·
LEG_DOWN/SHALLOW_BOUNCE→BEAR_shallow_bounce (ou countertrend_bounce_in_bear se macro≠BEAR) ·
LEG_DOWN/DEEP|TERMINATING→BEAR_deep_capitulation · LEG_FLAT/BASE_BOTTOM→RANGE_accumulation_bottom ·
LEG_FLAT/DISTRIBUTION_TOP→RANGE_distribution_top_bear · LEG_FLAT/NEUTRAL→RANGE_neutral.

## 3. Pernas, âncoras, famílias
- **legs[]**: run maximal de leg_dir; extremos = running max/min (causais, publicados no fecho do run
  via histerese — ZERO retro-confirmação). Registo: {leg_id, dir, t_start, t_end, top_t/px, bot_t/px,
  travel_atr, eff_final, dur_h, macro_regime_at_close}.
- **anchors_ledger**: ao fechar perna/regime → {px, t_known, type ∈ {leg_top, leg_bottom, regime_top,
  regime_bottom}, origin_leg_id}. Âncoras sobrevivem entre pernas e blocos (carry).
  Regra de uso (tese dos 35 prints): BULL = toque OU continuação sem toque · RANGE = só banda bottom ·
  BEAR = só capitulação profunda no bottom do regime anterior (repique raso cortado).
- **family_label** determinística de (macro_regime, leg_dir, leg_phase, retr_fam, d_vale).
  Check de construção: medianas por família ±30% da tabela do catálogo
  (BULL-pullback retr 0,17/drop 2,8/d_vale 0 · BEAR-reversal 0,73/7,4/2 · RANGE-base 0,34/5,8/19).

## 4. Eventos (emitidos ao fecho; **(E11) dois known_at por evento**)
Cada evento carrega `region_known_at` (barra em que o ESTADO qualifica a região válida) e
`floor_known_at` (barra da confirmação mínima de floor). **Confirmação de floor ≠ entry trigger** —
proibido reutilizar como entry na Fase 2 sem re-medição declarada.
1. `BOTTOM_BULL_PULLBACK` — macro BULL, PULLBACK com drop ≥ pb_min; floor = fecho>anterior +
   reclaim curto price-only OU toque de âncora. Fundo = running-min do pullback.
2. `BOTTOM_BEAR_CAPITULATION_END` — macro BEAR, DEEP atingido E TERMINATING; âncora-rule BEAR.
3. `BOTTOM_RANGE_BASE` — macro RANGE, BASE_BOTTOM maduro + toque da banda/âncora inferior.
4. `REJECT_BOUNCE_IN_DOWNLEG` / `REJECT_MICRO` — rejeições explícitas (medem os INVALIDO).
**(E3) PROIBIDO emitir evento em leg_phase IMPULSE ou DISTRIBUTION_TOP (anti-A-BULL). A regra de
entry "BULL continuação sem toque de âncora" pertence à Fase 2, continua a exigir pullback ≥ pb_min
(a isenção é do TOQUE, nunca do pullback) e só nasce com revisão visual do Cris.**
**(E13) Eventos IMUTÁVEIS: ledger append-only, snapshot de todas as colunas congelado no
floor_known_at; evento cujo estado mudaria depois = provisional, NUNCA usável. Âncoras utilizáveis
só para eventos com t ≥ t_known da âncora.**
Colunas do CSV: t_low, px_low, region_known_at, floor_known_at, family_label, macro_regime,
leg_state, retr_fam, d_vale, reject_reason + anotações E7 (smc_cascade_n, choch_recent — nunca
condição) (satisfaz blocker structural-first).

## 5. Constantes
| constante | papel | seed | grid pré-registado |
|---|---|---|---|
| eff_thr / slope_thr / tol_anchor | herança v5 | 0,30 / 0,20 / 0,7 ATR | CONGELADOS |
| M (janela eff, 1H) | eficiência | 15 | {12,15,24} |
| K_up / K_down | histerese | 5 / 5 | {4,5,6} / {3,5} (C8: seed∈grid) |
| D_flush (ATR15) | override | novo | {1,5, 2,0, 2,5} |
| mom (barras 15M) | momentum override | 24 | {16,24,32} |
| pb_min (ATR) | pullback mínimo | novo | {1,0, 1,25, 1,5} |
| deep_thr (ATR) | capitulação | novo | {4,5,6} |
| base_min (barras) | base RANGE | novo | {32,48,64} |
Calibração POR CAMADA (leg_dir vs PLT/DM → eventos vs GT), looks contados no ledger, holdout 1×.
**(E1) Triagem em 2 estágios na camada de pernas (162 combos vs 21 marcas = mining risk):**
estágio 1 = plausibilidade SEM olhar GT (nº pernas/mês, duração mediana, % tempo por estado)
elimina configs degeneradas; estágio 2 = só top ≤20 vão ao matcher PLT/DM; contagem de flips
PROIBIDA como feature de seleção; mining-null do F1.5 (marcas deslocadas cluster-aware) reportado.
**(E6)** Se F1.5 falhar por ≤1 marca com pernas visualmente plausíveis → STOP + arbitragem visual
do Cris (nunca expandir grid às cegas).

## 6. Métricas e alvos (avaliação vs GT, matcher v2: |Δt|≤8h ∧ −3ATR ≤ px_cand−low_GT ≤ +1ATR)
- recall_42 ≥ 36/42 (≥22/26 BULL · ≥10/12 BEAR · RANGE n=4 reportado SEM gate, sempre EXPLORATORY)
  · recall_50 reportado (sem gate)
- **(E5) BEAR = CALIBRAÇÃO, NÃO VALIDAÇÃO** (12 fundos no MESMO episódio bear 2026, autocorrelação;
  validação BEAR real = bear futuro/forward)
- reject_5 = 5/5 (4 INVALIDO + 1 POLARIDADE sem evento válido / emitidos como REJECT_*)
- **(E4) curva recall×FP/dia COMPLETA obrigatória** por família+regime + razão eventos/janela-GT;
  teto estrutural de precisão (densidade sósia 28-108:1) DECLARADO no report; ponto de operação =
  decisão Cris; **gate mínimo: recall observado bate null-de-detector com P ≤ 0,05** — recall alto
  com FP ilimitado NÃO passa
- dist_low mediana ≤2h e ≤0,5 ATR · latency (floor_known_at − t_low) < 1,5h em ≥50% dos BULL-pullback
- Nulls episódicos: (a) null-de-detector dentro da mesma ocupação de estado; (b) null-de-GT
  cluster-aware (deslocamento ±3-10d preservando clusters); (c) mining-null do grid (GT permutado).
  NUNCA permutação por-trade simples. R uncapped onde aplicável.

## 7. Módulos (a criar SÓ após aprovação)
`raw_loader_20260709.py` (gz direto; dedup por bar time com assert OHLC nas bordas; warmup-holes +
carry de estado; SMC/NAS first-appearance com re-seed por bloco; zonas OB resurrection-aware) →
`macro_context_20260709.py` (port v5 + assert paridade) → `leg_state_machine_20260709.py` (streaming)
→ `bottom_events_20260709.py` → `equiv_pltdm_20260709.py` (F1.5 gate) → `calibrate_grid_20260709.py`
→ `evaluate_gt_20260709.py` → `null_episodic_20260709.py` → `da_truncation/da_block_boundary/
da_grid_leakage_20260709.py` → REPORT + claims_ledger.csv → `run_xau_15m_lab_gate.py`.

## 8. Fases e gates
F0 loader+paridade macro (asserts verdes) → F1 máquina de pernas → **F1.5 GATE DURO: ≥9/10 PLT e
≥10/11 DM (matcher ±0,7 ATR, ±2d) — falhou, para e reporta** → F2 calibração de eventos (split) →
F3 holdout 1× + nulls + DA completo → F4 hand-off para lab de entry (SL V1, exit 3R first-touch,
filtro Intra-BEAR = TRANSFER intactos).

## 9. Verificação anti-lookahead (DA obrigatório, zero tolerância)
1. Truncation test: 200 timestamps aleatórios + todos os known_at → recompute truncado == streaming.
2. Grep-assert: nenhum `conf_i`/pivot-confirmation em caminho de decisão (anti zz r=6).
3. known_at ≤ t em todos os eventos SMC; re-seed por bloco sem flood.
4. 8 fronteiras: stitched vs cold-start, convergência ≤ W, zero evento em warmup_flag.
5. Ledger prova que nenhum look tocou holdout; resultado final reproduzível por script único fail-loud.
6. Matcher atacado: recall paralelo com |Δt|≤4h.
7. Paridade macro em toda a interseção temporal.
8. Nada da máquina consome RAW HTF nativo (só agregação price-only interna).

## 10. Fora de escopo deste lab
Entry/SL/exit/sizing (Fase 2) · indicadores como evidência (Fase 3, RAW direto, só DENTRO dos baldes)
· produção/runtime/Telegram/broker (NUNCA sem autorização) · SHORT.

## 11. Correções do DA — v1.2 (C1-C8, vinculantes; detalhe no manifest)
- **C1** paridade de LÓGICA (fixtures sintéticas), nunca contra série primitives-derived (§2.1, §9.7).
- **C2** classificador raw de leg_dir = transposição VERBATIM CONGELADA do `raw_stable()` v5 com
  barra=bucket 1H (E50/E100, slope lb5, s100 lb10, pos N=30, R_thr 2,0, banda 0,15-0,85, cutoffs
  0,55/0,6) — ~10 constantes herdadas congeladas listadas no manifest; **W warmup = 400 barras 15M**;
  **rec_flush = 5×mom** (rácio herdado). Contagem honesta: 10 herdadas + 6 novas em grid. NENHUMA
  constante decidida em tempo de código fora do manifest.
- **C3** estágio-1 pré-registado: janela SÓ pré-holdout (2024-05-25→2025-12-31); bounds congelados
  (pernas/mês [2,20] · duração mediana [8h,120h] · % leg_dir [5%,85%] · FLAT ≤70%); top-20 = menor
  nº de desvios do seed v5, desempate lexicográfico (GT-free).
- **C4** check de construção (medianas ±30%): SÓ marcas de calibração (holdout excluído) e
  REPORT-ONLY até F3.
- **C5** mining-null F1.5 com GATE P≤0,05 + sensibilidade matcher ±0,5d.
- **C6** ponte losers ≤10 declarada em TODO report: teto sósia 28-108:1 ⇒ o engine sozinho NÃO
  atinge a fasquia; gap ~30-70× a fechar nas Fases 2/3.
- **C7** firewall temporal: constantes partilhadas congelam no fim do F1.5 ANTES de qualquer leitura
  BEAR-2026; sequência: F1.5 freeze → BULL calib 2025 → BEAR calib → holdout BULL 1×.
- **C8** latência unificada (stop = mediana >2h; % <1,5h informativa) · retr_fam UNDEFINED na 1ª
  perna pós-warmup (eventos suprimidos) · tol_anchor na banda BASE_BOTTOM = parâmetro novo com valor
  reciclado congelado (declarado) · contingência slope_thr {0,15,0,20,0,25} · caveat: cutoffs
  retr_fam herdam calibração dos 50 círculos ⇒ recall_50 parcialmente auto-realizável (declarado).

## 12. Registo de revisão
v1.0 desenho · v1.1 = edits E1-E13 (critical review) · v1.2 = correções C1-C8 (DA
PARTIAL_REVIEW_INCOMPLETE). GO condicionado à ordem explícita do Cris; paragem obrigatória no F1.5.

## 13. Critério final do Cris + painel obrigatório (E8)
- **Fasquia (ordem Cris 2026-07-09): sinais winners de continuidade SÓ são válidos se os losers da
  estratégia downstream forem reduzidos para ≤10.** Este engine entrega as REGIÕES; a fasquia é
  julgada na Fase 2 — mas fica registada AQUI para que nenhuma fase declare sucesso sem ela.
- Painel final obrigatório em qualquer report com trades: winners preservados · losers restantes ·
  losers cortados · maxDD · losing streak · FP/dia · trades concorrentes · clusters · R com SL V1 +
  exit 3R first-touch · N por família/regime/ano.
- **Revisão visual do Cris OBRIGATÓRIA antes de qualquer upgrade de status** (10_DO_NOT_DO_RULES);
  status language do protocolo §F sempre (nunca "validated" nu).
- Fontes banidas explícitas: `*.primitives.json`, `raw_features_*.jsonl`
  (RAW_FEATURES_IS_NOT_RAW_INDICATOR_SOURCE), CSVs regenerados, `15M/superseded/*` (E12).
