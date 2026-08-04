begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260804_5m_off:memory_items:5m')::uuid,
  'product','internal','decision',
  'Candle-reader: leitura Opus 5M PARADA (ordem Cris 2026-08-04 fim-do-dia) — le so 15M+1H no fecho; mata saturacao Opus (~200 reads/dia de velas mortas) e protege o caminho de sinal de rate-limit',
  'Cris ordenou parar a leitura de 5min do candle-reader (revisao tinha anotado saturacao Opus como pendente-mantido-por-ordem-B; Cris reverteu a parte do 5M). TFS agora {15, 60-agregado}; prioridade 60>15. O 5M CONTINUA capturado no bar-store (bars_5m.jsonl) e disponivel ao validador/liquidez como contexto — so o read Opus por vela 5M parou. Ganho: fim da saturacao (~200 reads/dia de velas 5M mortas), caminho de sinal (E2 + consults vela + reads 15M/1H) com capacidade folgada, 15M/1H sempre a tempo. selftest PASS, daemon recarregado. Config final do candle-reader p/ a vigilia Asia: Opus le 15M+1H no fecho com leitura canonica de todos os indicadores; Telegram so confirmado.',
  array['seed:memory_delta_20260804_5m_off','candle-reader-5m-parado','le-so-15m-1h','fim-saturacao-opus','5m-continua-no-store-como-contexto','ordem-cris-fim-do-dia'],
  'alert-bridge/candle_reader.py · project_candle_reader_constant',
  'active'
)
on conflict (id) do nothing;
commit;
