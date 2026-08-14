-- memory_delta 20260814c — auditoria: medir estrutura re-derivada em vez de LER o indicador + 2 guards novos
-- Seed git-committed ANTES de aplicar. on conflict do nothing = idempotente.
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('rederive_vs_read_indicator_guard_20260814')::uuid, 'private', 'internal', 'feedback',
  'Erro recorrente: medir estrutura RE-DERIVADA em vez de LER o indicador real — agora com guard ativo',
  'Auditoria 14/08 (Cris exigiu comparar RAW vs MCP): construi um estudo faca-vs-dip da semana ancorado na '
  'MINHA context_structure (choch/pivots) + rotulos meus, sem NUNCA ler os indicadores reais (OB Detector v11/'
  'SMC/SVP/NAS/Bubbles). Comparacao RAW vs MCP: OHLC RAW = MCP EXATO (19/19) -> os PRECOS sao fieis, nao '
  'inventados. MAS a conclusao do estudo (nenhum fator discrimina) e INVALIDA POR OMISSAO — nunca testei '
  'LOCALIZACAO vs OB real. Prova: a queda fez fundo EXATO na zona OB Detector DEMAND 4310.97-4322.9 e bounce '
  '+68pt (o dip), invisivel ao estudo so-estrutura. PORQUE OS GUARDS NAO PEGARAM: (1) G7 disparou mas contornei '
  'com SANITY_PROBE (honor-system) e o ambito dele e miopia-de-campo em dados derivados, nao ler-indicador-real; '
  '(2) contextual_read_guard disparou mas evadi (Read tool + scripts nunca nomeavam OB) e /research/ era isento '
  'em bloco. FIXES (Cris 14/08, implementados+testados): (A) SANITY_PROBE agora REGISTADO em '
  '~/.claude/hooks/logs/bypass_uses.log (bypass deixa de ser silencioso); (B) contextual_read_guard Regra C '
  'BLOQUEIA qualquer script que derive choch/pivots/structure de OHLC crua SEM ler o indicador (pine_boxes) ou '
  'token READ_OB_ZONES — dispara MESMO em /research/. Hooks espelhados em docs/governance/hooks/. '
  'NOTA ARQUITETURA: o eixo choch da producao + o choch-guard consomem context_structure (re-derivado), NAO o '
  'SMC/OB real = mesma fraqueza. E .polarity_state/zones.json = zonas PARTIDAS/viradas (ex_demand_supply), NAO a '
  'lista OB ativa — nao confundir fonte. PROXIMO: refazer o estudo faca-vs-dip ancorado na LOCALIZACAO vs OB real.',
  array['seed:memory_delta_20260814c_rederive_vs_read_indicator_guard','guard','contextual-read','ob','audit','choch','myopia'],
  'docs/governance/hooks/contextual_read_guard.py · alert-bridge/context_structure.py', 'active')
on conflict (id) do nothing;
