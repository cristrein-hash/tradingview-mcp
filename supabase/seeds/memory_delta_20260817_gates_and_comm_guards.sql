-- memory_delta_20260817_gates_and_comm_guards
-- Trabalho de 2026-08-17: HTF location gate (final binario) + a1a2 agility gate + guards de comportamento.
-- commit git ANTES do apply (G2).
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('htf_location_gate_final_20260817')::uuid, 'private', 'internal', 'reference',
  'HTF LOCATION GATE (reclaim long + espelho short) — final binario, sem params inventados',
  'commits 84baff1 (v1) -> 574b904 (afinado). my-strategy/core/reclaim_location_gate.py consome o dossier E0\n'
  'canonico (axes.mtf[tf].zones.stack + .leg). RECLAIM (long, router run_reclaim): ENFORCING binario = entrada DENTRO\n'
  'de zona de demanda HTF (1H/4H/1D) E na metade inferior (ponto-medio geometrico, sem knob). So envia gate_pass ao\n'
  'Telegram pessoal; reprovados ficam no ledger. SHORT (e2_quality.notify_surfaced, SHORT-only): perna 1H DOWN ESTRITO\n'
  '+ nao acima de demanda HTF por baixo -> suprime shorts como o 08:02 (@4405, perna up, stop a 4427). Auditoria do Cris\n'
  'removeu: POS_MAX/EDGE_TOL/DEMAND_NEAR (params inventados) e o SL-alargado (shadow quase inerte). Fonte NUNCA inventada.\n'
  'NAO e edge provado; forward=arbitro. Wiring provado end-to-end (send/suprime/ledger).',
  array['seed:memory_delta_20260817_gates_and_comm_guards','xau','reclaim','short','gate','live'],
  'my-strategy/core/reclaim_location_gate.py', 'active'),
 (md5('a1a2_agility_gate_20260817')::uuid, 'private', 'internal', 'project',
  'A1/A2 macro_gate — agilidade na transicao (1D nao-BEAR OU rapido 4H BULL+legs up)',
  'commit 6f978ad. a1a2_runtime.py::macro_gate. Problema: regime autoridade = Layer1 1D estrutural (structural_1d),\n'
  'lento, so recalcula ao fecho diario 22:00; ficou BEAR/13-08 e travou A1/A2 (so corre em BULL) apesar do dia bullish\n'
  '4368->4427. Fix (decisao Cris opcao meio-termo): elegivel se 1D NAO-BEAR (BULL ou RANGE) OU caminho-rapido = v5_4h\n'
  'BULL + legs 1H e 4H ambos up (dois rapidos a concordar, proxy de cruzamento; mtf_cross NAO exposto no E0). cycle()\n'
  'corre limpo, gate PASS testado com dossier real. NAO-live ate reload do daemon A1/A2 (falta autorizar). Detetores de\n'
  'regime distintos: Layer1 1D (autoridade router), v5_4h (auxiliar), mtf_cross (reader, nao no E0), e2_quality.regime.',
  array['seed:memory_delta_20260817_gates_and_comm_guards','xau','a1a2','regime','gate'],
  'my-strategy/strategies/xau_15m_long/continuation_A1A2/a1a2_runtime.py', 'active'),
 (md5('comm_and_claim_guards_20260817')::uuid, 'private', 'internal', 'feedback',
  'Guards de comportamento — comunicacao curta (UserPromptSubmit) + nao-afirmar-sem-prova (Stop)',
  'Cris exausto (2026-08-17) de textos longos, perguntas excessivas, e afirmar feito/funciona sem testar. Memoria nao\n'
  'chega (regride) -> guards deterministicos. (1) ~/.claude/hooks/comm_brevity_guard.py = UserPromptSubmit, injeta\n'
  'checklist de brevidade ANTES de eu responder (curto/uma-pergunta/nao-operacionalizar-sem-ordem). (2)\n'
  '~/.claude/hooks/no_unproven_claim_guard.py = Stop, BLOQUEIA (exit 2) se a resposta afirma feito/provado/live sem correr\n'
  'Bash de verificacao real no turno (echo/ls nao contam; py_compile/--selftest/test/git commit/python3 -c contam). Escape\n'
  'CLAIM_WAIVED. Selftest 11/11. Raiz do vies: treino pro-acao -> produzir em vez de validar; so guard externo corrige.',
  array['seed:memory_delta_20260817_gates_and_comm_guards','feedback','guards','comunicacao','disciplina'],
  '~/.claude/hooks/', 'active')
on conflict (id) do nothing;
