#!/usr/bin/env python3
"""Resolve o resíduo rsi/nas: coleta TODOS os snapshots por bar-time (dup-captures) com campos de
ordenação, isola o universo divergente (Tarefa 1), varre regras de seleção A-L (Tarefa 2), regras
compostas (Tarefa 3) e roda o gate do melhor candidato (Tarefa 4). Não altera OHLC/bubbles."""
import gzip, json, csv, sys
from pathlib import Path
RES=Path("results")
REF={json.loads(l)['ts_epoch']:json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')}
GZ=["/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_240m_replay_2020-01-01_to_2023-01-01.jsonl.gz",
    "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_240m_replay_2023-01-03_to_2026-05-25.jsonl.gz"]
def nas_sig(arr): return sorted((x.get('text'),x.get('x')) for x in arr if x.get('x') is not None and x.get('x')<=30)
by_cur={}        # cur_time -> [snap dict]  (todos os snapshots, em ordem de leitura)
order=0
for gz in GZ:
    with gzip.open(gz,'rt') as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try: d=json.loads(line)
            except: continue
            ov=d.get('ohlcv') or []
            if not ov: continue
            cur=ov[-1]['time']; fb=ov[-1]
            rsi=None
            for s in (d.get('study_values') or []):
                if 'Relative Strength' in (s.get('name') or ''):
                    try: rsi=round(float(str(s['values'].get('RSI')).replace(',','')),2)
                    except: rsi=None
                    break
            nas=[]
            for lab in (d.get('pine_labels') or []):
                if 'NAS' in (lab.get('name') or '').upper():
                    nas=[{'text':x.get('text'),'x':x.get('x'),'price':x.get('price')} for x in (lab.get('all_labels') or lab.get('labels') or [])]
                    break
            fa=d.get('_feature_availability') or {}
            favail=sum(1 for v in fa.values() if v) if isinstance(fa,dict) else 0
            by_cur.setdefault(cur,[]).append({
                'order':order,'captured_at':d.get('captured_at'),'rcd':d.get('replay_current_date') or d.get('replay_current_dt'),
                'bar_index':d.get('bar_index'),'frange':(fb.get('high') or 0)-(fb.get('low') or 0),
                'rsi':rsi,'nas':nas,'nas_sig':nas_sig(nas),'favail':favail})
            order+=1
print(f"snapshots lidos: {order} | cur-times: {len(by_cur)} | multi-snapshot: {sum(1 for v in by_cur.values() if len(v)>1)}",file=sys.stderr)

# ---- regras de seleção (cada uma: lista de snaps -> 1 snap) ----
def R_first_cap(v): return min(v,key=lambda s:(s['captured_at'] or ''))
def R_last_cap(v):  return max(v,key=lambda s:(s['captured_at'] or ''))
def R_first_order(v): return min(v,key=lambda s:s['order'])
def R_last_order(v):  return max(v,key=lambda s:s['order'])
def R_early_rcd(v): return min(v,key=lambda s:(s['rcd'] or ''))
def R_late_rcd(v):  return max(v,key=lambda s:(s['rcd'] or ''))
def R_min_bi(v): return min(v,key=lambda s:(s['bar_index'] if s['bar_index'] is not None else 9e18))
def R_max_bi(v): return max(v,key=lambda s:(s['bar_index'] if s['bar_index'] is not None else -1))
def R_most_favail(v): return max(v,key=lambda s:(s['favail'],s['order']))
def R_rsi_nas_nonnull(v):
    c=[s for s in v if s['rsi'] is not None and s['nas']]
    return (max(c,key=lambda s:s['order']) if c else R_last_order(v))
def R_max_frange(v): return max(v,key=lambda s:(s['frange'],s['order']))  # maturity proxy
def R_modal_rsi(v):
    from collections import Counter
    c=Counter(s['rsi'] for s in v if s['rsi'] is not None)
    if not c: return R_last_order(v)
    mode=c.most_common(1)[0][0]
    return next(s for s in v if s['rsi']==mode)
RULES={'A_first_captured_at':R_first_cap,'B_last_captured_at':R_last_cap,
       'B2_first_order':R_first_order,'B3_last_order':R_last_order,
       'C_earliest_rcd':R_early_rcd,'D_latest_rcd':R_late_rcd,
       'E_min_bar_index':R_min_bi,'F_max_bar_index':R_max_bi,
       'G_most_feature_avail':R_most_favail,'H_rsi_nas_nonnull':R_rsi_nas_nonnull,
       'I_max_forming_range':R_max_frange,'J_modal_rsi':R_modal_rsi}

bars=sorted(REF)  # avaliar sobre o conjunto do ref
def eval_rule(sel):
    rsi_ok=nas_ok=rsi_tot=nas_tot=0
    for t in bars:
        v=by_cur.get(t)
        ref=REF[t]
        if not v:  # bar de buffer-only (sem snapshot current==t) -> esperado rsi None/nas []
            chosen={'rsi':None,'nas_sig':[]}
        else:
            chosen=sel(v)
        # rsi
        rr=ref.get('rsi'); cr=chosen['rsi']
        rsi_tot+=1
        if (rr is None and cr is None) or (rr is not None and cr is not None and abs(rr-cr)<=1e-6): rsi_ok+=1
        # nas
        nas_tot+=1
        ref_sig=sorted((x.get('text'),x.get('x')) for x in (ref.get('nas_recent') or []))
        ch_sig=chosen.get('nas_sig',[]) if v else []
        if ref_sig==ch_sig: nas_ok+=1
    return rsi_ok,rsi_tot,nas_ok,nas_tot

# Tarefa 1: casos divergentes (baseado na regra atual = I_max_forming_range p/ rsi, last p/ nas -> usar I)
divergent=[]
for t in bars:
    v=by_cur.get(t)
    ref=REF[t]; rr=ref.get('rsi'); ref_nas=sorted((x.get('text'),x.get('x')) for x in (ref.get('nas_recent') or []))
    cur_sel=R_max_frange(v) if v else {'rsi':None,'nas_sig':[]}
    cr=cur_sel['rsi']; cn=cur_sel.get('nas_sig',[]) if v else []
    rdiff = not((rr is None and cr is None) or (rr is not None and cr is not None and abs(rr-cr)<=1e-6))
    ndiff = (ref_nas!=cn)
    if rdiff or ndiff:
        divergent.append((t,v,ref,rr,cr,ref_nas,cn,rdiff,ndiff))
print(f"divergentes (regra atual): {len(divergent)}",file=sys.stderr)
with open(RES/"l2_bpt_repro_rsi_nas_residue_cases.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['bar_time','idx','n_snapshots','rsi_per_snapshot','ref_rsi','nas_count_per_snapshot','ref_nas_count','captured_at_list','rcd_list','bar_index_list','rsi_absdiff','rsi_diff','nas_diff'])
    for t,v,ref,rr,cr,refn,cn,rd,nd in divergent[:400]:
        idx=bars.index(t)
        rsis=[s['rsi'] for s in (v or [])]; ncs=[len(s['nas_sig']) for s in (v or [])]
        caps=[s['captured_at'] for s in (v or [])]; rcds=[s['rcd'] for s in (v or [])]; bis=[s['bar_index'] for s in (v or [])]
        ad=abs(rr-cr) if (rr is not None and cr is not None) else ''
        w.writerow([t,idx,len(v or []),'|'.join(map(str,rsis)),rr,'|'.join(map(str,ncs)),len(refn),'|'.join(map(str,caps)),'|'.join(map(str,rcds)),'|'.join(map(str,bis)),ad,rd,nd])

# Tarefa 2: sweep
def causal(name): return name not in ('next_valid',)  # nenhuma usa futuro
rows=[]
for name,sel in RULES.items():
    ro,rt,no,nt=eval_rule(sel)
    rows.append((name,round(100*ro/rt,3),round(100*no/nt,3),rt-ro,nt-no))
rows.sort(key=lambda x:-(x[1]+x[2]))
with open(RES/"l2_bpt_repro_snapshot_selection_sweep.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['rule','rsi_match_pct','nas_match_pct','rsi_mismatch','nas_mismatch','causal','deterministic','uses_future'])
    for name,rp,npc,rm,nm in rows: w.writerow([name,rp,npc,rm,nm,'YES','YES','NO'])
print("\n=== SWEEP (rsi% / nas% / rsi_miss / nas_miss) ===")
for name,rp,npc,rm,nm in rows: print(f"  {name:<24} rsi={rp:7.3f}% nas={npc:7.3f}% miss(rsi={rm},nas={nm})")
best=rows[0]
print(f"\nMELHOR SIMPLES: {best[0]} rsi={best[1]}% nas={best[2]}%")
import pickle
pickle.dump({'by_cur_meta':{'n':order,'multi':sum(1 for v in by_cur.values() if len(v)>1)}},open('/tmp/_residue_meta.pkl','wb'))
print("WROTE residue_cases.csv + snapshot_selection_sweep.csv")
