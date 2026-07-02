#!/usr/bin/env python3
"""Generate supabase/seeds/memory_cards_wave2c_seed.sql from memory cards (Wave 2C, sub-batch 1).

Same contract as generate_wave2a/2b_seed.py: reads ONLY frontmatter (description +
metadata.type) — never the card body. Archive/index migration: historical and
refuted research preserved as retrievable index, NOT hot memory. Zero RAW,
zero edge parameters, zero secrets.
See docs/architecture/SUPABASE_MEMORY_WAVE2C_REVIEW_20260702.md.

Selection (50): 17 remaining reference cards + 33 clearly-cold project cards
(refuted/invalidated/retracted/deactivated -> deprecated; session snapshots,
audits and Caminho A/B research trail -> archived; created-but-inactive -> dormant).
Excluded: legacy/no-metadata (Wave 2D), remaining project historicals (2C sub-batch 2).

Idempotent: id = md5('seed:memory_cards_wave2c:<filename>')::uuid + ON CONFLICT.
Apply is ALWAYS manual (Cris via SQL Editor, DEV only). MCP stays read-only.

Usage: python3 scripts/memory/generate_wave2c_seed.py
"""
import os
import re

MEM = os.path.expanduser('~/.claude/projects/-Users-cristrein-tradingview-mcp/memory')
OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'supabase', 'seeds',
                   'memory_cards_wave2c_seed.sql')
TAG = 'seed:memory_cards_wave2c'
WAVE = '2C'

# (filename, scope, status)
CARDS = [
    # Reference restantes (17) — lookup util, mantidas active salvo superseded
    ('reference_bubbles_auction_theory.md', 'private', 'active'),
    ('reference_cdp_wedged_diagnosis.md', 'product', 'active'),
    ('reference_cloudflared_tunnel.md', 'private', 'active'),
    ('reference_d2r_daily_logs.md', 'private', 'archived'),
    ('reference_hardware.md', 'private', 'active'),
    ('reference_imac_bridge.md', 'private', 'active'),
    ('reference_L2_SMC_definitions_canonicas.md', 'private', 'active'),
    ('reference_long_position_overrides_ticks_bug.md', 'product', 'active'),
    ('reference_market_microstructure_explained_leonardo.md', 'private', 'active'),
    ('reference_market_microstructure_philosophy.md', 'private', 'active'),
    ('reference_mcp_ohlcv_time_range.md', 'product', 'active'),
    ('reference_SMC_Unified_Rebuild_v0_preregistro.md', 'private', 'active'),
    ('reference_svp_value_area_provenance.md', 'private', 'active'),
    ('reference_system_leigo_map.md', 'private', 'active'),
    ('reference_trade_plotting_canonical.md', 'private', 'active'),
    ('reference_xau_4h_backtest_resumo_leonardo.md', 'private', 'active'),
    ('reference_xau_4h_prints_archive.md', 'private', 'active'),
    # Project refutados/invalidados/retratados/deactivated (11) -> deprecated
    ('project_caminho_a_v3_A1_BALANCE_OFICIAL.md', 'private', 'deprecated'),
    ('project_caminho_a_v3_A1_PRIME_SUPERTREND_OFICIAL.md', 'private', 'deprecated'),
    ('project_caminho_a_v3_PR50n_pullback_reclaim.md', 'private', 'deprecated'),
    ('project_xau_15m_direction_short_mirror_refuted.md', 'private', 'deprecated'),
    ('project_xau_15m_macro_bottom_refuted.md', 'private', 'deprecated'),
    ('project_xau_15m_window_cleaning_refuted.md', 'private', 'deprecated'),
    ('project_xau_15m_entry_engine2.md', 'private', 'deprecated'),
    ('project_l2_bpt_legbear_block.md', 'private', 'deprecated'),
    ('project_l2_bpt_volume_1dbear_confluence.md', 'private', 'deprecated'),
    ('project_bubbles_nas_shadow.md', 'private', 'deprecated'),
    ('project_smc_btc_audit_v3.md', 'private', 'deprecated'),
    # Snapshots de sessao / audits historicos (6) -> archived
    ('project_checkpoint_2026_06_14.md', 'private', 'archived'),
    ('project_session_2026_05_21_consolidated.md', 'private', 'archived'),
    ('project_session_2026_05_22_23_consolidated.md', 'private', 'archived'),
    ('project_sessao_autonoma_2026_06_06_resultados.md', 'private', 'archived'),
    ('project_lookahead_audit_2026_06_06.md', 'private', 'archived'),
    ('project_raw_revalidation_2026_06_03.md', 'private', 'archived'),
    # Caminho A trilha historica (7)
    ('project_caminho_a_L1_roadmap_pos_eur_test.md', 'private', 'archived'),
    ('project_caminho_a_L1_v1_F4F5_status_candidato_escasso.md', 'private', 'archived'),
    ('project_caminho_a_padroes_visuais_5_layers.md', 'private', 'archived'),
    ('project_caminho_a_pending_validations.md', 'private', 'archived'),
    ('project_caminho_a_v3_A1_prime_preregistro.md', 'private', 'archived'),
    ('project_caminho_a_v3_preregistro.md', 'private', 'archived'),
    ('project_pine_alerts_v1.md', 'private', 'dormant'),
    # Caminho B trilha historica (9) -> archived (findings absorvidos; estrategia dormant na 2A)
    ('project_caminho_b_fraqueza_2020_2022.md', 'private', 'archived'),
    ('project_caminho_b_hipoteses_30_grupos.md', 'private', 'archived'),
    ('project_caminho_b_raw_v1_strata_B_C.md', 'private', 'archived'),
    ('project_caminho_b_score_filter_approved.md', 'private', 'archived'),
    ('project_caminho_b_v_stair_exit_approved.md', 'private', 'archived'),
    ('project_caminho_b_v15_AB_combined.md', 'private', 'archived'),
    ('project_caminho_b_v16_composite_filter_approved.md', 'private', 'archived'),
    ('project_caminho_b_v16_vstair_v6_climax_approved.md', 'private', 'archived'),
    ('project_caminho_b_volume_features.md', 'private', 'archived'),
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
-- SUPABASE MEMORY — CARDS WAVE {WAVE} (sub-batch 1) · {TAG}
-- gerado por scripts/memory/generate_wave2c_seed.py
-- ============================================================================
-- Review: docs/architecture/SUPABASE_MEMORY_WAVE2C_REVIEW_20260702.md
-- {len(CARDS)} memory cards historicos/reference -> memory_items (archive/index).
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
