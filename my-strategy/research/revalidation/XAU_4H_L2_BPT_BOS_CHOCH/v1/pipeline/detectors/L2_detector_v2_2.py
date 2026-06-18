#!/usr/bin/env python3
"""L2 Detector v2.2 — escopo mínimo aprovado.

Mudanças sobre v2.1:
1. Adicionar source swing_high_simples (causal, sem futuro)
2. Adicionar source nivel_interno (mecânico, sem GT label)
3. Corrigir gather_polarities — não perder polaridades válidas
4. Janela timing 60 → 100 bars
5. NÃO usar gt_visual_explicita (vazamento ground truth)
6. NÃO remendar GT01

Único veto duro Camada 1: falso Tipo B dump direto (anti-GT06A).
Blockers continuam apenas diagnóstico.
"""
import json
import os
from datetime import datetime, timezone

RAW = [json.loads(l) for l in open(os.environ.get('L2_RAW_FEATURES','/tmp/raw_features_2020_2026.jsonl'))]
RAW.sort(key=lambda b: b['ts_epoch'])
N = len(RAW)

D = [json.loads(l) for l in open(os.environ.get('L2_1D_BARS','/tmp/XAU_1D_bars.jsonl'))]
D.sort(key=lambda b: b['time'])
ND = len(D)


def build_atr(p=14):
    a = [None]*N
    for i in range(p, N):
        trs = []
        for j in range(i-p+1, i+1):
            if j == 0: continue
            trs.append(max(RAW[j]['high']-RAW[j]['low'],
                           abs(RAW[j]['high']-RAW[j-1]['close']),
                           abs(RAW[j]['low']-RAW[j-1]['close'])))
        a[i] = sum(trs)/len(trs) if trs else None
    return a
ATR = build_atr(14)


def build_sma(p):
    a = [None]*N
    for i in range(p-1, N):
        a[i] = sum(RAW[j]['close'] for j in range(i-p+1, i+1)) / p
    return a
SMA50 = build_sma(50)


def build_sma_d(p):
    a = [None]*ND
    for i in range(p-1, ND):
        a[i] = sum(D[j]['close'] for j in range(i-p+1, i+1)) / p
    return a
SMA200_D = build_sma_d(200)


def daily_idx_for_4h(ts_4h):
    lo, hi = 0, ND
    while lo < hi:
        mid = (lo+hi)//2
        if D[mid]['time'] + 86400 <= ts_4h:
            lo = mid + 1
        else:
            hi = mid
    return lo - 1


LARGE_BUY = 'plot_4'
LARGE_SELL = 'plot_8'
SELL_PLOTS = {'plot_6', 'plot_8', 'plot_10'}


# ============================================================
# FONTES DE POLARIDADE (todas causais — sem futuro além de p+3)
# ============================================================

def find_fractal_3_3(i, lookback):
    out = []
    for p in range(max(3, i-lookback), i-2):
        if p < 6: continue
        h = RAW[p]['high']
        if any(RAW[j]['high'] >= h for j in range(p-3, p)): continue
        if any(RAW[j]['high'] >= h for j in range(p+1, min(p+4, i+1))): continue
        out.append({'source': 'fractal_3_3', 'p': p, 'level': h})
    return out


def find_fractal_2_2(i, lookback):
    out = []
    for p in range(max(2, i-lookback), i-1):
        if p < 4: continue
        h = RAW[p]['high']
        if any(RAW[j]['high'] >= h for j in range(p-2, p)): continue
        if any(RAW[j]['high'] >= h for j in range(p+1, min(p+3, i+1))): continue
        out.append({'source': 'fractal_2_2', 'p': p, 'level': h})
    return out


def find_topo_duplo(i, lookback, window=15, band_atr=0.5):
    out = []
    seen = set()
    for p1 in range(max(3, i-lookback), i-window-2):
        h1 = RAW[p1]['high']
        atr1 = ATR[p1]
        if not atr1: continue
        for p2 in range(p1+3, min(p1+window+1, i-2)):
            h2 = RAW[p2]['high']
            if abs(h2-h1) > band_atr*atr1: continue
            level = max(h1, h2)
            key = (p2, round(level, 0))
            if key in seen: continue
            seen.add(key)
            out.append({'source': 'topo_duplo', 'p': p2, 'level': level})
    return out


def find_range_top(i, lookback):
    out = []
    for p in range(max(20, i-lookback), i-2):
        h = RAW[p]['high']
        atr_v = ATR[p]
        if not atr_v: continue
        toques = sum(1 for j in range(p-20, p) if abs(RAW[j]['high']-h) <= 0.5*atr_v)
        if toques < 1: continue
        if any(RAW[j]['high'] > h for j in range(p-3, p)): continue
        if any(RAW[j]['high'] > h for j in range(p+1, min(p+4, i+1))): continue
        out.append({'source': 'range_top', 'p': p, 'level': h})
    return out


def find_swing_high_simples(i, lookback):
    """Causal: high máximo dos últimos 10 bars ANTES de p (sem usar futuro além de p)."""
    out = []
    for p in range(max(10, i-lookback), i-1):
        h = RAW[p]['high']
        # h é maior que todos os 10 bars anteriores
        if any(RAW[j]['high'] > h for j in range(p-10, p)): continue
        out.append({'source': 'swing_high_simples', 'p': p, 'level': h})
    return out


def find_nivel_interno(i, lookback):
    """High recente dentro de 1.5 ATR do close[i] (proximidade operacional)."""
    atr_e = ATR[i]
    if not atr_e: return []
    out = []
    for p in range(max(0, i-lookback), i-1):
        h = RAW[p]['high']
        if abs(h - RAW[i]['close']) > 1.5*atr_e: continue
        out.append({'source': 'nivel_interno', 'p': p, 'level': h})
    return out


def gather_polarities_v2_2(i, lookback=100):
    """Retorna TODAS polaridades de todas fontes, com dedup mínimo (só níveis idênticos)."""
    all_pol = []
    all_pol.extend(find_fractal_3_3(i, lookback))
    all_pol.extend(find_fractal_2_2(i, lookback))
    all_pol.extend(find_topo_duplo(i, lookback))
    all_pol.extend(find_range_top(i, lookback))
    all_pol.extend(find_swing_high_simples(i, lookback))
    all_pol.extend(find_nivel_interno(i, lookback))

    # Dedup mínimo: por (level rounded to 0.1, p exato) — preserva sources distintas
    seen = set()
    unique = []
    for pol in all_pol:
        key = (round(pol['level'], 1), pol['p'])
        if key in seen: continue
        seen.add(key)
        unique.append(pol)
    return unique


# ============================================================
# GATES DA CAMADA 1
# ============================================================

def find_break_permissive(p, level, max_k):
    for k in range(p+1, max_k+1):
        if RAW[k]['close'] > level:
            return k
    return None


def has_acceptance_minimal(k, level, max_horizon=6, min_closes=1):
    end = min(k + max_horizon, N-1)
    closes_above = sum(1 for j in range(k, end+1) if RAW[j]['close'] > level)
    return closes_above >= min_closes


def is_tipo_A(i, level):
    b = RAW[i]
    return b['close'] > b['open'] and b['close'] >= level


def is_tipo_B_absorption(i, level, atr_e):
    b = RAW[i]
    if b['close'] >= b['open']: return False
    rng = b['high'] - b['low']
    if rng == 0: return False
    lw = min(b['open'], b['close']) - b['low']
    if lw/rng < 0.20: return False
    if b['close'] < level - 0.7*atr_e: return False
    return True


def is_tipo_B_contextual(i, level, atr_e, min_sell=5):
    b = RAW[i]
    if b['close'] >= b['open']: return False
    if b['close'] < level - 0.7*atr_e: return False
    bubs = b.get('bubbles_recent') or []
    sell_count = sum(1 for bb in bubs if bb.get('plot_id') in SELL_PLOTS
                     and bb.get('bars_ago') is not None and 0 <= bb['bars_ago'] <= 10)
    return sell_count >= min_sell


def is_falso_tipo_B_dump_direto(i):
    """Único veto duro Camada 1."""
    b = RAW[i]
    if b['close'] >= b['open']: return False
    rng = b['high'] - b['low']
    if rng == 0: return False
    body = abs(b['close'] - b['open'])
    lw = min(b['open'], b['close']) - b['low']
    uw = b['high'] - max(b['open'], b['close'])
    return (body/rng > 0.5) and (lw/rng < 0.20) and (uw/rng < 0.10)


def candidate_l2_v2_2(i):
    """Camada 1 v2.2 — itera TODAS as polaridades sem prematuramente parar."""
    if ATR[i] is None: return None
    atr_e = ATR[i]

    if is_falso_tipo_B_dump_direto(i):
        return {'reject': 'falso_tipo_B_dump_direto'}

    polarities = gather_polarities_v2_2(i, lookback=100)
    if not polarities:
        return {'reject': 'sem_polaridade'}

    best = None
    best_score = -1
    rejection_reasons = []

    # Variant 1: BOS clássico (itera todas)
    for topo in polarities:
        p, level = topo['p'], topo['level']

        k = find_break_permissive(p, level, max_k=i-1)
        if k is None:
            rejection_reasons.append(f'{topo["source"]} p={p}: sem break')
            continue

        if not has_acceptance_minimal(k, level, max_horizon=6, min_closes=1):
            rejection_reasons.append(f'{topo["source"]} p={p}: aceitação nula')
            continue

        if i - k > 100 or i <= k:
            rejection_reasons.append(f'{topo["source"]} p={p}: timing >100 bars')
            continue

        band_top = level + 0.8 * atr_e
        if RAW[i]['low'] > band_top:
            rejection_reasons.append(f'{topo["source"]} p={p}: low entry > banda')
            continue

        if RAW[i]['close'] < level - 0.7 * atr_e:
            rejection_reasons.append(f'{topo["source"]} p={p}: close perdeu polaridade')
            continue

        if min(RAW[j]['low'] for j in range(k+1, i+1)) > band_top:
            rejection_reasons.append(f'{topo["source"]} p={p}: pullback não tocou banda')
            continue

        is_a = is_tipo_A(i, level)
        is_b = is_tipo_B_absorption(i, level, atr_e)
        is_b_ctx = is_tipo_B_contextual(i, level, atr_e)
        if not (is_a or is_b or is_b_ctx):
            rejection_reasons.append(f'{topo["source"]} p={p}: tipo candle não A/B/B_ctx')
            continue

        tipo = 'A' if is_a else ('B' if is_b else 'B_ctx')
        atr_k = ATR[k]
        bos_mag_atr = (RAW[k]['close']-level)/atr_k if atr_k else None
        score = (1.0 if topo['source'] in ('fractal_3_3', 'topo_duplo') else 0.5)
        score += (1 if RAW[i]['close'] >= level else 0)

        if score > best_score:
            best_score = score
            best = {
                'pivot_idx': p, 'pivot_ts': RAW[p]['ts_epoch'], 'level': level,
                'break_idx': k, 'entry_idx': i, 'entry_close': RAW[i]['close'],
                'source': topo['source'], 'tipo': tipo, 'variant': 'classic_BOS',
                'bos_mag_atr': bos_mag_atr, 'score': score
            }

    # Variant 2: Tipo B contextual sem BOS clássico (GT27)
    if best is None:
        for topo in polarities:
            p, level = topo['p'], topo['level']
            if abs(RAW[i]['close'] - level) > 1.0 * atr_e: continue
            if RAW[i]['close'] < level - 0.7*atr_e: continue
            if not is_tipo_B_contextual(i, level, atr_e, min_sell=5): continue
            score = 0.3
            if score > best_score:
                best_score = score
                best = {
                    'pivot_idx': p, 'pivot_ts': RAW[p]['ts_epoch'], 'level': level,
                    'break_idx': None, 'entry_idx': i, 'entry_close': RAW[i]['close'],
                    'source': topo['source'], 'tipo': 'B_ctx', 'variant': 'contextual_no_BOS',
                    'bos_mag_atr': None, 'score': score
                }

    if best:
        return best
    return {'reject': rejection_reasons[0] if rejection_reasons else 'no_match',
            'all_rejections': rejection_reasons[:5]}


def run_candidate_generator():
    raw = []
    for i in range(50, N):
        r = candidate_l2_v2_2(i)
        if r and 'pivot_idx' in r:
            raw.append(r)
    # Dedup por entry_idx (cada bar produz no máximo 1 trigger)
    by_entry = {}
    for t in raw:
        if t['entry_idx'] not in by_entry or t['score'] > by_entry[t['entry_idx']]['score']:
            by_entry[t['entry_idx']] = t
    return sorted(by_entry.values(), key=lambda x: x['entry_idx'])


if __name__ == '__main__':
    cands = run_candidate_generator()
    print(f"Candidatos v2.2: {len(cands)}")
    from collections import Counter
    by_tipo = Counter(c['tipo'] for c in cands)
    by_source = Counter(c['source'] for c in cands)
    by_variant = Counter(c['variant'] for c in cands)
    print(f"Tipos: {dict(by_tipo)}")
    print(f"Sources: {dict(by_source)}")
    print(f"Variants: {dict(by_variant)}")
