-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_raw_15m_extension_20260704
-- ============================================================================
-- Bloco: RAW_15M_EXTENSION_COLLECT_TO_TODAY_20260704 (+ post-close hygiene).
-- APLICACAO: MANUAL pelo Cris via SQL Editor (DEV, trading-system-memory-dev /
--   vgfofofozptrtjvtuyzy). MCP permanece read-only. NAO APLICADO nesta sessao.
-- IDEMPOTENTE: md5(seed_key)::uuid + on conflict (id) do nothing. Re-executavel.
-- CONTEUDO: zero RAW/candles, zero secrets, zero edge params. Titulos/resumos/pointers.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_raw_15m_extension_20260704'];
-- Total: 5 rows memory_items.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_raw_15m_extension_20260704:memory_items:raw-15m-extension-complete')::uuid,
  'product', 'internal', 'project',
  'RAW 15M extension COMPLETE — cobertura 2024-05-25 -> 2026-07-03 16:30 UTC (9 blocos)',
  '9o bloco coletado via safe_backtest_window --replay-collect (run-2 apos fix manual de visibilidade SMC/NAS; run-1 BLOCKED por drift de indicadores). 2710 snapshots / 2714 barras curadas. Validacao v2 na convencao do builder (last-write-wins cura corrida de captura). Promovido ao HD com sha256+gzip-t+roundtrip triplo-verificado + manifest. Derivados (primitives/bubbles/candidates 4502->4742) promovidos com prefixo antigo byte-identico; baseline N435 +291,5R reproduz. DA independente CONFIRMA.',
  array['seed:memory_delta_raw_15m_extension_20260704','raw-15m','coverage','extension'],
  'HD: raw_replay/XAUUSD/15M/XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz sha256=52e9d748a9c8be338147010bf65673290e966c648c5c937020411cbdb28ea705 · docs/architecture/RAW_15M_EXTENSION_COLLECT_TO_TODAY_{MANIFEST,REPORT}_20260704.md · commits feaae36+43a870c',
  'active'
),
(
  md5('seed:memory_delta_raw_15m_extension_20260704:memory_items:system-a-virgin-killcheck-inconclusive')::uuid,
  'product', 'internal', 'project',
  'Sistema A EMA-SHAKEOUT — kill-check virgem = VIRGIN_INCONCLUSIVE_N_LT_20 (N=0)',
  'Janela virgem 2026-05-25 -> 2026-07-03 e 100% BEAR pelo detector v5h (240/240 candidatos, recomputado pelo DA). Sistema A e BULL-only por construcao -> zero picks em todos os paineis (spec congelada e bounds htf). Criterios pre-registrados exigem N>=20: nao aprova nem mata. Status permanece EXPLORATORY_CALIBRATION / POSITIVO_FRAGIL; kill-criteria armados para proxima janela nao-BEAR.',
  array['seed:memory_delta_raw_15m_extension_20260704','system-a','killcheck','inconclusive'],
  'docs/architecture/XAU_15M_SYSTEM_A_VIRGIN_KILLCHECK_20260704.md · results/system_a_virgin_killcheck_summary.json',
  'active'
),
(
  md5('seed:memory_delta_raw_15m_extension_20260704:memory_items:system-a-stand-aside-bear')::uuid,
  'product', 'internal', 'project',
  'Sistema A stand-aside em BEAR = PASS_BEHAVIORAL_OBSERVATION_NOT_VALIDATION',
  'Numa queda de ~12% (4565->4166, low 3942), o Sistema A teria ficado 100% de fora (zero LONGs, zero perdas) — o gate de regime funcionou como desenhado. Base #4 (gate !=BEAR) e lane BEAR-pullback congelada tambem: 0 casos. Diagnostico rotulado: sem o gate, 1 trade loser. OBSERVACAO COMPORTAMENTAL, nao validacao: nao marca Sistema A validado nem refutado; nada de producao; SHORT nao abre automaticamente.',
  array['seed:memory_delta_raw_15m_extension_20260704','system-a','regime-gate','stand-aside'],
  'docs/architecture/XAU_15M_SYSTEM_A_VIRGIN_KILLCHECK_20260704.md',
  'active'
),
(
  md5('seed:memory_delta_raw_15m_extension_20260704:memory_items:htf-staleness-deferred')::uuid,
  'product', 'internal', 'project',
  'HTF 4H/1D staleness = DEFERRED (exige novas coletas de chart)',
  'htf_4H.primitives cobre ate 2026-06-09 (fonte: coleta 4H SVP_LUX de 10-jun) e htf_1D ate 2026-05-24 (coleta 1D ate 25-mai). Estender exige novas coletas replay 4H/1D (chart) — fora do escopo do bloco de higiene. Impacto atual nulo: dependencia do Sistema A de htf_demand_any = 0/53 picks historicos; janela virgem N=0. Lookups sao asof-stale (causais, nunca antecipam). Bloco futuro proprio quando necessario.',
  array['seed:memory_delta_raw_15m_extension_20260704','htf','staleness','deferred'],
  'docs/architecture/RAW_15M_EXTENSION_POST_CLOSE_CHECKPOINT_20260704.md',
  'active'
),
(
  md5('seed:memory_delta_raw_15m_extension_20260704:memory_items:source-guard-calibrated')::uuid,
  'product', 'internal', 'project',
  'Source guard 15M calibrado (2 classes de falso-positivo) — politica RAW-first intacta',
  'Calibracao cirurgica pos-extensao: (1) token proibido como NOME DE CAMPO sendo escrito (f["macro_bear"]=...) nao flagra mais (so uso como fonte); (2) exec do engine sancionado + intermediario deterministico lab_g_candidates.jsonl adicionados aos allowed tokens (lineage guard-PASS; RAW segue unica autoridade). Guard PASS 7/7 na cadeia inteira. Nenhum check removido.',
  array['seed:memory_delta_raw_15m_extension_20260704','source-guard','calibration'],
  'research/xau_15m_bb_nas_leonardo/_source_guard.py · docs/architecture/RAW_15M_EXTENSION_POST_CLOSE_HYGIENE_REPORT_20260704.md',
  'active'
)
on conflict (id) do nothing;

commit;

-- ============================================================================
-- ROLLBACK (manual, se necessario):
-- begin;
-- delete from memory_items where tags @> array['seed:memory_delta_raw_15m_extension_20260704'];
-- commit;
-- ============================================================================
