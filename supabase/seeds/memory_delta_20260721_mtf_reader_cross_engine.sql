-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260721_mtf_reader_cross_engine
-- ============================================================================
-- Sessao 2026-07-21: Reader Profundo + Motor de Cruzamento MTF + decisao FRACO/FORTE
-- live; licao recorrente declarar-indisponivel-o-ja-resolvido (bubbles/NAS decode).
-- Aplicar via scripts/supabase/apply_memory_delta.py. Idempotente. Total: 2 rows.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260721_mtf_reader_cross_engine:memory_items:mtf-reader-cross-fraco-forte')::uuid,
  'product', 'internal', 'project',
  'READER PROFUNDO + MOTOR CRUZAMENTO MTF + decisao FRACO/FORTE LIVE (XAU, Cris 2026-07-21; validado visual)',
  'Reset metodologico do Cris apos o sistema perder um BUY grande nos ~4000 (zona DEMAND com apoio HTF) por ler OB so por posicao/aproximacao em vez do TIPO, e por NAO cruzar zonas entre TFs. CONSTRUIDO + VALIDADO VISUAL (Cris PASS 3/3: tipos SUPPLY/DEMAND, tags institucional, niveis BOS/CHoCH). (1) STORE (bar_store_cycle read_tab): capta pine_boxes(verbose).all_boxes TIPADO SUPPLY/DEMAND + SVP POC/VAH/VAL (study_values_at_bar mesclado como estudo SVP Levels) + SMC labels BOS/CHoCH; escrita atomica, backward-compat, daemon StartInterval aplica sozinho. (2) READER (contextual_read.py): _zones tipa por match all_boxes<->zones (round hi/lo 2dp); le o chart TODO por TF (OB/SMC/PO3/Sessions + RSI/DMI/SVP/NAS/Bubbles/CHOP/Volume + BOS/CHoCH). (3) MOTOR (mtf_cross.py cross()): por zona OB tipada 15M = confluencia OB-MESMO-TIPO a sobrepor em 1H/4H/1D (institucional) + SVP-dentro-da-zona + SMC-box + NAS/bubbles ESPACIAIS (join por tempo com bars_15m da PRECO ao evento: NAS LONG->low/fundo, SHORT->high/topo; bubble->faixa low..high, mapa canonico plot_0/2/4=BUY plot_6/8/10=SELL; janela 24h; NAS SHORT em 4070 ja NAO conta p/ DEMAND 4000) + regime (current_regime.json) + RSI multi-TF 5M/15M/1H (alinhamento >=2/3, amortece tremor da barra em formacao) + ADX/CHOP. (4) DECISAO FRACO/FORTE (price_shock check_ob_touch + classify_zone): gatilho = preco 5M entra na zona tipada; DIRECAO pelo TIPO (SUPPLY->SHORT / DEMAND->LONG, NUNCA aproximacao); confirm = excursao >=6pts na direcao certa (rejeicao/reclaim); modo continuacao(regime-align) vs reversao; FORTE = confirm E ancora(institucional na reversao / regime-align na continuacao) E >=2 suportes convergentes [institucional, fluxo, RSI, trend-fit] (canon: convergencia, NAO veto/score). SO FORTE vai ao Telegram, FRACO so loga; slow_pts instrumentado no log p/ calibrar o gatilho lento com DADOS REAIS (nao palpite/overfit). 4 flags auditados c/ Cris: NAS/bubbles->ESPACIAL (resolvido, era remendo direcional); BOS/CHoCH direcao inferida->FORA da decisao (so contexto, ate validar); momentum->RSI multi-TF; regime 1h stale->OK. LIVE alert-only no daemon price-shock (ciclos limpos); Telegram MUTED (.telegram_muted) ate Cris validar em realtime (religar = rm .telegram_muted). DOM/order book = FORA (tick sintetico CFD = ruido, decisao Cris). Commits 1f1d30a/4f395b6/c0b9247 (pushed). PROXIMO: religar + calibrar gatilho-lento e bubbles com slow_pts/nas_n/bub_n reais.',
  array['seed:memory_delta_20260721_mtf_reader_cross_engine','mtf-cross-engine','deep-reader','ob-tipado-supply-demand','spatial-confluence','fraco-forte','price-shock','rsi-multi-tf','live-alert-only','telegram-muted','user-validated'],
  'my-strategy/core/{mtf_cross.py,contextual_read.py,bar_store/bar_store_cycle.py,price_shock/price_shock_cycle.py} · docs project_mtf_deep_reader_cross_engine · commits 1f1d30a/4f395b6/c0b9247',
  'active'
),
(
  md5('seed:memory_delta_20260721_mtf_reader_cross_engine:memory_items:declare-unavailable-antipattern')::uuid,
  'product', 'internal', 'feedback',
  'LICAO RECORRENTE: declarar nao-da/nao-existe o que JA esta resolvido no repo (bubbles/NAS decode) — grep primeiro (Cris 2026-07-21)',
  'Recorrencia da doenca dos 4000, agora sobre o DECODE em vez da zona. Declarei que bubbles nao dava para cruzar honestamente (plots todos Shapes, polaridade por cor nao capturada) quando o mapa canonico buy/sell JA estava em DEZENAS de scripts: plot_0/2/4=BUY S/M/L, plot_6/8/10=SELL S/M/L, plot_12=POC (cp_engine.py, a1_context_build.py, a2_context_build.py). Tambem re-sondei o shape_plots do NAS (plot_0=LONG / plot_1=SHORT) que ja sabia; e mais cedo na mesma frente declarei SVP nao-exposto (era study_values_at_bar) e OB sem tipo (era all_boxes.text verbose). Cris: JA TENS ISSO PRONTO, JA LESTE MILHARES DE VEZES ISSO, BUBBLES E NAS. REGRA DURA: antes de dizer nao-da / nao-capturado / nao-existe -> grep no PROPRIO repo (o decode/mapa quase sempre ja existe la). Declarar-indisponivel-o-ja-resolvido = mesma doenca dos 4000. PRINCIPIO ADICIONAL (Cris): confluencia de fluxo (NAS/bubbles) tem de ser ESPACIAL, ancorada ao preco via join por tempo com as barras, NUNCA proxy direcional-global (isso e remendo grosseiro). Ver feedback_never_invent_read_existing_indicator.',
  array['seed:memory_delta_20260721_mtf_reader_cross_engine','declare-unavailable-antipattern','grep-repo-first','bubbles-nas-decode','spatial-not-directional','recurring-lesson','user-feedback'],
  'memory feedback_never_invent_read_existing_indicator.md · my-strategy/core/mtf_cross.py',
  'active'
)
on conflict (id) do nothing;
commit;
