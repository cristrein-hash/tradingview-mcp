insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('cris_discipline_pact_20260807')::uuid, 'private', 'private', 'feedback',
  'PACTO DE DISCIPLINA do Cris (07/08): obedecer LONGs, corrigir vies de reversao, nunca fechar exceto SL',
  'Apos -4,4% FundedNext + -1,2% FTMO na semana 05-07/08 por shorts teimosos CONTRA o uptrend 4007->4306 (vies de reversao = fraqueza pessoal declarada). O sistema segurou 8+ GOs short (todos certos em chat - era acumulacao), o comportamento do Cris nao. PACTO aceite: (1) obedecer os sinais LONG do sistema com gestao de risco 0.5-1%/trade (A1/A2 = motor do lado fraco); (2) corrigir vies de reversao - short SO em 4H/1D (4337-82) com clara rejeicao macro; (3) REGRA DE SAIDA: NUNCA fechar operacao exceto se der SL (deixar correr ao alvo/SL, nao fechar por medo). CONTRATO DO CLAUDE: questionar todo short fora do macro; questionar toda vontade de fechar long a meio; proteger a pista nao o heroi (desincentivar trades no NFP/eventos, lembrar limites 5%dia/10%total); nao reconfigurar mapa a cada flip - ajudar a REFLETIR sob hesitacao. Padrao a vigiar: flip-flop direcional sob stress. Antidoto: vies LONG por defeito, short so macro, deixar correr. Claude = guarda-livros da disciplina.',
  array['seed:memory_delta_discipline_pact_20260807','disciplina','pacto','reversao','risco','comportamento','long'],
  'memory/feedback_cris_discipline_pact_20260807.md', 'active')
on conflict (id) do nothing;
