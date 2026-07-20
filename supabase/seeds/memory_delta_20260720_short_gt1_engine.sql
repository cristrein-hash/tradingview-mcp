-- memory_delta_20260720_short_gt1_engine
-- Resolucao do forward-call E2 (GT#1: ambos SHORTs de sexta = SL) + discriminador do Cris + arranque do engine SHORT.
-- Sem secrets/RAW/params de edge. ASCII. Sem ponto-e-virgula no texto.
-- ROLLBACK (via SQL Editor): apagar memory_items com a tag deste seed.
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('e2_forward_call_gt1_resolved_20260720')::uuid, 'private', 'private', 'project',
  'E2 forward-call RESOLVIDO (GT#1): os 2 SHORTs de sexta 2026-07-17 = ambos SL, Cris acertou',
  'O pipeline E1/E2 sinalizou 2 SHORTs na sexta 2026-07-17 (zone_reject 15M, tese 1D/4H DOWN + supply + up-leg esticada). Cris fez forward-call falsificavel: ambos SL ate segunda. RESOLVIDO 2026-07-20 pelo backfill contrafactual first-touch (e2_outcomes.jsonl): SHORT1 entry 4012.27 SL 4024.69 rr-alvo 3.15 = SL em 33 barras; SHORT2 entry 4015.10 SL 4024.52 rr-alvo 4.45 = SL em 29 barras. AMBOS SL. Cris ACERTOU, E2 errou os dois. Preco subiu pelos stops ~4024.5 e continuou ate 4040 na segunda (ai rejeitado). Este e o GT ponto 1 do E2 = NEGATIVO: regime cru shortou o topo de uma up-leg madura pos-climax, e horas antes recusou os 2 LONGs certos que o E1 detetou (a inversao). Confirma a direcao do de-enviesamento E1/E2 (regime = uma voz nao veredito). Doc memory project_e0e1e2_forward_case_20260717 + feedback_e2_calibration_cris_reads.',
  array['seed:memory_delta_20260720_short_gt1_engine','e2','forward-call','gt1','short','2026-07-17'],
  'e2_outcomes.jsonl + memory project_e0e1e2_forward_case_20260717', 'active'),
 (md5('xau_short_engine_dev_kickoff_20260720')::uuid, 'private', 'private', 'project',
  'XAU SHORT engine = DEV arrancado esta semana (Cris 2026-07-20): discriminador teste-e-rejeicao NO iman (BB 15M + SVP 15M)',
  'Cris decidiu construir as estrategias SHORT ao longo desta semana (sai de PENDING/DEFERRED para dev ativo). Regra permanente: SHORT nao e espelho do LONG, nunca gates invertidos, regime = roteador/contexto nao direcao. DISCRIMINADOR CENTRAL (leitura do Cris = o edge), extraido do contraste sexta-vs-hoje: SEXTA (errado) = venda PRECIPITADA a 4012/4015 ABAIXO dos imanes, sem teste do BB 15M e sem tocar o range SVP 15M (a perna ainda ia buscar os imanes de cima entao subiu = SL). HOJE (maior-prob) = preco CHEGOU a 4040, testou o BB 15M (ponto de entrada do Cris) + range SVP 15M e REJEITOU com spike claro = rejeicao validada NO iman, nao antes. REGRA DO ENGINE: um SHORT so e valido depois do preco TESTAR o iman superior (BB 15M + range SVP 15M) e rejeitar la, nunca abaixo do iman nao-testado. Componentes a encodar: maturidade/exaustao da perna (nao 1o pullback, pos-climax comprador) + teste-e-rejeicao no iman + leilao (iniciativa vendedora real na rejeicao nao rally vazio) + regime como contexto nao direcao. Metodo canon: RAW-first BB/SVP/OB 15M, close-only causal, painel completo, null/jackknife, DA so-lookahead, prereg+forward = arbitro, protocolo XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1, alert-only. Doc memory project_xau_short_engine_dev_20260720.',
  array['seed:memory_delta_20260720_short_gt1_engine','short','engine','dev','bb-15m','svp-15m','iman','maturidade-perna'],
  'memory project_xau_short_engine_dev_20260720', 'active')
on conflict (id) do nothing;
