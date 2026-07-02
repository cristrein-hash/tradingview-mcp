#!/usr/bin/env python3
"""Generate supabase/seeds/memory_cards_wave2a_seed.sql from memory cards (Wave 2A).

Reads ONLY frontmatter (description + metadata.type) of the 50 curated cards below —
never the card body — so the seed carries title/summary/status/pointer, zero RAW,
zero edge parameters, zero massive content. Full nuance stays in the local card
(source_ref points to it). See docs/architecture/SUPABASE_MEMORY_WAVE2_PLAN.md.

Idempotent output: id = md5('seed:memory_cards_wave2a:<filename>')::uuid
+ ON CONFLICT (id) DO NOTHING, single transaction, batch tag in tags[].
Apply is ALWAYS manual (Cris via SQL Editor, DEV only). MCP stays read-only.

Usage: python3 scripts/memory/generate_wave2a_seed.py
"""
import os
import re

MEM = os.path.expanduser('~/.claude/projects/-Users-cristrein-tradingview-mcp/memory')
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'supabase', 'seeds',
                   'memory_cards_wave2a_seed.sql')
TAG = 'seed:memory_cards_wave2a'

# (filename, scope, status) — curated selection per SUPABASE_MEMORY_WAVE2_PLAN.md §4 (Wave 2A)
CARDS = [
    # PRINCIPAL (3)
    ('PRINCIPAL_1_claude_behavior.md', 'product', 'active'),
    ('PRINCIPAL_2_engineering_discipline.md', 'product', 'active'),
    ('PRINCIPAL_3_anti_myopia.md', 'product', 'active'),
    # Protocolos permanentes (23)
    ('feedback_never_use_slim_features.md', 'product', 'active'),
    ('feedback_no_oos_no_crossasset_validation.md', 'private', 'active'),
    ('feedback_validate_before_presenting.md', 'product', 'active'),
    ('feedback_never_capture_screenshot_unless_requested.md', 'product', 'active'),
    ('feedback_full_panel_always.md', 'private', 'active'),
    ('feedback_devils_advocate_fulltime.md', 'product', 'active'),
    ('feedback_close_only_causal_universal.md', 'product', 'active'),
    ('feedback_engine_objetivo_lucro_nao_winrate.md', 'private', 'active'),
    ('feedback_operational_viability_streak.md', 'private', 'active'),
    ('feedback_episode_unit_of_analysis_canon.md', 'product', 'active'),
    ('feedback_calibration_vs_validation_45_groups.md', 'private', 'active'),
    ('feedback_no_superficial_hasty_reading.md', 'product', 'active'),
    ('feedback_no_auto_recommend_next_lane.md', 'product', 'active'),
    ('feedback_pause_daemon_and_cron.md', 'private', 'active'),
    ('feedback_canonical_trade_plotting.md', 'private', 'active'),
    ('feedback_nas_long_short_never_top_bottom.md', 'private', 'active'),
    ('feedback_bubbles_polarity_rule.md', 'private', 'active'),
    ('feedback_indicators_raw_first.md', 'product', 'active'),
    ('feedback_never_declare_blocked_without_provenance_search.md', 'product', 'active'),
    ('feedback_macro_engine_methodological_canon.md', 'private', 'active'),
    ('feedback_prior_layers_conditional_evidence.md', 'product', 'active'),
    ('reference_backtest_methodology_checklist.md', 'product', 'active'),
    ('reference_loops_cron_governance.md', 'product', 'active'),
    # Production safety / regras operacionais (4)
    ('feedback_regras_operacionais_2026_06_06.md', 'private', 'active'),
    ('feedback_safe_backtest_window_executes.md', 'product', 'active'),
    ('feedback_backtest_chart_isolation.md', 'private', 'active'),
    ('feedback_use_plan_agent_for_architecture.md', 'product', 'active'),
    # Estrategias — estado atual (11)
    ('project_l2_bpt_structural_regime_level_engine.md', 'private', 'active'),
    ('project_l2_bpt_base_approved.md', 'private', 'active'),
    ('project_l2_bpt_sl_exit_approved.md', 'private', 'active'),
    ('project_xau_15m_swept_runner_signal.md', 'private', 'active'),
    ('project_xau_15m_loser_filters.md', 'private', 'active'),
    ('project_xau_15m_8atr_stack_preapproved.md', 'private', 'active'),
    ('project_xau_15m_regime_detector_and_direction.md', 'private', 'active'),
    ('project_regime_turnstate_engine.md', 'private', 'active'),
    ('project_external_factors_v2_plan.md', 'private', 'active'),
    ('project_xau_4h_long_objetivo_final.md', 'private', 'active'),
    ('project_fundednext_constraints.md', 'private', 'active'),
    # Producao — dormant/paused (5)
    ('project_xau_4h_reversal_v1_4g_rws_a6_a7.md', 'private', 'dormant'),
    ('project_xau_4h_caminho_b_long.md', 'private', 'dormant'),
    ('project_regime_classifier_v3_official.md', 'private', 'dormant'),
    ('project_python_strategy_monitor.md', 'private', 'dormant'),
    ('project_xau_l1_paused_2026_06_23.md', 'private', 'paused'),
    # User (2)
    ('user_role.md', 'private', 'active'),
    ('user_name_ris.md', 'private', 'active'),
    # Agentic OS / Supabase / EF fontes (2)
    ('project_supabase_memory_full_migration.md', 'private', 'active'),
    ('reference_gold_analysts_sources.md', 'private', 'active'),
]

# Cards whose frontmatter description is a stub — explicit body override
BODY_OVERRIDE = {
    'PRINCIPAL_3_anti_myopia.md':
        'PRINCIPAL #3 — protocolo anti-miopia (sintese permanente). '
        'Conteudo integral no card local.',
}

FORBIDDEN = re.compile(r'sbp_|eyJ|password|api_key|SERVICE_ROLE', re.IGNORECASE)


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
            # YAML: strip matching surrounding quotes leaked from frontmatter
            if len(desc) >= 2 and desc[0] == desc[-1] and desc[0] in '"\'':
                desc = desc[1:-1].strip()
        if t:
            mtype = t.group(1).strip()
    return desc, mtype


def q(s):
    """SQL single-quote escape."""
    return s.replace("'", "''")


def main():
    rows = []
    for fn, scope, status in CARDS:
        path = os.path.join(MEM, fn)
        desc, mtype = frontmatter(path)
        desc = BODY_OVERRIDE.get(fn, desc)
        if not desc:
            raise SystemExit(f'ABORT: {fn} sem description e sem override')
        if not mtype:
            mtype = fn.split('_')[0].lower()
            if mtype == 'principal':
                mtype = 'feedback'
        if FORBIDDEN.search(desc):
            raise SystemExit(f'ABORT: padrao proibido em {fn}')
        title = fn[:-3]  # sem .md
        visibility = 'internal' if scope == 'product' else 'private'
        tags = [TAG, f'wave:2A', f'type:{mtype}']
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
-- SUPABASE MEMORY — CARDS WAVE 2A · {TAG} · gerado por scripts/memory/generate_wave2a_seed.py
-- ============================================================================
-- Plano: docs/architecture/SUPABASE_MEMORY_WAVE2_PLAN.md
-- {len(CARDS)} memory cards criticos/atuais -> memory_items (1 card = 1 row).
-- body = frontmatter description do card (resumo curado); conteudo integral
--   permanece no card local (source_ref). Zero RAW, zero edge detalhado, zero secrets.
-- APLICACAO: MANUAL pelo Cris via SQL Editor (DEV). MCP permanece read-only.
-- IDEMPOTENTE: md5-uuid deterministico + ON CONFLICT (id) DO NOTHING.
-- Copiar SEMPRE do ficheiro/raw (nunca de render de chat — corrompe aspas).
-- ROLLBACK (comentado no fim): delete por batch tag.
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
    sql = header + ',\n'.join(rows) + footer
    out = os.path.abspath(OUT)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(sql)
    print(f'OK: {len(CARDS)} rows -> {out}')


if __name__ == '__main__':
    main()
