-- memory_delta_20260720_ob_touch_5m
-- Alerta de toque em zona OB 15M real com timing 5M (fix do trade perdido 4040). Aprovado Cris.
-- Sem secrets. ASCII. Sem ponto-e-virgula no texto.
-- ROLLBACK (via SQL Editor): apagar memory_items com a tag deste seed.
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('ob_touch_5m_timing_20260720')::uuid, 'private', 'private', 'project',
  'Price-shock: alerta de toque em ZONA OB 15M REAL com timing 5M (fix do trade 4040 perdido)',
  'Perdemos o trade do 4040 hoje porque a detecao era 15M e o fecho da barra chegava 8-18pts tarde no spike (o 5M apanhava, a 15M nao). Verificacao do 5M no live: dados 5M frescos (bars + OB Detector + indicadores, 2s), preco 5M live lido a cada 30s pelo price-shock, deteccao de CHOQUE 5M existia (excursao >=10pts) MAS faltava o TOQUE EM ZONA-IMAN no 5M. Config aprovada pelo Cris (a mais simples/barata/eficiente): reutilizar o loop 30s do price-shock (ja le a barra 5M em formacao) + zonas OB Detector 15M REAIS do pine_boxes (pelo CONTEXTUAL_READ_PROTOCOL - NUNCA inventadas, ao contrario do BB/zona-a-mao que foram derrubados). check_ob_touch: quando o preco 5M live ENTRA numa zona OB 15M -> Telegram - a subir para a zona = RESISTENCIA (contexto short), a descer = SUPORTE (contexto long) - dedup por zona (rearma ao sair >2pts) - realca REJEICAO (excursao contra a aproximacao). Custo ZERO (nenhum daemon/leitor CDP novo, as zonas OB ja estao no store 2s frescas). Resolve o 4040: o loop 5M ve o preco entrar na zona OB 4032-4040 e rejeitar -> alerta em tempo real sem esperar o fecho 15M. Tripwire check_no_invented_zones PASSA (le OB real). Testado: toque/classificacao/dedup/rearma OK, preco fora de zona nao dispara. Alert-only, gated L1_PRODUCTION_AUTHORIZED. Live via StartInterval 30s. Commit c37eebd. E a peca base do futuro engine SHORT (toque-e-rejeicao no iman OB).',
  array['seed:memory_delta_20260720_ob_touch_5m','ob-touch','5m','timing','price-shock','iman','fix-4040'],
  'commit c37eebd + my-strategy/core/price_shock/price_shock_cycle.py (check_ob_touch)', 'active')
on conflict (id) do nothing;
