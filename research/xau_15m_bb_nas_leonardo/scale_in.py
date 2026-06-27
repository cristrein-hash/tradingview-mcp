#!/usr/bin/env python3
"""SCALE-IN na ACEITAÇÃO — adiciona 1 unidade no fechamento da vela W SE o trade já foi aceito (dispR@W>=thr).
Regra estrutural HONESTA (não tunável p/ número bonito):
  - base: 1 unidade no entry, risco R0=max(dist_estrutural,0.5ATR), SL em entry-R0, let-run trail (cf_low/high, +0.1ATR).
  - no bar ei+W, SE ainda viva (stop não disparou até o close de W) E dispR@W>=thr: ADD 1 unidade no close (P_add) e
    SOBE o trail p/ o swing-low da janela pós-entrada (structLow_W-0.1ATR) — a add NÃO arrisca de volta ao stop original.
  - daí pra frente as DUAS unidades compartilham o MESMO trail estrutural até a saída (ex). Saída consistente p/ ambas.
Contabilidade em R0: base_R=(ex-entry)/R0 ; add_R=(ex-P_add)/R0 (real, pode ser negativo se reverter pós-add).
Baseline = MESMOS trades sem add (do_add=False ≡ engine let-run v2). Compara sumR/avgR/WR/DD/streak/runners/leave-top2/ano.
Causal RAW-only. off-by-one do alive CORRIGIDO (stop checado no topo com trail anterior; add só se não-stopada até close de W). 2026-06-26."""
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
def cap(r): return max(-1.0,min(RCAP,r))        # base: stop em entry-R0 → piso -1R correto
def addcap(r): return min(RCAP,r)                # add: entra a +disp, stop no trail (abaixo da entrada) → SEM piso -1; perda real (trail-P_add)/R0
def simulate(s,ei,entry,long,atr,R0,W,thr,do_add):
    """Retorna (base_R, add_R, added). Engine let-run; add estrutural opcional no bar W."""
    sl0=(entry-R0) if long else (entry+R0); trail=sl0; r1=False; added=False; P_add=None; add_risk=0.0
    end=min(ei+HMAX,len(s)-1); ex=None; lows=[]; highs=[]
    for k in range(1,end-ei+1):
        i=ei+k; bar=s[i]; lows.append(bar["l"]); highs.append(bar["h"])
        # stop checado no TOPO com trail conhecido (do bar anterior) — causal, sem off-by-one
        if long and bar["l"]<=trail: ex=trail; break
        if (not long) and bar["h"]>=trail: ex=trail; break
        # let-run ratchet
        fav=((bar["h"]-entry) if long else (entry-bar["l"]))/R0
        if fav>=1: r1=True
        if r1:
            if long:
                sw=cf_low(s,i)
                if sw: trail=max(trail,sw-0.1*atr)
            else:
                sh=cf_high(s,i)
                if sh: trail=min(trail,sh+0.1*atr)
        # ADD no close de W (já passou o stop do bar W → viva)
        if do_add and k==W and not added:
            dispR=((bar["c"]-entry) if long else (entry-bar["c"]))/R0
            if dispR>=thr:
                added=True; P_add=bar["c"]
                if long:
                    structLow=min(lows); trail=max(trail,structLow-0.1*atr)
                else:
                    structHigh=max(highs); trail=min(trail,structHigh+0.1*atr)
                add_risk=((P_add-trail) if long else (trail-P_add))/R0   # risco REAL da add (em R0)
    if ex is None: ex=s[end]["c"]
    base_R=cap(((ex-entry) if long else (entry-ex))/R0)
    add_R=addcap(((ex-P_add) if long else (P_add-ex))/R0) if added else 0.0
    return base_R,add_R,added,add_risk
def build(W,thr,do_add):
    out=[]
    for b,pr in PRIM.items():
        s=pr["series"]; n=len(s); L=[x["l"] for x in s]; H=[x["h"] for x in s]
        nas_ts=sorted([e["t"] for e in pr["nas_events"] if e["t"]])
        last={"L":-999,"S":-999}
        for i in range(LB+K,n-2):
            t=s[i]["t"]; atr=s[i]["atr"]
            if not atr: continue
            mac=macro_at(t); yr=dt.datetime.utcfromtimestamp(t).year
            for long in (True,False):
                if long and mac!="BULL": continue
                if (not long) and mac!="BEAR": continue
                if gate(s,i,long,atr,nas_ts): continue
                liq,lp=(sw_low(L,i) if long else sw_high(H,i))
                if liq is None: continue
                v_sweep=(L[i]<liq-EPS*atr and s[i]["c"]>liq) if long else (H[i]>liq+EPS*atr and s[i]["c"]<liq)
                if not v_sweep: continue
                key="L" if long else "S"
                if i-last[key]<8: continue
                ei=i+1
                if ei+2>=n: continue
                entry=s[ei]["c"]; sl0=(L[i]-0.1*atr) if long else (H[i]+0.1*atr)
                R0=max((entry-sl0) if long else (sl0-entry),MINR*atr)
                if R0<=0: continue
                base_R,add_R,added,add_risk=simulate(s,ei,entry,long,atr,R0,W,thr,do_add)
                out.append({"block":b,"t":t,"yr":yr,"base":base_R,"add":add_R,"added":added,"tot":base_R+add_R,"add_risk":add_risk}); last[key]=i
    return out
def summ(out,col,label):
    n=len(out); ts=sorted(out,key=lambda x:x["t"]); sm=sum(x[col] for x in out)
    eq=pk=dd=0; stk=mstk=0
    for x in ts:
        eq+=x[col]; pk=max(pk,eq); dd=min(dd,eq-pk)
        if x[col]<=0: stk+=1; mstk=max(mstk,stk)
        else: stk=0
    wr=100*sum(1 for x in out if x[col]>0)/n; run=sum(1 for x in out if x[col]>=3)
    byb={};
    for x in out: byb.setdefault(x["block"][:16],[]).append(x)
    drop=set(sorted(byb,key=lambda bb:sum(z[col] for z in byb[bb]),reverse=True)[:2]); rem=sum(x[col] for x in out if x["block"][:16] not in drop)
    yrs=" ".join(f"{y}:{sum(x[col] for x in out if x['yr']==y):+.0f}R" for y in (2024,2025,2026) if any(x['yr']==y for x in out))
    print(f"  {label:<22} sumR={sm:+.1f} avgR={sm/n:+.2f} WR={wr:.0f}% DD={dd:.0f}R streak={mstk} run(>=3R)={run} | leave-top2→{rem:+.0f} | {yrs}")
# BASELINE (1 unidade, sem add) — col base com do_add=False
base=build(8,1.0,False)
print(f"[AUDIT] n={len(base)} trades | base = let-run 1 unidade")
summ(base,"base","BASELINE 1u let-run")
base_rd=sum(1.0 for _ in base)  # 1 R0 por trade baseline
print(f"  baseline risco-real deployado={base_rd:.0f} R0 | ret/risco={sum(x['base'] for x in base)/base_rd:.3f}")
print("\n========== SCALE-IN na aceitação (add 1u no close da vela W se dispR@W>=thr) [floor da add CORRIGIDO] ==========")
def riskstats(out):
    adds=[x for x in out if x["added"]]; nadd=len(adds)
    real_risk=len(out)*1.0+sum(x["add_risk"] for x in adds)   # base 1R0 cada + risco real das adds
    rr=sum(x["tot"] for x in out)/real_risk if real_risk else 0
    mean_addrisk=sum(x["add_risk"] for x in adds)/nadd if nadd else 0
    return nadd,real_risk,rr,mean_addrisk
for W in (4,8,12):
    for thr in (1.0,1.5,2.0):
        out=build(W,thr,True); nadd,real_risk,rr,mar=riskstats(out)
        addsm=sum(x["add"] for x in out if x["added"]); addpos=sum(1 for x in out if x["added"] and x["add"]>0)
        print(f"\n--- W={W} thr={thr:+.1f} (adds={nadd}, risco-real-add médio={mar:.2f}R0, add-unit sumR={addsm:+.1f}, add-unit WR={100*addpos/max(1,nadd):.0f}%) ---")
        summ(out,"tot","  TOTAL (base+add)")
        print(f"      risco-real deployado={real_risk:.0f} R0 (vs {len(out):.0f} baseline) | ret/risco-REAL={rr:.3f} (baseline 0.246)")
print("\n========== NULL: add-burro em TODO trade vivo no bar 8 (sem filtro de aceitação) ==========")
dumb=build(8,-1e9,True); nadd,real_risk,rr,mar=riskstats(dumb)
summ(dumb,"tot","  TOTAL add-all-alive")
print(f"      adds={nadd} risco-real-add médio={mar:.2f}R0 | risco-real deployado={real_risk:.0f} R0 | ret/risco-REAL={rr:.3f}")
print("  → se o filtro de aceitação NÃO bate isto em ret/risco, a 'leitura' não agrega além de pyramiding genérico.")
