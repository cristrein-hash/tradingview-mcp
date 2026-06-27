#!/usr/bin/env python3
"""ENGINE 2 — Phase A/C (Cris 2026-06-27). LÓGICA DISTINTA do Eng1: aqui é ENTRADA CAUSAL em tempo real.
Fluxo de candidatos = TODA mínima fractal (k=3) CONFIRMADA; entry = close do bar de confirmação cj=p+3 (causal:
decisão usa só barras<=cj). Cada candidato recebe FEATURES NOVAS focadas na REAÇÃO pós-mínima (reclaim/rejeição/
micro-HL/decel/demand-reclaim/coiled) + fingerprint Eng1 causal + multi-TF. LABEL = tier do M8 BOT casado (|Δ|<=2 bars):
MONFORTE / MEDIO / FRACO / NONE (mínima que não é fundo M8 = ruído). tier = só p/ avaliar, nunca feature.
RAW-causal. -> entry_candidates.jsonl"""
import json,bisect,datetime as dt,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
MR=json.loads((HERE/"macro_regime_4h.json").read_text())["bars_4h"]; MEND=[b["t_end"] for b in MR]
def macro_at(t): k=bisect.bisect_right(MEND,t)-1; return MR[k]["macro"] if k>=0 else "WARMUP"
BUB={}
for bf in sorted((HERE/"bubbles").glob("*.bubbles.jsonl")): BUB[bf.name[:10]]=sorted([json.loads(l) for l in bf.read_text().splitlines() if l],key=lambda x:x["t"])
SZ={"S":1,"M":2,"L":3}
# tier por (block, t) do Eng1
TIER={}
for l in (HERE/"bottom_features.jsonl").read_text().splitlines():
    r=json.loads(l); TIER[(r["block"],r["t"])]=r["tier"]
def ema(vals,n):
    if not vals: return None
    k=2/(n+1); e=vals[0]
    for v in vals[1:]: e=v*k+e*(1-k)
    return e
def htf_bars(s,period):
    g={}
    for b in s:
        kk=b["t"]//period; gg=g.setdefault(kk,{"o":b["o"],"h":b["h"],"l":b["l"],"c":b["c"],"t_end":b["t"]+900})
        gg["h"]=max(gg["h"],b["h"]); gg["l"]=min(gg["l"],b["l"]); gg["c"]=b["c"]; gg["t_end"]=b["t"]+900
    return [g[k] for k in sorted(g)]
def rsi_w(cl,n=14):
    if len(cl)<n+1: return None
    g=l=0.0
    for x in range(1,n+1): d=cl[x]-cl[x-1]; g+=max(d,0); l+=max(-d,0)
    ag=g/n; al=l/n
    for x in range(n+1,len(cl)): d=cl[x]-cl[x-1]; ag=(ag*(n-1)+max(d,0))/n; al=(al*(n-1)+max(-d,0))/n
    return 100.0 if al==0 else 100-100/(1+ag/al)
def htf_ctx(hb,tc,c,atr):
    done=[b for b in hb if b["t_end"]<=tc]
    if len(done)<25: return {}
    cl=[b["c"] for b in done]; hi=[b["h"] for b in done]; lo=[b["l"] for b in done]
    e20=ema(cl[-60:],20); e50=ema(cl[-120:],50) if len(cl)>=50 else ema(cl,min(50,len(cl)))
    e20p=ema(cl[-65:-5],20) if len(cl)>=25 else e20
    trend=1 if(e20>e50 and e20>e20p)else(-1 if(e20<e50 and e20<e20p)else 0)
    rl=min(lo[-20:]); rh=max(hi[-20:]); pos=(c-rl)/(rh-rl) if rh>rl else .5
    rsi=rsi_w(cl[-60:])
    return {"trend":trend,"pos":round(pos,2),"rsi":round(rsi,1) if rsi else None,"dist":round((c-e20)/atr,2)}

rows=[]
for bkey,pr in PRIMK.items():
    s=pr["series"]; nn=len(s); L=[x["l"] for x in s]
    h1=htf_bars(s,3600); h4=htf_bars(s,14400)
    zones=pr.get("zones",[]); zd=[z for z in zones if "DEMAND" in str(z.get("text","")).upper()]; zs=[z for z in zones if "SUPPLY" in str(z.get("text","")).upper()]
    nas=sorted([e for e in pr["nas_events"] if e.get("t") and e.get("dir")],key=lambda e:e["t"]); nas_t=[e["t"] for e in nas]
    bub=BUB.get(bkey,[]); bub_t=[x["t"] for x in bub]
    # tier por idx (M8 bottoms deste bloco)
    tmap={b["t"]:idx for idx,b in enumerate(s)}
    bot_idx={}
    for (bk,bt),tr in TIER.items():
        if bk==bkey and bt in tmap: bot_idx[tmap[bt]]=tr
    botkeys=sorted(bot_idx)
    last_cj=-99
    for p in range(96,nn-4):
        if L[p]!=min(L[p-3:p+4]): continue   # mínima fractal k=3 (confirma em p+3)
        cj=p+3
        if cj>=nn-1 or cj-last_cj<3: continue
        atr=s[p]["atr"]
        if not atr: continue
        last_cj=cj; tc=s[cj]["t"]; lo=s[p]["l"]; c=s[cj]["c"]; catr=s[cj]["atr"] or atr
        # LABEL: M8 BOT casado |Δ|<=2
        lab="NONE"
        for b in botkeys:
            if abs(b-p)<=2: lab=bot_idx[b]; break
        f={}
        # === FEATURES NOVAS DE REAÇÃO (entry-time, causal: barras p..cj) ===
        f["reclaim_atr"]=round((c-lo)/atr,2)                       # quanto reclamou até a entrada
        e21=ema([b["c"] for b in s[max(0,cj-60):cj+1]],21)
        f["above_ema21"]=1 if (e21 and c>e21) else 0
        f["reclaim_ema_bars"]=99
        for x in range(p,cj+1):
            ee=ema([b["c"] for b in s[max(0,x-60):x+1]],21)
            if ee and s[x]["c"]>ee: f["reclaim_ema_bars"]=x-p; break
        rng=s[p]["h"]-s[p]["l"]; f["low_wick"]=round((min(s[p]["o"],s[p]["c"])-lo)/rng,2) if rng>0 else 0   # rejeição na mínima
        f["confirm_body_atr"]=round((c-s[cj]["o"])/catr,2)         # corpo do bar de entrada
        f["up_closes_pc"]=sum(1 for x in range(p+1,cj+1) if s[x]["c"]>s[x]["o"])  # quantas velas verdes na reação
        # micro higher-low entre p e cj
        f["micro_hl"]=1 if any(s[x]["l"]>lo and x>p for x in range(p+1,cj+1)) and s[cj]["l"]>lo else 0
        # decel da perna de baixa (últimas 6 barras antes de p)
        rngs=[s[x]["h"]-s[x]["l"] for x in range(max(0,p-6),p+1)]
        f["downleg_decel"]=1 if len(rngs)>=4 and st.mean(rngs[-3:])<st.mean(rngs[:3]) else 0
        # pullback raso: profundidade do pullback vs perna de alta anterior
        up0=max(0,p-60); hi_prev=max(s[x]["h"] for x in range(up0,p+1)); lo_prev=min(s[x]["l"] for x in range(up0,p+1))
        f["pullback_depth"]=round((hi_prev-lo)/((hi_prev-lo_prev) or 1),2)   # baixo=pullback raso (forte)
        # demand reclaim (causal born<=tc): mínima tocou demanda e fechou acima do topo
        dem=[z for z in zd if z["born_t"]<=tc and z["low"]-0.3*atr<=lo<=z["high"]+0.5*atr]
        f["demand_reclaim"]=1 if (dem and c>min(z["high"] for z in dem)) else 0
        f["in_demand"]=1 if dem else 0
        dem_below=[z for z in zd if z["born_t"]<=tc and z["high"]<=c+0.3*atr]
        f["dist_demand_atr"]=round(min((c-z["high"])/atr for z in dem_below),2) if dem_below else 99
        sup_above=[z for z in zs if z["born_t"]<=tc and z["low"]>c]
        f["clean_sky_atr"]=round(min((z["low"]-c)/atr for z in sup_above),2) if sup_above else 99
        f["n_supply_overhead"]=len(sup_above)
        # sweep de swing-low anterior (causal, só barra p)
        sl=None
        for q in range(p-1,3,-1):
            if q+2<p and s[q]["l"]==min(x["l"] for x in s[q-2:q+3]): sl=q; break
        f["swept_prior_low"]=1 if (sl is not None and lo<s[sl]["l"]) else 0
        # === fingerprint Eng1 (causal as-of p) ===
        for N in (60,90):
            a=max(0,p-N); lw=min(x["l"] for x in s[a:p+1]); hw=max(x["h"] for x in s[a:p+1])
            f[f"legpos{N}"]=round((lo-lw)/(hw-lw),3) if hw>lw else .5
        f["rsi_low"]=round(s[p].get("rsi") or 50,1)
        r8=[s[x].get("rsi") for x in range(max(0,p-8),p+1) if s[x].get("rsi") is not None]; f["rsi_min8"]=round(min(r8),1) if r8 else 50
        a50=[s[b]["atr"] for b in range(max(0,p-50),p+1) if s[b]["atr"]]; f["atr_regime"]=round(atr/st.median(a50),2) if a50 else 1
        a_pre=[s[b]["atr"] for b in range(max(0,p-15),max(1,p-5)) if s[b]["atr"]]; f["atr_compression_pre"]=round(st.median(a_pre)/atr,2) if a_pre else 1
        seg=[x["c"] for x in s[max(0,p-20):p+1]]; net=abs(seg[-1]-seg[0]); pth=sum(abs(seg[x]-seg[x-1]) for x in range(1,len(seg))); f["downleg_eff"]=round(net/pth,2) if pth>0 else .5
        f["n_demand_near"]=sum(1 for z in zd if z["born_t"]<=tc and abs((z["high"]+z["low"])/2-c)<=3*atr)
        # multi-TF
        for tag,hb in (("h1",h1),("h4",h4)):
            ct=htf_ctx(hb,tc,c,catr)
            for kk in ("trend","pos","rsi","dist"): f[f"{tag}_{kk}"]=ct.get(kk)
        f["macro_bull"]=1 if macro_at(tc)=="BULL" else 0; f["macro_bear"]=1 if macro_at(tc)=="BEAR" else 0
        # flow: buyer step-in (BUY bubble por cj) + sell climax
        a=bisect.bisect_left(bub_t,s[max(0,p-12)]["t"]); bw=sw=0
        for x in bub[a:]:
            if x["t"]>tc: break
            if (x.get("known_at") or x["t"])>tc: continue
            if x["side"]=="BUY": bw+=SZ[x["size"]]
            else: sw+=SZ[x["size"]]
        f["buy_bub_w"]=bw; f["sell_bub_w"]=sw
        na=bisect.bisect_left(nas_t,s[max(0,p-16)]["t"]); nb=bisect.bisect_right(nas_t,tc)
        f["nas_long_16"]=sum(1 for e in nas[na:nb] if e["dir"]=="LONG")
        hh=dt.datetime.utcfromtimestamp(tc).hour; f["killzone"]=1 if (7<=hh<12 or 13<=hh<18) else 0
        rec={"block":bkey,"t":int(s[p]["t"]),"cj_t":int(tc),"yr":dt.datetime.utcfromtimestamp(s[p]["t"]).year,
             "label":lab,"is_monforte":int(lab in("MONSTRO","FORTE")),"is_medfraco":int(lab in("MEDIO","FRACO")),"is_bottom":int(lab!="NONE")}
        rec.update(f); rows.append(rec)
with open(HERE/"entry_candidates.jsonl","w") as fo:
    for r in rows: fo.write(json.dumps(r)+"\n")
from collections import Counter
lc=Counter(r["label"] for r in rows)
nmf=sum(r["is_monforte"] for r in rows)
print(f"entry_candidates.jsonl: {len(rows)} candidatos (mínimas fractais confirmadas) | labels {dict(lc)}")
print(f"  MON+FORTE casados: {nmf} | base precisão se pegar tudo = {100*nmf/len(rows):.1f}%")
# recall ceiling: quantos dos MON+FORTE conhecidos estão no universo
known_mf=sum(1 for v in TIER.values() if v in("MONSTRO","FORTE"))
print(f"  recall-ceiling: {nmf}/{known_mf} MON+FORTE conhecidos capturados no universo de candidatos")
print(f"  features ({len([k for k in rows[0] if k not in ('block','t','cj_t','yr','label','is_monforte','is_medfraco','is_bottom')])})")
