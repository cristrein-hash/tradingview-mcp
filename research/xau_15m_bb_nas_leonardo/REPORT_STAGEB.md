# XAU 15M BB+NAS — RELATÓRIO Stage-B (detector de candidatos)

Fonte: RAW gz 15M exclusivo → `build_causal_primitives.py` → `primitives/*.json` → `detect_candidates.py`.
Source guard PASS. Proveniência registrada (`MANIFEST_PROVENANCE.json`). **Sem backtest, sem regra, sem threshold.**

## Candidatos
- **TOTAL = 791** | cobertura 2024-05-28 → 2026-05-24 (104 semanas / 24 meses).
- Frequência BRUTA: **7.6/semana, 33/mês** — universo NAS-em-zona ANTES de seleção. Alvo 1-3/sem é pós-seleção (não desta etapa).
- Direção: LONG 326 (41%) | SHORT 465 (59%) — consistente com NAS SHORT-leaning do RAW e amostra curada do Leonardo.
- Por bloco: 84–117 (homogêneo nos 8 blocos / 2 anos).

## Campos mapeados ao RAW (todas as colunas do CSV)
zona: zone_type(SUPPLY/DEMAND·all_boxes.text), zone_low/high, zone_width_atr, zone_age_bars, zone_pre_existing, zone_virgin, mitig_count · interação: penetration_pct, bars_in_zone, acceptance_beyond_mid, arrival_atr, nas_dist_ema_atr, dist_edge_atr · NAS: nas_count_in_zone, nas_cluster_span_bars, nas_before_touch · fluxo: op_flow, setup_vs_flow, last_smc, bars_since_smc, smc_bos_choch_50 · contexto: rsi, hour_utc, dow.
**Nenhum campo UNKNOWN_BLOCKED** — todos derivam do RAW. SMC direção: label não carrega direção → fluxo derivado de swing OHLC (mapeável, documentado).

## Famílias do FEATURE_MAP NÃO computadas (por design, não bloqueadas)
- **E (pós-entrada: MAE/MFE/deslocamento/let-run)** e **F (reentry-CHoCH)** = lado-saída/futuro → ficam para a fase de outcome/backtest (proibido agora).

## Sanity (distribuições, sem threshold)
- penetration_pct: q1 0.11 / med 0.51 / q3 0.82 — bom espalhamento (rejeição rasa ↔ consumo).
- bars_in_zone: med 2, q3 4, max 12 — coerente (rápido vs preso).
- zone_virgin True 83%; mitig_count med 0 — maioria zonas frescas.
- nas_count_in_zone med 1, max 5 — bate com PDF (1-5, sweet 2-5).
- rsi bimodal (q1 32 / q3 69) = LONG-demanda baixo + SHORT-oferta alto.
- dist_edge_atr med 0.28 — entrada perto da extremidade (assinatura da estratégia).

## DEVIL'S ADVOCATE — veredito (executado 2026-06-26)
SOUND: RAW exclusivo; zona-viva sem leak (0/2588 ids ressuscitados → presença contígua); swing_flow causal (i+k≤j); entrada SHIFT1; proxy BigBeluga registrado; polaridade correta.
- **FLAW corrigido**: bug de init quando o 1º snapshot do bloco não tinha labels → flood de 500 SMC/NAS fantasmas num timestamp (bloco 2024-08→11). Fix = seed por-stream no 1º snapshot COM labels + assert anti-flood (>10 ev/timestamp). **Verificado: `smc_bos_choch_50` 504 → 9; flood ausente; candidatos 791 inalterados** (NAS fantasmas já caíam por ATR=None).
- **setup_vs_flow** (reversal 515 / continuation 42): DA confirmou detector CORRETO — NAS-em-zona é intrinsecamente fade do swing local (compra DEMAND em down-swing / vende SUPPLY em up-swing); continuation n=42 é sub-população fina. Fato de regime, não bug.

## Itens carregados (NÃO bloqueiam a etapa; tratar antes de SELEÇÃO)
1. **DA#3 — colunas do bar j+1** (`dist_edge_atr`,`entry_dt`,`hour_utc`,`dow`): descrevem o bar de ENTRADA → rótulo/contexto, PROIBIDO usar como filtro de entrada (comentado no código).
2. **DA#5 — tie-break "zona mais estreita"** (11.3% dos candidatos têm ≥2 zonas vivas): favorece R maior por construção → justificar (value-area mais específica) OU teste de sensibilidade (mais larga / mais recente) antes de seleção.
3. **DA#6 — timing pivot-vs-confirmação**: 343/350 preços de NAS caem em bar anterior ao snapshot de confirmação (NAS=detector de pivot); containment usa preço do pivot, entrada usa close de j+1 → lag multi-bar documentado.
4. **DA#5(freq)/overfit**: 791→1-3/sem = corte ~80%. Pré-registrar a seleção como RISK-SHAPING (cortar clusters de loss), NÃO alpha-mining; validar dentro dos 8 blocos (sub-janela/jackknife/null); cap ≤4 features/rodada; nunca lockar threshold na calibração.

## Look-ahead (auditado SOUND)
Entrada=close j+1 (SHIFT1), decisão até close de j; NAS/SMC first-appearance as-of close; zona-viva sem leak (contiguidade verificada); swing causal. Resíduo: NAS pode retrair tardiamente (SHIFT1 só cobre same-bar) — a monitorar.

## Próximos passos (após revisão visual; nada vira regra)
1. Revisão VISUAL de amostra de candidatos no chart (plotar) p/ validar leitura zona+NAS+penetração.
2. Tratar itens carregados 1-4 (tie-break sensibilidade; pré-registro risk-shaping).
3. Só então: features E/F (pós-entrada/reentry) na fase de outcome; depois seleção+risco; depois backtest let-run com DA+checklist-15.
