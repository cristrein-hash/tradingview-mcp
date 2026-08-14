-- memory_delta 20260814b — GUARD-CHoCH: limitacao confirmada + alinhamento cosmetico/rename + decisao do guard convergente
-- Seed git-committed ANTES de aplicar (protocolo). on conflict do nothing = idempotente.
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('choch_guard_limitation_confirmed_20260814')::uuid, 'private', 'internal', 'feedback',
  'GUARD-CHoCH bloqueia por PERDA-DE-REGIAO, nao por short convergente (limitacao confirmada no codigo)',
  'Verificacao profunda (Cris 14/08): blocks_long() = choch_dn no 4H **E** 1H (AND). A fonte choch_dn vem de '
  'context_structure.py:54 = C[i] < prot_low (fecho abaixo do higher-low imediato confirmado). Ou seja: o gatilho '
  'do bloqueio e PURA perda de regiao de preco — NAO le pavio, NAO le quem absorve, NAO le follow-through, NAO le '
  'localizacao, NAO le rejeicao-no-iman. RISCO: numa perna de alta com recuo forte que feche abaixo do ultimo '
  'higher-low menor no 4H E 1H (o fundo compravel, cenario A1/A2), bloquearia um LONG de continuacao legitimo. O '
  'instinto do Cris estava certo. NAO cumpre o criterio dele ("bloqueio so apos condicoes de short convergentes'
  '"). ALINHAMENTO COSMETICO feito 14/08 (zero logica): (a) cabecalho mentia "SHADOW/log-only/nao bloqueia" com '
  'blocks_long ATIVO em 5 emissores -> corrigido + documenta a limitacao; (b) o log forward media OR (dn_1h OR '
  'dn_4h) enquanto o bloqueio usa AND -> log alinhado a AND (verdict.block agora = AND, mede o que bloqueia); (c) '
  'rename choch_shadow*->choch_guard* (modulo choch_guard.py, label com.cristrein.choch-guard, plist, logs jsonl/'
  'out/err), 5 imports atualizadas, reload launchd limpo, selftest PASS. blocks_long INALTERADO (ainda AND). '
  'DECISAO (Cris 14/08): CONSTRUIR NOVO guard que exige CONVERGENCIA DE SINAIS LEGITIMOS DE SHORT antes de '
  'bloquear (nao perda de regiao sozinha). O novo guard deve CONSUMIR os sinais de short que JA existem no '
  'dossie E0 (market_context.json: axes.liquidity sweep+reclaim, axes.confluence sell, OB/SMC, rejeicao-no-iman) '
  '— NAO reconstruir um reader paralelo. Pressupostos a DECLARAR antes de construir (disciplina declara-antes).',
  array['seed:memory_delta_20260814b_choch_guard_limitation_and_rename','guard','choch','xau','long-block','convergence','rename'],
  'alert-bridge/choch_guard.py · alert-bridge/context_structure.py:54', 'active')
on conflict (id) do nothing;
