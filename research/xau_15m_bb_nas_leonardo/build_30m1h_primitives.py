#!/usr/bin/env python3
"""EXTRATOR 30M + 1H — cópia FIEL da lógica validada de build_htf_primitives.py (Cris autorizou 2026-07-07).
RAW gz EXCLUSIVO (raw_replay/XAUUSD/{30M,1H}). Mesma extração causal as-of-close: série OHLC+RSI+ATR14+
EMA21+SVP(POC/VAH/VAL), NAS LONG/SHORT (first-appearance by id), SMC BOS/CHoCH/EQH/EQL (first-appearance),
zonas Custom OB DEMAND/SUPPLY (born/last/high/low lifecycle). Cada bloco RAW = um replay contínuo → um
ficheiro primitives próprio (ids monotónicos DENTRO do bloco; convenção igual à do 15M multi-bloco).
Saída: htf_primitives/XAUUSD_{30m,60m}_<bloco>.primitives.json. NÃO toca RAW. NÃO resample."""
import gzip, json, glob
from pathlib import Path
OUT = Path(__file__).parent / "htf_primitives"; OUT.mkdir(exist_ok=True)
HD = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD"
def grp(rec, key, sub): return next((x for x in (rec.get(key) or []) if sub.lower() in str(x.get("name","")).lower()), None)
def fnum(x):
    try: return float(str(x).replace("−","-"))
    except Exception: return None
def process(path):
    snaps=[]
    with gzip.open(path,"rt") as fh:
        for line in fh:
            line=line.strip()
            if not line: continue
            try: r=json.loads(line)
            except Exception: continue
            if isinstance(r,dict) and r.get("ohlcv"): snaps.append(r)
    snaps.sort(key=lambda r: r.get("replay_current_date") or 0)
    bars={}; rsi_by_t={}; svp_by_t={}; nas_events=[]; smc_events=[]; zones={}
    max_nas=max_smc=-1; nas_init=smc_init=False; first_snap=True
    for r in snaps:
        oh=r.get("ohlcv") or []; cur_t=oh[-1]["time"] if oh and isinstance(oh[-1],dict) else None
        for b in oh:
            if isinstance(b,dict) and b.get("time") is not None:
                bars[b["time"]]={"o":b["open"],"h":b["high"],"l":b["low"],"c":b["close"],"v":b.get("volume")}
        rv=grp(r,"study_values","Relative Strength")
        if rv and cur_t is not None: rsi_by_t[cur_t]=fnum((rv.get("values") or {}).get("RSI"))
        sv=r.get("session_vp")
        if isinstance(sv,dict) and cur_t is not None:
            l3=sv.get("last3"); row=None
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
        series.append({"t":t,"o":o,"h":h,"l":l,"c":c,"v":b["v"],"rsi":rsi_by_t.get(t),"atr":atr,"ema21":ema,"poc":sp.get("poc"),"vah":sp.get("vah"),"val":sp.get("val")})
    return {"n_bars":len(series),"t_start":ts[0] if ts else None,"t_end":ts[-1] if ts else None,
            "series":series,"nas_events":nas_events,"smc_events":smc_events,"zones":[{"id":k,**v} for k,v in zones.items()]}
for tf,pat in [("30M",f"{HD}/30M/*.jsonl.gz"),("1H",f"{HD}/1H/*.jsonl.gz")]:
    for path in sorted(glob.glob(pat)):
        stem=Path(path).name.replace(".jsonl.gz","")
        out=process(path); out["tf"]=tf; out["source_raw"]=path
        (OUT/f"{stem}.primitives.json").write_text(json.dumps(out,default=str))
        nl=sum(1 for e in out["nas_events"] if e["dir"]=="LONG"); zt={}
        for z in out["zones"]: zt[z["text"]]=zt.get(z["text"],0)+1
        print(f"{tf} {stem}: bars={out['n_bars']} {out['t_start']}→{out['t_end']} NAS L{nl}/S{len(out['nas_events'])-nl} SMC {len(out['smc_events'])} zones {dict(zt)} SVP {sum(1 for s in out['series'] if s['poc'] is not None)}/{out['n_bars']}")
print("OK — 30M/1H primitives extraídos para htf_primitives/ (RAW nativo, extractor validado)")
