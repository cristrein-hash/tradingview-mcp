-- Delta 2026-08-05: madrugada da virada BULL + overhaul do live (ordens Cris)
insert into memory_nodes (name, description, node_type, content) values
('project_night_0508_bull_turn_and_system_overhaul',
 'Madrugada 04-05/08: pernada BULL 4060-4167 (leitura Cris certa; long na demanda = melhor sinal). Overhaul: TG grupo so qualificados (L1/L2/15M-BULL/reader-validados; resto -> chat privado), reader-gate em validador E vela, fast-5M bands (bug load_map descartava fast_5m corrigido), A1/A2 LIVE (task 35, daemon xau-a1a2-cycle, consome a1_causal_entry), gates de regime OFF por env (L1+A1A2, ordem DESTRAVA TUDO), AMD em repouso. Cp TINHA apanhado a capitulacao: 3 sinais TG 28-29/07 entries 4033.53/4033.17/4007, alvos atingidos. Router 15M: 1631 ciclos 100% BEAR - ramo RANGE nunca correu. DEFEITO ABERTO: classificador macro 1D gruda (rotulou BEAR um mes de range).',
 'project',
 'Ver ficheiro project_night_0508_bull_turn_and_system_overhaul.md no memory dir. Pendencias: consertar classificador macro 1D; wiring registo forward A1/A2; zonas acima 4166; persistir estado sentinela.'),
('feedback_system_neutral_signaler_not_confirmer',
 'Sistema = sinalizador NEUTRO, nao confirmador do bias (Cris 05/08): o LONG mecanico na demanda 4060-66 contra regime BEAR e contra o short do Cris foi O MELHOR SINAL DA NOITE. NUNCA vetar/silenciar sinal por direcao contra-tese; conflito vai anotado no texto, decisao e do Cris. Filtros de QUALIDADE (RR>=1.5, dedup, reader-gate de timing) legitimos; filtros de DIRECAO proibidos.',
 'feedback',
 'Quase deployei veto-de-regime no TG da vela; Cris travou (PODE ESTAR CORRETO, CALMA) e foi revertido sem deploy. Reader-gate aprovado pelo Cris: julga qualidade/timing do gatilho, nao a direcao.')
on conflict (name) do update set description = excluded.description, content = excluded.content;
