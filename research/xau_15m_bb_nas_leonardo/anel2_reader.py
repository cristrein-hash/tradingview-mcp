#!/usr/bin/env python3
"""ANEL 2 — leitura multi-lente POR EPISÓDIO (trade-a-trade) sobre os 4 setups da Fase 1.
Cada trade (episódio) é lido por um PAINEL de lentes ortogonais, todas CAUSAIS (bars<=i, RAW-only):
  L_macro   : contexto macro (preço do lado certo da EMA21 + EMA inclinando a favor)
  L_zone    : reação numa zona Custom OB (proxy BigBeluga) — demand(long)/supply(short) viva e defendida
  L_liq     : sweep+reclaim LIMPO (varreu swing e fechou de volta no mesmo bar, profundidade>=0.05ATR)
  L_leg     : estrutura da perna intacta (HL subindo / LH descendo)
  L_room    : espaço livre >=2ATR até estrutura oposta
  L_flow    : vela de rejeição na direção (pavio a favor >=40% do range + close na metade certa)
  L_rsi     : RSI não-exausto (long 35..70 / short 30..65)
  L_nas     : confluência NAS recente (<=20 bars) na direção do trade
  L_session : killzone (Londres/NY)
Convergência = nº de lentes "sim". Mede se a LEITURA separa winner/loser por setup:
  base WR/avgR ; WR/avgR por bucket de convergência ; lift por lente ; melhor corte com validação
  (por ano + leave-top2-blocos + top5 concentração). Scoring let-run AUDITADO (loser=-1R cheio). 2026-06-26."""
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
LENSES=["L_macro","L_zone","L_liq","L_leg","L_room","L_flow","L_rsi","L_nas","L_session"]
def read_lenses(s,i,long,atr,L,H,zones_d,zones_s,nas_events,liq):
    t=s[i]["t"]; c=s[i]["c"]; o=s[i]["o"]; hi=s[i]["h"]; lo=s[i]["l"]; rng=max(hi-lo,1e-9); rsi=s[i].get("rsi")
    e=s[i]["ema21"]; e10=s[i-10]["ema21"] if i>=10 else e
    L_macro=1 if ((c>e and e>=e10) if long else (c<e and e<=e10)) else 0
    # zona Custom OB (proxy BigBeluga): zona viva (born_t<=t) e defendida pelo bar
    L_zone=0
    zl=zones_d if long else zones_s
    for z in zl:
        if z["born_t"]>t: continue
        if long and (lo<=z["high"]+0.3*atr and lo>=z["low"]-0.3*atr and c>z["low"]): L_zone=1; break
        if (not long) and (hi>=z["low"]-0.3*atr and hi<=z["high"]+0.3*atr and c<z["high"]): L_zone=1; break
    # sweep+reclaim limpo
    L_liq=1 if (liq is not None and ((lo<liq-EPS*atr and c>liq) if long else (hi>liq+EPS*atr and c<liq))) else 0
    pls=prior_sw_lows(L,i,2) if long else prior_sw_highs(H,i,2)
    L_leg=1 if (len(pls)>=2 and ((pls[0]>pls[1]) if long else (pls[0]<pls[1]))) else 0
    opp=cf_high(s,i) if long else cf_low(s,i)
    L_room=1 if (opp and abs(opp-c)/atr>=2.0) else 0
    if long: wick=(min(o,c)-lo); L_flow=1 if (wick>=0.4*rng and c>=(lo+0.5*rng)) else 0
    else: wick=(hi-max(o,c)); L_flow=1 if (wick>=0.4*rng and c<=(hi-0.5*rng)) else 0
    if rsi is None: L_rsi=0
    else: L_rsi=1 if ((35<=rsi<=70) if long else (30<=rsi<=65)) else 0
    L_nas=0
    for ev in reversed(nas_events):
        if ev["t"]>t: continue
        if t-ev["t"]>20*900: break
        if (ev["dir"]=="LONG")==long: L_nas=1
        break
    L_session=killzone(dt.datetime.utcfromtimestamp(t).hour)
    return {"L_macro":L_macro,"L_zone":L_zone,"L_liq":L_liq,"L_leg":L_leg,"L_room":L_room,"L_flow":L_flow,"L_rsi":L_rsi,"L_nas":L_nas,"L_session":L_session}
def detect():
    res={1:[],2:[],3:[],4:[]}
    for b,pr in PRIM.items():
        s=pr["series"]; n=len(s); L=[x["l"] for x in s]; H=[x["h"] for x in s]
        nas_ts=sorted([e["t"] for e in pr["nas_events"] if e["t"]])
        nas_events=sorted([e for e in pr["nas_events"] if e.get("t") and e.get("dir")],key=lambda e:e["t"])
        smc=pr["smc_events"]
        eqh=[(e["price"],e["t"]) for e in smc if e["text"] and "EQH" in str(e["text"]) and e["price"] and e["t"]]
        eql=[(e["price"],e["t"]) for e in smc if e["text"] and "EQL" in str(e["text"]) and e["price"] and e["t"]]
        zones_d=[z for z in pr["zones"] if "DEMAND" in str(z["text"]).upper()]
        zones_s=[z for z in pr["zones"] if "SUPPLY" in str(z["text"]).upper()]
        last={1:-999,2:-999,3:-999,4:-999}
        for i in range(LB+K,n-2):
            t=s[i]["t"]; atr=s[i]["atr"]
            if not atr: continue
            mac=macro_at(t); hr=dt.datetime.utcfromtimestamp(t).hour; yr=dt.datetime.utcfromtimestamp(t).year
            for long in (True,False):
                if long and mac!="BULL": continue
                if (not long) and mac!="BEAR": continue
                if gate(s,i,long,atr,nas_ts): continue
                liq,lp=(sw_low(L,i) if long else sw_high(H,i))
                if liq is None: continue
                v_sweep=(L[i]<liq-EPS*atr and s[i]["c"]>liq) if long else (H[i]>liq+EPS*atr and s[i]["c"]<liq)
                pls=prior_sw_lows(L,i,2) if long else prior_sw_highs(H,i,2)
                v_freshHL=(len(pls)>=2 and ((pls[0]>pls[1]) if long else (pls[0]<pls[1])))
                lo20=min(L[max(0,i-20):i+1]); hi20=max(H[max(0,i-20):i+1])
                ext=(s[i]["c"]-lo20)/(hi20-lo20) if hi20>lo20 else 0.5
                v_young=(ext<=0.5) if long else (ext>=0.5)
                v_session=killzone(hr)
                rh=max(H[i-23:i-3]) if i>=23 else None
                v_trapped=(rh and s[i]["c"]>rh and all(s[k]["c"]>rh for k in range(i-2,i+1))) if long else False
                v_eqfake=False
                if long:
                    elig=[p for p,te in eql if te<=t and p<s[i]["c"]]
                    if elig: lv=max(elig); v_eqfake=L[i]<lv and s[i]["c"]>lv
                else:
                    elig=[p for p,te in eqh if te<=t and p>s[i]["c"]]
                    if elig: lv=min(elig); v_eqfake=H[i]>lv and s[i]["c"]<lv
                opp=cf_high(s,i) if long else cf_low(s,i)
                v_room=(opp and abs(opp-s[i]["c"])/atr>=2.0)
                v_momdecay=(s[i-2]["h"]-s[i-2]["l"])>(s[i-1]["h"]-s[i-1]["l"])>(s[i]["h"]-s[i]["l"]) if i>=3 else False
                fires=[]
                if long and sum([v_freshHL or v_young, v_sweep, bool(v_session)])>=2: fires.append(1)
                if sum([v_sweep, v_momdecay])>=2: fires.append(2)
                if sum([bool(v_session), bool(v_room), killzone(hr)])>=2 and v_session: fires.append(3)
                if sum([bool(v_trapped), v_eqfake, bool(v_room)])>=2: fires.append(4)
                if not fires: continue
                ei=i+1
                if ei+2>=n: continue
                entry=s[ei]["c"]; sl0=(L[i]-0.1*atr) if long else (H[i]+0.1*atr)
                lens=read_lenses(s,i,long,atr,L,H,zones_d,zones_s,nas_events,liq)
                conv=sum(lens.values())
                R=outcome(s,ei,entry,sl0,long,atr)
                if R is None: continue
                for setup in fires:
                    if i-last[setup]<8: continue
                    tr={"block":b,"t":t,"yr":yr,"dir":"LONG" if long else "SHORT","R":R,"w":R>0,"conv":conv}
                    tr.update(lens); res[setup].append(tr); last[setup]=i
    return res
def wr(v): return 100*sum(1 for x in v if x["w"])/len(v) if v else 0
def avg(v): return sum(x["R"] for x in v)/len(v) if v else 0
def leave_top2(v):
    byb={};
    for x in v: byb.setdefault(x["block"][:16],[]).append(x)
    drop=set(sorted(byb,key=lambda bb:sum(x["R"] for x in byb[bb]),reverse=True)[:2])
    rem=[x for x in v if x["block"][:16] not in drop]; return sum(x["R"] for x in rem),len(rem)
def report(setup,name,v):
    if not v: print(f"\n### {name}: n=0"); return
    n=len(v); base_wr=wr(v); base_avg=avg(v); sm=sum(x["R"] for x in v)
    print(f"\n### {name}  base: n={n} WR={base_wr:.0f}% avgR={base_avg:+.2f} sumR={sm:+.1f}")
    # por bucket de convergência
    print("  conv | n  WR   avgR   sumR")
    for lo,hi in [(0,3),(4,5),(6,6),(7,9)]:
        sub=[x for x in v if lo<=x["conv"]<=hi]
        if sub: print(f"  {lo}-{hi} | {len(sub):>3} {wr(sub):>3.0f}% {avg(sub):+.2f} {sum(x['R'] for x in sub):+6.1f}")
    # lift por lente
    print("  lente     n1  WR1  avgR1 | n0  WR0  avgR0  | Δavg")
    for k in LENSES:
        a=[x for x in v if x[k]]; bz=[x for x in v if not x[k]]
        if a and bz:
            da=avg(a)-avg(bz)
            print(f"  {k:<9} {len(a):>3} {wr(a):>3.0f}% {avg(a):+.2f} | {len(bz):>3} {wr(bz):>3.0f}% {avg(bz):+.2f} | {da:+.2f}")
    # melhor corte de convergência (max sumR mantendo n>=15), com validação
    best=None
    for thr in range(3,9):
        sub=[x for x in v if x["conv"]>=thr]
        if len(sub)<15: continue
        if best is None or sum(x["R"] for x in sub)>sum(x["R"] for x in best[1]): best=(thr,sub)
    if best:
        thr,sub=best; lo,ln=leave_top2(sub); allr=sorted([x["R"] for x in sub],reverse=True)
        yrs={y:[x for x in sub if x["yr"]==y] for y in (2024,2025,2026)}
        ys=" ".join(f"{y}:{wr(vv):.0f}%/{sum(x['R'] for x in vv):+.0f}R" for y,vv in yrs.items() if vv)
        top5=100*sum(allr[:5])/max(0.1,sum(allr))
        print(f"  ► melhor corte conv>={thr}: n={len(sub)} WR={wr(sub):.0f}%(base {base_wr:.0f}) avgR={avg(sub):+.2f}(base {base_avg:+.2f}) sumR={sum(x['R'] for x in sub):+.1f}")
        print(f"     valida: leave-top2bloc {sum(x['R'] for x in sub):+.0f}→{lo:+.0f}(n{ln}) | top5={top5:.0f}% | por ano {ys}")
r=detect()
allt=[x for v in r.values() for x in v]
half=sum(1 for x in allt if abs(x["R"]+0.5)<1e-9)
print(f"[AUDIT scoring] trades={len(allt)} | suspeitos −0.5R={half} (deve ser 0) | conv média={st.mean([x['conv'] for x in allt]):.1f}/9")
print("\n========== ANEL 2 — leitura multi-lente por episódio (trade-a-trade) ==========")
for sid,name in [(1,"S1 BULL-cont"),(2,"S2 reversao-exaustao"),(3,"S3 session-driven"),(4,"S4 trap-fade")]:
    report(sid,name,r[sid])
