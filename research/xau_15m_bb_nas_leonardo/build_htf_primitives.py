#!/usr/bin/env python3
"""ENGINE 3 — Fase 0: extrator causal de primitivas NATIVAS 4H + 1D (Cris 2026-06-28). RAW gz EXCLUSIVO.
Cópia fiel do extrator 15M (build_causal_primitives) — TF-agnóstico — saída ISOLADA em htf_primitives/ (não contamina
o glob *.primitives.json do 15M). Extrai série OHLC+RSI+ATR14+EMA21, NAS LONG/SHORT (first-appearance), SMC BOS/CHoCH,
zonas Custom OB (born/text/high/low/ciclo-de-vida) + SVP (POC/VAH/VAL as-of, session_vp.last3). Causal as-of close."""
import gzip, json, sys
from pathlib import Path
from collections import Counter
OUT = Path(__file__).parent / "htf_primitives"; OUT.mkdir(exist_ok=True)
FILES = {
 "4H": Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"),
 "1D": Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/1D/XAUUSD_1D_replay_2012-06-19_to_2026-05-25.jsonl.gz"),
}
def grp(rec, key, sub): return next((x for x in (rec.get(key) or []) if sub.lower() in str(x.get("name","")).lower()), None)
def fnum(x):
    try: return float(str(x).replace("−","-"))
    except Exception: return None
def process(tf, path):
    snaps=[]
    with gzip.open(path,"rt") as fh:
        for line in fh:
            line=line.strip()
            if not line: continue
            try: r=json.loads(line)
            except Exception: continue
            if isinstance(r,dict) and r.get("ohlcv"): snaps.append(r)
    snaps.sort(key=lambda r: r.get("replay_current_date") or 0)
    bars={}; rsi_by_t={}; nas_dist_by_t={}; svp_by_t={}; nas_events=[]; smc_events=[]; zones={}
    max_nas=max_smc=-1; nas_init=smc_init=False; first_snap=True
    for r in snaps:
        oh=r.get("ohlcv") or []; cur_t=oh[-1]["time"] if oh and isinstance(oh[-1],dict) else None
        for b in oh:
            if isinstance(b,dict) and b.get("time") is not None:
                bars[b["time"]]={"o":b["open"],"h":b["high"],"l":b["low"],"c":b["close"],"v":b.get("volume")}
        rv=grp(r,"study_values","Relative Strength")
        if rv and cur_t is not None: rsi_by_t[cur_t]=fnum((rv.get("values") or {}).get("RSI"))
        nv=grp(r,"study_values","NAS")
        if nv and cur_t is not None: nas_dist_by_t[cur_t]=fnum((nv.get("values") or {}).get("NAS_DISTANCE_FROM_EMA_ATR"))
        # SVP POC/VAH/VAL (session_vp.last3 -> última sessão [t,POC,VAH,VAL])
        sv=r.get("session_vp")
        if isinstance(sv,dict) and cur_t is not None:
            l3=sv.get("last3")
            row=None
            if isinstance(l3,dict): row=(l3.get("v") or [None])[-1] if isinstance(l3.get("v"),list) else l3.get("v")
            elif isinstance(l3,list) and l3: row=l3[-1]
            if isinstance(row,list) and len(row)>=4: svp_by_t[cur_t]={"poc":fnum(row[1]),"vah":fnum(row[2]),"val":fnum(row[3])}
        ng=grp(r,"pine_labels","NAS"); ng_ids=[l.get("id") for l in (ng.get("labels") or []) if l.get("id") is not None] if ng else []
        if not nas_init:
            if ng_ids: max_nas=max(ng_ids); nas_init=True
        else:
            for l in (ng.get("labels") or []) if ng else []:
                lid=l.get("id")
                if lid is None or lid<=max_nas: continue
                txt=str(l.get("text","")).upper()
                if "LONG" in txt or "SHORT" in txt: nas_events.append({"t":cur_t,"id":lid,"dir":"LONG" if "LONG" in txt else "SHORT","price":l.get("price")})
            if ng_ids: max_nas=max(max_nas,max(ng_ids))
        sg=grp(r,"pine_labels","Smart Money"); sg_ids=[l.get("id") for l in (sg.get("labels") or []) if l.get("id") is not None] if sg else []
        if not smc_init:
            if sg_ids: max_smc=max(sg_ids); smc_init=True
        else:
            for l in (sg.get("labels") or []) if sg else []:
                lid=l.get("id")
                if lid is None or lid<=max_smc: continue
                smc_events.append({"t":cur_t,"id":lid,"text":l.get("text"),"price":l.get("price")})
            if sg_ids: max_smc=max(max_smc,max(sg_ids))
        ob=grp(r,"pine_boxes","Custom OB")
        for bx in (ob.get("all_boxes") if ob else []) or []:
            zid=bx.get("id")
            if zid is None: continue
            if zid not in zones: zones[zid]={"text":str(bx.get("text","")).upper(),"high":bx.get("high"),"low":bx.get("low"),"born_t":cur_t,"last_t":cur_t,"pre_existing":first_snap}
            else: zones[zid]["last_t"]=cur_t; zones[zid]["high"]=bx.get("high"); zones[zid]["low"]=bx.get("low")
        first_snap=False
    ts=sorted(bars); series=[]; ema=None; kE=2/22; trs=[]
    for i,t in enumerate(ts):
        b=bars[t]; o,h,l,c=b["o"],b["h"],b["l"],b["c"]
        ema=c if ema is None else c*kE+ema*(1-kE)
        if i>0: pc=bars[ts[i-1]]["c"]; trs.append(max(h-l,abs(h-pc),abs(l-pc)))
        atr=sum(trs[-14:])/14 if len(trs)>=14 else None
        sp=svp_by_t.get(t) or {}
        series.append({"t":t,"o":o,"h":h,"l":l,"c":c,"v":b["v"],"rsi":rsi_by_t.get(t),"atr":atr,"ema21":ema,
                       "poc":sp.get("poc"),"vah":sp.get("vah"),"val":sp.get("val")})
    out={"tf":tf,"n_bars":len(series),"t_start":ts[0] if ts else None,"t_end":ts[-1] if ts else None,
         "series":series,"nas_events":nas_events,"smc_events":smc_events,"zones":[{"id":k,**v} for k,v in zones.items()]}
    (OUT/f"htf_{tf}.primitives.json").write_text(json.dumps(out,default=str))
    nl=sum(1 for e in nas_events if e["dir"]=="LONG"); sup=sum(1 for z in zones.values() if "SUPPLY" in z["text"]); dem=sum(1 for z in zones.values() if "DEMAND" in z["text"])
    svpok=sum(1 for s in series if s["poc"] is not None)
    print(f"{tf}: bars={len(series)} {out['t_start']}→{out['t_end']} | NAS L{nl}/S{len(nas_events)-nl} | SMC {len(smc_events)} | OB sup{sup}/dem{dem} | RSI {sum(1 for s in series if s['rsi'] is not None)}/{len(series)} | SVP {svpok}/{len(series)}")
    return out
for tf,p in FILES.items():
    if p.exists(): process(tf,p)
    else: print(f"{tf}: FALTA {p}")
