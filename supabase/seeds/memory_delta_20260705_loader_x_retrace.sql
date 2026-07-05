-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260705_loader_x_retrace
-- ============================================================================
-- Bloco: cruzamento declarado loader sequencial x retracao macro (2026-07-05, noite).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py (protocolo 2026-07-05).
-- IDEMPOTENTE: md5(seed_key)::uuid + on conflict (id) do nothing.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260705_loader_x_retrace'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260705_loader_x_retrace:memory_items:cross-confirma-negativo')::uuid,
  'product', 'internal', 'project',
  'Cruzamento loader sequencial x retracao macro profunda = CONFIRMA_NEGATIVO (DA)',
  'Passo declarado em memoria (buy_recent x banda retr 0,5-1,3) morreu no ledger v1 (universo N4739: X2 P=0,70, X4 P=0,48; banda sozinha 23,5% < base 27,6%). v2 no dominio selado NB parecia positivo (X4-linha N12 58,3% stk-1 anos+) mas DA refutou: X3-linha = RWS54 intersecao banda por IGUALDADE EXATA de conjuntos — slice do engine ja validado; Fisher dentro do RWS54 p=0,43 (banda nao adiciona); mesma regra fora de NB = 6,7% hit; Sidak 0,23-0,92. FATOS: loader vive em pullback RASO (RWS-54 retr mediana 0,30; 14/54 na banda profunda); QUEM (acumulacao) e ONDE (retracao profunda) NAO compoem — bubbles esparsos em fundo profundo. LICOES DA: re-look de dominio apos ledger falhar = re-look (conta na familia de testes); slice de engine validado != engine novo. Gargalo confirmado = amostra GT-60: proximo passo e pedir ~30 circulos novos ao Cris antes de nova familia de features.',
  array['seed:memory_delta_20260705_loader_x_retrace','rws-15m','macro-retrace','confirma-negativo','method-lesson'],
  'rws_loader_x_macro_retrace{,_v2}_20260705.py + rws_x_retrace_attack_da2_.py (commit 9318432)',
  'active'
)
on conflict (id) do nothing;

commit;
