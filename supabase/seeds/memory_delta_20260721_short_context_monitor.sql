-- memory_delta_20260721_short_context_monitor
-- Monitor de contexto SHORT live (advisory, human-in-the-loop) - alimenta o live, NAO constroi estrategia.
-- Sem secrets. ASCII. Sem ponto-e-virgula no texto.
-- ROLLBACK (via SQL Editor): apagar memory_items com a tag deste seed.
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('short_context_monitor_live_20260721')::uuid, 'private', 'private', 'project',
  'Monitor de contexto SHORT LIVE (advisory, human-in-the-loop) - alimenta o live, GT para estrategia futura',
  'Cris 2026-07-21: abrir o bloco SHORT SO para alimentar o live, NAO construir/validar estrategia ainda. Construido no price-shock (reutiliza o loop 5M + le o dossie E0, zero MCP, custo ZERO). Enriquece o alerta de toque em zona OB 15M REAL (resistencia = contexto short) com um checklist de 6 fatores REAIS + qualidade FORTE/MEDIO/FRACO que REALCA nunca VETA (o Cris e o arbitro, os 3 pontos confirmados por ele). _short_context le market_context.json: (1) regime v5+layer1 (BEAR/RANGE favoravel) (2) maturidade da perna de alta pos_in_leg (madura>=0.5 vs 1a pullback imatura=a trap) (3) iman testado = o proprio toque na zona OB Detector (4) rejeicao = excursao 5M contra a subida (5) esticamento RSI vs MA (6) iniciativa vendedora confluence. Encoda os 2 exemplos: 4040=FORTE (perna madura pos0.83 + iman + rejeicao + RSI66 esticado + SELL), sexta=FRACO (perna imatura = 1a pullback). Alerta 5M timing zona 15M. Human-in-the-loop igual ao AMD: Cris le -> decide -> entra manual -> marca #N short -> journal aprende = esses marks viram o GT da estrategia SHORT FUTURA (nao mecaniza nada agora). Tripwire check_no_invented_zones PASSA (le OB Detector + E0 reais, zero invencao). Alert-only, gated L1_PRODUCTION_AUTHORIZED, live via StartInterval 30s. Commit 9f4b80b. PROXIMO (pedido Cris): estudo para fazer o MESMO com LONG em live (mirror-adaptado, aproveitando Cp/A1A2/B/MON+FORTE ja existentes).',
  array['seed:memory_delta_20260721_short_context_monitor','short','monitor','live','advisory','ob-touch','human-in-loop'],
  'commit 9f4b80b + my-strategy/core/price_shock/price_shock_cycle.py (_short_context)', 'active')
on conflict (id) do nothing;
