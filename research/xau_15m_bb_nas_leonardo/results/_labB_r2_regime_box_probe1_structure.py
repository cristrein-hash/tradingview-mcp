#!/usr/bin/env python3
"""LAB B r2 — REGIME BOX probe 1 (STRUCTURE ONLY, no outcome look).
Constrói, para cada membro da base N435 (g_in_base435==1, g_v5h!='BEAR'):
  - segmento do regime v5h corrente: horas consecutivas com mesmo estado v5h (hour-causal, replica engine)
  - box do segmento = hi/lo dos bars 15m com t em [inicio_segmento, cj_t]  (causal: só bars fechados)
  - rbox_pos = (entry - lo)/(hi - lo)
  - rbox_age_h = idade do regime em horas de mercado; rbox_h_atr = altura do box em ATR
  - segmento ANTERIOR: estado + box hi -> prev_hi_dist_atr = (prev_box_hi - entry)/atr (teto herdado)
Valida v5h reconstruído vs g_v5h do jsonl. Imprime SÓ distribuições/cobertura (sem R).
"""
import json,bisect
from pathlib import Path
HERE=Path(__file__).parent.parent   # .../xau_15m_bb_nas_leonardo
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
bars={}
for pr in PRIM.values():
    for b in pr["series"]: bars.setdefault(b["t"],b)
T15=sorted(bars)
H={}
for t in T15:
    b=bars[t]; hk=t//3600; g=H.setdefault(hk,{"c":b["c"],"h":b["h"]}); g["h"]=max(g["h"],b["h"]); g["c"]=b["c"]
HK=sorted(H); HC=[H[k]["c"] for k in HK]; HH=[H[k]["h"] for k in HK]
days={}
for t in T15:
    b=bars[t]; k=t//86400; g=days.setdefault(k,{"h":b["h"],"l":b["l"],"c":b["c"]})
    g["h"]=max(g["h"],b["h"]); g["l"]=min(g["l"],b["l"]); g["c"]=b["c"]
DK=sorted(days); DC=[days[k]["c"] for k in DK]; DH=[days[k]["h"] for k in DK]; DL=[days[k]["l"] for k in DK]
TR=[0.0]
for i in range(1,len(DK)): TR.append(max(DH[i]-DL[i],abs(DH[i]-DC[i-1]),abs(DL[i]-DC[i-1])))
def atrd(i,n=14): a=TR[max(1,i-n+1):i+1]; return sum(a)/len(a) if a else 1.0
def ema_at(arr,i,n):
    c=arr[max(0,i-3*n):i+1]; k=2/(n+1); e=c[0]
    for v in c[1:]: e=v*k+e*(1-k)
    return e
E50=[ema_at(DC,i,50) for i in range(len(DK))]; E100=[ema_at(DC,i,100) for i in range(len(DK))]
N,eff_thr,slope_thr,R_thr,K,Kbear=15,0.30,0.20,2.0,5,5
def raw_stable(i):
    if i<max(2*N,40): return "RANGE"
    a=atrd(i) or 1.0; slope=(E50[i]-E50[i-5])/a
    seg=DC[i-N:i+1]; net=seg[-1]-seg[0]; path=sum(abs(seg[j]-seg[j-1]) for j in range(1,len(seg))); eff=abs(net)/path if path>0 else 0
    hh=max(DH[i-N:i]); ll=min(DL[i-N:i]); pos=(DC[i]-ll)/(hh-ll) if hh>ll else .5; s100=(E100[i]-E100[i-10])/a
    tu=eff>=eff_thr and slope>slope_thr; td=eff>=eff_thr and slope<-slope_thr
    sb=E50[i]>E100[i] and s100>0; se=E50[i]<E100[i] and s100<0
    cont=eff<eff_thr and 0.15<=pos<=0.85 and abs(slope)<slope_thr
    peak=max(DH[i-30:i+1]); retreat=(peak-DC[i])/a; lh=max(DH[i-N:i])<max(DH[i-2*N:i-N]); bef=DC[i]<E50[i] and (E50[i]-E50[i-5])<0; bl=DC[i]<min(DL[i-N:i-2])
    if (bl and bef) or (retreat>=R_thr and lh and bef) or td or (se and pos<0.6 and not cont): return "BEAR"
    if tu or (sb and pos>0.55 and not cont): return "BULL"
    return "RANGE"
rawS=[raw_stable(i) for i in range(len(DK))]
stable=[]; cur="RANGE"; pend=None; pn=0
for v in rawS:
    if v==cur: pend=None; pn=0
    elif v==pend: pn+=1
    else: pend=v; pn=1
    need=Kbear if pend=="BEAR" else K
    if pn>=need: cur=pend; pend=None; pn=0
    stable.append(cur)
P,mom,dd_intra,Krec_h=48,24,0.06,120
ov_hour=[]; ov=False; quiet=0
for j in range(len(HK)):
    if j<max(P,mom): ov_hour.append(False); continue
    peak=max(HH[j-P:j+1]); ddp=(peak-HC[j])/peak if peak>0 else 0
    fired= ddp>=dd_intra and HC[j]<HC[j-mom]
    if fired: ov=True; quiet=0
    elif ov:
        quiet+=1
        if quiet>=Krec_h: ov=False
    ov_hour.append(ov)
def regime_hourcausal(cjt):
    dk_today=cjt//86400
    di=bisect.bisect_left(DK,dk_today)-1
    st="RANGE" if di<0 else stable[di]
    hi=bisect.bisect_right(HK,(cjt//3600)-1)-1
    ovr= ov_hour[hi] if hi>=0 else False
    return "BEAR" if (ovr or st=="BEAR") else st
# ---- estado v5h POR HORA de mercado (constante dentro da hora) ----
STATE=[regime_hourcausal(hk*3600) for hk in HK]
# segmentos: runs consecutivos no eixo de horas de mercado
seg_id=[0]*len(HK)
for j in range(1,len(HK)):
    seg_id[j]=seg_id[j-1]+(1 if STATE[j]!=STATE[j-1] else 0)
seg_start={}; seg_end={}; seg_state={}
for j,sid in enumerate(seg_id):
    seg_start.setdefault(sid,j); seg_end[sid]=j; seg_state[sid]=STATE[j]
# ---- base 435 ----
rows=[json.loads(l) for l in (HERE/"results/lab_g_candidates.jsonl").read_text().splitlines()]
base=[r for r in rows if r.get("g_in_base435")==1 and r.get("g_v5h")!="BEAR"]
mismatch=0
feats=[]
T15arr=T15
for r in base:
    cjt=r["cj_t"]; entry=r["g_entry"]; atr=r["g_atr"]
    myst=regime_hourcausal(cjt)
    if myst!=r["g_v5h"]: mismatch+=1
    h=cjt//3600
    j=bisect.bisect_right(HK,h)-1
    sid=seg_id[j]; j0=seg_start[sid]
    t0=HK[j0]*3600
    # bars 15m do segmento até cj_t (fechados)
    i0=bisect.bisect_left(T15arr,t0); i1=bisect.bisect_right(T15arr,cjt)
    seg_bars=[bars[t] for t in T15arr[i0:i1]]
    hi=max(b["h"] for b in seg_bars); lo=min(b["l"] for b in seg_bars)
    pos=(entry-lo)/((hi-lo) or atr)
    age_h=j-j0+1
    height_atr=(hi-lo)/atr
    censored=1 if j0==0 else 0
    # segmento anterior
    if sid>0:
        pj0,pj1=seg_start[sid-1],seg_end[sid-1]
        pt0,pt1=HK[pj0]*3600,(HK[pj1]+1)*3600
        pi0=bisect.bisect_left(T15arr,pt0); pi1=bisect.bisect_left(T15arr,pt1)
        pb=[bars[t] for t in T15arr[pi0:pi1]]
        phi=max(b["h"] for b in pb); plo=min(b["l"] for b in pb)
        pstate=seg_state[sid-1]
        prev_hi_dist=(phi-entry)/atr   # >0 teto acima; <0 já rompeu teto herdado
        prev_len_h=pj1-pj0+1
    else:
        pstate=None; prev_hi_dist=None; phi=plo=None; prev_len_h=None
    feats.append({"cj_t":cjt,"block":r["block"],"yr":r["yr"],"v5h":r["g_v5h"],"entry":entry,"atr":atr,
                  "rbox_pos":round(pos,4),"rbox_age_h":age_h,"rbox_h_atr":round(height_atr,3),
                  "rbox_hi_dist_atr":round((hi-entry)/atr,3),"censored":censored,
                  "prev_state":pstate,"prev_hi_dist_atr":None if prev_hi_dist is None else round(prev_hi_dist,3),
                  "prev_len_h":prev_len_h,
                  "g_risk":r["g_risk"],"g_R":r["g_R"],"g_week":r["g_week"]})
(Path(__file__).parent/"_labB_r2_regime_box_feats.json").write_text(json.dumps(feats))
print(f"base {len(base)}  v5h mismatch reconstrução vs jsonl: {mismatch}")
import statistics as st
def qs(v):
    v=sorted(v); n=len(v)
    return {q:round(v[min(n-1,int(q*n))],3) for q in (0.1,0.25,0.5,0.75,0.9)}
for reg in ("BULL","RANGE"):
    F=[f for f in feats if f["v5h"]==reg]
    print(f"\n== {reg}  N{len(F)}  (censored {sum(f['censored'] for f in F)})")
    print(" rbox_pos      q:",qs([f["rbox_pos"] for f in F]))
    print(" rbox_age_h    q:",qs([f["rbox_age_h"] for f in F]))
    print(" rbox_h_atr    q:",qs([f["rbox_h_atr"] for f in F]))
    print(" rboxhi_dist   q:",qs([f["rbox_hi_dist_atr"] for f in F]))
    pv=[f["prev_hi_dist_atr"] for f in F if f["prev_hi_dist_atr"] is not None]
    print(f" prev_hi_dist  q ({len(pv)} com prev):",qs(pv))
    from collections import Counter
    print(" prev_state:",Counter(f["prev_state"] for f in F))
    # cobertura por quintil de rbox_pos (bins fixos 0-0.2-0.4-0.6-0.8-1+)
    bins=[0,.2,.4,.6,.8,1.0,99]
    lab=["<0.2","0.2-0.4","0.4-0.6","0.6-0.8","0.8-1.0",">1.0"]
    cnt=Counter()
    for f in F:
        for k in range(len(bins)-1):
            if bins[k]<=f["rbox_pos"]<bins[k+1]: cnt[lab[k]]+=1; break
        else: cnt["<0"]+=1
    print(" cobertura rbox_pos bins:",dict((l,cnt.get(l,0)) for l in ["<0"]+lab))
