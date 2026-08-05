insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('continuation_doctrine_gold_uptrend_20260805')::uuid, 'private', 'private', 'feedback',
  'DOUTRINA DE CONTINUACAO (Cris 05/08): ouro em alta = mentalidade de continuacao, nunca reversao',
  'Licao do dia 05/08 (+200pts 4060-4265 sem parar; dia inteiro cacando reversao = zero trades bons): (1) PARAR busca de reversao - reversao SO analisavel em regiao 4H/1D com CLARA rejeicao macro (unica no mapa: 4337-4382); (2) monitoracao 5M PARADA (fast-5M removido); (3) foco total = COMPRAS em pullbacks CURTOS com continuidade confirmada nas velas 15M (A1/A2 = motor; suporte 4138-4166 = ex-supply rompida); (4) zonas de venda intradia removidas do mapa, tese_geral = LONG/continuacao; (5) doutrina escrita no TAPE_SYS do candle_reader. ORDEM PESSOAL AO CLAUDE: Cris declara dificuldade propria com vies de reversao e pede que o Claude SINALIZE E QUESTIONE sempre que ele (ou detetor) sugerir venda contra tendencia fora da condicao macro - espelho, nao veto. Cris tambem elogiou: o reader nao enviou nenhum sinal onde nao houve reversao visivel.',
  array['seed:memory_delta_continuation_doctrine_20260805','doutrina','continuacao','reversao','a1a2','comportamento'],
  'memory/feedback_continuation_doctrine_gold_uptrend.md · trader_map.json tese_geral', 'active')
on conflict (id) do nothing;
