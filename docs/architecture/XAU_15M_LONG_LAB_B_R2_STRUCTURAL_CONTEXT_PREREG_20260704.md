# LAB B r2 — STRUCTURAL CONTEXT · PRÉ-REGISTRO (2026-07-04, ANTES da execução oficial)

**Bloco:** XAU_15M_LONG_LAB_B_R2_STRUCTURAL_CONTEXT_CONVERGENCE · research-only / prereg-first / multi-agent / LONG-only · sem produção/Telegram/runtime/chart/plot/RAW-write. Famílias = derivadas do discovery (`..._DISCOVERY_20260704.md`, workflow `wf_6e643ea3-184`), congeladas AQUI antes da medição oficial.

## 1. Strategy scope
XAU 15M LONG only · base #4 · baseline N435 · detector v5h retido (regime = mapa/rota, nunca direção) · SB $0,80 obrigatório · sem SHORT · sem produção. Separações: F4=sizing de conta · C=SL · D=re-entry · Sistema A=hipótese separada aguardando não-BEAR.

## 2. Source/data mapping
- Universo canônico SELADO: `results/lab_g_candidates.jsonl` (sha256 `f27fb229...` em `results/lab_g_candidates.sha256`; preâmbulo do script verifica sha+counts fail-loud). BASE = `g_in_base435==1 AND g_v5h!='BEAR'` (N435).
- Campos: legpos60/90, h1_pos, n_supply_overhead, clean_sky_atr, h1n/h4n_clean_sky_atr (sentinela 99 tratada), g_box96/480, g_ema21_dist/50, dist_demand_atr, in_demand, g_v5h, g_R, g_risk, g_week, cj_t, yr.
- `base4_maturation_features.json` (join cj_t==t, 435/435): room_above, ext_ema, pos20 etc.
- `results/_labB_r2_regime_box_feats.json` (435 rows por cj_t): rbox_pos/rbox_age_h/rbox_hi_dist_atr/prev_hi_dist_atr/prev_state/prev_len_h — **causalidade sujeita a ASSERT automatizado** (recompute truncado em cj_t via engine; divergência → FB3=BLOCKED_BY_MAPPING).
- Episódio/cluster: cadeia gap≤96 barras (canon labs). Lineage RAW-only, zero SLIM; source guard PASS 7/7 (calibrado 2026-07-04).

## 3. Baseline reproduction (fail-loud)
N435 · +291,5 bruto · **+233,6 NET-SB** · WR_liq 46,0 · DD −14,2 · r/DD 16,4 · stk −8 · **runners 53** · anos 13,6/183,4/36,6. Não bater → PARAR.

## 4. Famílias congeladas (predicados do discovery, verbatim; thresholds = quantis DA BASE, declarados CALIBRAÇÃO)
- **FB1 ANTI-VETO TETO** (CONTEXT_CLASS proteção): componentes conv4/box96top[0,906-0,947)/legtop legpos90≥0,804/htfceil/rb_p1/rb_p2/rb_p3 — medição oficial: cobertura, DEDUP par-a-par (componente com <30% membros novos = re-rotulação, kill), painel do conjunto protegido. Nada é removido; canon: nenhuma lente futura pode SKIP/size<1,0 nesses trades.
- **FB2 FUNDO_EARLYLEG** (`legpos60≤0,25 AND h1_pos≤0,61`): flagged panel · counterfactual SKIP (REPORTADO MAS BLOQUEADO — DA-pré) · **variante acionável = SIZE_50 (floor 0,5)** · overlap com F4 chain_pos (kill iii: >50% dupla-taxação) · nulls (random-skip week-aware 500 · size-null 500).
- **FB3 RB_LIMBO** (`BULL AND −10<prev_hi_dist_atr≤−2 AND (n_supply_overhead≥16 OR 178<rbox_age_h≤415)`): assert de causalidade → flagged/SKIP-counterfactual panels + null week-aware. Status: CANDIDATE prateleira (kill-criteria do discovery).
- **FB4 CLASSES F4** (`QUICKPOP room_above≤1,11` · `KNIFE_RUNNER g_ema21_dist≤0,16`): anotação/painéis por classe; zero eliminação; overlap com FB1 medido.
- **FB5 FORWARD-LEDGER**: congelar LISTAS EXATAS de cj_t por entrada (CONV1/EXT/CAL3_DVOID/CAL4_B480/H4_MIDLID) + regra pré-registrada (promover a SKIP sse flagged-forward NET<0 E runner-kill-forward=0 com N≥15; demover sse flagged-forward ≥ não-flagged). DEADMID = KILL (registrado).

## 5. Nulls
random-skip mesmo-N **week-aware** (500; matched por semana ISO) · size-null (SIZE_50 aleatório mesmo-N, 500) · episode-aware onde couber · sanity por ano · runner-preservation como gate (não null) · bruto+SB sempre · ledger: ~100 looks do discovery DECLARADOS — nenhum p-value desta rodada é validação (CALIBRAÇÃO; árbitro = extensão RAW futura).

## 6. Metrics
N kept/flagged · WR_liq · sumR bruto/NET · avgR · DD · r/DD · streak · runners kept/lost · losers cut · retention % · por-ano · jackknife-episódio · impacto nos clusters/loss-runs · FN-proxy (WR/streak/DD).

## 7. Acceptance criteria (congelados)
Avança se: melhora material WR/streak/DD **E** retém ≥75% SB-net (salvo risk-control explícito) **E** preserva runners (kill 2026 = veto automático) **E** não depende de poucos episódios (>15% delta) **E** bate nulls **E** DA não rebaixa. Classificações possíveis: STRUCTURAL_CONTEXT_EDGE_FOUND · STRUCTURAL_REVIEW_LAYER_FOUND · RISK_CONTROL_ONLY · NO_CONTEXT_SOLUTION · BLOCKED_BY_MAPPING · DEFERRED_HTF_STALE.

## 8. Forbidden interpretations
room_above sozinho como filtro · cortar bucket que carrega lucro/runners (canon FB1!) · supply visual como hindsight · macro-BEAR veto · concluir produção · SHORT · alterar gates/detector · promover SKIP de FB2/FB3 nesta rodada (forward-ledger obrigatório).

## 9. Outputs
Script `lab_b_r2_structural_context_analysis.py` · `results/lab_b_r2_structural_context_results.csv` + `_summary.json` (pequenos, com listas de membros do ledger) · DA `..._DA_20260704.md` · report `..._REPORT_20260704.md` · commit `"Evaluate XAU 15M long structural context lab"` — sem push sem autorização.
