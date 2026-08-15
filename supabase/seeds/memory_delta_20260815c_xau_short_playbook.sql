-- memory_delta_20260815c_xau_short_playbook
-- Ponteiro do XAU SHORT 15M Build Playbook + auditoria de precisao (numeros byte-exato, correcao L2-beta).
-- commit git ANTES do apply (G2).
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('xau_short_build_playbook_20260815')::uuid, 'private', 'internal', 'reference',
  'XAU SHORT 15M Build Playbook (docs/project_authority/) — sintese 6 nucleos + auditoria byte-exato + correcao L2-beta',
  'docs/project_authority/XAU_SHORT_15M_BUILD_PLAYBOOK.md (Cris 2026-08-15, commits 97df54b criado + c6fbeee correcao L2).\n'
  'Sintese que resgata e organiza TODO o conhecimento comprovado das estrategias XAU LONG para construir a SHORT 15M\n'
  'de forma simples/rapida/auditavel, sem invencoes e sem erros. Produzido por 4 Agent-tools reais sobre material real.\n'
  '6 NUCLEOS: (1) 8 melhores praticas comprovadas — estrutura-primeiro; SL estrutural ∓0,1ATR+3R (trailing rejeitado);\n'
  'gate-regime corta streak-killer; gate-posicao rejeita topo/esticado; causalidade auditada (edge encolhe sem lookahead);\n'
  'distinguir edge de beta com nulls; winners/losers coexistem no espaco de entrada (lever=gate+gestao nao selecao fina);\n'
  'validacao=forward. (2) Workflow canonico manifest->source-guard->bucket-estrutural->indicador-no-balde->hipotese-congelada\n'
  '->script-fail-loud->null+DA->claim-ledger->painel->lab-gate PASS. (3) Auditoria 14 erros (insight: protege o guard que\n'
  'BLOQUEIA, nao o advisory). (4) Conhecimento SHORT decidido: criterio aceitacao (quebra 1H+15M+retest OU rejeicao impressa\n'
  'no iman superior BB/SVP/OB 15M); continuacao=default-nao-veto; NENHUM gate mecanico separa faca/dip na entrada; semente\n'
  'GT#1 13/08; regra nunca-espelho (perna-1H imediata manda, nao macro lento). (5) Passo-a-passo 11 passos, cada um com gate\n'
  '+ erro que evita (recall-gate PRIMEIRO; nucleo SHORT nativo; distancia-ATR nao flag binaria). (6) Guards novos GS1-GS7\n'
  '(prioridade aos bloqueantes GS1 manifest/GS2 source-gate-realtime/GS3 recall-gate).\n'
  'AUDITORIA DE PRECISAO (a pedido do Cris): numeros verificados byte-exato contra a fonte — L1 N24 75% +45,2R; L2 V2 N17\n'
  '53% +36,2R (exit +105,3R); Cp N21 43% +0,60 +12,6R GT5/5; A1 13/14 A2 16/18; N96 52W/44L +112R (intra-BEAR +13R=13L/0W);\n'
  'RWS swept null p=0; GT#1 4406,5->quebra05:30(-18,6)->4356; perna-1H #1 separador COM56%/CONTRA27%. Sintese NAO alucinou.\n'
  'CORRECAO aplicada (c6fbeee): L2 +36,2R rotulado BETA long-gold (nao alpha de entrada; phase51 pure-edge nao bate random);\n'
  'RWS = unico com edge de sinal genuino provado. Regra: N/sumR+ nao e edge ate o null pagar.\n'
  'RETOMADA: ponto de entrada = Passo 0 (manifest); decisao pendente = implementar GS1-GS3 primeiro ou manifest direto.\n'
  'NADA implementado (estudo/plano). Teto: garante PROCESSO auditavel, NAO garante edge (nulls/DA/forward decidem).',
  array['seed:memory_delta_20260815c_xau_short_playbook','xau-short','playbook','15m','workflow','auditoria','best-practices','guards'],
  'docs/project_authority/XAU_SHORT_15M_BUILD_PLAYBOOK.md + memory/reference_xau_short_build_playbook.md', 'active')
on conflict (id) do nothing;
