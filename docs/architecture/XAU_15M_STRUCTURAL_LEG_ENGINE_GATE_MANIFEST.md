# GATE MANIFEST — XAU 15M STRUCTURAL LEG ENGINE (lab v1)

> Protocolo: `docs/project_authority/XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1.md` (Stage 1 exige este
> ficheiro em docs/architecture/ — movido do dir do lab no critical review, edit E9).
> Criado 2026-07-09; v1.1 pós `XAU_15M_STRUCTURAL_LEG_ENGINE_CRITICAL_REVIEW_20260709.md` (edits E1-E13).
> Espec congelada: `research/xau_15m_structural_leg_engine/XAU_15M_STRUCTURAL_LEG_ENGINE_SPEC_20260709.md` (v1.1).
> STATUS: PRE-CODE — nenhum módulo escrito até aprovação explícita do Cris.

```json
{
  "lab_name": "xau_15m_structural_leg_engine_v1",
  "strategy": "XAU 15M LONG — detecção estrutural de pernas/fundos/âncoras (máquina do regime detector v5 transposta à escala 15M)",
  "direction": "LONG",
  "timeframe": "15M",
  "raw_files": [
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2024-05-25_to_2024-08-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2024-08-25_to_2024-11-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2024-11-25_to_2025-02-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-02-25_to_2025-05-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"
  ],
  "derived_files": [
    {
      "path": "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/results/catalog_manual_tags_20260707.json",
      "source_ref": "marcação manual do Cris no chart TradingView XAUUSD/15 extraída via MCP em 2026-07-07 (42 notes VELA DE FUNDO + 50 circles + 4 INVALIDO + 1 POLARIDADE_TOPO + 24 ENTRY + 65 trades); ground truth de CALIBRAÇÃO, nunca feature",
      "checksum": "sha256:8171b99d3ae5298116e71b2d8b34cd940a76201fe9283e068b843933954ae59f"
    }
  ],
  "banned_sources_explicit": [
    "*.primitives.json (qualquer)",
    "raw_features_*.jsonl (RAW-features do programa 4H — RAW_FEATURES_IS_NOT_RAW_INDICATOR_SOURCE)",
    "qualquer CSV/JSON regenerado como fonte de dados de mercado",
    "15M/superseded/* (bloco 2026-02-25→05-25 pré-baseline)"
  ],
  "allow_resample": true,
  "resample_clause": "APENAS agregação price-only interna de closes/highs/lows 15M do próprio RAW declarado em buckets 1H (camada estável leg_dir) e 1D FECHADO D-1 (contexto macro v5 hour-causal) — mesmo padrão do engine canónico engine_substrate4_v5_hourcausal.py. leg_phase/eventos/pb_min/d_vale operam SEMPRE em barras 15M nativas (edit E2). PROIBIDO substituir RAW HTF nativo para leitura de indicadores HTF; nenhum indicador HTF é consumido neste lab.",
  "htf_stale_declared": "1D price-agg interna cobre até 2026-07-03 (deriva do RAW 15M, não congela). RAW HTF nativo NÃO é fonte deste lab. Consumidores HTF externos (filtro Intra-BEAR 1D_px_vs_ema) pertencem à camada de ENTRY (lab futuro) e lá declaram freeze 1D 2026-05-24.",
  "structural_buckets": [
    "BULL_impulse", "BULL_pullback", "BULL_excess_top",
    "RANGE_neutral", "RANGE_distribution_top_bear", "RANGE_accumulation_bottom",
    "BEAR_active", "BEAR_shallow_bounce", "BEAR_deep_capitulation",
    "countertrend_bounce_in_bear", "management_do_not_filter"
  ],
  "emission_policy_v1": "emissão de eventos 100% price-only (edit E7); SMC/CHoCH/NAS/Bubbles/OB = colunas ANOTADAS com known_at, avaliadas como evidência SÓ na Fase 3 dentro de baldes; eventos PROIBIDOS em leg_phase IMPULSE ou DISTRIBUTION_TOP (edit E3, anti-A-BULL); eventos IMUTÁVEIS append-only, snapshot congelado no known_at; evento que mudaria = provisional, nunca usável (edit E13)",
  "outputs": [
    "/Users/cristrein/tradingview-mcp/research/xau_15m_structural_leg_engine/results/leg_engine_events.csv",
    "/Users/cristrein/tradingview-mcp/research/xau_15m_structural_leg_engine/results/leg_engine_legs.csv",
    "/Users/cristrein/tradingview-mcp/research/xau_15m_structural_leg_engine/results/gt_evaluation.csv"
  ],
  "claims_ledger": "/Users/cristrein/tradingview-mcp/research/xau_15m_structural_leg_engine/claims_ledger.csv",
  "scripts": [],
  "grid_preregistered": {
    "frozen_inherited_v5": {"eff_thr": 0.30, "slope_thr": 0.20, "tol_anchor_atr": 0.7},
    "classifier_raw_frozen_verbatim_v5": "transposição VERBATIM congelada do raw_stable() do engine v5 com barra=bucket 1H (correção DA C2): E50/E100, slope lookback 5, s100 lookback 10, pos sobre N=30 buckets, R_thr 2.0, banda 0.15-0.85, cutoffs 0.55/0.6, regras de decisão idênticas — ~10 constantes HERDADAS CONGELADAS, listadas para contagem honesta; nenhuma constante decidida em tempo de código fora deste manifest",
    "W_warmup_bars_15m": 400,
    "rec_flush": "5 x mom (rácio herdado do override 1H do v5: rec120/mom24) — derivado, não novo parâmetro",
    "M_eff_window_1h": [12, 15, 24],
    "K_hysteresis_up": [4, 5, 6],
    "K_hysteresis_down": [3, 5],
    "D_flush_atr15": [1.5, 2.0, 2.5],
    "mom_bars_15m": [16, 24, 32],
    "pb_min_atr": [1.0, 1.25, 1.5],
    "deep_thr_atr": [4, 5, 6],
    "base_min_bars": [32, 48, 64],
    "protocol": "calibração POR CAMADA com triagem em 2 estágios (edit E1): estágio 1 = plausibilidade GT-free; estágio 2 = só top<=20 configs vão ao matcher PLT/DM; contagem de flips PROIBIDA como feature de seleção; TODOS os looks (inclusive estágio 1) no claims ledger; holdout lido 1x",
    "stage1_preregistered": "correção DA C3 — janela de medição SÓ pré-holdout (2024-05-25 a 2025-12-31); bounds congelados: pernas/mês em [2,20], duração mediana de perna em [8h,120h], % tempo por leg_dir em [5%,85%], LEG_FLAT <=70%; ordenação do top-20 = menor nº de desvios do seed v5, desempate lexicográfico determinístico (GT-free)",
    "mining_null_f15": "recall PLT/DM do melhor config re-medido sob marcas deslocadas cluster-aware — GATE P<=0.05 (correção DA C5) + linha de sensibilidade com matcher apertado ±0.5d reportada",
    "contingency_preregistered": "se Fase 1.5 falhar com herdados congelados, abrir eff_thr {0.25,0.30,0.35} E slope_thr {0.15,0.20,0.25} (correção DA C8) custa +looks declarados no ledger ANTES de correr; se falhar por <=1 marca com pernas visualmente plausíveis, STOP + arbitragem visual do Cris em vez de expandir grid (edit E6)"
  },
  "calibration_splits": {
    "leg_layer": "PLT/DM ago-out/2025 (janela independente dos 42 fundos); fasquia >=9/10 PLT e >=10/11 DM",
    "events_BULL_pullback": "calibra 13 primeiros (2025-04 a 2025-12), holdout 13 de 2026 (lido 1x)",
    "events_BEAR_reversal": "6 primeiros de mar/2026 + 6 restantes — AMBOS = CALIBRAÇÃO, NÃO VALIDAÇÃO (edit E5: mesmo episódio bear, autocorrelacionado; validação BEAR real = bear futuro/forward)",
    "events_RANGE_base": "n=4 total => SEMPRE EXPLORATORY, nunca gate",
    "circles_50": "camada secundária de recall — NUNCA calibração; CAVEAT declarado (DA C8): cutoffs retr_fam {0.5,1.3} herdam calibração feita nos 50 círculos em lab anterior => recall_50 parcialmente auto-realizável; cutoffs CONGELADOS, nunca re-fitados aqui",
    "trades_65": "FORA deste lab (21/65 timestamps corrompidos; re-derivar antes do lab de entry)",
    "temporal_firewall": "correção DA C7 — as constantes PARTILHADAS da camada de pernas (M, K_up, K_down, D_flush, mom) CONGELAM no fim do F1.5, ANTES de qualquer leitura de marcas BEAR-2026 (que vivem dentro da janela do holdout BULL-2026); nenhuma iteração nessas constantes guiada por performance BEAR; sequência obrigatória: F1.5 freeze -> eventos BULL calib 2025 -> BEAR calib -> holdout BULL 1x",
    "construction_check": "correção DA C4 — check de medianas por família (±30%) recomputado SÓ sobre marcas de CALIBRAÇÃO (13 BULL 2026 do holdout EXCLUÍDAS) e rebaixado a REPORT-ONLY (sem poder de rejeição) até F3",
    "retr_fam_bootstrap": "correção DA C8 — na 1ª perna pós-warmup retr_fam=UNDEFINED e eventos suprimidos até a 1ª perna estável fechar (L0 indefinido não inventa valor)"
  },
  "report_gates": {
    "recall_42_target": ">=36/42 global; >=22/26 BULL; >=10/12 BEAR(calibração); RANGE reportado sem gate",
    "reject_5": "5/5 (4 INVALIDO + 1 POLARIDADE sem evento válido ou emitidos como REJECT_*)",
    "fp_curve_mandatory": "curva recall x FP/dia completa + razão eventos/janela-GT por família e regime (edit E4); teto estrutural de precisão (densidade sósia 28-108:1) DECLARADO; ponto de operação = decisão do Cris",
    "null_detector_gate": "recall observado tem de bater null-de-detector (amostragem uniforme dentro da mesma ocupação de estado) com P<=0.05 (edit E4)",
    "dist_low": "mediana |dt|<=2h e |dpx|<=0.5 ATR",
    "latency": "UNIFICADA (DA C8): stop se MEDIANA (floor_known_at - t_low) > 2h nos BULL-pullback; % com latencia <1.5h reportada como informativa (sem gate)"
  },
  "success_criteria_final": {
    "cris_bar": "sinais winners de continuidade SÓ são válidos se os losers da estratégia downstream forem reduzidos para <=10 (ordem Cris 2026-07-09)",
    "losers_bridge_arithmetic": "correção DA C6, DECLARAÇÃO OBRIGATÓRIA EM TODO REPORT: com densidade sósia:winner 28-108:1, o teto de precisão evento-nível deste engine é ~1-3%; a fasquia losers<=10 exige precisão downstream da ordem de >70% => o ENGINE SOZINHO NÃO ATINGE A FASQUIA; as Fases 2/3 têm de fechar um gap de ~30-70x; omitir esta declaração = violação",
    "final_panel_mandatory": "winners preservados · losers restantes · losers cortados · maxDD · losing streak · FP/dia · trades concorrentes · clusters · R com SL V1 + exit 3R first-touch · N por família/regime/ano",
    "visual_review": "revisão visual do Cris OBRIGATÓRIA antes de qualquer upgrade de status (10_DO_NOT_DO_RULES: não promover sem visual review); status language protocolo §F sempre"
  },
  "stop_conditions": [
    "HD externo desmontado => BLOCKED (nunca fallback para qualquer store derivado)",
    "Fase 1.5 PLT/DM abaixo da fasquia apos contingencia declarada => STOP e reportar ao Cris (nao avancar para eventos)",
    "truncation test falha em qualquer timestamp => STOP imediato (lookahead)",
    "paridade de LOGICA do port v5 falha (fixtures sinteticas deterministicas) => STOP (port defeituoso); correção DA C1: PROIBIDO correr/comparar contra serie derivada de primitives — paridade e de CODIGO (funcoes portadas verbatim + testes em fixtures), nunca de dados primitives-derived; divergencia em dados reais RAW vs memoria historica do canonico = investigar FONTE antes de declarar defeito",
    "divergencia OHLC em sobreposicao de borda de bloco => STOP fail-loud",
    "latency floor_known_at mediana > 2h nos BULL-pullback na F2 => reportar e aguardar decisao do Cris antes de F3",
    "qualquer necessidade de pivot confirmado-por-rally => STOP (proibido; redesenhar)",
    "qualquer evento emitido em IMPULSE/DISTRIBUTION_TOP => bug, STOP",
    "producao/runtime/Telegram/broker => NUNCA (fora de escopo)"
  ]
}
```

## Notas
- **PROIBIÇÕES ativas (Cris 2026-07-09):** primitives como fonte (qualquer uso), zigzag por rally
  N·ATR como estrutura, port de features 4H como solução 15M. Este lab lê exclusivamente os 9
  `.jsonl.gz` acima + o GT declarado.
- Warmup-holes ~24h nas 8 fronteiras de bloco: carry do vetor de estado + eventos suprimidos por W
  barras pós-gap; GT em janela de warmup = `UNSCORABLE` explícito.
- Âncoras: utilizáveis apenas para eventos com t ≥ t_known da âncora (edit E13).
- Blockers: `check_xau_15m_raw_lineage.py` → `check_xau_15m_structural_first.py` →
  `check_xau_15m_claims_ledger.py` → `run_xau_15m_lab_gate.py` = `XAU_15M_LAB_GATE_PASS`.
- Critical review: `research/xau_15m_structural_leg_engine/XAU_15M_STRUCTURAL_LEG_ENGINE_CRITICAL_REVIEW_20260709.md`
  (+ DA da auditoria no mesmo dir).
