# XAU 15M LONG — MTF STRUCTURAL SIGNATURE · DISCOVERY (2026-07-04)

**Status: EXPLORATORY_CALIBRATION sobre HINDSIGHT_TARGET_SET** (não é validação, não é produção, não é aprovação).

## Origem
Cris plotou manualmente no chart 15M as **35 operações que ELE faria** (ago-2025→fev-2026; extraídas via MCP read-only, `extract_cris_trades_20260704.py`). Moldura obrigatória do DA: entries ancorados retroativamente no fundo do flush (mediana 0,83R abaixo do preço disponível) — nenhum outcome delas é evidência de edge; elas definem o ALVO de reconhecimento. Painéis honestos só para escala: market@âncora +35,3R WR86; limit-forward +18,3R WR73 (13 no-fill).

## Universo do mapeamento
35 trades-alvo vs **1.107 controles** (candidatos flush do universo SELADO na mesma janela, >24 barras de distância). Timeframes: **15M (oficial) + 30M + 1H** (primitives/bubbles sandbox via builder canônico re-alvo; mapping de bubbles auditado BUY-up% ≫ SELL-up% nos 2 TFs). Indicadores mapeados: estrutura (RSI/EMA21-dist/box96/volume-percentil) · NAS (direção/recência/contagens) · SMC (recência CHoCH/BOS — **sem direção**, bug conhecido do builder, declarado) · zonas Custom OB (demand/supply ativas, distâncias em ATR, inside) · Bubbles por lado/tamanho (absorção SELL-M/L, iniciativa BUY-M/L, net ponderado). **SVP indisponível** (blocos RAW da janela não capturavam SVP — só o 9º bloco tem).

## Perfil causal dos 35 (vs base435)
Mesmo substrato de fundos (35/35 casam com flush ≤24 barras), seleção diferente: **swept 43% vs 100% exigido** · legpos60 0,38 vs 0,49 · h1_pos 0,60 vs 0,78 · box96 0,55 vs 0,78 · ema21_dist 0,42 vs 0,65 · rec_speed 0,41 vs 0,69. Cobertura dos sinais atuais: 1/35 base435 · 0/35 Sistema A · 7/35 FB2-fundo. Regimes: 22 BULL / 9 RANGE / 4 BEAR.

## ASSINATURA ENCONTRADA
**`supply_far_3atr(15M) AND demand_near_1atr(1H)`** — céu limpo no TF de execução (sem supply OB ativo a <3 ATR acima) + demanda OB de 1H a ≤1 ATR abaixo (ou dentro dela).
- Cobertura: **60% dos 35 (21/35; CI95 ~42-75%)** vs 7,3% dos controles no cj.
- **Lift corrigido pelo DA: 5,7-6,7×** (o 8,2× bruto tinha viés de maturidade dos controles; corrigido com controles deslocados +4/+12/+20 barras — piso 5,7×).
- **Null de multiplicidade (200 reps, pipeline integral replicado em pseudo-conjuntos): melhor par jamais passou de 2,18× → P(≥8,2×|H0)=0/200; P<0,005** mesmo para o valor corrigido.
- Causalidade das zonas OB verificada CONTRA O RAW (lifecycle first-appearance; presença contígua; bounds imutáveis; 5/5 spot-checks).
Camadas sugestivas (não passaram o gate do null, N baixo): demanda 30M+1H empilhada 3,1× · inside_demand 1H 3,5× · CHoCH 15M ≤24b (80%, 1,5×) · absorção SELL-M/L 1H 3,3× · **anti-iniciativa** (BUY-M/L recente = lift inverso 0,6-0,7× — ele compra o dip QUIETO).

## Artefatos
KEEP (commitados): `extract_cris_trades_20260704.py` · `analyze_cris_trades_20260704.py` · `map_cris_trades_indicators_20260704.py` · `plot_system_a_53.py` · JSONs pequenos (`cris_manual_trades/cris_trades_analysis/cris_trades_mtf_indicator_map`) · DA scripts (`_DA_cris_trades_{1..3}`, `_DA_mtf_*`) · sobras Lab B r2 (`_labB2_step*`, `reports/_lab_b_r2_*`, `results/_labB_r2_*`). TEMP (path registrado, regenerável): sandbox 30M/1H primitives+bubbles em scratchpad `mtf_sandbox/` (builders `build30/build60/bub30/bub60.py` = builder canônico re-alvo; política do repo não versiona primitives) · `base4_maturation_features.json` · universo `lab_g_candidates.jsonl` (selado por sha commitado).

## Próximos passos
Teste formal como GATE no universo selado com exit-engine e painel completo (bloco `XAU_15M_LONG_MTF_SIGNATURE_GATE_TEST`, prereg-first, thresholds congelados 3 ATR/1 ATR) — autorizado pelo Cris 2026-07-04.
