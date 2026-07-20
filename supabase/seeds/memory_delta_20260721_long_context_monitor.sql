-- memory_delta_20260721_long_context_monitor
-- Monitor de contexto LONG live (advisory) complementando o Cp - alimenta o live, GT futuro.
-- Sem secrets. ASCII. Sem ponto-e-virgula no texto.
-- ROLLBACK (via SQL Editor): apagar memory_items com a tag deste seed.
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('long_context_monitor_live_20260721')::uuid, 'private', 'private', 'project',
  'Monitor de contexto LONG LIVE (advisory) complementando o Cp - mesmo padrao do SHORT, mirror-adaptado',
  'Cris 2026-07-21: apos o monitor SHORT, o mesmo para LONG em live (estudo aprovado + build). Construido no price-shock, enriquece o alerta de toque em zona OB 15M demand (suporte = contexto long) com o dossie E0 (zero MCP, custo ZERO). _long_context le market_context.json, checklist LONG-adaptado + qualidade FORTE/MEDIO/FRACO (realca nunca veta): (1) regime v5+layer1 (BULL/RANGE favoravel) (2) maturidade da down-leg / capitulacao pos_in_leg (exausta>=0.5 vs faca fresca) (3) iman demand testado = o toque (4) RECLAIM-GATE anti-faca = excursao ALTA - SEM reclaim a qualidade cai a FRACO (nao chamar LONG numa faca a cair, licao Cp facas=custo estrutural gate 1o-reclaim) (5) oversold RSI<45 (6) iniciativa BUY confluence. Complementa o Cp (NAO substitui): o Cp cobre a capitulacao mecanica afiada e ja e live, o monitor e o advisory LONG amplo em qualquer toque em demand com reclaim (nota no alerta + dedup por zona para nao spam-duplicar). Vantagem vs SHORT: temos muito mais GT LONG (Cp A1/A2 B MON+FORTE RWS). Caveat honesto: fundos sao MAIS dificeis que topos (MON+FORTE nao identificavel ex-ante por features 15M ~10pct teto) - o monitor da o contexto, a discriminacao fundo-genuino-vs-faca e fraca, o reclaim-gate e o filtro principal. Human-in-the-loop: Cris marca #N long -> journal = GT da estrategia futura. Testado: mock capitulacao=FORTE, sem-reclaim=FRACO(faca). Tripwire passa. Alert-only gated, live StartInterval 30s. Commit f414668. Simetrico ao monitor SHORT (9f4b80b).',
  array['seed:memory_delta_20260721_long_context_monitor','long','monitor','live','advisory','ob-demand','reclaim-gate','complementa-cp'],
  'commit f414668 + my-strategy/core/price_shock/price_shock_cycle.py (_long_context)', 'active')
on conflict (id) do nothing;
