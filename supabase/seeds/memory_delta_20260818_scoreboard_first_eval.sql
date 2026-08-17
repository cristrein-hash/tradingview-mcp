-- memory_delta_20260818_scoreboard_first_eval
-- Scoreboard forward semanal + 1a avaliacao real de TODOS os sinais enviados (3R e segurar).
-- commit git ANTES do apply (G2).
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('scoreboard_first_eval_20260818')::uuid, 'private', 'internal', 'project',
  'Scoreboard forward semanal (commit d670865) + 1a avaliacao real dos sinais enviados: total +12R (3R fixo)',
  'my-strategy/core/scoreboard/scoreboard.py + plist com.cristrein.scoreboard-weekly (domingo 20:00 Lisboa).' || chr(10) ||
  'Painel por linha dos ledgers existentes: N, W-L-O, sumR(3R SL-first vs bars_15m), streak, mediana MFE e' || chr(10) ||
  'R-se-segurasse (SL nunca tocado = marca ao preco atual; tocado = -1R). Metas de fecho: reclaim/cp/e2/b N>=20,' || chr(10) ||
  'a1a2/l1/l2 N>=15; ao atingir N -> veredito GO/KILL com o Cris; REGRA: nada de novo ate algo fechar.' || chr(10) ||
  '1a AVALIACAO REAL (18/08, janela store ~30d): cp 3-0-0 +9R (segurar +67,9R; 4007 deu 37R) - a1a2 15 5-9-1 +6R' || chr(10) ||
  '(streak 5L, facas 12-13/08 = 7 losses seguidos) - e2_reader 17 5-11-1 +4R (streak 8L; segurar +56,5R) -' || chr(10) ||
  'reclaim 10 0-7-3 -7R (unica negativa; agora gated) = TOTAL +12R. Leituras: nao e tudo perda - a sensacao do' || chr(10) ||
  'Cris vem da ultima semana (pior troco); Cp = joia (pouco e certeiro); segurar confirma-se nos winners mas' || chr(10) ||
  'losers deram 1,3-3,9R de MFE antes de morrer -> o ganho esta em saidas GERIDAS, nao hold cego; o lucro ficou' || chr(10) ||
  'nos ledgers e as perdas na conta (execucao pegou a semana ma) - e isso que scoreboard+gates atacam.' || chr(10) ||
  'Contexto: Cris muito frustrado (meses sem resultado na conta; urgencia = aprovar conta challenge, chega de' || chr(10) ||
  'perdas); diagnostico aceite = largura-sem-fecho + imposto-dos-erros-do-Claude; decisao: manter 5 linhas.',
  array['seed:memory_delta_20260818_scoreboard_first_eval','scoreboard','forward','avaliacao','xau'],
  'my-strategy/core/scoreboard/scoreboard.py', 'active')
on conflict (id) do nothing;
