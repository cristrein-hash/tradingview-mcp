insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('weekclose_20260807_state')::uuid, 'private', 'private', 'project',
  'Fecho de semana 07/08 - estado para retomar domingo',
  'POSICAO ABERTA (swing fim de semana): LONG A1/A2 pullback 15M XAU (sinal do sistema, continuacao, dentro do pacto). FN entry 4338, FTMO entry 4341, SL ambos 4300, size 1% risco/conta (lote ajustado - stop largo + size cortado = risco $ controlado). Preco fecho ~4334. Suporte-chave 4315 (demanda 1M/5M), SL 4300 abaixo. 1o alvo ~4368-4370, acima de 4382 c/ fecho = novos maximos. Gap domingo mitigado pelo size 1%. CONTAS: FTMO +0.68% (positivada), FundedNext -4% (recuperavel). PLANO SEMANA: recuperar 4% FN so com trades sinalizados OU pre-avaliados com Claude; disciplina, paciencia, size pequeno, deixar correr (2-3 winners 3R recuperam). SISTEMA: continuacao bull (inversao 4285), gate de doutrina reposto (short so 4337-82 macro), fail-closed p/ shorts (reader indisponivel nao envia short), anti-prematuro no reader-gate (surfaced+conv>=55+nao auto-contraditorio), AMD reativado, BLBE tecnica em estudo. Retomar abertura de domingo ~22h UTC.',
  array['seed:memory_delta_weekclose_20260807','fecho-semana','estado','long-aberto','disciplina','retomar-domingo'],
  'memory/project_weekclose_20260807_state.md', 'active')
on conflict (id) do nothing;
