#!/usr/bin/env python3
"""Generate supabase/seeds/memory_cards_wave2c_b_seed.sql (Wave 2C, sub-batch 2).

Same contract as generate_wave2a/2b/2c_seed.py: reads ONLY frontmatter
(description + metadata.type) — never the card body. Archive/index migration of
the remaining project historicals: L2/BPT findings cluster (incl. overfade, as
flagged), 15M labs/studies, 4H strategy lineage, resolved bugs and records.
Dead research stays cold (archived/deprecated/superseded/dormant) — never
reactivated as hot memory. Zero RAW, zero edge parameters, zero secrets.
See docs/architecture/SUPABASE_MEMORY_WAVE2C_B_REVIEW_20260702.md.

Idempotent: id = md5('seed:memory_cards_wave2c_b:<filename>')::uuid + ON CONFLICT.
Apply is ALWAYS manual (Cris via SQL Editor, DEV only). MCP stays read-only.

Usage: python3 scripts/memory/generate_wave2c_b_seed.py
"""
import os
import re

MEM = os.path.expanduser('~/.claude/projects/-Users-cristrein-tradingview-mcp/memory')
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'supabase', 'seeds',
                   'memory_cards_wave2c_b_seed.sql')
TAG = 'seed:memory_cards_wave2c_b'
WAVE = '2C-b'

# (filename, scope, status) — todos private (research/estrategia)
CARDS = [
    # Cluster L2/BPT — findings historicos + modulos pausados (14)
    ('project_l2_bpt_bearleg_refined_approved.md', 'private', 'archived'),
    ('project_l2_bpt_convergence_elimination_signal_2026_06_24.md', 'private', 'archived'),
    ('project_l2_bpt_dynamic_structural_path_aggregator.md', 'private', 'dormant'),
    ('project_l2_bpt_episode_reading_276_library.md', 'private', 'archived'),
    ('project_l2_bpt_exit_lab_regime_bound.md', 'private', 'archived'),
    ('project_l2_bpt_feature_clean_sky_room_above.md', 'private', 'dormant'),
    ('project_l2_bpt_feature_conv_le1_skip.md', 'private', 'archived'),
    ('project_l2_bpt_lineB_bottom_add_rescue.md', 'private', 'archived'),
    ('project_l2_bpt_lineB_bull_absorb_preapproved.md', 'private', 'dormant'),
    ('project_l2_bpt_overfade_irreducible_at_entry_2026_06_23.md', 'private', 'archived'),
    ('project_l2_bpt_rabbithole_audit.md', 'private', 'archived'),
    ('project_l2_bpt_raw_backbone_rebuild_2026_06_23.md', 'private', 'archived'),
    ('project_l2_bpt_svp_acceptance_raw_2026_06_23.md', 'private', 'archived'),
    ('project_l2_bpt_telegram_bear_flags_FUTURE.md', 'private', 'dormant'),
    # Cluster XAU 15M — labs/estudos/kickoffs (10)
    ('project_xau_15m_bb_nas_leonardo_kickoff.md', 'private', 'archived'),
    ('project_xau_15m_bottom_power_engine.md', 'private', 'dormant'),
    ('project_xau_15m_bubbles_nas_clusters.md', 'private', 'archived'),
    ('project_xau_15m_engine_learnings.md', 'private', 'archived'),
    ('project_xau_15m_managed_agents_engine.md', 'private', 'dormant'),
    ('project_xau_15m_range_t2_t3_study.md', 'private', 'archived'),
    ('project_xau_15m_reversal_power.md', 'private', 'archived'),
    ('project_xau_15m_session_patterns.md', 'private', 'archived'),
    ('project_xau_15m_sl_exit_entry_lab.md', 'private', 'archived'),
    ('project_xau_15m_transversal_monforte_entry.md', 'private', 'dormant'),
    # Linhagem 4H/1H estrategias (11)
    ('project_xau_4h_backtest_v1.md', 'private', 'archived'),
    ('project_xau_4h_breakout_d1a_maturation.md', 'private', 'dormant'),
    ('project_xau_4h_long_FINAL_l1_l2_approved.md', 'private', 'active'),
    ('project_xau_4h_reversal_capitulation_long.md', 'private', 'dormant'),
    ('project_xau_4h_reversal_discr_v1_base_sweep.md', 'private', 'archived'),
    ('project_xau_4h_reversal_discretionary_long.md', 'private', 'dormant'),
    ('project_xau_4h_reversal_v1_4g_rws_a6.md', 'private', 'superseded'),
    ('project_xau_4h_reversal_v1_4j.md', 'private', 'dormant'),
    ('project_zone_touch_smc_module.md', 'private', 'dormant'),
    ('project_xau_1h_demand_reclaim_reentry_long_v1.md', 'private', 'dormant'),
    ('project_l1_refinement_approved_2026_06_16.md', 'private', 'archived'),
    # Findings bubbles/CF/MTF (4)
    ('project_bubble_gate_relaxed_by_tf.md', 'private', 'archived'),
    ('project_bubble_sell_regime_dependent.md', 'private', 'archived'),
    ('project_cf_vs_obs_v2.md', 'private', 'archived'),
    ('project_mtf_gate_audit.md', 'private', 'archived'),
    # Registros/bugs resolvidos/planos historicos (11)
    ('project_alerts_dataset_full.md', 'private', 'archived'),
    ('project_autonomous_execution_plan.md', 'private', 'archived'),
    ('project_cdp_chart_lock.md', 'private', 'archived'),
    ('project_creative_strategy_engine_managed_agents.md', 'private', 'dormant'),
    ('project_d2r_indicator_appendix.md', 'private', 'archived'),
    ('project_enrich_outcomes_v2_multi_lens.md', 'private', 'dormant'),
    ('project_forward_outcome_layer_spec.md', 'private', 'dormant'),
    ('project_hard_blocks_mechanical_subset.md', 'private', 'dormant'),
    ('project_hard_blocks_refactor.md', 'private', 'archived'),
    ('project_indicator_signals_dedup_bug.md', 'private', 'archived'),
    ('project_pine_slot_duplicate_bug.md', 'private', 'archived'),
]

BODY_OVERRIDE = {}

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
            if len(desc) >= 2 and desc[0] == desc[-1] and desc[0] in '"\'':
                desc = desc[1:-1].strip()
        if t:
            mtype = t.group(1).strip()
    return desc, mtype


def q(s):
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
            raise SystemExit(f'ABORT: {fn} sem metadata.type — mover para Wave 2D (revisao cuidadosa)')
        if FORBIDDEN.search(desc):
            raise SystemExit(f'ABORT: padrao proibido em {fn}')
        title = fn[:-3]
        visibility = 'internal' if scope == 'product' else 'private'
        tags_sql = ','.join(f"'{q(t)}'" for t in [TAG, f'wave:{WAVE}', f'type:{mtype}'])
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
-- SUPABASE MEMORY — CARDS WAVE {WAVE} (sub-batch 2) · {TAG}
-- gerado por scripts/memory/generate_wave2c_b_seed.py
-- ============================================================================
-- Review: docs/architecture/SUPABASE_MEMORY_WAVE2C_B_REVIEW_20260702.md
-- {len(CARDS)} project historicos -> memory_items (archive/index, nao hot memory).
-- body = frontmatter description (resumo curado); conteudo integral permanece
--   no card local (source_ref). Zero RAW, zero edge detalhado, zero secrets.
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
    print(f'OK: {len(CARDS)} rows -> {out}')


if __name__ == '__main__':
    main()
