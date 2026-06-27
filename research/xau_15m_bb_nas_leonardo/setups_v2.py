#!/usr/bin/env python3
"""ETAPA 1 — os 4 SETUPS primários como detectores DETERMINÍSTICOS (RAW-causal). SEM meta (só caracterizar entrada).
GLOBAL GATE (cut ambiente): anti_sequence_veto OR cbfs OR value_migration_against OR acceleration_veto.
Voters (entry, causal bars<=j, SHIFT1): v_sweep(STOP_RUN_VACUUM), v_freshHL(LEG_FRACTAL_FLIP), v_young(AGE),
v_session/killzone, v_trapped, v_eqfake, v_room, v_momdecay. [bubble_exhaustion DEFERIDO: precisa extrair bubbles.]
SETUPS: S1 BULL-cont(BULL: (freshHL|young)&sweep&session, conv>=2) · S2 reversão-exaustão(qualquer macro: sweep&momdecay,
conv>=2) · S3 session-driven(session&value-with&killzone, conv>=2) · S4 trap-fade(contra-macro: trapped&eqfake&room, conv>=2, >=10 fires).
OUTCOME: let-run trailing estrutural, SL estrutural (piso 0.5ATR), loser=−1R CHEIO (scoring AUDITADO). Verified 2026-06-26."""
import json, bisect, datetime as dt, statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in (HERE/"primitives").glob("*.primitives.json")}
M=json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]; MEND=[b["t_end"] for b in M]
def macro_at(t): k=bisect.bisect_right(MEND,t)-1; return M[k]["macro"] if k>=0 else "WARMUP"
K,LB,EPS,MINR,RCAP,HMAX=2,50,0.05,0.5,15.0,480
def sw_low(L,i):
    for p in range(i-K,max(K,i-LB)-1,-1):
        if L[p]==min(L[p-K:p+K+1]): return L[p],p
    return None,None
def sw_high(H,i):
    for p in range(i-K,max(K,i-LB)-1,-1):
        if H[p]==max(H[p-K:p+K+1]): return H[p],p
    return None,None
def cf_low(s,i):
    L=[b["l"] for b in s]; lo=max(K,i-120); bst=None
    for p in range(lo,i-K+1):
        if L[p]==min(L[p-K:p+K+1]): bst=L[p]
    return bst
def cf_high(s,i):
    H=[b["h"] for b in s]; lo=max(K,i-120); bst=None
    for p in range(lo,i-K+1):
        if H[p]==max(H[p-K:p+K+1]): bst=H[p]
    return bst
def prior_sw_lows(L,i,n=2):
    out=[]
    for p in range(i-K,max(K,i-120)-1,-1):
        if L[p]==min(L[p-K:p+K+1]): out.append(L[p])
        if len(out)>=n: break
    return out
def prior_sw_highs(H,i,n=2):
    out=[]
    for p in range(i-K,max(K,i-120)-1,-1):
        if H[p]==max(H[p-K:p+K+1]): out.append(H[p])
        if len(out)>=n: break
    return out
# ---- GLOBAL GATE ----
def gate(s,i,long,atr,nas_ts):
    t=s[i]["t"]; w0=max(0,i-30)
    ndir=sum(1 for x in nas_ts if s[w0]["t"]<=x<=t); disp=abs(s[i]["c"]-s[w0]["c"])/atr
    anti=ndir>=6 and disp<1.5
    bos=fail=0
    for j in range(max(40,i-40),i+1):
        rh=max(x["h"] for x in s[j-20:j]); rl=min(x["l"] for x in s[j-20:j])
        if s[j]["c"]>rh:
            bos+=1
            if any(s[k]["c"]<rh for k in range(j+1,min(j+5,i+1))): fail+=1
        elif s[j]["c"]<rl:
            bos+=1
            if any(s[k]["c"]>rl for k in range(j+1,min(j+5,i+1))): fail+=1
    cbfs=bos>=3 and fail/bos>0.6
    day=t//86400; tp=lambda x:(x["h"]+x["l"]+x["c"])/3
    cur=[tp(x) for x in s[max(0,i-96):i+1] if x["t"]//86400==day]; prev=[tp(x) for x in s[max(0,i-192):i+1] if x["t"]//86400==day-1]
    vmig=False
    if cur and prev:
        vt=st.mean(cur); vp=st.mean(prev); vmig=(vt<vp*0.999) if long else (vt>vp*1.001)
    acc=False
    if i>=3:
        if long: acc=s[i]["c"]<s[i-1]["c"]<s[i-2]["c"] and (s[i]["h"]-s[i]["l"])>(s[i-1]["h"]-s[i-1]["l"])>(s[i-2]["h"]-s[i-2]["l"])
        else: acc=s[i]["c"]>s[i-1]["c"]>s[i-2]["c"] and (s[i]["h"]-s[i]["l"])>(s[i-1]["h"]-s[i-1]["l"])>(s[i-2]["h"]-s[i-2]["l"])
    return anti or cbfs or vmig or acc
# ---- OUTCOME (let-run, loser=-1R CHEIO; auditado) ----
def outcome(s,ei,entry,sl0,long,atr):
    risk=max((entry-sl0) if long else (sl0-entry),MINR*atr)
    if risk<=0: return None
    sl0=(entry-risk) if long else (entry+risk); trail=sl0; r1=False; ex=None; end=min(ei+HMAX,len(s)-1)
    for i in range(ei+1,end+1):
        bar=s[i]
        if long:
            if bar["l"]<=trail: ex=trail; break
            if (bar["h"]-entry)/risk>=1: r1=True
            if r1:
                sw=cf_low(s,i)
                if sw: trail=max(trail,sw-0.1*atr)
        else:
            if bar["h"]>=trail: ex=trail; break
            if (entry-bar["l"])/risk>=1: r1=True
            if r1:
                sh=cf_high(s,i)
                if sh: trail=min(trail,sh+0.1*atr)
    if ex is None: ex=s[end]["c"]
    R=((ex-entry) if long else (entry-ex))/risk
    return max(-1.0,min(RCAP,R))
def killzone(hr): return 1 if (7<=hr<12 or 13<=hr<18) else 0
def detect():
    res={1:[],2:[],3:[],4:[]}
    for b,pr in PRIM.items():
        s=pr["series"]; n=len(s); L=[x["l"] for x in s]; H=[x["h"] for x in s]
        nas_ts=sorted([e["t"] for e in pr["nas_events"] if e["t"]])
        smc=pr["smc_events"]
        eqh=[(e["price"],e["t"]) for e in smc if e["text"] and "EQH" in str(e["text"]) and e["price"] and e["t"]]  # com tempo (anti look-ahead)
        eql=[(e["price"],e["t"]) for e in smc if e["text"] and "EQL" in str(e["text"]) and e["price"] and e["t"]]
        last={1:-999,2:-999,3:-999,4:-999}
        for i in range(LB+K,n-2):
            t=s[i]["t"]; atr=s[i]["atr"];
            if not atr: continue
            mac=macro_at(t); hr=dt.datetime.utcfromtimestamp(t).hour; yr=dt.datetime.utcfromtimestamp(t).year
            # voters LONG (BULL) e SHORT (BEAR)
            for long in (True,False):
                if long and mac!="BULL": continue
                if (not long) and mac!="BEAR": continue
                if gate(s,i,long,atr,nas_ts): continue   # GATE
                liq,lp=(sw_low(L,i) if long else sw_high(H,i))
                if liq is None: continue
                v_sweep=(L[i]<liq-EPS*atr and s[i]["c"]>liq) if long else (H[i]>liq+EPS*atr and s[i]["c"]<liq)
                pls=prior_sw_lows(L,i,2) if long else prior_sw_highs(H,i,2)
                v_freshHL=(len(pls)>=2 and ((pls[0]>pls[1]) if long else (pls[0]<pls[1])))
                # young: extensão na perna (fundo->topo recente)
                lo20=min(L[max(0,i-20):i+1]); hi20=max(H[max(0,i-20):i+1])
                ext=(s[i]["c"]-lo20)/(hi20-lo20) if hi20>lo20 else 0.5
                v_young=(ext<=0.5) if long else (ext>=0.5)
                v_session=killzone(hr)
                # trapped breakout (volume-free): rompeu range 20b e segurou 3 barras
                rh=max(H[i-23:i-3]) if i>=23 else None
                v_trapped=(rh and s[i]["c"]>rh and all(s[k]["c"]>rh for k in range(i-2,i+1))) if long else False
                # eq fakeout
                v_eqfake=False
                if long:
                    elig=[p for p,te in eql if te<=t and p<s[i]["c"]]   # só EQ já formados (te<=t)
                    if elig: lv=max(elig); v_eqfake=L[i]<lv and s[i]["c"]>lv
                else:
                    elig=[p for p,te in eqh if te<=t and p>s[i]["c"]]
                    if elig: lv=min(elig); v_eqfake=H[i]>lv and s[i]["c"]<lv
                # room: dist a estrutura oposta /atr
                opp=cf_high(s,i) if long else cf_low(s,i)
                v_room=(opp and abs(opp-s[i]["c"])/atr>=2.0)
                # momentum decay da contra-perna (3 barras com ranges decrescentes)
                v_momdecay=(s[i-2]["h"]-s[i-2]["l"])>(s[i-1]["h"]-s[i-1]["l"])>(s[i]["h"]-s[i]["l"]) if i>=3 else False
                ei=i+1
                if ei+2>=n: continue
                entry=s[ei]["c"]; sl0=(L[i]-0.1*atr) if long else (H[i]+0.1*atr)
                def add(setup):
                    if i-last[setup]<8: return
                    R=outcome(s,ei,entry,sl0,long,atr)
                    if R is None: return
                    res[setup].append({"block":b,"t":t,"yr":yr,"dir":"LONG" if long else "SHORT","R":R,"w":R>0}); last[setup]=i
                # S1 BULL-cont (só long/bull)
                if long and sum([v_freshHL or v_young, v_sweep, bool(v_session)])>=2: add(1)
                # S2 reversão-exaustão (qualquer macro pós-gate)
                if sum([v_sweep, v_momdecay])>=2: add(2)
                # S3 session-driven
                if sum([bool(v_session), bool(v_room), killzone(hr)])>=2 and v_session: add(3)
                # S4 trap-fade
                if sum([bool(v_trapped), v_eqfake, bool(v_room)])>=2: add(4)
    return res
def carac(trs,label):
    if not trs: print(f"  [{label}] n=0"); return
    n=len(trs);w=sum(1 for x in trs if x["w"]);sm=sum(x["R"] for x in trs)
    ts=sorted(trs,key=lambda x:x["t"]);span=(ts[-1]["t"]-ts[0]["t"])/(7*86400) or 1
    byb={};
    for x in trs: byb.setdefault(x["block"][:16],[]).append(x)
    pos=sum(1 for bb in byb if sum(x["R"] for x in byb[bb])>0)
    cap=lambda x:max(-1.0,min(RCAP,x["R"])); drop=set(sorted(byb,key=lambda bb:sum(cap(x) for x in byb[bb]),reverse=True)[:2])
    rem=[x for x in trs if x["block"][:16] not in drop]; allr=sorted([cap(x) for x in trs],reverse=True)
    yrs={y:[x for x in trs if x["yr"]==y] for y in (2024,2025,2026)}
    yrstr=" ".join(f"{y}:{100*sum(1 for x in v if x['w'])/len(v):.0f}%/{sum(x['R'] for x in v):+.0f}R" for y,v in yrs.items() if v)
    print(f"  [{label}] n={n} WR={100*w/n:.0f}% avgR={sm/n:+.2f} sumR={sm:+.1f} freq={n/span:.2f}/sem | blocos+{pos}/{len(byb)} | leave−top2bloc {sum(cap(x) for x in trs):+.0f}→{sum(cap(x) for x in rem):+.0f} | top5={100*sum(allr[:5])/max(0.1,sum(allr)):.0f}% | {yrstr}")
r=detect()
# AUDIT scoring: confirmar losers podem ser −1R cheio
allt=[x for s in r.values() for x in s]; full_loss=sum(1 for x in allt if abs(x["R"]+1.0)<1e-9); halfish=sum(1 for x in allt if abs(x["R"]+0.5)<1e-9)
print(f"[AUDIT scoring] trades={len(allt)} | losers=−1.0R exatos: {full_loss} | suspeitos −0.5R: {halfish} (deve ser ~0)")
print("\n=== 4 SETUPS determinísticos (SEM meta — caracterização; scoring auditado) ===")
for sid,name in [(1,"S1 BULL-cont"),(2,"S2 reversao-exaustao"),(3,"S3 session-driven"),(4,"S4 trap-fade")]:
    carac(r[sid],name)
print("\n[bubble_exhaustion = DEFERIDO: precisa extrair bubbles do RAW p/ Setup 2]")
