#!/usr/bin/env python3
"""FASE 2B.5 — confluência/interação entre especialistas. DIAGNÓSTICO (outcome pós-hoc).
NÃO cria aggregator/decisão/regra. Métricas cap-independentes (hit_2R/runner/stop/scratch) + avgR +
drop-top2 + CI + min-n. Estratifica por Stage A. Produz as CSVs do bloco."""
import json,csv,glob,os,math,random
from collections import Counter,defaultdict
random.seed(20260619)
D="results"
mat={(int(r['episode_id']),r['specialist_id']):r for r in csv.DictReader(open(f"{D}/l2_bpt_specialist_ablation_ready_matrix.csv"))}
net={}
for fp in glob.glob(f"{D}/specialist_out/*.jsonl"):
    fam=os.path.basename(fp)[:-6]
    for l in open(fp):
        if l.strip(): r=json.loads(l); net[(int(r['episode_id']),fam)]=r.get('net_read')
out={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_decisions_merged.csv"))}
sa={int(json.loads(l)['_bar_idx']):json.loads(l).get('context_label') for l in open(f"{D}/l2_bpt_stage_a_context_labels.jsonl")}
SPEC=["demand_supply","capitulation","exhaustion_top","volume_vp","nas","bubbles","rsi_momentum","risk_sl","bull_beta","devils_advocate"]
EP=sorted(set(i for i,_ in mat if i in out))
def stance(i,s): return net.get((i,s),'neutral')
def veto(i,s): return int(mat.get((i,s),{}).get('veto_count','0') or 0)>0
def review(i,s): return int(mat.get((i,s),{}).get('review_flag_count','0') or 0)>0
def state(i,s):
    if veto(i,s): return 'veto'
    st=stance(i,s)
    if review(i,s) and st=='neutral': return 'review_flag'
    return st  # supportive/hostile/neutral
def R(i): return float(out[i]['realR'])
def ex(i): return out[i]['exitype']
def hit2(i): return ex(i).startswith('WIN')            # reached +2R partial
def runner(i): return ex(i)=='WIN_RUNNER'              # reached +6R (=cap +3.9R)
def stop(i): return ex(i)=='STOP_LOSS'
def scratch(i): return ex(i)=='SCRATCH'
def win(i): return hit2(i)
take_lose=set(i for i in EP if dec[i]['decision']=='TAKE' and not win(i))
skip_win=set(i for i in EP if dec[i]['decision']=='SKIP' and win(i))

# ---- TAREFA 1: state matrix ----
with open(f"{D}/l2_bpt_specialist_state_matrix.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['episode_id','context_label']+SPEC)
    for i in EP: w.writerow([i,sa.get(i,'')]+[state(i,s) for s in SPEC])

def metrics(ids):
    ids=list(ids); n=len(ids)
    if n==0: return dict(n=0,avgR=0,WR=0,hit2=0,runner=0,stop=0,scratch=0,avgR_drop2=0,ci='[]',cut_losers=0,kill_skipwin=0)
    Rs=sorted(R(i) for i in ids)
    avg=sum(Rs)/n; sd=math.sqrt(sum((x-avg)**2 for x in Rs)/(n-1)) if n>1 else 0
    ci=1.96*sd/math.sqrt(n) if n>1 else 0
    drop2=sum(Rs[:-2])/(n-2) if n>2 else avg
    return dict(n=n,avgR=round(avg,3),WR=round(100*sum(1 for i in ids if win(i))/n),
                hit2=round(100*sum(1 for i in ids if hit2(i))/n),runner=round(100*sum(1 for i in ids if runner(i))/n),
                stop=round(100*sum(1 for i in ids if stop(i))/n),scratch=round(100*sum(1 for i in ids if scratch(i))/n),
                avgR_drop2=round(drop2,3),ci=f"[{avg-ci:.2f},{avg+ci:.2f}]",
                cut_losers=len(set(ids)&take_lose),kill_skipwin=len(set(ids)&skip_win))
BASE=metrics(EP)
def subset(reqs):  # reqs = {spec:state}
    return [i for i in EP if all(state(i,s)==st for s,st in reqs.items())]
def comp_subset(s,st): return [i for i in EP if state(i,s)==st]

# ---- TAREFAS 2+3: pairwise + three-way ----
PAIRS=[('nas+demand_supply',{'nas':'supportive','demand_supply':'supportive'}),
 ('nas+risk_sl',{'nas':'supportive','risk_sl':'supportive'}),
 ('nas+exhaustion_top',{'nas':'supportive','exhaustion_top':'supportive'}),
 ('nas+bull_beta',{'nas':'supportive','bull_beta':'supportive'}),
 ('nas+rsi_momentum',{'nas':'supportive','rsi_momentum':'supportive'}),
 ('nas+bubbles',{'nas':'supportive','bubbles':'supportive'}),
 ('nas+volume_vp',{'nas':'supportive','volume_vp':'supportive'}),
 ('demand_supply+risk_sl',{'demand_supply':'supportive','risk_sl':'supportive'}),
 ('demand_supply+volume_vp',{'demand_supply':'supportive','volume_vp':'supportive'}),
 ('demand_supply+bubbles',{'demand_supply':'supportive','bubbles':'supportive'}),
 ('demand_supply+rsi_momentum',{'demand_supply':'supportive','rsi_momentum':'supportive'}),
 ('capitulation+bubbles',{'capitulation':'supportive','bubbles':'supportive'}),
 ('capitulation+rsi_momentum',{'capitulation':'supportive','rsi_momentum':'supportive'}),
 ('capitulation+volume_vp',{'capitulation':'supportive','volume_vp':'supportive'}),
 ('exhaustion_top+bull_beta(hostile)',{'exhaustion_top':'hostile','bull_beta':'hostile'}),
 ('exhaustion_top+rsi_momentum(hostile)',{'exhaustion_top':'hostile','rsi_momentum':'hostile'}),
 ('DAveto+exhaustion_top(hostile)',{'devils_advocate':'veto','exhaustion_top':'hostile'}),
 ('DAveto+demand_supply(hostile)',{'devils_advocate':'veto','demand_supply':'hostile'}),
 ('DAveto+risk_sl(hostile)',{'devils_advocate':'veto','risk_sl':'hostile'}),
]
def write_combo(path,combos):
    with open(path,"w",newline="") as f:
        cols=['combo','reqs','n','avgR','avgR_drop2','WR','hit2R','runner3R','stop','scratch','ci','diff_vs_base','diff_vs_comp_min','cut_losers','kill_skipwin','min_n_warn']
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for name,reqs in combos:
            m=metrics(subset(reqs))
            comps=[metrics(comp_subset(s,st))['avgR'] for s,st in reqs.items()]
            dcomp=round(m['avgR']-max(comps),3) if comps else 0  # ganho sobre o melhor componente
            w.writerow(dict(combo=name,reqs=';'.join(f"{s}={st}" for s,st in reqs.items()),n=m['n'],avgR=m['avgR'],
                avgR_drop2=m['avgR_drop2'],WR=m['WR'],hit2R=m['hit2'],runner3R=m['runner'],stop=m['stop'],scratch=m['scratch'],
                ci=m['ci'],diff_vs_base=round(m['avgR']-BASE['avgR'],3),diff_vs_comp_min=dcomp,
                cut_losers=m['cut_losers'],kill_skipwin=m['kill_skipwin'],min_n_warn='WARN_n<12' if m['n']<12 else ''))
write_combo(f"{D}/l2_bpt_specialist_pairwise_confluence.csv",PAIRS)
TRIOS=[('nas+demand_supply+risk_sl',{'nas':'supportive','demand_supply':'supportive','risk_sl':'supportive'}),
 ('nas+demand_supply+exhaustion_top',{'nas':'supportive','demand_supply':'supportive','exhaustion_top':'supportive'}),
 ('nas+risk_sl+exhaustion_top',{'nas':'supportive','risk_sl':'supportive','exhaustion_top':'supportive'}),
 ('nas+demand_supply+rsi_momentum',{'nas':'supportive','demand_supply':'supportive','rsi_momentum':'supportive'}),
 ('nas+demand_supply+bubbles',{'nas':'supportive','demand_supply':'supportive','bubbles':'supportive'}),
 ('nas+demand_supply+volume_vp',{'nas':'supportive','demand_supply':'supportive','volume_vp':'supportive'}),
 ('capitulation+bubbles+rsi_momentum',{'capitulation':'supportive','bubbles':'supportive','rsi_momentum':'supportive'}),
 ('capitulation+bubbles+volume_vp',{'capitulation':'supportive','bubbles':'supportive','volume_vp':'supportive'}),
 ('capitulation+rsi_momentum+demand_supply',{'capitulation':'supportive','rsi_momentum':'supportive','demand_supply':'supportive'}),
 ('demand_supply+risk_sl+exhaustion_top',{'demand_supply':'supportive','risk_sl':'supportive','exhaustion_top':'supportive'}),
 ('bull_beta+exhaustion_top+DAveto(hostile)',{'bull_beta':'hostile','exhaustion_top':'hostile','devils_advocate':'veto'}),
 ('DAveto+exhaustion_top+risk_sl(hostile)',{'devils_advocate':'veto','exhaustion_top':'hostile','risk_sl':'hostile'}),
]
write_combo(f"{D}/l2_bpt_specialist_three_way_confluence.csv",TRIOS)

# ---- TAREFA 4: por contexto ----
CTX=['demand_reclaim','bottom_reversal_capitulation','bull_pullback_continuation','late_top_exhaustion','bear_bounce','liquidity_sweep_reversal','mid_range_noise']
MAIN=[('nas',{'nas':'supportive'}),('demand_supply',{'demand_supply':'supportive'}),('volume_vp',{'volume_vp':'supportive'}),
 ('bubbles',{'bubbles':'supportive'}),('rsi_momentum',{'rsi_momentum':'supportive'}),('capitulation',{'capitulation':'supportive'}),
 ('bull_beta',{'bull_beta':'supportive'}),('nas+demand_supply',{'nas':'supportive','demand_supply':'supportive'})]
with open(f"{D}/l2_bpt_specialist_confluence_by_context.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['context_label','combo','n','avgR','hit2R','runner3R'])
    for ctx in CTX:
        ctxids=[i for i in EP if sa.get(i)==ctx]; cm=metrics(ctxids)
        w.writerow([ctx,'<all-in-context>',cm['n'],cm['avgR'],cm['hit2'],cm['runner']])
        for name,reqs in MAIN:
            ids=[i for i in ctxids if all(state(i,s)==st for s,st in reqs.items())]; m=metrics(ids)
            w.writerow([ctx,name,m['n'],m['avgR'],m['hit2'],m['runner']])

# ---- TAREFA 5: hit-rate (cap-independente) por especialista supportive ----
with open(f"{D}/l2_bpt_specialist_confluence_hit_rate_metrics.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(['specialist_state','n','hit_2R','hit_3R_runner','stop_first','scratch','winner_vs_loser'])
    for s in SPEC:
        for st in ['supportive','hostile']:
            ids=comp_subset(s,st); m=metrics(ids)
            wvl=f"{sum(1 for i in ids if win(i))}W/{sum(1 for i in ids if not win(i))}L"
            w.writerow([f"{s}={st}",m['n'],m['hit2'],m['runner'],m['stop'],m['scratch'],wvl])
print("WROTE state_matrix, pairwise, three_way, by_context, hit_rate")
print(f"BASE: n={BASE['n']} avgR={BASE['avgR']} hit2R={BASE['hit2']}% runner={BASE['runner']}% stop={BASE['stop']}%")
print("\n=== PAIRWISE (top por avgR, n>=12) ===")
for r in sorted(csv.DictReader(open(f"{D}/l2_bpt_specialist_pairwise_confluence.csv")),key=lambda x:-float(x['avgR'])):
    if int(r['n'])>=12: print(f"  {r['combo']:<34} n={r['n']:<3} avgR={r['avgR']:>6}(drop2 {r['avgR_drop2']:>6}) hit2R={r['hit2R']}% run={r['runner3R']}% Δbase={r['diff_vs_base']:>6} Δcomp={r['diff_vs_comp_min']:>6} cutL={r['cut_losers']} killSW={r['kill_skipwin']}")
print("\n=== THREE-WAY (n>=8) ===")
for r in csv.DictReader(open(f"{D}/l2_bpt_specialist_three_way_confluence.csv")):
    if int(r['n'])>=8: print(f"  {r['combo']:<40} n={r['n']:<3} avgR={r['avgR']:>6}(drop2 {r['avgR_drop2']}) hit2R={r['hit2R']}% Δcomp={r['diff_vs_comp_min']} cutL={r['cut_losers']} killSW={r['kill_skipwin']} {r['min_n_warn']}")
