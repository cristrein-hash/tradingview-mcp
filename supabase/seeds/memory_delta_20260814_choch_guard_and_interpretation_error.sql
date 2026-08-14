insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('choch_guard_active_20260814')::uuid, 'private', 'internal', 'project',
  'GUARD-CHoCH ATIVO bloqueia longs na faca (4H+1H)',
  'Cris 14/08: implementado guard ATIVO que bloqueia emissao de LONG quando ha CHoCH-down (quebra do higher-low) no 4H E 1H (AND, menos falso-positivo). blocks_long() em alert-bridge/choch_shadow_guard.py CONSOME o campo choch do dossie E0 (market_context.json axes.mtf) — ZERO metrica inventada; fail-open (sem dossie=nao bloqueia). GATE ATIVO em: reader send_confirmed_tg, entry_validator GO-LONG, e2 notify_surfaced (e1/R9/R10), A1/A2 runtime, L1 cycle. So toca LONG, isolado por-emissor (nao no _tg_send partilhado), auditado deterministicamente. Backtest 13/08 (context_structure causal, sem lookahead): bloquearia 67% dos longs induzidos incl. 100% dos tardios (a faca); FP nos dias de alta 0/3 (amostra PEQUENA, n=3 — nao validado, forward=arbitro; vigiar over-block). launchd choch-shadow 5min = registo forward. commit local+push.',
  array['seed:memory_delta_20260814_choch_guard_and_interpretation_error','guard','choch','xau','long-block'],
  'alert-bridge/choch_shadow_guard.py · research/guard_backtest_20260813.py', 'active'),
 (md5('interpretation_error_trend_vs_choch_20260814')::uuid, 'private', 'internal', 'feedback',
  'Erro de INTERPRETACAO (nao processo): 1 campo vs multi-campo',
  'Erro 13/08: no backtest li o campo trend do E0 = UP e conclui 4H bullish, IGNORANDO choch_dn=True (quebra, close 4318 abaixo do swing-low 4356) e a VELA 4H real (vermelha corpo -35). O trend (rotulo de swing HH/HL) ATRASA; choch e a vela dao o sinal em tempo real. Cris apanhou: como assim 4H up? PORQUE NENHUM GUARD APANHOU: guards bloqueiam PROCESSO (inventar/RAW-first/saltar-TF/commit-sem-DA), NAO INTERPRETACAO (ler dado real e concluir errado) — um guard deterministico nao valida interpretacao sem SER interprete (circular). Rede real p/ interpretacao = auditor adversarial + Cris. FIX: G7 alargado dispara em analise de estrutura e LE o conteudo do script (nao so comando) + regra #7 multi-campo (nunca decidir por 1 campo: trend E choch E vela). Regra permanente: interpretar estrutura = trend E choch E vela, sempre.',
  array['seed:memory_delta_20260814_choch_guard_and_interpretation_error','interpretation','myopia','g7','choch','trend'],
  'memory/feedback_interpretation_error_trend_vs_choch.md', 'active'),
 (md5('accounts_grave_20260813')::uuid, 'private', 'internal', 'project',
  'Contas GRAVE 13/08: reader viés long induziu perdas',
  'Reader deu 0 shorts num dia inteiro de faca (viés long estrutural); modulos (validador/A1A2/L1/e1) emitiram longs o dia todo num down-leg -> Cris e Leonardo compraram a faca -> perdas. FTMO +2,5% (metade do conquistado perdida). FN 93.500 USD = 1,5% de estourar a conta (grave). A ponte-Telegram (2o Claude) NAO desligou nada de facto (auditado: 0 commits, 0 daemon disabled, 0 flags novas, sistema intacto) — o desligar foram palavras dela. Guard-CHoCH ativo agora previne repetir a inducao de longs na faca.',
  array['seed:memory_delta_20260814_choch_guard_and_interpretation_error','accounts','ftmo','fn','xau'],
  'memory/feedback_interpretation_error_trend_vs_choch.md', 'active')
on conflict (id) do nothing;
