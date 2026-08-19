-- memory_delta_20260819_signal_reorg_deep_cleanup
-- Dia 19/08: reorganizacao TOTAL dos sinais + deep audit + cleanup autonomo L1-L7 (tudo pushed).
-- commit git ANTES do apply (G2).
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('signal_reorg_20260819')::uuid, 'private', 'internal', 'project',
  'REORG SINAIS 19/08: sender unico notify.py, formato A, 4 canais; TG = so ENTRADA + LEITURA-LONG; reclaim/retoma DELETADOS; L1 ativada BULL-Cris',
  'Gatilho: sinais AMD/price-shock saiam no grupo rotulados L1 EMA21 4H (7 modulos importavam telegram_notify' || chr(10) ||
  'da L1 que prefixava tudo) + scoreboard 30d. Decisoes Cris por linha: Cp APROVADA (4-0 +12R) - A1/A2 APROVADA' || chr(10) ||
  '(6-10 +8R, discricao melhora streak) - L1 ATIVA (regime BULL validado manualmente 19/08; gate ja OFF desde' || chr(10) ||
  '05/08; fecho 4H 4459 abriu EMA21) - L2 MANTIDA (0-4 mecanico mas leitura-Cris ao adiar p/ FVG inferior =' || chr(10) ||
  '~3W-1L; PENDENTE research fine-tune) - RECLAIM DELETADO do codigo (1W-14L -11R) - RETOMA removida -' || chr(10) ||
  'Reader E2+vela: sinal SO LONG, SHORT = contexto anti-faca em shadow - AMD = ESTRATEGIA 2 fases (fase1 setup' || chr(10) ||
  'busca FVG inferior no 1H, fase2 candidato c/ niveis) - candle-reader DESLIGADO (custo Opus ~300/dia, sobreposto' || chr(10) ||
  'ao E2) - AVISOS todos em aviso_shadow.jsonl - INFRA nunca ao Telegram (infra_events.jsonl, Claude monitora).' || chr(10) ||
  'Formato unico A (vertical alinhado, texto plano, sem tabelas): canal-nome-TF / direcao / entry-SL-alvo(R) /' || chr(10) ||
  'hora Lisboa - decisao humana - #N. Engine de B: 0 candidatos em 3020 ciclos (Layer1 nunca marcou RANGE).' || chr(10) ||
  'PENDENTES: research L2 fine-tune - Layer1 RANGE-recall (falhou 2 ranges reais; override manual OU research) -' || chr(10) ||
  'avaliar aviso-shadow no futuro.',
  array['seed:memory_delta_20260819_signal_reorg_deep_cleanup','sinais','notify','reorg','xau'],
  'alert-bridge/notify.py', 'active'),
 (md5('deep_cleanup_20260819')::uuid, 'private', 'internal', 'project',
  'DEEP AUDIT + CLEANUP AUTONOMO 19/08 (L1-L7, 18 commits pushed ate 6864dcf): sistema simplificado sem tocar alpha',
  'Auditoria 5 agentes (doc DEEP_AUDIT_20260819.md A-O) + execucao autonoma aprovada pelo Cris (governanca nova:' || chr(10) ||
  'lotes autonomos, travas so p/ risco real). FIXES: freshness E0/MTF+a1a2 (decidiam sobre store congelado ate' || chr(10) ||
  '45min) - AMD ping2 nao marca enviado em falha - choch_guard fail-open em dossie velho - market_open por' || chr(10) ||
  'America/New_York (DST; 21:00utc hardcoded errava 1h no inverno) - R real nos rotulos - TZ Lisboa scoreboard -' || chr(10) ||
  'htf_location_gate (rename de reclaim_location_gate c/ shim) - zonas zone_watch com expires - news_gate prefere' || chr(10) ||
  'evento futuro. CENTRALIZACAO: e2/L1/L2 transportes 100% via notify.py (urlopen removidos); guard executavel' || chr(10) ||
  'check_single_telegram_sender = BLOCKER em regressao. O1: claude_recheck OFF permanente (flag' || chr(10) ||
  '.claude_recheck_off; E2 = unico caminho LLM; recheck idle desde 02/08). O3: cluster D2R 14 ficheiros + ilha' || chr(10) ||
  'input_normalization ARQUIVADOS (alert-bridge/archive/cleanup_20260819); DELETE c/ prova: config_stack,' || chr(10) ||
  'arm_level, investinglive_news. O4: RAW canonico FICA em research/revalidation, contrato' || chr(10) ||
  'REGIME_AND_RAW_AUTHORITY_CONTRACT_20260819 (Layer1=macro, v5-4H=auxiliar, regime_l1_v4=gate interno L1;' || chr(10) ||
  'dono do RAW = bar_store). O6: realtime-monitor+fj-ws plists _disabled_. ROBUSTEZ: ThrottleInterval 45s nos' || chr(10) ||
  '8 KeepAlive; price-shock no health_check; selftest routing do notify. C2 do audit provado FALSO (heartbeat' || chr(10) ||
  'poll so atualiza apos escrita ok). NAO TOCADO: RAW (so appends), engines/gates aprovados, thresholds,' || chr(10) ||
  'ledgers, parity/reports (evidencia). DIFERIDO c/ razao: consolidar SL-first 4x (risco outcomes),' || chr(10) ||
  'fallback_ok regime/price_shock, flag morta E2_CONT_SIGNAL, lock RAW 4H dual-writer.',
  array['seed:memory_delta_20260819_signal_reorg_deep_cleanup','cleanup','audit','arquitetura'],
  'docs/architecture/DEEP_AUDIT_20260819.md', 'active'),
 (md5('incidente_tv_crash_20260818')::uuid, 'private', 'internal', 'reference',
  'Incidente 18/08 02:11: lap travou -> TV sem CDP -> stack cego na janela da rejeicao 4436; short perdido',
  'Rejeicao impressa 02:00 (sweep 4436.2 + fecho terco inferior no OB supply 4428-4436) era detetavel; stack' || chr(10) ||
  'esteve cego 02:11-03:45 (TV relancado sem CDP). tv_launch restaura; tabs XAU persistem, DXY 1D perde-se' || chr(10) ||
  '(recriacao manual Cris; tab_new via MCP nao cria chart target). Cris: sem alarme novo (lap travado e raro).' || chr(10) ||
  'Fix estrutural que ficou: freshness gates no E0/a1a2 (cleanup 19/08) limitam decisao sobre dados velhos.',
  array['seed:memory_delta_20260819_signal_reorg_deep_cleanup','incidente','cdp','freshness'],
  'docs/architecture/DEEP_AUDIT_20260819.md', 'active')
on conflict (id) do nothing;
