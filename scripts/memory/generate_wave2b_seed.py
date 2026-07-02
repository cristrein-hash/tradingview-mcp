#!/usr/bin/env python3
"""Generate supabase/seeds/memory_cards_wave2b_seed.sql from memory cards (Wave 2B).

Same contract as generate_wave2a_seed.py: reads ONLY frontmatter (description +
metadata.type) of the 50 curated cards below — never the card body. Seed carries
title/summary/status/pointer; zero RAW, zero edge parameters, zero secrets.
See docs/architecture/SUPABASE_MEMORY_WAVE2B_REVIEW_20260702.md.

Selection: remaining feedback cards WITH metadata (43) + 7 active project cards
(L2/BPT knowledge, Reader, 15M state, macro engine, signals pipeline).
Excluded here: 6 legacy/no-metadata feedback cards (Wave 2D, careful review),
historic/refuted project + remaining reference cards (Wave 2C).

Idempotent: id = md5('seed:memory_cards_wave2b:<filename>')::uuid + ON CONFLICT.
Apply is ALWAYS manual (Cris via SQL Editor, DEV only). MCP stays read-only.

Usage: python3 scripts/memory/generate_wave2b_seed.py
"""
import os
import re

MEM = os.path.expanduser('~/.claude/projects/-Users-cristrein-tradingview-mcp/memory')
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'supabase', 'seeds',
                   'memory_cards_wave2b_seed.sql')
TAG = 'seed:memory_cards_wave2b'
WAVE = '2B'

# (filename, scope, status)
CARDS = [
    # Feedback restantes com metadata (43)
    ('feedback_anticipate_platform_constraints.md', 'product', 'active'),
    ('feedback_audit_full_list_mandatory.md', 'product', 'active'),
    ('feedback_bonferroni_pedidos_disciplina.md', 'product', 'active'),
    ('feedback_chart_cleanup_manual_cris.md', 'private', 'active'),
    ('feedback_check_input_alive_before_code.md', 'product', 'active'),
    ('feedback_collaboration_signals.md', 'private', 'active'),
    ('feedback_communication_style.md', 'private', 'active'),
    ('feedback_convergent_contextual_vs_aggregate_stats.md', 'product', 'active'),
    ('feedback_DA_calibrado_veto_vs_reporta.md', 'product', 'active'),
    ('feedback_deep_source_reading.md', 'product', 'active'),
    ('feedback_defense_in_depth_ordering.md', 'product', 'active'),
    ('feedback_defenses_dimensioned_to_signal_origin.md', 'product', 'active'),
    ('feedback_distance_quality_not_binary_presence.md', 'product', 'active'),
    ('feedback_dont_conclude_from_broken_period.md', 'product', 'active'),
    ('feedback_em_validacao_term.md', 'private', 'active'),
    ('feedback_especificidade_ativo_vs_generalizacao.md', 'private', 'active'),
    ('feedback_estatistica_aplicada_realidade.md', 'product', 'active'),
    ('feedback_event_driven_failures.md', 'product', 'active'),
    ('feedback_full_scan_after_pattern_fix.md', 'product', 'active'),
    ('feedback_manual_over_token.md', 'private', 'active'),
    ('feedback_memory_proactive_consultation.md', 'product', 'active'),
    ('feedback_multi_window_validation.md', 'product', 'active'),
    ('feedback_name_vs_definition_mismatch.md', 'product', 'active'),
    ('feedback_no_easy_paths.md', 'private', 'active'),
    ('feedback_no_generalize_negative_findings.md', 'product', 'active'),
    ('feedback_no_stderr_suppress_in_git.md', 'product', 'active'),
    ('feedback_no_tables_in_chat.md', 'private', 'active'),
    ('feedback_ob_detectors_micro_vs_macro.md', 'private', 'active'),
    ('feedback_outcome_proxy_lift_and_episode.md', 'product', 'active'),
    ('feedback_pine_alert_no_chart_required.md', 'product', 'active'),
    ('feedback_python_path_for_new_strategies.md', 'private', 'active'),
    ('feedback_raw_data_lookup_order.md', 'product', 'active'),
    ('feedback_recall_gate_before_backtest.md', 'product', 'active'),
    ('feedback_review_cadence.md', 'private', 'active'),
    ('feedback_root_cause_over_symptom.md', 'product', 'active'),
    ('feedback_sample_gate_for_rules.md', 'product', 'active'),
    ('feedback_self_verification_protocol.md', 'product', 'active'),
    ('feedback_strategy_validity_gate.md', 'private', 'active'),
    ('feedback_telegram_chat_ids_loop.md', 'product', 'active'),
    ('feedback_tv_alert_caches_pine.md', 'product', 'active'),
    ('feedback_validate_before_manual_user_work.md', 'product', 'active'),
    ('feedback_validate_plot_id_mapping.md', 'private', 'active'),
    ('feedback_xau_only_focus.md', 'private', 'active'),
    # Project ativos prioritarios (7)
    ('project_l2_bpt_consolidated_knowledge.md', 'private', 'active'),
    ('project_l2_bpt_reader_layer2_library_and_dossier.md', 'private', 'active'),
    ('project_l2_bpt_loser_cuts_consolidated.md', 'private', 'active'),
    ('project_l2_bpt_trade_qualification_engine.md', 'private', 'active'),
    ('project_xau_15m_fase1_state.md', 'private', 'active'),
    ('project_macro_structural_reading_engine.md', 'private', 'active'),
    ('project_indicator_signals_pipeline.md', 'private', 'active'),
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
-- SUPABASE MEMORY — CARDS WAVE {WAVE} · {TAG} · gerado por scripts/memory/generate_wave2b_seed.py
-- ============================================================================
-- Review: docs/architecture/SUPABASE_MEMORY_WAVE2B_REVIEW_20260702.md
-- {len(CARDS)} memory cards -> memory_items (1 card = 1 row).
-- body = frontmatter description (resumo curado); conteudo integral permanece
--   no card local (source_ref). Zero RAW, zero edge detalhado, zero secrets.
-- APLICACAO: MANUAL pelo Cris via SQL Editor (DEV). MCP permanece read-only.
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
