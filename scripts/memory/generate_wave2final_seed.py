#!/usr/bin/env python3
"""Generate supabase/seeds/memory_cards_wave2final_seed.sql (Wave 2FINAL — fecho da migracao).

Migra os cards restantes em batch conjunto (Decisao Cris 2026-07-02):
  Grupo A — project operacionais/config ainda ativos (status por evidencia;
            'active' de runtime so quando comprovado pelo Production Logic Re-Audit);
  Grupo B — legacy/no-metadata, revisados card a card (nunca inseridos cegamente;
            sem description confiavel -> body minimo padrao; nunca active sem
            justificativa explicita; 'unknown_review' quando duvidoso).

RECONCILIACAO 229/229 EMBUTIDA: este script varre o diretorio de memoria,
extrai os filenames ja migrados dos geradores das waves 2A/2B/2C/2C-b e ABORTA
se (migrados + este seed) != conjunto exato de cards no disco. Nao ha como
gerar o seed final com card faltando ou duplicado.

Mesmo contrato das waves anteriores: frontmatter description como body, zero
RAW/edge/secrets, id deterministico + ON CONFLICT, apply manual (Cris/SQL Editor),
MCP read-only. Review: docs/architecture/SUPABASE_MEMORY_WAVE2FINAL_REVIEW_20260702.md

Usage: python3 scripts/memory/generate_wave2final_seed.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
MEM = os.path.expanduser('~/.claude/projects/-Users-cristrein-tradingview-mcp/memory')
OUT = os.path.join(HERE, '..', '..', 'supabase', 'seeds', 'memory_cards_wave2final_seed.sql')
TAG = 'seed:memory_cards_wave2final'
WAVE = '2FINAL'
PRIOR_GENERATORS = ['generate_wave2a_seed.py', 'generate_wave2b_seed.py',
                    'generate_wave2c_seed.py', 'generate_wave2c_b_seed.py']

# (filename, scope, status, justificativa) — classificacao card a card
CARDS = [
    # ---- Grupo A: project operacionais/config (12) ----
    ('project_custom_ob_detector_v10.md', 'private', 'active',
     'ferramenta em uso: backbone L2 reconstruido do RAW Custom OB'),
    ('project_monitor_targets_leak.md', 'private', 'dormant',
     'backlog #14 aberto, sem trabalho ativo'),
    ('project_pipeline_fase3.md', 'private', 'dormant',
     'crons de enrich/report fora do runtime vivo (Re-Audit: runtime estreito)'),
    ('project_receiver_broker_prefix_normalization.md', 'private', 'active',
     'receiver VIVO comprovado pelo PRODUCTION_LOGIC_REAUDIT_20260702'),
    ('project_replay_historical_base_multitf.md', 'private', 'active',
     'base historica multi-TF existe e e usada (datasets RAW registrados)'),
    ('project_roadmap_post_xau_1h_v1.md', 'private', 'archived',
     'roadmap antigo superseded pela ordem de tarefas vigente'),
    ('project_smc_eur_audit_v3.md', 'private', 'archived',
     'EUR fora do foco XAU-only; shadow logging historico'),
    ('project_smc_xau_audit_v3.md', 'private', 'archived',
     'audit concluida; conclusoes absorvidas no conhecimento L2'),
    ('project_telegram_silencer_observacao.md', 'private', 'active',
     'config vigente do canal Telegram (Telegram/receiver vivos per Re-Audit)'),
    ('project_tf_15m_long_liberated.md', 'private', 'archived',
     'regra historica ligada ao contexto D2R (legado)'),
    ('project_tv_layouts_architecture.md', 'private', 'active',
     'layouts TradingView aprovados e em uso'),
    ('project_watchlist_focus_5_plus_usousd.md', 'private', 'active',
     'config vigente da watchlist'),
    # ---- Grupo A2: historicos recuperados pela reconciliacao embutida (2) ----
    ('project_external_factors_audit_roadmap.md', 'private', 'superseded',
     'audit/roadmap do EF v1.2 substituido pelo External Factors v2 (card 2A ativo)'),
    ('project_l2_bpt_sl_structural.md', 'private', 'superseded',
     'SL estrutural trade-a-trade substituido pelo SL_CONTEXT oficial (l2_bpt_sl_exit_approved, 2A)'),
    # ---- Grupo B: legacy/no-metadata (16), revisados card a card ----
    ('feedback_cadence.md', 'private', 'active',
     'regra comportamental ainda operante (trabalho em etapas/camadas), sintetizada no PRINCIPAL_1'),
    ('feedback_memory_methodology.md', 'product', 'active',
     'protocolo de memoria por sessao ainda operante'),
    ('feedback_partnership.md', 'private', 'active',
     'natureza da parceria (assistente colaborativo, nao automator) segue vigente'),
    ('feedback_session_persistence.md', 'product', 'active',
     'persistencia de memoria fim-de-sessao segue operante'),
    ('feedback_statistical_patience.md', 'product', 'active',
     'amostras pequenas = direcionais, nao verdictais — canon estatistico vigente'),
    ('feedback_trades_in_chat.md', 'private', 'active',
     'preferencia vigente do Cris: listas de trades no chat, nunca so ponteiro p/ MD'),
    ('project_d2r_state.md', 'private', 'archived',
     'estado de backfill D2R 2026-05-13; conceito D2R substituido (Forward Outcome Layer)'),
    ('project_execution_context.md', 'private', 'active',
     'contexto operacional ainda verdadeiro: conta simulada, zero trades reais'),
    ('project_external_factors.md', 'private', 'superseded',
     'EF v1 passive logging substituido pelo External Factors v2 (card 2A ativo)'),
    ('project_naming_proposal.md', 'private', 'unknown_review',
     'proposta de renomeacao sem evidencia de adocao — revisar com Cris'),
    ('project_operational_decisions.md', 'private', 'archived',
     'snapshot de decisoes 2026-05-13, superseded pelo status master'),
    ('project_oracle_score.md', 'private', 'deprecated',
     'DEACTIVATED 2026-05-21 (3 abordagens falharam)'),
    ('project_pending_work.md', 'private', 'archived',
     'backlog datado (maio/2026), superseded pela ordem de tarefas vigente'),
    ('project_xau_losing_patterns.md', 'private', 'archived',
     'finding historico n=7 (pequeno), preservado como indice'),
    ('reference_d2r_mechanics.md', 'private', 'archived',
     'mecanica do D2R (legado substituido)'),
    ('reference_files.md', 'private', 'unknown_review',
     'mapa de navegacao possivelmente stale pos-cleanups/cold-storage — revisar'),
]

FALLBACK_BODY = 'legacy/no-metadata card preserved as archive/index; see source_ref'
FORBIDDEN = re.compile(r'sbp_|eyJ|password|api_key|SERVICE_ROLE', re.IGNORECASE)


def all_disk_cards():
    return {f for f in os.listdir(MEM)
            if f.endswith('.md') and f not in ('MEMORY.md', 'MEMORY_ARCHIVE.md')}


def migrated_cards():
    got = set()
    for g in PRIOR_GENERATORS:
        txt = open(os.path.join(HERE, g), encoding='utf-8').read()
        got |= set(re.findall(r"\('([^']+\.md)',", txt))
    return got


def frontmatter(path):
    txt = open(path, encoding='utf-8').read()
    m = re.match(r'^---\n(.*?)\n---', txt, re.S)
    desc, mtype = '', ''
    if m:
        fm = m.group(1)
        d = re.search(r'^description:\s*(.+)$', fm, re.M)
        t = re.search(r'^\s*type:\s*(\S+)', fm, re.M)
        if d:
            desc = d.group(1).strip()
            if len(desc) >= 2 and desc[0] == desc[-1] and desc[0] in '"\'':
                desc = desc[1:-1].strip()
        if t:
            mtype = t.group(1).strip()
    return desc, mtype


def q(s):
    return s.replace("'", "''")


def main():
    disk = all_disk_cards()
    migrated = migrated_cards()
    ours = {fn for fn, *_ in CARDS}
    remaining = disk - migrated
    # ---- reconciliacao dura ----
    missing = remaining - ours          # cards no disco fora de todos os seeds
    stale = ours - remaining            # cards no seed que nao restam (dup/typo)
    print(f'RECONCILIACAO: disco={len(disk)} · migrados(2A/2B/2C/2C-b)={len(migrated)} '
          f'· restantes={len(remaining)} · neste seed={len(ours)}')
    if missing or stale:
        if missing:
            print('FALTAM NO SEED:', sorted(missing))
        if stale:
            print('NO SEED MAS NAO RESTANTES:', sorted(stale))
        raise SystemExit('ABORT: reconciliacao falhou — corrigir CARDS antes de gerar')
    print(f'RECONCILIACAO OK: {len(migrated)} + {len(ours)} = {len(disk)} / {len(disk)} cards')

    rows = []
    legacy_count = 0
    for fn, scope, status, why in CARDS:
        desc, mtype = frontmatter(os.path.join(MEM, fn))
        if not mtype:
            mtype = fn.split('_')[0].lower()
            legacy_count += 1
        if not desc:
            desc = FALLBACK_BODY
        if FORBIDDEN.search(desc):
            raise SystemExit(f'ABORT: padrao proibido em {fn}')
        title = fn[:-3]
        visibility = 'internal' if scope == 'product' else 'private'
        tags = [TAG, f'wave:{WAVE}', f'type:{mtype}']
        tags_sql = ','.join(f"'{q(t)}'" for t in tags)
        rows.append(
            "(\n"
            f"  md5('{TAG}:{fn}')::uuid,\n"
            f"  '{scope}', '{visibility}', '{q(mtype)}',\n"
            f"  '{q(title)}',\n"
            f"  '{q(desc)}',\n"
            f"  array[{tags_sql}],\n"
            f"  '~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/{fn}',\n"
            f"  '{status}'\n"
            ")"
        )

    header = f"""-- ============================================================================
-- SUPABASE MEMORY — CARDS WAVE {WAVE} (fecho da migracao) · {TAG}
-- gerado por scripts/memory/generate_wave2final_seed.py (reconciliacao 229/229 embutida)
-- ============================================================================
-- Review: docs/architecture/SUPABASE_MEMORY_WAVE2FINAL_REVIEW_20260702.md
-- {len(CARDS)} cards restantes -> memory_items: Grupo A operacionais/config +
--   Grupo B legacy/no-metadata (revisao card a card; 'unknown_review' quando duvidoso).
-- APLICACAO: MANUAL pelo Cris via SQL Editor (DEV). MCP permanece read-only.
--   Pos-Run, verificar no proprio SQL Editor:
--   SELECT count(*) FROM memory_items WHERE tags @> ARRAY['{TAG}'];  -- esperado {len(CARDS)}
-- IDEMPOTENTE: md5-uuid deterministico + ON CONFLICT (id) DO NOTHING.
-- Copiar SEMPRE do ficheiro/raw (nunca de render de chat — corrompe aspas).
-- ============================================================================

begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
"""
    footer = f"""
on conflict (id) do nothing;

commit;

-- ============================================================================
-- ROLLBACK (NAO EXECUTAR JUNTO — so em DEV, manual, sob autorizacao)
-- ============================================================================
-- begin;
-- delete from memory_items where '{TAG}' = any(tags);
-- commit;
-- ============================================================================
"""
    out = os.path.abspath(OUT)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(header + ',\n'.join(rows) + footer)
    print(f'OK: {len(CARDS)} rows -> {out} (tipos inferidos de prefixo: {legacy_count})')


if __name__ == '__main__':
    main()
