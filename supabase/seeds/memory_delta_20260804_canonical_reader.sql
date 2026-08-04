begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260804_canonical_reader:memory_items:path')::uuid,
  'product','internal','feedback',
  'CAMINHO DE LEITURA CANONICO PERMANENTE (Cris 2026-08-04 "tem que ser permanente, nao podes errar fluxo e caminho de leitura"): zonas/niveis/indicadores vem SEMPRE do REAL, NUNCA aproximar. Leitor unico market_read.snapshot(tf) = TODOS os indicadores consumindo store_reader',
  'ORDEM PERMANENTE do Cris apos dia -4R causado por zonas aproximadas. REGRA (todo o sessao): qualquer zona/nivel/indicador vem SEMPRE da fonte REAL, nunca aproximada/inferida/inventada. OB Detector v11 = store pine_boxes_{tf}.json (o bar-store capta via MCP periodicamente) OU on-demand data_get_pine_boxes. Indicadores (RSI/SVP/NAS/Bubbles/Volume/SMC) = store study_values_{tf}.json OU data_get_study_values. LEITOR CANONICO UNICO CODIFICADO: alert-bridge/market_read.py -> snapshot(tf) devolve UM snapshot normalizado de TODOS os indicadores REAIS por TF (preco+OB Detector zonas reais+SMC+SVP+NAS+Bubbles+RSI+Volume); CONSOME store_reader (que ja le tudo o que o bar-store capta via MCP); read_line(tf)=linha legivel. ob_zones.py=caminho OB especifico. selftest PASS. Vela/validador/candle-reader/map-sync devem consumir market_read.snapshot, nunca aproximar. O ERRO QUE ISTO TRAVA: em 04/08 construi o trader_map por inferencia/aproximacao (4088-91/4099-4106/4101-16) em vez de ler os boxes reais do OB Detector que JA estavam no store; um short real falhou por 0.36pt de regua inventada + as zonas estavam erradas. NAO foi falta de acesso MCP (o store capta sempre + MCP on-demand com Mac+TV) — foi eu NAO consumir o que existe. Regra-mae: o sistema live TEM acesso; o erro e nao ler. Mapa 04/08 reconciliado ao OB real: supply forte 4090.59-4106.46, supply 4149-4166, demanda/alvo 3995-4010, suporte 4045-4060; todas as zonas declaradas do Cris mantidas em monitoracao. Caveat: SVP nao capturado no store TF15; pine_boxes_240 pode ter dados stale — verificar snapshot()[fresh].',
  array['seed:memory_delta_20260804_canonical_reader','caminho-leitura-canonico-permanente','market_read-snapshot-todos-indicadores','ob_zones-leitor-ob','nunca-aproximar-ler-o-real','store-capta-tudo-via-mcp','consome-store_reader','erro-0.36pt-zonas-aproximadas','sistema-tem-acesso-erro-e-nao-ler'],
  'alert-bridge/market_read.py + ob_zones.py · store_reader.py · trader_map.json · feedback_canonical_reading_path_permanent',
  'active'
)
on conflict (id) do nothing;
commit;
