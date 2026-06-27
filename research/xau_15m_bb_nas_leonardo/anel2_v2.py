#!/usr/bin/env python3
"""ANEL 2 v2 — leitura CORRIGIDA (responde à crítica do Cris: a v1 era leitura mal-construída).
Defeitos da v1 consertados:
  (1) RANGE-RESTRICTION: media lente DENTRO do setup que já foi selecionado por ela → absurdo (horário piora o
      setup-de-horário). v2 mede no UNIVERSO NÃO-CONDICIONADO = todo retest pós-sweep gated (1 só premissa, não os voters).
  (2) BINÁRIO ESTÁTICO: lentes viram GRADUADAS (0..1 contínuo), não joinha 0/1 na barra i.
  (3) ALVO=MAGNITUDE (cauda): além de WR, mede TAXA-DE-SEGURAR (held = chegou a +1R MFE antes de stopar) =
      'entrada fraca vs forte' de verdade, menos dominado por 2-3 runners.
  (4) ZONA contaminada (look-ahead de bounds, DA): EXCLUÍDA do score; reportada à parte.
Universo: macro-gated (BULL long/BEAR short) + global-gate + sweep+reclaim (premissa única). Lentes ORTOGONAIS à premissa.
Causal RAW-only. Scoring let-run auditado (loser=-1R). 2026-06-26."""
import json, bisect, datetime as dt, statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in (HERE/"primitives").glob("*.primitives.json")}
M=json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]; MEND=[b["t_end"] for b in M]
def macro_at(t): k=bisect.bisect_right(MEND,t)-1; return M[k]["macro"] if k>=0 else "WARMUP"
K,LB,EPS,MINR,RCAP,HMAX=2,50,0.05,0.5,15.0,480
def clip(x,a=0.0,b=1.0): return a if x<a else (b if x>b else x)
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
    sl0=(entry-risk) if long else (entry+risk); trail=sl0; r1=False; held=False; ex=None; end=min(ei+HMAX,len(s)-1)
    for i in range(ei+1,end+1):
        bar=s[i]
        if long:
            if bar["l"]<=trail: ex=trail; break
            if (bar["h"]-entry)/risk>=1: r1=True; held=True
            if r1:
                sw=cf_low(s,i)
                if sw: trail=max(trail,sw-0.1*atr)
        else:
            if bar["h"]>=trail: ex=trail; break
            if (entry-bar["l"])/risk>=1: r1=True; held=True
            if r1:
                sh=cf_high(s,i)
                if sh: trail=min(trail,sh+0.1*atr)
    if ex is None: ex=s[end]["c"]
    R=((ex-entry) if long else (entry-ex))/risk
    return max(-1.0,min(RCAP,R)),held
# lentes GRADUADAS (0..1), todas causais, ORTOGONAIS à premissa sweep+reclaim
def graded(s,i,long,atr,L,H,nas_events,liq,lp):
    c=s[i]["c"]; o=s[i]["o"]; hi=s[i]["h"]; lo=s[i]["l"]; rng=max(hi-lo,1e-9); rsi=s[i].get("rsi")
    e=s[i]["ema21"]; e10=s[i-10]["ema21"] if i>=10 else e
    dist=((c-e) if long else (e-c))/atr; slope=((e-e10) if long else (e10-e))/atr
    g_macro=clip(0.5*clip(dist/3.0)+0.5*clip(slope/1.0))                    # contexto: distância+inclinação EMA21 a favor
    depth=((liq-lo) if long else (hi-liq))/atr if liq is not None else 0     # profundidade do sweep
    g_sweep=clip(depth/1.0)
    opp=cf_high(s,i) if long else cf_low(s,i)
    room=abs(opp-c)/atr if opp else 0; g_room=clip(room/4.0)                 # espaço até estrutura oposta
    wick=((min(o,c)-lo) if long else (hi-max(o,c)))/rng; g_flow=clip(wick)   # rejeição na vela de gatilho
    if rsi is None: g_rsi=0.0
    else: g_rsi=clip(((70-rsi) if long else (rsi-30))/40.0)                  # headroom de RSI (não-exausto)
    pls=prior_sw_lows(L,i,2) if long else prior_sw_highs(H,i,2)
    g_leg=1.0 if (len(pls)>=2 and ((pls[0]>pls[1]) if long else (pls[0]<pls[1]))) else 0.0
    g_nas=0.0
    for ev in reversed(nas_events):
        if ev["t"]>s[i]["t"]: continue
        if s[i]["t"]-ev["t"]>20*900: break
        g_nas=1.0 if (ev["dir"]=="LONG")==long else 0.0; break
    hr=dt.datetime.utcfromtimestamp(s[i]["t"]).hour; g_session=1.0 if (7<=hr<12 or 13<=hr<18) else 0.0
    return {"macro":g_macro,"sweepdepth":g_sweep,"room":g_room,"flow":g_flow,"rsi":g_rsi,"leg":g_leg,"nas":g_nas,"session":g_session}
LENS=["macro","sweepdepth","room","flow","rsi","leg","nas","session"]
def build_universe():
    U=[]
    for b,pr in PRIM.items():
        s=pr["series"]; n=len(s); L=[x["l"] for x in s]; H=[x["h"] for x in s]
        nas_ts=sorted([e["t"] for e in pr["nas_events"] if e["t"]])
        nas_events=sorted([e for e in pr["nas_events"] if e.get("t") and e.get("dir")],key=lambda e:e["t"])
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
                if not v_sweep: continue                                    # PREMISSA ÚNICA (universo não-condicionado p/ as lentes)
                key="L" if long else "S"
                if i-last[key]<8: continue
                ei=i+1
                if ei+2>=n: continue
                entry=s[ei]["c"]; sl0=(L[i]-0.1*atr) if long else (H[i]+0.1*atr)
                oc=outcome(s,ei,entry,sl0,long,atr)
                if oc is None: continue
                R,held=oc; g=graded(s,i,long,atr,L,H,nas_events,liq,lp)
                score=sum(g[k] for k in LENS)/len(LENS)
                tr={"block":b,"t":t,"yr":yr,"dir":key,"R":R,"w":R>0,"held":held,"score":score}; tr.update(g)
                U.append(tr); last[key]=i
    return U
def stat(v):
    n=len(v);
    return (n, 100*sum(1 for x in v if x["w"])/n if n else 0, 100*sum(1 for x in v if x["held"])/n if n else 0, sum(x["R"] for x in v)/n if n else 0, sum(x["R"] for x in v))
def deciles(U,key,nb=5):
    vs=sorted(U,key=lambda x:x[key]); m=len(vs)//nb
    print(f"  {key:>10} por quintil (baixo→alto):  n | WR% held% avgR")
    for q in range(nb):
        seg=vs[q*m:(q+1)*m] if q<nb-1 else vs[q*m:]
        n,wr,hd,ar,sm=stat(seg)
        print(f"     Q{q+1}: n={n:>3}  WR={wr:>3.0f}  held={hd:>3.0f}  avgR={ar:+.2f}")
U=build_universe()
half=sum(1 for x in U if abs(x["R"]+0.5)<1e-9)
n,wr,hd,ar,sm=stat(U)
print(f"[AUDIT] universo sweep-gated não-condicionado: n={n} | suspeitos −0.5R={half} | BASE WR={wr:.0f}% held={hd:.0f}% avgR={ar:+.2f} sumR={sm:+.1f}")
print("\n=== separação por LENTE GRADUADA (universo único, sem range-restriction) ===")
for k in LENS+["score"]:
    deciles(U,k,5)
print("\n=== reading score: topo vs base + validação ===")
vs=sorted(U,key=lambda x:x["score"],reverse=True)
for frac in (0.2,0.33,0.5):
    top=vs[:int(len(vs)*frac)]; bot=vs[int(len(vs)*frac):]
    nt,wrt,hdt,art,smt=stat(top); nb_,wrb,hdb,arb,smb=stat(bot)
    byb={};
    for x in top: byb.setdefault(x["block"][:16],[]).append(x)
    drop=set(sorted(byb,key=lambda bb:sum(x["R"] for x in byb[bb]),reverse=True)[:2]); rem=[x for x in top if x["block"][:16] not in drop]
    yrs=" ".join(f"{y}:{100*sum(1 for x in top if x['yr']==y and x['w'])/max(1,sum(1 for x in top if x['yr']==y)):.0f}%/{sum(x['R'] for x in top if x['yr']==y):+.0f}R" for y in (2024,2025,2026) if any(x['yr']==y for x in top))
    print(f"  top{int(frac*100)}%: n={nt} WR={wrt:.0f} held={hdt:.0f} avgR={art:+.2f} sumR={smt:+.1f} | bottom: WR={wrb:.0f} held={hdb:.0f} avgR={arb:+.2f} | leave-top2bloc→{sum(x['R'] for x in rem):+.0f}(n{len(rem)}) | {yrs}")
