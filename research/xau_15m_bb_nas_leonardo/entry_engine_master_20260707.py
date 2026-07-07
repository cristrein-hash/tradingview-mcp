#!/usr/bin/env python3
"""ENGINE DE ENTRY 3R — MASTER = leitura contextual de perna (markup/correção) (2026-07-07, diretriz Cris).
Recontextualização: a CAMINHADA de pernas (markup/correção) é MASTER e permanece sempre por cima.
Sobre cada evento de demanda-de-perna procuro o selecionador de entry entre as FEATURES JÁ TESTADAS
para trazer 3R reais SEM lookahead. NÃO criar micro-features novas; NÃO snapshot isolado.
FUNDAÇÃO (este script): universo de eventos na janela ago/2025→2026-07-03; entry causal (reclaim EMA21
após a demanda); SL estrutural (demanda −0,1ATR, regra V1 oficial); target 3R; outcome sem lookahead;
features testadas no entry (SEQ bubbles / RSI / NAS / estrutura / zonas); baseline hit-3R por kind/ano.
SANITY_PROBE: MASTER=caminhada de perna (processo, markup/correção); multi-fatorial; trajetória (SEQ
multi-barra, drop/reclaim lookback); outcome 3R forward-only known_at; features JÁ testadas; não snapshot."""
import json, glob, bisect
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
# ---- séries + estrutura + bubbles + nas + zonas (fontes já testadas) ----
series={}; nas=[]; smc=[]; zones=[]
for p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    d=json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"],b)
    nas+=[e for e in d.get("nas_events",[]) if e.get("t")]
    smc+=[e for e in d.get("smc_events",[]) if e.get("t")]
    zones+=[z for z in d.get("zones",[]) if z.get("born_t")]
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]
ATR=[b.get("atr") or 5.0 for b in S]; EMA=[b.get("ema21") for b in S]; RSI=[b.get("rsi") for b in S]
RSIMA=[None]*N
for i in range(N):
    w=[RSI[j] for j in range(max(0,i-13),i+1) if RSI[j] is not None]; RSIMA[i]=sum(w)/len(w) if w else None
BUB=sorted([json.loads(l) for p in glob.glob(str(HERE/"bubbles"/"*.bubbles.jsonl")) for l in open(p)],
           key=lambda x:(x.get("known_at") or x["t"]))
BUBK=[(x.get("known_at") or x["t"]) for x in BUB]
nas.sort(key=lambda e:e["t"]); NAST=[e["t"] for e in nas]
def bub_upto(t0,wlo,whi):
    hi=bisect.bisect_right(BUBK,t0); return [BUB[i] for i in range(hi) if t0-whi*900<=BUB[i]["t"]<=t0-wlo*900]
W={"S":1,"M":2,"L":3}
def seq_feats(t0):
    recent=bub_upto(t0,0,4); older=bub_upto(t0,5,10); win8=bub_upto(t0,0,8)
    br=sum(W[x["size"]] for x in recent if x["side"]=="BUY"); bo=sum(W[x["size"]] for x in older if x["side"]=="BUY")
    i=bisect.bisect_right(TS,t0)-1
    return {"buy_recent":br,"burst":br-bo,
            "large_buy8":int(any(x["side"]=="BUY" and x["size"]=="L" for x in win8)),
            "sell_ml8":sum(1 for x in win8 if x["side"]=="SELL" and x["size"] in ("M","L")),
            "rsi_above_ma":int(RSI[i] is not None and RSIMA[i] is not None and RSI[i]>RSIMA[i]),
            "nas_long_rec":int(any(e["dir"]=="LONG" and t0-e["t"]<=8*900 for e in nas[max(0,bisect.bisect_right(NAST,t0)-12):bisect.bisect_right(NAST,t0)]))}
# ---- caminhada de pernas (MASTER) r=6 ----
def zz(r):
    piv=[]; d=0; ehi=elo=0
    for i in range(1,N):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d<=0 and HI[i]-LO[elo]>=r*a and elo<i: piv.append(("L",elo,LO[elo],i)); d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
        elif d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i: piv.append(("H",ehi,HI[ehi],i)); d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
    return piv
def legwalk(r=6):
    piv=zz(r); ev=[]; prevH=prevL=None; lastH=None
    for tp,i,pr,ci in piv:
        if tp=="H": prevH=pr; lastH=pr
        else:
            if prevH is not None and lastH is not None:
                kind="MARKUP" if (prevL is None or pr>prevL) else "CORRECAO"
                ev.append({"i":i,"lo":pr,"conf_i":ci,"kind":kind,"leg_top":lastH,"prevL":prevL})
            prevL=pr
    return ev
EV=legwalk(6)
# ---- entry causal: reclaim EMA21 após a demanda (dentro de janela), SL estrutural, 3R ----
def build_entry(e, win=24, horizon=1440):
    i=e["i"]; lo=e["lo"]; a=ATR[i] or 5
    # reclaim: 1º bar j>i com close>ema21 (markup context da perna anterior já confirmado em conf_i-1)
    j=None
    for k in range(i+1, min(N,i+win+1)):
        if EMA[k] is not None and CL[k]>EMA[k] and CL[k]>CL[k-1]: j=k; break
    if j is None: return None
    ent=CL[j]; sl=lo-0.1*a; risk=ent-sl
    if risk<=0.05*a: return None
    tgt=ent+3*risk
    out=0; end=None
    for m in range(j+1, min(N,j+horizon+1)):
        if LO[m]<=sl: out=0; end=m; break
        if HI[m]>=tgt: out=1; end=m; break
    return {"j":j,"t":TS[j],"ent":ent,"sl":sl,"tgt":tgt,"risk":risk,"reclaim_lag":j-i,"out":out}
def zone_dist(t0, kind_):
    # distância à zona SUPPLY/DEMAND ativa mais próxima (nascida antes)
    i=bisect.bisect_right(TS,t0)-1; px=CL[i]; a=ATR[i] or 5; best=None
    for z in zones:
        if z["born_t"]>t0: continue
        if z["text"]!=kind_: continue
        mid=(z["high"]+z["low"])/2; d=abs(px-mid)/a
        if best is None or d<best: best=d
    return round(best,2) if best is not None else 99
def struct_feats(e):
    i=e["i"]; a=ATR[i] or 5; lo=e["lo"]
    drop=(e["leg_top"]-lo)/a
    lb=LO[max(0,i-96):i]; sweep=(min(lb)-lo)/a if lb else 0    # >0 = varreu mínimo prévio
    win=LO[max(0,i-96):i+1]; hiw=HI[max(0,i-96):i+1]
    box96=(lo-min(win))/((max(hiw)-min(win)) or 1)
    ema_dist=(lo-(EMA[i] or lo))/a
    return {"drop":round(drop,2),"sweep":round(sweep,2),"box96":round(box96,2),"ema_dist":round(ema_dist,2),
            "rsi_lo":RSI[i],"supply_d":zone_dist(TS[i],"SUPPLY"),"demand_d":zone_dist(TS[i],"DEMAND")}
smc.sort(key=lambda e:e["t"]); SMCT=[e["t"] for e in smc]
def casc_feats(e, ent_t):
    """features CASCEX testadas: cascade (nº eventos SMC entre demanda e entry) + CHoCH desde a low."""
    i=e["i"]; lo_t=TS[i]
    seg=[smc[k] for k in range(bisect.bisect_left(SMCT,lo_t-96*900), bisect.bisect_right(SMCT,ent_t))]
    casc=len(seg)
    choch=sum(1 for x in seg if x["text"]=="CHoCH" and x["t"]>=lo_t)
    bos=sum(1 for x in seg if x["text"]=="BOS" and x["t"]>=lo_t)
    j=bisect.bisect_right(TS,ent_t)-1; a=ATR[j] or 5
    recl_str=(CL[j]-(EMA[j] or CL[j]))/a
    return {"cascade":casc,"choch_since_lo":choch,"bos_since_lo":bos,"recl_str":round(recl_str,2)}
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
W0=dt.datetime(2025,8,1).timestamp(); W1=dt.datetime(2026,7,4).timestamp()  # ago/2025 → sex 2026-07-03
rows=[]
for e in EV:
    if not (W0<=TS[e["i"]]<=W1): continue
    en=build_entry(e)
    if en is None: continue
    f={**seq_feats(en["t"]),**struct_feats(e),**casc_feats(e,en["t"])}
    rows.append({"kind":e["kind"],"t":en["t"],"d":ds(en["t"]),"out":en["out"],"reclaim_lag":en["reclaim_lag"],
                 "risk":round(en["risk"],2),**f})
def year(d): return d[:4]
def panel(sel,tag):
    if not sel: print(f"  {tag:<28} N0"); return
    n=len(sel); hit=sum(r["out"] for r in sel)
    yrs=sorted(set(year(r["d"]) for r in sel))
    ybk=" ".join(f"{y}:{sum(r['out'] for r in sel if year(r['d'])==y)}/{sum(1 for r in sel if year(r['d'])==y)}" for y in yrs)
    print(f"  {tag:<28} N{n:<4} hit-3R {hit/n:.1%} ({hit}/{n}) · {ybk}")
print(f"eventos MASTER na janela ago25→2026-07-03: {len(rows)} (markup {sum(1 for r in rows if r['kind']=='MARKUP')} / correção {sum(1 for r in rows if r['kind']=='CORRECAO')})")
print("\n=== BASELINE hit-3R (MASTER, sem seletor) ===")
panel(rows,"todos")
panel([r for r in rows if r["kind"]=="MARKUP"],"MARKUP")
panel([r for r in rows if r["kind"]=="CORRECAO"],"CORRECAO")
# feature medians hit vs miss (que features testadas discriminam 3R?)
import statistics as st
print("\n=== features testadas: mediana HIT vs MISS (dentro do MASTER) ===")
for k in ("cascade","choch_since_lo","bos_since_lo","recl_str","drop","sweep","box96","ema_dist","rsi_lo","supply_d","demand_d","reclaim_lag"):
    h=[r[k] for r in rows if r["out"]==1 and r.get(k) is not None]; m=[r[k] for r in rows if r["out"]==0 and r.get(k) is not None]
    if h and m: print(f"  {k:<14} HIT {st.median(h):.2f}  MISS {st.median(m):.2f}")
json.dump(rows,open(HERE/"results"/"entry_engine_master_20260707.json","w"),indent=1)
# ---- BUSCA DE SELETOR dentro do MASTER (markup preservado), exigindo todos-anos-positivo ----
def allyears_ok(sel, floor=0.45):
    if len(sel)<25: return False
    for y in ("2025","2026"):
        sy=[r for r in sel if year(r["d"])==y]
        if len(sy)<8 or sum(r["out"] for r in sy)/len(sy)<floor: return False
    return True
MK=[r for r in rows if r["kind"]=="MARKUP"]
print(f"\n=== SELETOR dentro do MARKUP (N{len(MK)}, base {sum(r['out'] for r in MK)/len(MK):.1%}) — configs c/ todos-anos>=45% e N>=25 ===")
import itertools
gates={
 "recl_str>=0.3":lambda r:r["recl_str"]>=0.3, "recl_str>=0.6":lambda r:r["recl_str"]>=0.6,
 "reclaim_lag<=4":lambda r:r["reclaim_lag"]<=4, "reclaim_lag<=6":lambda r:r["reclaim_lag"]<=6,
 "choch>=1":lambda r:r["choch_since_lo"]>=1, "cascade>=3":lambda r:r["cascade"]>=3, "cascade>=5":lambda r:r["cascade"]>=5,
 "sweep<=0.1":lambda r:r["sweep"]<=0.1, "drop>=6":lambda r:r["drop"]>=6, "drop<=9":lambda r:r["drop"]<=9,
 "box96<=0.3":lambda r:r["box96"]<=0.3, "rsi_lo<=40":lambda r:(r["rsi_lo"] or 50)<=40, "rsi_above":lambda r:r["rsi_above_ma"]==1,
 "demand_near":lambda r:r["demand_d"]<=0.5,
}
res=[]
for name,fn in gates.items():
    sel=[r for r in MK if fn(r)]
    if len(sel)>=25: res.append((sum(r['out'] for r in sel)/len(sel),name,sel,allyears_ok(sel)))
for a,b in itertools.combinations(gates.items(),2):
    fn=lambda r,a=a,b=b:a[1](r) and b[1](r); sel=[r for r in MK if fn(r)]
    if len(sel)>=25: res.append((sum(r['out'] for r in sel)/len(sel),f"{a[0]} & {b[0]}",sel,allyears_ok(sel)))
res.sort(key=lambda x:x[0],reverse=True)
for hit,name,sel,ok in res[:16]:
    ybk=" ".join(f"{y}:{sum(r['out'] for r in sel if year(r['d'])==y)}/{sum(1 for r in sel if year(r['d'])==y)}" for y in ("2025","2026"))
    print(f"  {'✅' if ok else '  '} {name:<34} N{len(sel):<4} hit-3R {hit:.1%} · {ybk}")
print("\nsaved · OK")
