#!/usr/bin/env python3
"""L2 Detector v2.2 Audit vs Ground Truth v1."""
import json
from datetime import datetime, timezone
import sys
sys.path.insert(0, '/tmp')
from L2_detector_v2_2 import RAW, candidate_l2_v2_2, run_candidate_generator
from collections import Counter

GT = json.load(open('/tmp/L2_ground_truth_v1.json'))


def parse_ts(s):
    return int(datetime.strptime(s, '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc).timestamp())


def idx_at_ts(ts):
    for i, b in enumerate(RAW):
        if b['ts_epoch'] == ts:
            return i
    return None


print("Rodando L2 Detector v2.2...")
candidates = run_candidate_generator()
cand_by_idx = {t['entry_idx']: t for t in candidates}
print(f"Total candidatos: {len(candidates)}")
print()

# AUDIT 1 — BOM recall
print('='*120)
print('AUDIT 1 — BOM_HIGH recall (16 eventos)')
print('='*120)

bom_hits = 0
bom_misses = []
bom_detail = []

for ev in GT['BOM_HIGH']:
    gt_id = ev['GT_ID']
    ts = parse_ts(ev['entry_ts_utc'])
    i = idx_at_ts(ts)
    if i is None:
        bom_misses.append((gt_id, 'bar_not_in_raw', None))
        print(f"  ✗ {gt_id}: BAR NÃO ENCONTRADO")
        continue
    direct_hit = i in cand_by_idx
    near_hit = None
    if not direct_hit:
        for di in range(-2, 3):
            if di == 0: continue
            if (i+di) in cand_by_idx:
                near_hit = i+di
                break
    if direct_hit:
        bom_hits += 1
        c = cand_by_idx[i]
        bom_detail.append((gt_id, ev['entry_ts_utc'], 'DIRETO', c))
        print(f"  ✓ {gt_id} {ev['entry_ts_utc']}: DIRETO (tipo {c['tipo']}, source {c['source']}, variant {c['variant']})")
    elif near_hit is not None:
        bom_hits += 1
        c = cand_by_idx[near_hit]
        bom_detail.append((gt_id, ev['entry_ts_utc'], f'NEAR{near_hit-i:+d}', c))
        print(f"  ~ {gt_id} {ev['entry_ts_utc']}: NEAR ±{abs(near_hit-i)} (tipo {c['tipo']}, source {c['source']})")
    else:
        r = candidate_l2_v2_2(i)
        reason = r.get('reject', 'no_result') if r else 'no_result'
        all_rej = r.get('all_rejections', [])[:3] if r else []
        bom_misses.append((gt_id, reason, all_rej))
        print(f"  ✗ {gt_id} {ev['entry_ts_utc']}: NÃO É CANDIDATO ({reason})")
        for r_msg in all_rej:
            print(f"      → {r_msg}")

print(f"\nBOM candidatos: {bom_hits}/{len(GT['BOM_HIGH'])}")


# AUDIT 2 — NAOs com ts
print()
print('='*120)
print('AUDIT 2 — NAOs com ts')
print('='*120)
nao_as_cand = 0
nao_correct_reject = 0
for ev in GT['NAO_CONFIRMED']:
    gt_id = ev['GT_ID']
    if 'entry_ts_utc' not in ev:
        continue
    ts = parse_ts(ev['entry_ts_utc'])
    i = idx_at_ts(ts)
    if i is None: continue
    direct_hit = i in cand_by_idx
    near_hit = any((i+di) in cand_by_idx for di in range(-2, 3) if di != 0)
    if direct_hit or near_hit:
        nao_as_cand += 1
        idx_used = i if direct_hit else next(i+di for di in range(-2, 3) if di != 0 and (i+di) in cand_by_idx)
        c = cand_by_idx[idx_used]
        print(f"  ✗ {gt_id} {ev['entry_ts_utc']}: VIROU CANDIDATO (tipo {c['tipo']}, source {c['source']})")
    else:
        nao_correct_reject += 1
        r = candidate_l2_v2_2(i)
        reason = r.get('reject', '?') if r else '?'
        print(f"  ✓ {gt_id} {ev['entry_ts_utc']}: REJEITADO ({reason})")


# AUDIT 3 — Densidade
print()
print('='*120)
print('AUDIT 3 — Densidade global')
print('='*120)
by_year = Counter()
by_tipo = Counter()
by_source = Counter()
by_variant = Counter()
for t in candidates:
    y = datetime.fromtimestamp(RAW[t['entry_idx']]['ts_epoch'], tz=timezone.utc).year
    by_year[y] += 1
    by_tipo[t['tipo']] += 1
    by_source[t['source']] += 1
    by_variant[t['variant']] += 1
print(f"  Anual: {dict(by_year)}")
print(f"  Tipos: {dict(by_tipo)}")
print(f"  Sources: {dict(by_source)}")
print(f"  Variants: {dict(by_variant)}")
print(f"  Total: {len(candidates)} / {len(by_year)} anos = {len(candidates)/len(by_year):.1f}/ano")


# AUDIT 4 — Sources em BOMs detectados
print()
print('='*120)
print('AUDIT 4 — Sources usadas em cada BOM detectado')
print('='*120)
src_in_bom = Counter()
for gt_id, ts_str, mode, c in bom_detail:
    src_in_bom[c['source']] += 1
    print(f"  {gt_id} ({ts_str}, modo {mode}): {c['source']} | tipo {c['tipo']} | variant {c['variant']}")
print(f"\nSources mais usadas em BOM: {dict(src_in_bom)}")


# SUMÁRIO
print()
print('='*120)
print('SUMÁRIO FINAL — L2 Detector v2.2 vs v2.1')
print('='*120)
total_bom = len(GT['BOM_HIGH'])
print(f"  BOM candidatos v2.2: {bom_hits}/{total_bom} ({bom_hits*100//total_bom}%)")
print(f"  BOM candidatos v2.1: 8/16 (50%) — comparação")
print(f"  Improvement: {bom_hits - 8:+d} BOMs")
print(f"  NAO viraram candidatos: {nao_as_cand}")
print(f"  NAO corretamente rejeitados: {nao_correct_reject}")
print(f"  Densidade total: {len(candidates)} / {len(by_year)} anos")
print(f"  Meta ≥14/16: {'✓ ATINGIU' if bom_hits >= 14 else '✗ NÃO ATINGIU'}")
