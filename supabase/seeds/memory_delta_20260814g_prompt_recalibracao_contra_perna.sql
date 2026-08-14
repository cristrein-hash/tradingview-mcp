insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('prompt_recalib_contra_perna_20260814')::uuid, 'private', 'internal', 'feedback',
  'Recalibracao prompt (impl B): CONTEXTO ESTRUTURAL 4H suspende o veto contra-perna — LIVE, forward=arbitro',
  'Cris 14/08 (impl B, sem shadow, forward=arbitro): READ_SYS (e2_quality) E TAPE_SYS (candle_reader) ganham a
  regra "CONTEXTO ESTRUTURAL 4H = MOLDURA". Consome a seccao do briefing (que consome market_context.json +
  sweep_reject_guard). Quando SWEEP-REJECT 4H ATIVO (distribuicao): veto "contra-perna" sobre SHORTS SUSPENSO
  (short na rejeicao de lower-high qualifica; o rotulo perna-up-1H e o dado atrasado; long dentro=faca ate a
  quebra). Quando QUEBRA 15M DADA (HH+HL): RETOMADA, long de estrutura legitimo (nao chop/absorcao). Sem a
  moldura impressa, doutrina de continuacao por inteiro. MOTIVO: auditoria dos 2 misses de 14/08 (retest 4410
  short recusado como contra-perna; reclaim 06:00 tratado como chop) = frame-anchoring sem contexto HTF de 1a
  classe. MUDA DECISAO/EDGE do reader -> DA=a propria auditoria dos misses; Cris autorizou direto, forward=arbitro
  via candle_reads/e2_verdicts. candle-reader+e2-quality+entry-validator recarregados.',
  array['seed:memory_delta_20260814g_prompt_recalibracao_contra_perna','reader','prompt','contra-perna','contexto-4h','forward'],
  'alert-bridge/candle_reader.py TAPE_SYS + e2_quality.py READ_SYS', 'active')
on conflict (id) do nothing;
