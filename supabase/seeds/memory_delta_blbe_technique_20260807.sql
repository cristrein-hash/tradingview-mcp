insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('blbe_technique_study_20260807')::uuid, 'private', 'private', 'reference',
  'Tecnica em estudo: Buy-Limit-Breakout em Evento (BLBE) - forward N>=5-6',
  'Origem 07/08: Cris usou buy-limit acima do topo antes do NFP; numero gold-positive, ouro +60pts, ganhou (FTMO +689, FN -4.2 para -3.74). Claude avisou contra apostar no NFP mas reconheceu que a tecnica bem-feita REAGE ao break nao prediz o numero - tem merito. Estudar com rigor, nao adotar por euforia de amostra-1. CONDICOES ESTRITAS: (1) alinhada com tendencia (buy acima so em uptrend); (2) so catalisador macro agendado; (3) entrada por CONFIRMACAO nao predicao; (4) risco <=0.5%; (5) nivel+SL fixos ANTES do evento. FALHA: fakeout/whipsaw + slippage; so boa se winners pagam os fakeouts. PREREG: aprovar so com N>=5-6, expectancia>0 a 0.5%, winners sobrevivem aos fakeouts; amostra-1 nao valida; registar TODOS os usos sem cherry-pick. VIES DE RESULTADO: deu-certo=seguro e a mesma logica dos shorts de reversao que custaram -4.2%. Log: research/techniques/buy_limit_breakout_event_log.md.',
  array['seed:memory_delta_blbe_technique_20260807','tecnica','blbe','breakout','forward','estudo'],
  'research/techniques/buy_limit_breakout_event_log.md', 'active')
on conflict (id) do nothing;
