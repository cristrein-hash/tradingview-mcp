#!/usr/bin/env python3
"""EXPLORAÇÃO MULTI-FRENTE (Cris: descobrir testando) — o que separa WINNERS de LOSERS nas entradas de RANGE?
Junta features ricas (dspa_path_features_276: sweep/reclaim, flush, aceitação/rejeição, BOS/CHoCH, range-pos, svp;
deep_master_matrix: rsi_bull_div, sweet_spot_falling_knife, legpos, nas, bubbles) + tempo-no-range + N-holds-demanda,
às range-trades (regua_structural, R let-run pós-custo). Rankeia features por separação win-vs-loss.
n pequeno + muitas features = HIPÓTESE, não validação (multiple-testing brutal). Objetivo: achar candidato COERENTE p/ cortar os chasing."""
import json,csv,io,contextlib,sys,bisect,statistics as st,datetime as dt
from pathlib import Path
COST=0.35;VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;L=P.L;H=P.H;C=P.C
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json")) if s["regime"]=="RANGE"]
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
# features por bar_idx
path={int(r["bar_idx"]):r for r in csv.DictReader(open(D/"l2_bpt_dspa_path_features_276.csv"))}
mm={}
for r in csv.DictReader(open(D/"l2_bpt_deep_master_matrix_62.csv")):
    pass  # matrix é 62-subset, join por datetime; usamos path (276) como principal
def num(v):
    try: return float(v)
    except: return None
tr=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    box=next((s for s in segs if s['start']<=t<=s['end']),None)
    if not box: continue
    R=round(float(r["letrun_struct"])-COST,2)
    i0=bisect.bisect_left(T,box['start']);a=atr(bi);rmin=min(L[i0:bi+1])
    # frentes do Cris: tempo-no-range, N-holds-demanda (bounce>=1ATR e volta<=0.5ATR ANTES da entrada)
    tir=bi-i0;holds=0;armed=False;rm=L[i0]
    for j in range(i0+1,bi):
        rm=min(rm,L[j])
        if C[j]>rm+1.0*a: armed=True
        if armed and L[j]<=rm+0.5*a: holds+=1;armed=False
    d={"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"win":R>0,"R":R,"yr":y,
       "tempo_no_range":tir,"n_holds_demanda":holds,"dist_demanda_atr":(float(r['entry'])-rmin)/a,
       "box2025":(box['d0']=="2025-04-22")}
    pf=path.get(bi,{})
    for k in ("f1_swept_low_reclaim","f1_sweep_depth_atr","f1_bars_since_sweep","f2_flush_state","f2_drop_atr",
              "f3_acceptance_state","f3_closes_above_res","f3_rejections_at_res","f3_breaks_support","f4_BOS","f4_CHoCH",
              "f4_structure_state","f5_range_pos_4h","f6_dist_poc_atr","f6_below_value","f7_cascade_now"):
        d[k]=pf.get(k)
    tr.append(d)
W=[x for x in tr if x["win"]];Lz=[x for x in tr if not x["win"]]
print(f"RANGE-trades: {len(tr)} ({len(W)}W/{len(Lz)}L). Join features: {sum(1 for x in tr if x.get('f4_BOS') is not None)}/{len(tr)} têm path-features.")
print("\n### FRENTES DO CRIS + features numéricas — média WINNER vs LOSER (|Δ| ordenado) ###")
numk=["tempo_no_range","n_holds_demanda","dist_demanda_atr","f1_sweep_depth_atr","f1_bars_since_sweep","f2_drop_atr","f3_closes_above_res","f3_rejections_at_res","f4_n_pivots_lb","f5_range_pos_4h","f6_dist_poc_atr"]
res=[]
for k in numk:
    wv=[num(x.get(k)) for x in W if num(x.get(k)) is not None];lv=[num(x.get(k)) for x in Lz if num(x.get(k)) is not None]
    if len(wv)>=3 and len(lv)>=3:
        mw,ml=st.mean(wv),st.mean(lv);sd=(st.pstdev(wv+lv) or 1);res.append((abs(mw-ml)/sd,k,mw,ml))
for sc,k,mw,ml in sorted(res,reverse=True):
    print(f"  {k:22} WIN {mw:+7.2f} vs LOSS {ml:+7.2f}  (sep {sc:.2f})")
print("\n### features CATEGÓRICAS/binárias — WR por valor ###")
for k in ["f1_swept_low_reclaim","f2_flush_state","f3_acceptance_state","f3_breaks_support","f4_BOS","f4_CHoCH","f4_structure_state","f6_below_value","f7_cascade_now"]:
    vals={}
    for x in tr:
        v=x.get(k)
        if v in (None,""): continue
        vals.setdefault(v,[]).append(x)
    parts=[f"{v}:{100*sum(1 for z in g if z['win'])/len(g):.0f}%WR(n{len(g)})" for v,g in sorted(vals.items()) if len(g)>=3]
    if parts: print(f"  {k:22} "+" | ".join(parts))
print("\n### as 2025-range trades (o caso 13-losers/2-winners) — features das que ganharam vs perderam ###")
b25=[x for x in tr if x["box2025"]]
for x in sorted(b25,key=lambda z:z['bi']):
    print(f"  {x['date']} {'WIN ' if x['win'] else 'loss'} R{x['R']:+.1f} | sweep_reclaim={x.get('f1_swept_low_reclaim')} accept={x.get('f3_acceptance_state')} BOS={x.get('f4_BOS')} CHoCH={x.get('f4_CHoCH')} nholds={x['n_holds_demanda']} tir={x['tempo_no_range']} rejeic={x.get('f3_rejections_at_res')}")
# CANDIDATOS (avaliação, multi-front)
def curve(rs):
    rs=sorted(rs,key=lambda x:x["bi"]);n=len(rs)
    if not n: return "N=0"
    s=sum(x["R"] for x in rs);w=sum(1 for x in rs if x["win"]);cum=peak=dd=0
    for x in rs: cum+=x["R"];peak=max(peak,cum);dd=min(dd,cum-peak)
    return f"N={n:2} WR={100*w/n:3.0f}% sumR={s:+6.1f} DD={dd:6.1f}"
seen=set();first=[]
for x in sorted(tr,key=lambda z:z["bi"]):
    box=next((s for s in segs if s['start']<=T[x['bi']]<=s['end']),None);key=(box['d0'],box['d1'])
    if key not in seen: seen.add(key);first.append(x)
print("\n### CANDIDATOS (base 70) ###")
print(f"  BASE                         {curve(tr)}")
print(f"  skip HOLDING/BROKE_SUPPORT   {curve([x for x in tr if x.get('f3_acceptance_state') not in ('HOLDING_SUPPORT','BROKE_SUPPORT')])}")
print(f"  skip STRUCTURE_UP            {curve([x for x in tr if x.get('f4_structure_state')!='STRUCTURE_UP'])}")
print(f"  1a-entrada-por-range         {curve(first)}")
print(f"  skip HOLDING/BROKE + !STRUCT_UP {curve([x for x in tr if x.get('f3_acceptance_state') not in ('HOLDING_SUPPORT','BROKE_SUPPORT') and x.get('f4_structure_state')!='STRUCTURE_UP'])}")
print("\n### 2025-range (13L/2W) sob filtros ###")
b25=[x for x in tr if x["box2025"]]
print(f"  base                {curve(b25)}")
print(f"  skip HOLDING/BROKE  {curve([x for x in b25 if x.get('f3_acceptance_state') not in ('HOLDING_SUPPORT','BROKE_SUPPORT')])}")
print(f"  1a-por-range        {curve([x for x in b25 if x in first])}")
