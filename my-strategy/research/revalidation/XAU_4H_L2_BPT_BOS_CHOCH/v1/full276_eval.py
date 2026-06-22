#!/usr/bin/env python3
"""FULL 276 — avaliação cronológica + ablation + error analysis. outcome/realR só p/ avaliação."""
import csv
from collections import Counter, defaultdict

D = "results"
rows = list(csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv")))
def fn(v):
    try: return float(v)
    except: return None
for r in rows: r['_r'] = fn(r['realR']); r['_y'] = r['datetime'][:4]
rows.sort(key=lambda r: r['datetime'])  # cronológico

def metrics(allowed):
    rs = [r['_r'] for r in allowed if r['_r'] is not None]
    if not rs: return {}
    w = [x for x in rs if x > 0]; l = [x for x in rs if x <= 0]
    sumR = sum(rs); pf = (sum(w)/abs(sum(l))) if l and sum(l) != 0 else float('inf')
    # equity / DD / streaks cronológicos
    cum = 0; peak = 0; dd = 0; cl = cw = mcl = mcw = 0; eq = []
    for x in rs:
        cum += x; peak = max(peak, cum); dd = max(dd, peak-cum)
        if x > 0: cw += 1; mcw = max(mcw, cw); cl = 0
        else: cl += 1; mcl = max(mcl, cl); cw = 0
        eq.append(round(cum, 2))
    return dict(n=len(rs), wins=len(w), losses=len(l), WR=round(len(w)/len(rs)*100, 1),
                sumR=round(sumR, 1), avgR=round(sumR/len(rs), 2), PF=round(pf, 2) if pf != float('inf') else 'inf',
                maxDD=round(dd, 1), max_lose_streak=mcl, max_win_streak=mcw), eq

allowed = [r for r in rows if r['blocked'] == 'NO']
blocked = [r for r in rows if r['blocked'] == 'YES']
M, eq = metrics(allowed)
Mall, _ = metrics(rows)

# ---- SUMMARY ----
summ = [("total_episodes", len(rows)), ("allow", len(allowed)), ("block", len(blocked))]
summ += list(M.items())
summ += [("baseline_all276_sumR", Mall['sumR']), ("baseline_all276_WR", Mall['WR']),
         ("baseline_all276_maxDD", Mall['maxDD']), ("baseline_all276_PF", Mall['PF'])]
# trades/year + por regime
for y, n in sorted(Counter(r['_y'] for r in allowed).items()): summ.append((f"allow_{y}", n))
with open(f"{D}/l2_bpt_full276_macro_bear_v3_summary.csv", "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n"); w.writerow(["metric", "value"]); [w.writerow(r) for r in summ]

# ---- EQUITY CURVE ----
with open(f"{D}/l2_bpt_full276_macro_bear_v3_equity_curve.csv", "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n"); w.writerow(["seq", "datetime", "realR", "cumR"])
    c = 0
    for i, r in enumerate(a for a in allowed if a['_r'] is not None):
        c += r['_r']; w.writerow([i+1, r['datetime'], round(r['_r'], 2), round(c, 2)])

# ---- por regime/leg ----
print("=== AGREGADO PRINCIPAL (allowed, cronológico) ===")
for k, v in M.items(): print(f"  {k}: {v}")
print(f"\n  baseline all-276 (sem gate): sumR={Mall['sumR']} WR={Mall['WR']}% maxDD={Mall['maxDD']} PF={Mall['PF']}")
print("\n=== WR/sumR por leg (allowed) ===")
byleg = defaultdict(list)
for r in allowed:
    if r['_r'] is not None: byleg[r['macro_reader_leg']].append(r['_r'])
for leg, rs in sorted(byleg.items(), key=lambda x: -len(x[1])):
    w = sum(1 for x in rs if x > 0)
    print(f"  {leg:26} n={len(rs):3} WR={w/len(rs)*100:4.0f}% sumR={sum(rs):+6.1f} avgR={sum(rs)/len(rs):+.2f}")

# ---- LAYER ABLATION ----
def cfg_block(r, layers):
    leg = r['macro_reader_leg']; rc = r['reason_codes']; bt = r['bottom_turn'] == 'True'
    # PRESERVE_BOTTOM_TURN sempre preserva (override) se carveout ativo
    if 'bottom_turn' in rc and r['decision'] == 'PRESERVE_BOTTOM_TURN' and 'carveout' in layers: return False
    if 'bear_markdown' in rc and 'bear' in layers: return True
    if 'range_chop' in rc and 'range' in layers: return True
    if 'corrective_shallow' in rc and 'corrective' in layers: return True
    return False
ABL = [("macro_reader_only", set()), ("+bear_markdown", {'bear','carveout'}),
       ("+range_chop", {'bear','range','carveout'}), ("+corrective", {'bear','range','corrective','carveout'}),
       ("full_v3 (carveout on)", {'bear','range','corrective','carveout'})]
# nota: carveout só importa quando há blocks; macro_reader_only = nada bloqueado
abl_rows = []
for name, layers in ABL:
    al = [r for r in rows if not cfg_block(r, layers)]
    m, _ = metrics(al)
    abl_rows.append(dict(config=name, allow=m['n'], block=len(rows)-m['n'], WR=m['WR'], sumR=m['sumR'],
                         avgR=m['avgR'], PF=m['PF'], maxDD=m['maxDD'], max_lose_streak=m['max_lose_streak']))
with open(f"{D}/l2_bpt_full276_macro_bear_v3_layer_ablation.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(abl_rows[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(abl_rows)
print("\n=== LAYER ABLATION ===")
print(f"  {'config':24}{'allow':6}{'block':6}{'WR':6}{'sumR':8}{'avgR':7}{'PF':6}{'maxDD':7}{'Lstreak':7}")
for r in abl_rows:
    print(f"  {r['config']:24}{r['allow']:<6}{r['block']:<6}{r['WR']:<6}{r['sumR']:<8}{r['avgR']:<7}{str(r['PF']):<6}{r['maxDD']:<7}{r['max_lose_streak']:<7}")

# ---- ERROR ANALYSIS ----
err = []
# winners bloqueados (perdas do gate)
wblk = sorted([r for r in blocked if r['_r'] is not None and r['_r'] > 0], key=lambda r: -r['_r'])
lpres = sorted([r for r in allowed if r['_r'] is not None and r['_r'] <= 0], key=lambda r: r['_r'])
for r in wblk[:12]: err.append(dict(type="winner_blocked", bar_idx=r['bar_idx'], datetime=r['datetime'], realR=r['_r'], reason=r['block_reason'], leg=r['macro_reader_leg']))
for r in lpres[:12]: err.append(dict(type="loser_preserved", bar_idx=r['bar_idx'], datetime=r['datetime'], realR=r['_r'], reason=r['decision'], leg=r['macro_reader_leg']))
with open(f"{D}/l2_bpt_full276_macro_bear_v3_error_analysis.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(err[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(err)
print(f"\n=== ERROR ANALYSIS ===")
print(f"  winners bloqueados: {sum(1 for r in blocked if r['_r'] and r['_r']>0)} (sumR perdido={sum(r['_r'] for r in blocked if r['_r'] and r['_r']>0):+.1f})")
print(f"  losers preservados: {sum(1 for r in allowed if r['_r'] is not None and r['_r']<=0)} (sumR={sum(r['_r'] for r in allowed if r['_r'] is not None and r['_r']<=0):+.1f})")
print(f"  blocked: winners={sum(1 for r in blocked if r['_r'] and r['_r']>0)} losers={sum(1 for r in blocked if r['_r'] is not None and r['_r']<=0)}")
top_wblk=wblk[:5]; print("  maiores winners bloqueados:",[(r['bar_idx'],r['_r'],r['block_reason']) for r in top_wblk])
