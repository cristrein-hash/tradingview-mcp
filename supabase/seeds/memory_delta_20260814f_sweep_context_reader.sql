-- memory_delta 20260814f — CONTEXTO ESTRUTURAL 4H (sweep-reject/distribuicao) como INFORMACAO no reader
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('sweep_context_reader_info_20260814')::uuid, 'private', 'internal', 'project',
  'CONTEXTO ESTRUTURAL 4H (sweep-reject/distribuicao/retomada) como INFORMACAO no reader',
  'Cris 14/08 (impl A, apos auditar 2 misses): render_composite ganha seccao "# CONTEXTO ESTRUTURAL 4H" que
  CONSOME sweep_reject_guard.verdict (secc. do reader que consome market_context.json). Info pura, nao gate,
  fail-safe. Da ao reader a moldura HTF que faltava: sweep-reject 4H ATIVO = distribuicao no topo -> SHORT na
  rejeicao de lower-high = legitimo (nao "contra-perna"), LONG = faca ate quebra 15M; quebra 15M dada =
  RETOMADA (long estrutural). Motivo: logs de 14/08 mostraram o reader (1) recusar o short do retest 4410 como
  "contra-perna/1a correcao de perna up" ignorando o sweep 4H, e (2) duvidar do reclaim das 06:00 chamando-lhe
  chop/absorcao em vez de quebra de estrutura 15M. Raiz = frame-anchoring na perna local sem contexto HTF de
  1a classe. candle-reader+e2-quality recarregados. Impl B (recalibrar veto contra-perna no prompt) fica p/
  depois com validacao (muda edge).',
  array['seed:memory_delta_20260814f_sweep_context_reader','reader','sweep-reject','contexto-4h','distribuicao','e2_quality'],
  'alert-bridge/e2_quality.py::_sweep_context', 'active')
on conflict (id) do nothing;
