insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('gold_capitulation_recovery_pattern_20260805')::uuid, 'private', 'private', 'reference',
  'Padrao das recuperacoes macro do ouro (RAW 1D 2012-2026, 15 capitulacoes) — prioridades de vigia pos-fundo 4007',
  'Estudo 05/08 (script my-strategy/research/gold_macro_recoveries_20260805.py, RAW 1D HD 3635 sessoes): apos fundo de capitulacao (queda >=8% do pico 90d), a perna 1 dispara e devolve em RECUO MEDIANO ~68% da perna (rasos 19-42%, fundos 97-99%; ~4.4% do preco; 3-22 sessoes). Fundo de capitulacao SEGURA em 14/15 (excecao 2020-11); continuacao para cima em 13/15. Gemeos do atual: 2013-06 (68%), 2022-09 (98% segurou e disparou), 2026-03 (fundo 4099->4602, recuo 50% em 1 dia). APLICACAO ao fundo 4007 de 29/07: perna 4007->4167+ (topo ainda nao confirmado; pode estender 4183-4203/4337-82). Topo ~4167 -> recuo mediano ~4058-4070 (= demanda 4060-66); raso ~4100-4124. Topo ~4200 -> mediano ~4070-4090. CENARIO-BASE: recuo grande SEM quebrar 4007 = reteste classico pre-subida sustentada, nao bear de volta. Base do recuo = zona de caca A1/A2 + L2; quebra de 4007 = excecao 1/15, reavaliar tudo. Cris 05/08: prioridades de monitoracao racionais embasadas em dados reais.',
  array['seed:memory_delta_gold_recovery_pattern_20260805','ouro','capitulacao','recuperacao','padrao-macro','a1a2','l2'],
  'my-strategy/research/gold_macro_recoveries_20260805.py · memory/reference_gold_capitulation_recovery_pattern.md', 'active')
on conflict (id) do nothing;
