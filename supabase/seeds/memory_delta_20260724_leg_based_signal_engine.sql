-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260724_leg_based_signal_engine
-- ============================================================================
-- Sessao 2026-07-24: motor price-shock (classify_zone) reescrito para DIRECAO=PERNA 1H + regra de zonas +
-- gate de reversao 4H/1D + price-detector gated. Substitui a direcao-por-voto-MTF (custou 3 stops/-2000 FN).
-- + guard fix (isencao /research//memory//docs/) + MEMORY.md tiering 43->27KB. Aprovado + LIVE (alert-only).
-- Aplicar via scripts/supabase/apply_memory_delta.py. Idempotente. Total: 1 row.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260724_leg_based_signal_engine:memory_items:price-shock-leg-based')::uuid,
  'product', 'internal', 'project',
  'Motor price-shock por PERNA 1H + regra de zonas + gate reversao 4H/1D + price-detector gated (Cris 2026-07-24, APROVADO+LIVE)',
  'A direcao-por-voto-MTF (15/60/240) do classify_zone fadava CONTRA o movimento — custou 3 stops / -2000 na conta FundedNext num dia (manha: nao-shortar->caiu; tarde: short->subiu). Diagnostico: o REGIME e contexto ATRASADO, nao direcao; a direcao mora na PERNA viva + fluxo. O Cris definiu a regra nova, implementei e validei, ele aprovou ("APROVADISSIMO"). REGRA (classify_zone, consome so o E0 market_context): (1) DIRECAO = PERNA 1H via _leg_1h — pivo 1H mais recente (low->vies up / high->vies down) CONFIRMADO pelo reclaim/perda das EMAs (micro_15m.ema.pos); se pivo e EMA discordam=virada nao confirmada->mantem a perna dominante (leg.dir). O reclaim das EMAs e a peca que apanha a virada (so HH/HL falhava: PM 2026-07-24 tinha estrutura LH+LL mas era perna de alta, o reclaim virou-a corretamente para BULL). (2) ZONAS: perna BULL->demanda=BUY (continuacao); supply 15M/1H = so marca pullback p/ demanda mais baixa (NAO vende, mode pullback-marker->q=SKIP loga sem alertar); SELL so em supply com OB 4H/1D + confluencias (reversao, gate = "4H" or "1D" in z.ob_htf). Perna BEAR=inverso. (3) QUALIDADE: continuacao anchor=a propria perna; reversao anchor=OB 4H/1D + rejeicao; FORTE=gatilho(excursao no sentido)+anchor+>=2 suportes(inst/fluxo/RSI/macro-ctx)+sem veto-fluxo; so FORTE vai ao Telegram. (4) PRICE-DETECTOR GATED: o choque (>=10pts) so ALERTA no Telegram quando coincide com uma operacao FORTE alinhada (LONG<->ALTA/SHORT<->BAIXA); sem setup, regista shock.json (E0/news) mas NAO alerta. VALIDACAO (Cris dispensou shadow/forward): research/leg_reader_validation_20260724.py = AM flush=BEAR (bateu o flush 4025), PM up-leg=BULL (bateu a subida 4070); research/classify_zone_smoke_20260724.py = 6/6 combos corretos; daemon com.cristrein.price-shock (30s) corre limpo. HIGIENE mesma sessao: removido dead-code _tier1; guard systematic_error_guards passou a isentar /research//memory//docs/+testes (falso-positivo PARALLEL_CONTEXT_BUILD); MEMORY.md tiering 43KB->27KB (detalhe integral preservado no topico/archive). ARBITRO = proximos trades da semana + avaliacao semanal + trades ideais do Cris (ground-truth). commit local.',
  array['seed:memory_delta_20260724_leg_based_signal_engine','price-shock','leg-based-direction','perna-1h','ema-reclaim','zone-rule','reversal-gate-htf-ob','price-detector-gated','regime-nao-e-direcao','fundednext','aprovado-live','user-approved'],
  'my-strategy/core/price_shock/price_shock_cycle.py::classify_zone/_leg_1h/main · research/leg_reader_validation_20260724.py · research/classify_zone_smoke_20260724.py · memoria project_price_shock_leg_based_signal',
  'active'
)
on conflict (id) do nothing;
commit;
