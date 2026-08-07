insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('trade_log_20260807_chase_be_exit')::uuid, 'private', 'private', 'project',
  'Trade log 07/08: LONG chase 4320 -> saida -500$ antes do NFP (disciplina)',
  'Cris declarou LONG entry 4320 SL 4307. Claude (co-piloto) avaliou na hora: MA localizacao - comprar DENTRO da supply 4310-4330 (OB 1H resistencia), RSI 1H 69.5 overbought, NAS 4.5xATR esticado = CHASE da extensao, nao pullback-buy; nao era sinal do sistema (sem A1/A2), discricionario. Plano inicial do Cris: BE antes do NFP + tentar a sorte de payroll favoravel. Claude questionou: heroi no NFP com conta a sangrar, BE stop NAO protege no NFP (slippage salta o BE). Desfecho: Cris saiu -500$ antes do NFP em vez de segurar = DISCIPLINA, protegeu a pista. LICOES: (1) declarar trade ANTES de entrar nao depois; (2) chase into supply overbought = evitar, a compra e o pullback que segura suporte; (3) sair pequeno antes de evento = VITORIA nao derrota (-500 evitou -2000 de slippage NFP); objetivo em dia de evento com conta a sangrar = nao perder nao ser heroi. Conta: FN -4.4%+este -500, FTMO -1.2%.',
  array['seed:memory_delta_trade_log_20260807','trade-log','disciplina','chase','be','nfp','licao'],
  'memory/project_trade_log_20260807_chase_be_exit.md', 'active')
on conflict (id) do nothing;
