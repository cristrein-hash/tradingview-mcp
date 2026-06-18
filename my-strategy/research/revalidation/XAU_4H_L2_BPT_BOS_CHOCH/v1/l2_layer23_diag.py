#!/usr/bin/env python3
"""L2/BPT v2.2 — Camadas 2-3 diagnostic: separar BOM vs NAO vs UNKNOWN.
Recall-first. NO veto, NO PnL, NO plot, NO production, NO slim. Diagnostic only.
Reusa os 12 blockers causais canônicos do L2_layer2_diagnostic_audit.py (re-definidos
aqui para não executar o audit no import) + tags de contexto causais do input v2.2.
"""
import json, csv, sys
import os
from datetime import datetime, timezone
from collections import Counter, defaultdict
sys.path.insert(0, os.environ.get('L2_DETECTOR_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)),'pipeline','detectors')))
from L2_detector_v2_2 import (RAW, ATR, SMA50, N, D, ND, SMA200_D, daily_idx_for_4h,
                              SELL_PLOTS, LARGE_BUY, LARGE_SELL, is_falso_tipo_B_dump_direto,
                              run_candidate_generator)

OUT = "/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results"
GT = json.load(open(os.environ.get('L2_GROUND_TRUTH','/tmp/L2_ground_truth_v1.json')))
def pts(s): return int(datetime.strptime(s,'%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc).timestamp())
def fmt(ts): return datetime.fromtimestamp(ts,tz=timezone.utc).strftime('%Y-%m-%d %H:%M')

# ---- 12 canonical causal blockers (verbatim from L2_layer2_diagnostic_audit.py) ----
def blk_false_tipo_B_dump_direto(c): return is_falso_tipo_B_dump_direto(c['entry_idx'])
def blk_CHoCH_not_BOS(c):
    p=c['pivot_idx']
    if p<20: return False
    return sum(1 for j in range(p-20,p) if RAW[j]['close']<RAW[j]['open'])>12
def blk_first_retomada(c,lookback=60,streak_thr=15):
    p=c['pivot_idx']
    if p<lookback or SMA50[p-1] is None: return False
    streak=mx=0
    for j in range(p-lookback,p):
        if SMA50[j] is not None and RAW[j]['close']<SMA50[j]: streak+=1; mx=max(mx,streak)
        else: streak=0
    return mx>=streak_thr
def blk_bear_flag(c,lookback=15):
    p=c['pivot_idx']
    if p<lookback: return False
    for j in range(p-lookback,p):
        aj=ATR[j]
        if not aj: continue
        rng=RAW[j]['high']-RAW[j]['low']
        if rng<1.0*aj: continue
        uw=RAW[j]['high']-max(RAW[j]['open'],RAW[j]['close'])
        if rng==0 or uw/rng<0.6: continue
        if RAW[j]['close']>=RAW[j]['open']: continue
        return True
    return False
def blk_BOS_fraco(c):
    k=c.get('break_idx')
    if k is None: return False
    ak=ATR[k]
    if not ak: return False
    return (RAW[k]['close']-c['level'])/ak<0.3
def blk_cluster_BUY_climax(c,window=9,thr=3):
    bubs=RAW[c['entry_idx']].get('bubbles_recent') or []
    return sum(1 for b in bubs if b.get('plot_id')==LARGE_BUY and b.get('bars_ago') is not None and 0<=b['bars_ago']<=window)>=thr
def blk_bear_macro(c):
    di=daily_idx_for_4h(RAW[c['entry_idx']]['ts_epoch'])
    if di<0 or di>=ND or SMA200_D[di] is None: return False
    return D[di]['close']<SMA200_D[di]
def blk_volume_fraco(c,ref=20,thr=0.7):
    i=c['entry_idx']
    if i<ref: return False
    refs=[RAW[j]['volume'] for j in range(i-ref,i)]
    med=sorted(refs)[len(refs)//2]
    if med<=0: return False
    return RAW[i]['volume']/med<thr
def blk_no_absorption(c):
    if c['tipo']!='B': return False
    b=RAW[c['entry_idx']]; rng=b['high']-b['low']
    if rng==0: return False
    return (min(b['open'],b['close'])-b['low'])/rng<0.20
def blk_no_polarity_defense(c): return RAW[c['entry_idx']]['close']<c['level']
def blk_no_retest(c):
    i=c['entry_idx']; k=c.get('break_idx')
    if k is None: return False
    ae=ATR[i]
    if not ae: return False
    return min(RAW[j]['low'] for j in range(k+1,i+1))>c['level']+0.4*ae
def blk_overextended_entry(c):
    ae=ATR[c['entry_idx']]
    if not ae: return False
    return RAW[c['entry_idx']]['close']>c['level']+1.0*ae
BLOCKERS={'false_tipo_B_dump_direto':blk_false_tipo_B_dump_direto,'CHoCH_not_BOS':blk_CHoCH_not_BOS,
 'first_retomada':blk_first_retomada,'bear_flag':blk_bear_flag,'BOS_fraco':blk_BOS_fraco,
 'cluster_BUY_climax':blk_cluster_BUY_climax,'bear_macro':blk_bear_macro,'volume_fraco':blk_volume_fraco,
 'no_absorption':blk_no_absorption,'no_polarity_defense':blk_no_polarity_defense,'no_retest':blk_no_retest,
 'overextended_entry':blk_overextended_entry}

# ---- extra causal context tags (from v2.2 input snapshots, causal by construction) ----
def tag_dist_to_polarity_atr(c):
    ae=ATR[c['entry_idx']]
    return round((c['entry_close']-c['level'])/ae,2) if ae else None
def tag_sell_bubbles_recent(c,window=10):   # bear-control / top-distribution proxy (SELL 6/8/10)
    bubs=RAW[c['entry_idx']].get('bubbles_recent') or []
    return sum(1 for b in bubs if b.get('plot_id') in SELL_PLOTS and b.get('bars_ago') is not None and 0<=b['bars_ago']<=window)
def tag_large_sell_recent(c,window=10):     # plot_10 = LARGE sell (memory canonical mapping)
    bubs=RAW[c['entry_idx']].get('bubbles_recent') or []
    return sum(1 for b in bubs if b.get('plot_id')=='plot_10' and b.get('bars_ago') is not None and 0<=b['bars_ago']<=window)
def tag_nas_nearest(c):                      # nearest NAS label by smallest x (caveat: x not strictly bars_ago)
    nas=RAW[c['entry_idx']].get('nas_recent') or []
    if not nas: return 'none'
    near=min(nas,key=lambda e:e.get('x',9999))
    return near.get('text','none')
def tag_nas_short_count(c):
    nas=RAW[c['entry_idx']].get('nas_recent') or []
    return sum(1 for e in nas if e.get('text')=='SHORT' and e.get('x',9999)<=10)
def tag_rsi(c):
    return RAW[c['entry_idx']].get('rsi')
def tag_atr_pct(c,win=100):                  # ATR percentile (volatility regime)
    i=c['entry_idx']; ae=ATR[i]
    if not ae or i<win: return None
    hist=[ATR[j] for j in range(i-win,i) if ATR[j]]
    if not hist: return None
    return round(sum(1 for x in hist if x<ae)/len(hist),2)

# ---- run generator + label ----
cands=run_candidate_generator()
cand_by_idx={c['entry_idx']:c for c in cands}
ts_by_idx={i:RAW[i]['ts_epoch'] for i in range(N)}
# GT bom/nao bars
bom_bars={}; nao_bars={}
for ev in GT['BOM_HIGH']:
    i=next((k for k in range(N) if RAW[k]['ts_epoch']==pts(ev['entry_ts_utc'])),None)
    if i is not None: bom_bars[i]=ev['GT_ID']
for ev in GT['NAO_CONFIRMED']:
    t=ev.get('entry_ts_utc')
    if not t: continue
    i=next((k for k in range(N) if RAW[k]['ts_epoch']==pts(t)),None)
    if i is not None: nao_bars[i]=ev['GT_ID']

def label_of(idx):
    for d in range(-2,3):
        if idx+d in bom_bars: return 'BOM', bom_bars[idx+d]
    for d in range(-2,3):
        if idx+d in nao_bars: return 'NAO', nao_bars[idx+d]
    return 'UNKNOWN', ''

# ---- build matrix ----
rows=[]
for c in cands:
    lab,gid=label_of(c['entry_idx'])
    blk={bn:bf(c) for bn,bf in BLOCKERS.items()}
    row={'candidate_id':f"C{c['entry_idx']}",'ts':fmt(RAW[c['entry_idx']]['ts_epoch']),
         'year':datetime.fromtimestamp(RAW[c['entry_idx']]['ts_epoch'],tz=timezone.utc).year,
         'level':round(c['level'],2),'entry_close':round(c['entry_close'],2),
         'source':c['source'],'variant':c['variant'],'tipo':c['tipo'],
         'bos_mag_atr':round(c['bos_mag_atr'],2) if c.get('bos_mag_atr') is not None else '',
         'label':lab,'gt_id':gid,
         'dist_pol_atr':tag_dist_to_polarity_atr(c),'sell_bub_10':tag_sell_bubbles_recent(c),
         'large_sell_10':tag_large_sell_recent(c),'nas_near':tag_nas_nearest(c),
         'nas_short_10':tag_nas_short_count(c),'rsi':round(tag_rsi(c),1) if tag_rsi(c) is not None else '',
         'atr_pct':tag_atr_pct(c)}
    for bn in BLOCKERS: row['blk_'+bn]=int(blk[bn])
    rows.append(row)

with open(f"{OUT}/l2_bpt_v2_2_candidate_matrix.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

# gt vs nao comparison (BOM + NAO rows only)
cmp_rows=[r for r in rows if r['label'] in ('BOM','NAO')]
cmp_rows.sort(key=lambda r:(r['label'],r['ts']))
with open(f"{OUT}/l2_bpt_v2_2_gt_nao_comparison.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(cmp_rows)

# ---- EVENT-LEVEL recall: each GT event = set of capturing candidate entry_idxs (within +-2) ----
# A winner is LOST by a filter only if ALL its capturing candidates are cut. >=1 survivor => recall preserved.
def event_caps(bars_map):
    ev=defaultdict(set)
    for c in cands:
        for d in range(-2,3):
            if c['entry_idx']+d in bars_map:
                ev[bars_map[c['entry_idx']+d]].add(c['entry_idx'])
    return ev
bom_ev=event_caps(bom_bars)   # gt_id -> set(entry_idx)
nao_ev=event_caps(nao_bars)
n_bom_ev=len(bom_ev); n_nao_ev=len(nao_ev)
n_bom=sum(1 for r in rows if r['label']=='BOM'); n_nao=sum(1 for r in rows if r['label']=='NAO')
n_unk=sum(1 for r in rows if r['label']=='UNKNOWN')
cut_idx_of={bn:set(c['entry_idx'] for c in cands if BLOCKERS[bn](c)) for bn in BLOCKERS}
layer_diag={}; atlas=[]
for bn in BLOCKERS:
    cut=cut_idx_of[bn]
    # event recall preserved if at least one capturing candidate survives (not in cut)
    bom_kept=sum(1 for gid,s in bom_ev.items() if (s-cut))
    bom_lost=n_bom_ev-bom_kept
    nao_removed=sum(1 for gid,s in nao_ev.items() if not (s-cut))  # fully removed NAO events
    unk_cut=sum(1 for r in rows if r['label']=='UNKNOWN' and r['blk_'+bn])
    if bom_lost==0 and (nao_removed>0 or unk_cut>=50):
        role='hard_veto_candidate'
    elif bom_lost==0 and unk_cut>0:
        role='soft_warning/noise-tag'
    elif bom_lost<=1 and nao_removed>=bom_lost and nao_removed>0:
        role='human_review_reason'
    elif bom_lost>=2:
        role='reject(kills winners)'
    else:
        role='tag'
    conf='low(GT_BOM_events=%d,NAO_events=%d)'%(n_bom_ev,n_nao_ev)
    layer_diag[bn]={'BOM_events_kept':bom_kept,'BOM_events_lost':bom_lost,
                    'NAO_events_removed':nao_removed,'UNKNOWN_cand_cut':unk_cut,'role':role}
    atlas.append({'reason_id':bn,'description':bn.replace('_',' '),
                  'preserved_BOM_count':bom_kept,'cut_NAO_count':nao_removed,'cut_UNKNOWN_count':unk_cut,
                  'recommended_role':role,'confidence':conf,
                  'notes':f'event-level: keeps {bom_kept}/{n_bom_ev} BOM, removes {nao_removed}/{n_nao_ev} NAO; cand-level UNKNOWN cut {unk_cut}/{n_unk}'})

with open(f"{OUT}/l2_bpt_v2_2_reason_atlas_v2.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(atlas[0].keys())); w.writeheader(); w.writerows(atlas)

# ---- density by source/path ----
by_src=Counter(r['source'] for r in rows)
bom_by_src=Counter(r['source'] for r in rows if r['label']=='BOM')
nao_by_src=Counter(r['source'] for r in rows if r['label']=='NAO')

# ---- safe reduction: union of blockers that lose 0 GT BOM events (recall 17/17 preserved) ----
zero_bom_blockers=[bn for bn in BLOCKERS if layer_diag[bn]['BOM_events_lost']==0]
union_cut=set().union(*[cut_idx_of[bn] for bn in zero_bom_blockers]) if zero_bom_blockers else set()
bom_kept_safe=sum(1 for gid,s in bom_ev.items() if (s-union_cut))
nao_removed_safe=sum(1 for gid,s in nao_ev.items() if not (s-union_cut))
unk_cut_safe=sum(1 for r in rows if r['label']=='UNKNOWN' and r['candidate_id'][1:] and int(r['candidate_id'][1:]) in union_cut)
remaining=len(rows)-len(union_cut)
# also: minimal single-layer safe reduction (best zero-BOM blocker by UNKNOWN cut)
best_single=max(zero_bom_blockers,key=lambda bn:layer_diag[bn]['UNKNOWN_cand_cut']) if zero_bom_blockers else None
# GREEDY union that strictly preserves 17/17 (naive union can break recall jointly)
def recall_ok(cutset): return all((s-cutset) for s in bom_ev.values())
greedy=[]; gcut=set()
for bn in sorted(zero_bom_blockers,key=lambda b:-layer_diag[b]['UNKNOWN_cand_cut']):
    trial=gcut|cut_idx_of[bn]
    if recall_ok(trial): greedy.append(bn); gcut=trial
g_unk=sum(1 for r in rows if r['label']=='UNKNOWN' and int(r['candidate_id'][1:]) in gcut)
g_nao=sum(1 for gid,s in nao_ev.items() if not (s-gcut))
g_remaining=len(rows)-len(gcut)

layer_diag['_meta']={'total_candidates':len(rows),'GT_BOM_events':n_bom_ev,'NAO_events':n_nao_ev,
   'cand_BOM':n_bom,'cand_NAO':n_nao,'cand_UNKNOWN':n_unk,
   'density_by_source':dict(by_src),'bom_cand_by_source':dict(bom_by_src),'nao_cand_by_source':dict(nao_by_src),
   'safe_reduction_union':{'zero_BOM_blockers':zero_bom_blockers,
     'BOM_events_kept':bom_kept_safe,'BOM_events_total':n_bom_ev,
     'NAO_events_removed':nao_removed_safe,'UNKNOWN_cand_cut':unk_cut_safe,
     'candidates_remaining':remaining,'density_reduction_pct':round(100*len(union_cut)/len(rows),1)},
   'best_single_zeroBOM_layer':best_single,
   'safe_reduction_greedy_17of17':{'layers':greedy,'BOM_events_kept':n_bom_ev,
     'NAO_events_removed':g_nao,'UNKNOWN_cand_cut':g_unk,'candidates_remaining':g_remaining,
     'density_reduction_pct':round(100*len(gcut)/len(rows),1)}}
with open(f"{OUT}/l2_bpt_v2_2_layer_diagnostic.json","w") as f:
    json.dump(layer_diag,f,indent=2)

# ---- console report ----
print(f"candidates={len(rows)}  GT_BOM_events={n_bom_ev}  NAO_events={n_nao_ev}  (cand labels BOM={n_bom} NAO={n_nao} UNK={n_unk})")
print(f"\nDensity by source: {dict(by_src)}")
print(f"BOM cand by source: {dict(bom_by_src)}")
print(f"NAO cand by source: {dict(nao_by_src)}")
print(f"\n{'LAYER':<28}{'BOMkept':>8}{'BOMlost':>8}{'NAOrm':>7}{'UNKcut':>8}  role")
for bn in BLOCKERS:
    d=layer_diag[bn]; print(f"  {bn:<26}{d['BOM_events_kept']:>8}{d['BOM_events_lost']:>8}{d['NAO_events_removed']:>7}{d['UNKNOWN_cand_cut']:>8}  {d['role']}")
sr=layer_diag['_meta']['safe_reduction_union']
print(f"\nSAFE REDUCTION (union of {len(zero_bom_blockers)} zero-BOM-loss layers):")
print(f"  layers: {zero_bom_blockers}")
print(f"  BOM events kept {sr['BOM_events_kept']}/{n_bom_ev} | NAO events removed {sr['NAO_events_removed']}/{n_nao_ev} | UNKNOWN cand cut {sr['UNKNOWN_cand_cut']}/{n_unk}")
print(f"  candidates {len(rows)} -> {sr['candidates_remaining']}  (-{sr['density_reduction_pct']}%)  [NOTE: naive union loses {n_bom_ev-sr['BOM_events_kept']} winner(s)]")
print(f"  best single zero-BOM layer: {best_single} (UNKcut {layer_diag[best_single]['UNKNOWN_cand_cut']}, BOM {layer_diag[best_single]['BOM_events_kept']}/{n_bom_ev})")
print(f"\nGREEDY 17/17-PRESERVING union: {greedy}")
print(f"  BOM events kept 17/17 | NAO events removed {g_nao}/{n_nao_ev} | UNKNOWN cand cut {g_unk}/{n_unk}")
print(f"  candidates {len(rows)} -> {g_remaining}  (-{round(100*len(gcut)/len(rows),1)}%)")
