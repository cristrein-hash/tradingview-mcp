-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260707_contextual_filter_wall
-- ============================================================================
-- Bloco: leitura visual validada (winners/losers) + filtragem contextual = muro de poisoning (2026-07-07).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260707_contextual_filter_wall'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260707_contextual_filter_wall:memory_items:filtro-contextual-poisoning')::uuid,
  'product', 'internal', 'project',
  'Leitura visual dos 96 entries VALIDADA pelo Cris (winners=markup jovem, losers=3 modos macro) + filtragem contextual = MURO de poisoning (features atuais nao cortam losers sem matar winners)',
  'Cris analisou 22 prints (#1-#96) e VALIDOU a leitura: WINNERS = pullback-a-demanda em perna de markup JOVEM/MEDIA (higher-low + BOS/CHoCH-up + VELA DE FUNDO + reclaim rapido R + perna nao esticada ao topo). LOSERS = 3 modos macro-contextuais = EXATAMENTE as 3 marcas de invalido do Cris: (1) exaustao de topo macro ("POLARIDADE TOPO": #21,#23,#31,#55,#65,#83,#85); (2) range/chop sem tendencia p/ 3R (#56-60,#5-8R); (3) perna bear macro ativa ("FUNDO NAO VALIDO POIS PERNA BEAR CLARA ANTECEDE": #66,#69,#93,#94,#89R; "FUNDOS PEQUENA ACUMULACAO": #49,#50R). markup=MASTER; reclaim-R so qualifica dentro dele (#64R/#77R/#89R/#93R sao R e vermelhos em topo/range/bear). CORRECAO HONESTA: o estudo de caso numerico anterior ("exaustao nao separa, bear refutado") estava ERRADO por medir escala errada (leg_pos micro-15M, EMA diaria lenta); a leitura visual macro prova que exaustao-topo e perna-bear SAO os grandes viveiros de losers (mesma miopia macro->micro). ALINHAMENTO: 96 entries recomputados = trades #1-#96, 32/32 outcomes alinhados = ground-truth limpo. BATERIA de 12 features macro/estruturais + ranking AUC (feature_battery_20260707.py): slope_emaD mais forte (exaustao: losers slope 20d-EMA +38 vs winners +14) MAS filtrar slope>30 ENVENENA (corta 23 losers matando 22 winners porque markup forte tem slope ingreme); supply_above (room-a-supply) AUC 0.619 dentro-de-R -> R&supply>=0.35 = 72% hit-3R N25 ambos-anos+ MAS corta ~9 winners fortes (romperam supply proxima) p/ ~10 losers = ~1:1 poison; range-demand-no-fundo REFUTADO p/ 3R (pos_in_20d 0-0.33 = 14% hit-3R, bounce de fundo de range so vai ~1R ate o topo). ACHADO CENTRAL: NENHUMA feature corta losers sem matar winners na mesma proporcao (~1:1) — winners e losers COEXISTEM no espaco de features; os winners de markup forte tem a MESMA assinatura macro (slope, supply proxima, bear) que os losers porque sao os que ROMPERAM. A distincao visual do Cris ("esta perna tem momentum p/ romper?") NAO esta nas features atuais = MESMO MURO do PLT/DM (leitura visual > features disponiveis). ESTADO LIMPO: markup master 54.2% -> reclaim-R 61.4% (ambos anos+, Cris-validado, nao-envenenado). Room-supply = DIAL de risco opcional (72% trocando winners; exaustao ex-ante defensavel pois nao sabes ex-ante quem rompe), decisao Cris. Diferenciacao fina (bull-genuino-em-bear / range-demand / exaustao-sem-poison) = precisa read visual do Cris OU features de momentum-de-rutura da perna que nao temos. LICAO DE METODO: com ground-truth rotulado, ranquear features por AUC em vez de impor proxy; e verificar poisoning (winners cortados) antes de declarar filtro, nunca so o hit-rate.',
  array['seed:memory_delta_20260707_contextual_filter_wall','filtro-contextual','poisoning-wall','leitura-visual-validada','exaustao-slope','room-supply-dial','range-demand-refutado','ground-truth-96','licao-metodo'],
  'docs/architecture/XAU15M_ENTRY_CONTEXTUAL_FILTER_STUDY_20260707.md; feature_battery/entry_macro_context/entry_struct_state_20260707.py (commit aab6f62)',
  'active'
)
on conflict (id) do nothing;

commit;
