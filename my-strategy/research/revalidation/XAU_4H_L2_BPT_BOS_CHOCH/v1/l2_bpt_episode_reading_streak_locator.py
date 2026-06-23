#!/usr/bin/env python3
"""Localiza a JANELA do loser-streak (V_stair 120) no conjunto TAKE da leitura, e mescla com os 32 críticos
para a plotagem. Diagnóstico; outcome só p/ localizar a sequência, nunca redefine a leitura."""
import json, csv
D="results"
rd={int(json.loads(l)['episode_id']):json.loads(l) for l in open(f"{D}/l2_bpt_episode_readings_276.jsonl")}
O={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
def fn(v):
    try: return float(v)
    except: return None
TAKE=sorted([b for b in rd if rd[b]['provisional_decision']=='TAKE'], key=lambda b:O[b]['datetime'])
# achar o run máximo de losers consecutivos (vstair r<=0)
best=[]; cur=[]
for b in TAKE:
    r=fn(O[b]['realized_vstair_120'])
    if r is not None and r<=0:
        cur.append(b)
        if len(cur)>len(best): best=cur[:]
    else:
        cur=[]
print(f"LOSER-STREAK máximo (V_stair120) no TAKE: {len(best)} trades consecutivos")
print(f"  janela: {O[best[0]]['datetime']}  →  {O[best[-1]]['datetime']}")
print(f"  {'bar':>5} {'datetime':16} {'type':22} {'conf':10} {'vstairR':>8} {'cappedR':>8} {'mfeR':>6}")
for b in best:
    print(f"  {b:>5} {O[b]['datetime']:16} {rd[b]['episode_type']:22} {rd[b]['qualitative_confidence'][:10]:10} {fn(O[b]['realized_vstair_120']):>8.1f} {fn(O[b]['capped_realR']):>8.1f} {fn(O[b]['mfe_R']):>6.1f}")
# mesclar com os 32 críticos
crit={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_episode_reading_plot_list.csv"))}
allbars=sorted(set(list(crit)+best), key=lambda b:O[b]['datetime'])
with open(f"{D}/l2_bpt_episode_reading_plot_list_v2.csv","w",newline="") as f:
    w=csv.writer(f,lineterminator="\n")
    w.writerow(['bar_idx','datetime','episode_type','decision','mfe_R','capped_realR','vstair_R','reason'])
    for b in allbars:
        in_crit=b in crit; in_streak=b in best
        reason=(crit[b]['reason_to_plot'] if in_crit else '')+('+' if in_crit and in_streak else '')+('loser_streak13' if in_streak else '')
        w.writerow([b,O[b]['datetime'],rd[b]['episode_type'],rd[b]['provisional_decision'],
                    fn(O[b]['mfe_R']),fn(O[b]['capped_realR']),fn(O[b]['realized_vstair_120']),reason])
print(f"\nMERGE: {len(crit)} críticos ∪ {len(best)} streak = {len(allbars)} episódios p/ plotar (overlap {len(set(crit)&set(best))})")
print(f"CSV: {D}/l2_bpt_episode_reading_plot_list_v2.csv")
