#!/usr/bin/env python3
"""RECONSTRUÇÃO v2 (não validação) — corrige v1: separa candidate-gen de trade-selection,
salva candidates_pre_cooldown, cooldown = dedup local, e traça o monumental 2024-03-26.
Gates IDÊNTICOS ao v1 (sem relaxar). Não toca produção, não MCP/chart, escreve só em rebuild_v2/.
"""
import gzip, json, bisect, statistics
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
RAW = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
REGIME = REPO / "my-strategy/strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl"

P_START = int(datetime(2020,1,1,tzinfo=timezone.utc).timestamp())
P_END   = int(datetime(2025,12,31,23,59,tzinfo=timezone.utc).timestamp())
ATR_MIN, ATR_MAX = 0.004, 0.030
BODY_MIN, F5_MAX, RET5_MIN = 0.35, 1.0, -0.04
OB_TOL, MA_TOL = 0.001, 0.002
R_FLOOR_ATR, R_CEIL_ATR = 0.3, 1.5
TARGET_R, TIME_STOP, SLIP = 20.0, 60, 0.1
DEDUP_K = 6  # cooldown local (ASSUMPTION, não tunado)
STAIR = [(2.0,0.0),(5.0,1.0),(8.0,3.0),(12.0,6.0),(16.0,10.0)]

# ---- RAW ----
bars={}; zones_at={}
with gzip.open(RAW,"rt") as f:
    for line in f:
        if '"replay_current_date"' not in line: continue
        r=json.loads(line); ov=r.get("ohlcv") or []
        if not ov: continue
        for b in ov:
            if b.get("time") is not None and b.get("close") is not None:
                bars[b["time"]]={"o":b["open"],"h":b["high"],"l":b["low"],"c":b["close"],"v":b.get("volume") or 0}
        cur=max(b["time"] for b in ov); zs=[]
        for s in (r.get("pine_boxes") or []):
            if "Custom OB" in s.get("name",""):
                for z in (s.get("zones") or []):
                    if z.get("high") is not None and z.get("low") is not None: zs.append((z["high"],z["low"]))
        if zs: zones_at[cur]=zs
T=sorted(bars); idx={t:i for i,t in enumerate(T)}; N=len(T)
O=[bars[t]["o"] for t in T];H=[bars[t]["h"] for t in T];L=[bars[t]["l"] for t in T];C=[bars[t]["c"] for t in T];V=[bars[t]["v"] for t in T]

def ema(s,sp):
    k=2/(sp+1);out=[None]*len(s);e=s[0]
    for i,x in enumerate(s): e=x if i==0 else x*k+e*(1-k);out[i]=e
    return out
def sma(s,n):
    out=[None]*len(s);q=deque();ss=0.0
    for i,x in enumerate(s):
        q.append(x);ss+=x
        if len(q)>n: ss-=q.popleft()
        if len(q)==n: out[i]=ss/n
    return out
EMA21=ema(C,21);SMA50=sma(C,50)
TR=[H[0]-L[0]]+[max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])) for i in range(1,N)]
ATR14=[None]*N
if N>=14:
    a=sum(TR[:14])/14;ATR14[13]=a
    for i in range(14,N): a=(a*13+TR[i])/14;ATR14[i]=a

reg=[]
for l in open(REGIME):
    r=json.loads(l);ts=r.get("ts")
    try: t=int(datetime.fromisoformat(ts.replace("Z","+00:00")).timestamp())
    except: t=int(datetime.strptime(ts[:10],"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
    reg.append((t,r.get("v3_state")))
reg.sort();RT=[t for t,_ in reg]
def regime_d1(et):
    i=bisect.bisect_left(RT,et)-1
    while i>0 and RT[i]>=et: i-=1
    return reg[i][1] if i>=0 else None

def demand_zone(i):
    zs=zones_at.get(T[i-1])
    if not zs:
        j=i-1
        while j>=0 and T[j] not in zones_at: j-=1
        zs=zones_at.get(T[j]) if j>=0 else None
    if not zs: return None
    cprev=C[i-1]; below=[(hi,lo) for hi,lo in zs if hi<cprev]
    if not below: return None
    return max(below,key=lambda z:z[0])

def gate_trace(i):
    """Retorna (passed, fail_gate, info). Gates idênticos ao v1, em ordem."""
    if i<60: return False,"history",{}
    if None in (EMA21[i-1],SMA50[i-1],ATR14[i-1]) or i-7<0 or SMA50[i-7] is None: return False,"indicators_none",{}
    t=T[i]
    if regime_d1(t)!="BULL": return False,"regime_d1_not_BULL",{}
    if not (C[i-1]>EMA21[i-1]): return False,"close_prev<=EMA21",{}
    if not (C[i-1]>SMA50[i-1]): return False,"close_prev<=SMA50",{}
    if not (EMA21[i-1]>EMA21[i-4]): return False,"ema21_slope3<=0",{}
    if not (SMA50[i-1]>SMA50[i-7]): return False,"sma50_slope6<=0",{}
    hh20=max(H[max(0,i-21):i-1])
    if not (hh20>max(C[max(0,i-21):i-1])): return False,"bos_fail",{}
    atrr=ATR14[i-1]/C[i-1]
    if not (ATR_MIN<=atrr<=ATR_MAX): return False,f"atr_ratio_oob({atrr:.4f})",{}
    dz=demand_zone(i);src="OB_v11"
    if dz is None: zhi=zlo=EMA21[i-1];src="EMA21_proxy";tol=MA_TOL
    else: zhi,zlo=dz;tol=OB_TOL
    touched=(L[i]<=zhi*(1+tol) and L[i]>=zlo*(1-tol)) or (L[i-1]<=zhi*(1+tol) and L[i-1]>=zlo*(1-tol)) or (L[i]<zlo and C[i]>zhi)
    if not touched: return False,"zone_not_touched",{"zhi":round(zhi,2),"zlo":round(zlo,2),"low":round(L[i],2)}
    if not (C[i]>zhi): return False,"close<=zone_high",{}
    rng=H[i]-L[i]
    if rng<=0 or (C[i]-O[i])/rng<BODY_MIN: return False,f"body_pct<{BODY_MIN}",{}
    if not (C[i]>C[i-1]): return False,"close<=prior",{}
    if i-5<0 or (C[i]/C[i-5]-1)<=RET5_MIN: return False,"ret5<=-4%",{}
    vmed=statistics.median(V[i-50:i]) if i-50>=0 else None
    if not vmed or vmed<=0: return False,"vmed_none",{}
    vr=V[i]/vmed
    if vr>F5_MAX: return False,f"F5_vol_ratio>{F5_MAX}({vr:.2f})",{}
    return True,"PASS",{"entry":round(C[i],2),"zone_source":src,"zhi":round(zhi,2),"zlo":round(zlo,2),"vol_ratio":round(vr,3)}

def simulate_exit(i_entry,entry,stop0):
    Runit=entry-stop0
    if Runit<=0: return None
    stop=stop0;mfe=0.0;locked=0.0;last=min(i_entry+TIME_STOP,N-1)
    for j in range(i_entry+1,last+1):
        fav=(H[j]-entry)/Runit
        if fav>mfe: mfe=fav
        for thr,lk in STAIR:
            if mfe>=thr and lk>=locked: locked=lk;stop=entry+locked*Runit
        if L[j]<=stop: return (stop-entry)/Runit-SLIP,mfe,T[j],"stop/lock"
        if H[j]>=entry+TARGET_R*Runit: return TARGET_R-SLIP,mfe,T[j],"target"
    return (C[last]-entry)/Runit-SLIP,mfe,T[last],"time"

# ---- candidate generation (sem cooldown) ----
candidates=[]
for i in range(60,N):
    t=T[i]
    if t<P_START or t>P_END: continue
    ok,reason,info=gate_trace(i)
    if ok: candidates.append({"i":i,"ts":datetime.utcfromtimestamp(t).isoformat(),"entry_time":t,**info})
with open(HERE/"candidates_pre_cooldown.jsonl","w") as f:
    for c in candidates: f.write(json.dumps(c)+"\n")

# ---- trace 2024-03-26 (todos bars do dia) ----
day0=int(datetime(2024,3,26,tzinfo=timezone.utc).timestamp());day1=day0+86400
mon_trace=[]
for i in range(N):
    if day0<=T[i]<day1:
        ok,reason,info=gate_trace(i)
        mon_trace.append({"bar":datetime.utcfromtimestamp(T[i]).isoformat(),"passed":ok,"fail_gate":reason})
appears_cand=any(day0<=c["entry_time"]<day1 for c in candidates)

# ---- trade selection: dedup local K ----
trades=[];last_entry_i=-10**9
for c in candidates:
    i=c["i"]
    if i-last_entry_i<DEDUP_K: continue
    zlo=c["zlo"];entry=c["entry"]
    sl=min(L[i],min(L[max(0,i-4):i+1]),zlo)-0.1*ATR14[i-1];Runit=entry-sl
    if Runit<=0: continue
    if Runit<R_FLOOR_ATR*ATR14[i-1]: sl=entry-R_FLOOR_ATR*ATR14[i-1];Runit=entry-sl
    if Runit>R_CEIL_ATR*ATR14[i-1]: continue
    res=simulate_exit(i,entry,sl)
    if res is None: continue
    R,mfe,texit,why=res
    trades.append({"ts":c["ts"],"entry":entry,"stop":round(sl,2),"R":round(R,2),"MFE_R":round(mfe,2),"zone_source":c["zone_source"],"exit_reason":why,"exit_ts":datetime.utcfromtimestamp(texit).isoformat()})
    last_entry_i=i
with open(HERE/"trades.jsonl","w") as f:
    for tr in trades: f.write(json.dumps(tr)+"\n")

# ---- summary ----
Rs=[tr["R"] for tr in trades];n=len(Rs);sumR=round(sum(Rs),2);wr=round(100*sum(1 for r in Rs if r>0)/n,1) if n else 0
appears_trade=any(day0<=int(datetime.fromisoformat(tr["ts"]).timestamp())<day1 for tr in trades)
old_n,old_sumR,old_wr=16,31.74,43.8
cpc=len(candidates)
if n==0: rec="FAILED_RECONSTRUCTION"
elif abs(n-old_n)<=2 and abs(sumR-old_sumR)<=10: rec="PARTIAL_RECONCILIATION"
elif n>3: rec="IMPROVED_BUT_UNFAITHFUL"
else: rec="FAILED_RECONSTRUCTION"
big15=sum(1 for r in Rs if r>=15)
summary={"strategy_id":"XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5","rebuild":"v2","NOT_VALIDATION":True,
  "candidate_count_pre_cooldown":cpc,"trade_count":n,
  "2024_03_26_appears_as_candidate":appears_cand,"2024_03_26_appears_as_trade":appears_trade,
  "gates_failed_2024_03_26":mon_trace,
  "sumR":sumR,"WR":wr,"avgR":round(sumR/n,2) if n else 0,"big15W":big15,
  "comparison_to_memory":{"expected_n":old_n,"expected_sumR":old_sumR,"expected_WR":old_wr},
  "reconciliation_status":rec,"warning":"NOT_VALIDATION",
  "dedup_K_bars":DEDUP_K,"dedup_K_is_assumption":True}
json.dump(summary,open(HERE/"summary.json","w"),indent=2)
print(json.dumps({k:summary[k] for k in ["candidate_count_pre_cooldown","trade_count","2024_03_26_appears_as_candidate","2024_03_26_appears_as_trade","sumR","WR","big15W","reconciliation_status"]},indent=2))
print("\n2024-03-26 trace:");[print("  ",x) for x in mon_trace]
print(f"\ncandidates_pre_cooldown: {cpc} | trades: {n}")
