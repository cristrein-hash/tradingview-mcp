-- memory_delta_20260815b_behavior_guards_tooling
-- Ferramentas das guardas de comportamento (~/.claude/hooks/) + caveat honesto do juiz Haiku (best-effort).
-- commit git ANTES do apply (G2).
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('behavior_guards_tooling_20260815')::uuid, 'private', 'internal', 'reference',
  'Guardas de comportamento tooling: juiz Haiku do G7 = BEST-EFFORT condicional ao Haiku (nao garantido) + telemetria + meta-runner + auditor',
  'Ferramentas das guardas de comportamento (~/.claude/hooks/, espelho versionado docs/governance/hooks/, Cris 2026-08-15):\n'
  '- JUIZ HAIKU do G7 (_g7_judge.py) = BEST-EFFORT, CONDICIONAL AO HAIKU, NAO garantido. 2o estagio do '
  'pre_analysis_myopia_guard: regex e so gatilho, o juiz le o script e classifica rubrica (is_market_analysis/'
  'multifatorial/trajetoria/dois_objetivos); so bloqueia se for analise E falhar. CAVEAT (auditado, corrigido de '
  'afirmacao minha exagerada): latencia do Haiku VARIA (3.7s->12.7s->>15s); em timeout o juiz devolve None -> o G7 '
  'DEGRADA para o checklist regex antigo (fail-closed seguro) e volta o reflexo-bypass. Logo a eficacia do fix '
  'keyword->raciocinio DEPENDE do Haiku. Mitigacoes: TIMEOUT=15s; marca Haiku-lento (/tmp/.claude_g7_judge_slow, '
  '60s) salta o juiz apos 1 timeout; cache 12h por hash SO em sucesso (/tmp/.claude_g7_judge/); reversivel G7_JUDGE=off.\n'
  '- TELEMETRIA guard_fires.jsonl (_guard_log.py, fail-open): 1 linha por bloqueio das 11 guardas (antes so o G7 '
  'logava bypasses em bypass_uses.log). Cruzar os dois apos ~1-2 semanas -> podar guardas que nao mordem.\n'
  '- META-RUNNER run_hook_selftests.py: prova deterministica (6 selftests nativos + black-box); reporta OK/FAIL/SKIP '
  '(caso pre_mcp_action faz SKIP se a flag ~/.claude/.mcp_action_ok estiver fresca = depende de estado, nao FAIL).\n'
  '- AUDITOR audit_g7_bypasses.py: dissuasao por auditoria — sinaliza bypasses cuja razao diz "nao e analise" mas '
  'correm um .py nao-exemptado (#3; auto-atestado nao se previne, so se audita).\n'
  '- pre_golive_da_guard: ledger da_ledger.jsonl REMOVIDO (morto, nunca escrito) — fica so o token DA_OK/NO_DA_NEEDED '
  'na mensagem do commit.\n'
  '- Falso-positivo do G7 baixado: exime --selftest + aplicadores de seed/governanca (apply_memory_delta, '
  'scripts/supabase|safety, checkers). systematic_error_guards exime /hooks/ tambem no file_path.\n'
  'TETO HONESTO: estas guardas protegem PROCESSO (nao inventar, ler todos os TFs, citar fonte, nao ir live sem DA, '
  'nao ser miope). NAO apanham a leitura contextual errada da fita — isso e forward-only. '
  'Detalhe em memory/reference_behavior_guards_tooling.md. Commits 86e6599, 56ce035, 86b1d98.',
  array['seed:memory_delta_20260815b_behavior_guards_tooling','guardas','hooks','g7','juiz-haiku','telemetria','best-effort','meta-runner'],
  'docs/governance/hooks/ + memory/reference_behavior_guards_tooling.md', 'active')
on conflict (id) do nothing;
