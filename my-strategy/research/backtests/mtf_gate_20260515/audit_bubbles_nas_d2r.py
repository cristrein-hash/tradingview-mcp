#!/usr/bin/env python3
"""Opção A — parse claude_stdout dos 290 D2R records, extrair menções estruturais
de Market Order Bubbles e NAS TOP/BOTTOM, cruzar com r_outcome.

Padrões procurados em stdout:
  bubble_cluster_present: regex "cluster" + "bubble" próximos OU "shapes >= 3"
  bubble_count: total de Shapes mencionados (se número aparece)
  nas_signal: TOP / BOTTOM / NONE
"""
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
from collections import defaultdict

RESEARCH_LOG = '/Users/cristrein/tradingview-mcp/alert-bridge/logs/setup_research_log.jsonl'
R_OUTCOME_LOG = '/Users/cristrein/tradingview-mcp/alert-bridge/logs/setup_r_outcome_log.jsonl'
OUT_DIR = Path(__file__).parent


# Regex patterns
RE_CLUSTER_POSITIVE = re.compile(
    r'(cluster[^.]*bubble|bubble[^.]*cluster|shapes?\s*[:=]?\s*[3-9]\d*|'
    r'✓[^✗]*(cluster|bubble)|3\+\s*bubbles|bubble\s*cluster)',
    re.IGNORECASE
)
RE_CLUSTER_NEGATIVE = re.compile(
    r'(sem\s+cluster|✗[^✓]*(cluster|bubble)|no\s+bubble|ausência[^.]*bubble|'
    r'shapes?\s*[:=]?\s*0(?!\d)|0\s+bubble|bubbles?\s+ausente|sem\s+bubble)',
    re.IGNORECASE
)
RE_NAS_TOP = re.compile(r'nas[^a-z]*top(?!\s*/\s*bottom)|nas_top', re.IGNORECASE)
RE_NAS_BOTTOM = re.compile(r'nas[^a-z]*bottom|nas_bot', re.IGNORECASE)
RE_SHAPES_NUM = re.compile(r'shapes?\s*[:=]?\s*(\d+)', re.IGNORECASE)


def classify_bubble_state(stdout):
    """Returns 'cluster_present' | 'cluster_absent' | 'unclear'"""
    if not stdout:
        return 'unclear'
    has_neg = bool(RE_CLUSTER_NEGATIVE.search(stdout))
    has_pos = bool(RE_CLUSTER_POSITIVE.search(stdout))
    # negativos prevalecem (texto explícito de "sem cluster")
    if has_neg and not has_pos:
        return 'cluster_absent'
    if has_pos and not has_neg:
        return 'cluster_present'
    if has_pos and has_neg:
        # ambíguo — pegar Shapes:N
        m = RE_SHAPES_NUM.search(stdout)
        if m:
            n = int(m.group(1))
            return 'cluster_present' if n >= 3 else 'cluster_absent'
        return 'unclear'
    return 'unclear'


def classify_nas(stdout):
    """Returns 'TOP' | 'BOTTOM' | 'BOTH' | 'NONE'"""
    if not stdout:
        return 'NONE'
    has_top = bool(RE_NAS_TOP.search(stdout))
    has_bot = bool(RE_NAS_BOTTOM.search(stdout))
    if has_top and has_bot:
        return 'BOTH'
    if has_top:
        return 'TOP'
    if has_bot:
        return 'BOTTOM'
    return 'NONE'


def extract_shapes_count(stdout):
    """Returns int or None."""
    if not stdout:
        return None
    m = RE_SHAPES_NUM.search(stdout)
    if m:
        return int(m.group(1))
    return None


def main():
    # 1. Load research log (event_id → stdout, symbol, classification, etc.)
    research = {}
    with open(RESEARCH_LOG) as f:
        for ln in f:
            try:
                d = json.loads(ln)
                eid = d.get('event_id')
                if not eid:
                    continue
                research[eid] = {
                    'symbol': d.get('base_symbol', '?'),
                    'tf': str(d.get('timeframe', '?')),
                    'cls': d.get('classification', ''),
                    'stdout': d.get('claude_stdout', '') or d.get('stdout', ''),
                }
            except: pass

    # 2. Load D2R outcomes
    d2r = []
    with open(R_OUTCOME_LOG) as f:
        for ln in f:
            try:
                d = json.loads(ln)
                eid = d.get('event_id')
                if not eid:
                    continue
                if d.get('theoretical_r_outcome') is None:
                    continue
                d2r.append({
                    'event_id': eid,
                    'r': float(d['theoretical_r_outcome']),
                    'r_label': d.get('r_outcome_label'),
                    'tradeable': d.get('would_have_been_tradeable'),
                    'cls_at_signal': d.get('classification_at_signal', ''),
                    'entry_model': d.get('entry_model'),
                })
            except: pass

    print(f"Research records: {len(research)}")
    print(f"D2R outcomes (com r): {len(d2r)}")

    # 3. Merge
    rows = []
    for r in d2r:
        eid = r['event_id']
        if eid not in research:
            continue
        rs = research[eid]
        bubble = classify_bubble_state(rs['stdout'])
        nas = classify_nas(rs['stdout'])
        shapes_n = extract_shapes_count(rs['stdout'])
        rows.append({
            'event_id': eid,
            'symbol': rs['symbol'],
            'tf': rs['tf'],
            'cls_at_signal': r['cls_at_signal'],
            'r': r['r'],
            'bubble': bubble,
            'nas': nas,
            'shapes_n': shapes_n,
        })
    df = pd.DataFrame(rows)
    print(f"D2R+research matched: {len(df)}")

    # 4. Análise — BUBBLE
    print(f"\n{'='*80}\nBUBBLE CLUSTER ANALYSIS\n{'='*80}")
    print(f"\nDistribuição:")
    print(df['bubble'].value_counts().to_string())

    print(f"\n--- All assets/TFs combined ---")
    for bub in ['cluster_present', 'cluster_absent', 'unclear']:
        sub = df[df['bubble'] == bub]
        if len(sub) == 0: continue
        r = sub['r'].values
        wins = r[r > 0].sum()
        losses = -r[r < 0].sum()
        pf = wins / losses if losses > 0 else 999
        print(f"  {bub:<20} n={len(sub):>3} | total={r.sum():>+7.2f}R | "
              f"avg={r.mean():>+5.2f}R | win={(r>0).mean()*100:>5.1f}% | PF={pf:.2f}")

    # Per asset/TF
    print(f"\n--- Por asset+TF (n>=10 cluster_present, top 8 cells) ---")
    by_cell = defaultdict(lambda: defaultdict(list))
    for _, row in df.iterrows():
        cell = f"{row['symbol']} {row['tf']}"
        by_cell[cell][row['bubble']].append(row['r'])
    rows_summary = []
    for cell, buckets in by_cell.items():
        present = buckets.get('cluster_present', [])
        absent = buckets.get('cluster_absent', [])
        if len(present) < 3 and len(absent) < 3:
            continue
        rows_summary.append({
            'cell': cell,
            'n_present': len(present),
            'n_absent': len(absent),
            'avg_present': np.mean(present) if present else 0,
            'avg_absent': np.mean(absent) if absent else 0,
            'win_present': (np.array(present) > 0).mean() * 100 if present else 0,
            'win_absent': (np.array(absent) > 0).mean() * 100 if absent else 0,
        })
    if rows_summary:
        sdf = pd.DataFrame(rows_summary)
        sdf['delta_avg'] = sdf['avg_present'] - sdf['avg_absent']
        sdf = sdf.sort_values('n_present', ascending=False).head(15)
        print(sdf.to_string(index=False, float_format='%.2f'))

    # 5. Análise — NAS
    print(f"\n{'='*80}\nNAS SIGNAL ANALYSIS\n{'='*80}")
    print(f"\nDistribuição:")
    print(df['nas'].value_counts().to_string())

    print(f"\n--- All assets/TFs combined ---")
    for nas in ['BOTTOM', 'TOP', 'BOTH', 'NONE']:
        sub = df[df['nas'] == nas]
        if len(sub) < 3: continue
        r = sub['r'].values
        wins = r[r > 0].sum()
        losses = -r[r < 0].sum()
        pf = wins / losses if losses > 0 else 999
        print(f"  NAS={nas:<8} n={len(sub):>3} | total={r.sum():>+7.2f}R | "
              f"avg={r.mean():>+5.2f}R | win={(r>0).mean()*100:>5.1f}% | PF={pf:.2f}")

    # 6. Combined Bubble × NAS
    print(f"\n{'='*80}\nCOMBINED — Bubble × NAS\n{'='*80}")
    for bub in ['cluster_present', 'cluster_absent']:
        for nas in ['BOTTOM', 'NONE', 'TOP']:
            sub = df[(df['bubble'] == bub) & (df['nas'] == nas)]
            if len(sub) < 3: continue
            r = sub['r'].values
            print(f"  bubble={bub[:8]:<8} nas={nas:<7} n={len(sub):>3} | "
                  f"avg={r.mean():>+5.2f}R | win={(r>0).mean()*100:>5.1f}%")

    # Save full results
    df.to_csv(OUT_DIR / 'bubbles_nas_d2r_analysis.csv', index=False)
    print(f"\n✅ Salvo em {OUT_DIR / 'bubbles_nas_d2r_analysis.csv'}")


if __name__ == '__main__':
    main()
