#!/usr/bin/env python3
"""DEVIL'S ADVOCATE independent re-derivation of l2_bpt_episode_reading_performance.csv.
Reads raw CSVs from scratch, does NOT import the original script's functions.
Purpose: falsify the reported TAKE metrics; check DD chronological ordering; compare TAKE vs ALL_276;
inspect for outcome leakage in reading input fields. Read-only on data; writes only this audit's stdout.
verified-at: 2026-06-23 (DA pass)"""
import json, csv
from collections import Counter
D = "results"

reads = [json.loads(l) for l in open(f"{D}/l2_bpt_episode_readings_276.jsonl")]
rd = {int(r['episode_id']): r['provisional_decision'] for r in reads}
rows = list(csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv")))
O = {int(r['bar_idx']): r for r in rows}

def f(v):
    try: return float(v)
    except: return None

# chronological order independent of original script
order = sorted(O, key=lambda b: O[b]['datetime'])

def metrics(bars, col, sort_chrono=True):
    seq = [b for b in (order if sort_chrono else bars) if b in bars]
    rs = [f(O[b][col]) for b in seq if f(O[b][col]) is not None]
    n = len(rs)
    if not n: return None
    wins = sum(1 for r in rs if r > 0)
    sumR = sum(rs)
    eq = peak = dd = 0.0
    for r in rs:
        eq += r; peak = max(peak, eq); dd = min(dd, eq - peak)
    mls = cur = 0
    for r in rs:
        if r <= 0: cur += 1; mls = max(mls, cur)
        else: cur = 0
    mws = cur = 0
    for r in rs:
        if r > 0: cur += 1; mws = max(mws, cur)
        else: cur = 0
    return dict(n=n, WR=round(100*wins/n,1), sumR=round(sumR,1), avgR=round(sumR/n,2),
                maxDD_R=round(dd,1), Lstreak=mls, Wstreak=mws)

POL = {'capped_realR':'capped_realR','vstair_120':'realized_vstair_120','letrun_120':'realized_letrun_120'}
TAKE = set(b for b in O if rd[b]=='TAKE')
ALL = set(O)
SKIP = set(b for b in O if rd[b]=='SKIP')

print("=== DECISION COUNTS ===", Counter(rd.values()))
for label, col in POL.items():
    t = metrics(TAKE, col)
    a = metrics(ALL, col)
    s = metrics(SKIP, col)
    print(f"\n#### {label} ####")
    print(f"  TAKE    : {t}")
    print(f"  ALL_276 : {a}")
    print(f"  SKIP    : {s}")
    # TAKE vs ALL comparison
    print(f"  Δ TAKE vs ALL: sumR {t['sumR']-a['sumR']:+.1f}  avgR {t['avgR']-a['avgR']:+.2f}  "
          f"DD {t['maxDD_R']-a['maxDD_R']:+.1f}  Lstreak {t['Lstreak']-a['Lstreak']:+d}")

# Item 2: prove DD is order-sensitive -> compute TAKE capped DD UNSORTED (by episode_id) to show it differs
print("\n=== DD ORDER SENSITIVITY (capped_realR, TAKE) ===")
sorted_dd = metrics(TAKE, 'capped_realR', sort_chrono=True)['maxDD_R']
# unsorted = iterate TAKE in episode_id ascending (NOT datetime)
rs_un = [f(O[b]['capped_realR']) for b in sorted(TAKE) if f(O[b]['capped_realR']) is not None]
eq=peak=dd=0.0
for r in rs_un:
    eq+=r; peak=max(peak,eq); dd=min(dd,eq-peak)
print(f"  chrono-sorted DD = {sorted_dd}   episode_id-sorted DD = {round(dd,1)}")

# Item 6: leakage scan — list all fields present in reading packets
print("\n=== READING PACKET FIELDS (leakage scan) ===")
print(sorted(reads[0].keys()))
# any field whose name hints at outcome
suspect = [k for k in reads[0] if any(t in k.lower() for t in
           ('outcome','real','mfe','mae','hit','run','pnl','profit','stop_before','realized','won','win','loss','result'))]
print("  name-suspect fields:", suspect)

# Item 2 (decisive): prove DD is order-dependent via random shuffles of TAKE under capped
import random
def dd_of(rs):
    eq=peak=dd=0.0
    for r in rs:
        eq+=r; peak=max(peak,eq); dd=min(dd,eq-peak)
    return round(dd,1)
rs_chrono=[f(O[b]['capped_realR']) for b in order if b in TAKE and f(O[b]['capped_realR']) is not None]
random.seed(0)
shuf_dds=[]
for _ in range(2000):
    c=rs_chrono[:]; random.shuffle(c); shuf_dds.append(dd_of(c))
print("\n=== DD ORDER-DEPENDENCE PROOF (capped TAKE) ===")
print(f"  chrono DD={dd_of(rs_chrono)}  shuffled DD range=[{min(shuf_dds)},{max(shuf_dds)}]  mean={round(sum(shuf_dds)/len(shuf_dds),1)}")
print(f"  -> DD varies with order, confirming the metric IS order-sensitive (chrono is the correct/required order)")

# Item 5: capped vs let-run WR on the SAME TAKE trades — how many capped 'wins' are scratched winners
take_bars=[b for b in order if b in TAKE]
capped=[f(O[b]['capped_realR']) for b in take_bars]
letrun=[f(O[b]['realized_letrun_120']) for b in take_bars]
both=[(c,l) for c,l in zip(capped,letrun) if c is not None and l is not None]
capped_win=sum(1 for c,l in both if c>0)
letrun_win=sum(1 for c,l in both if l>0)
# capped-positive but tiny (<1R) = scratched winner artifact
tiny_pos=sum(1 for c,l in both if 0<c<1)
print("\n=== WR AXIS (capped vs let-run, same TAKE trades) ===")
print(f"  capped wins={capped_win}/{len(both)} ({round(100*capped_win/len(both),1)}%)  letrun wins={letrun_win}/{len(both)} ({round(100*letrun_win/len(both),1)}%)")
print(f"  capped-positive-but-<1R (scratch-class) = {tiny_pos}  -> these inflate capped WR without being real R-wins")
