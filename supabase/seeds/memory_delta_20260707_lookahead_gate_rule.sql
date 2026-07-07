-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260707_lookahead_gate_rule
-- ============================================================================
-- Bloco: REGRA de comportamento — causalidade e PRE-CONDICAO SILENCIOSA antes de apresentar hit-rate (2026-07-07).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260707_lookahead_gate_rule'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260707_lookahead_gate_rule:memory_items:causalidade-precondicao-silenciosa')::uuid,
  'product', 'internal', 'feedback',
  'REGRA DURA: causalidade/lookahead = PRE-CONDICAO SILENCIOSA antes de apresentar qualquer hit-rate; salto por escala/agregacao = assumir lookahead ate prova causal',
  'Cris FURIOSO 2026-07-07 ("nem devias ter feito isso!!! ja e a milesima vez que crias expectativa e desilude por lookahead, foda-se"). REINCIDENCIA: ao subir a ESCALA do master walk apresentei "r=12 = 80% hit-3R robusto por-ano = breakthrough" e SO DEPOIS testei causalidade e descobri LOOKAHEAD (a confirmacao do pivo r=12 usa a subida futura = o movimento vencedor). Eu ja suspeitava do lookahead quando o numero subiu com a escala e mesmo assim mostrei o breakthrough primeiro. REGRA PERMANENTE AFIADA: (1) QUALQUER salto de hit-rate ao aumentar escala/agregacao/lookback de um detector zigzag/pivo/estrutura = ASSUMIR LOOKAHEAD ate prova causal em contrario (confirmacao de pivo usa movimento FUTURO). (2) A verificacao causal (features so-passado) e PRE-CONDICAO SILENCIOSA: corro-a EU sozinho ANTES de qualquer palavra ao Cris. (3) Se ha suspeita de lookahead/confound no meu raciocinio, NAO menciono o numero empolgante "pendente de checar" — so chega ao Cris o numero JA pos-verificacao-causal. Zero expectativa antes da causalidade selada. Isto reforca feedback_validate_before_presenting REGRA 1 (validar antes de apresentar) e feedback_close_only_causal_universal. Padrao a extinguir: "olha que otimo" seguido de "ah era bug/lookahead".',
  array['seed:memory_delta_20260707_lookahead_gate_rule','causalidade-precondicao','lookahead-gate','validar-antes-apresentar','comportamento','reincidencia-critica'],
  'feedback_validate_before_presenting.md (reincidencia 2026-07-07)',
  'active'
)
on conflict (id) do nothing;

commit;
