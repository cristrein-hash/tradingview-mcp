#!/usr/bin/env python3
"""REPLAY FIEL v3 — corrige as 5 discrepâncias da v2 (audit Cris):
 (1) 1D usa bars_1d reais (não 4H)  (2) confluence/bubbles janela populada  (3) tops/bots as-of (monkeypatch
 store_reader.bars por CUR_T)  (4) regime Layer1-1D via regime_l1 as-of  (5) sweep-context as-of monkeypatch.
IRREDUCÍVEL (live/stateful, não guardado por barra) e assinalado no prompt: v5-4H regime, polarity active-
supports, macro externo (yields/DXY/VIX). Inclui VELA EM FOCO. --show imprime prompt+audit e sai. READ_OB_ZONES."""
import sys, json, subprocess, datetime as dt
from pathlib import Path
ROOT = Path("/Users/cristrein/tradingview-mcp"); sys.path.insert(0, str(ROOT/"alert-bridge"))
sys.path.insert(0, str(ROOT/"my-strategy/core/regime_l1"))
import context_structure as CS, context_liquidity as CL, candle_reader as CR, e2_quality as E2
import sweep_reject_guard as SRG, store_reader as SR, regime_l1_v4 as RL1

def load(f): return sorted([(int(x['t']),float(x['o']),float(x['h']),float(x['l']),float(x['c'])) for x in (json.loads(l) for l in open(f) if l.strip())])
B15=load(ROOT/"my-strategy/core/bar_store/store/bars_15m.jsonl"); B1=load(ROOT/"my-strategy/research/revalidation/raw_1h_ohlc.jsonl")
B4=load(ROOT/"my-strategy/research/revalidation/raw_4h_ohlc.jsonl"); B1D=load(ROOT/"my-strategy/core/bar_store/store/bars_1d.jsonl")
CAP=ROOT/"alert-bridge/logs/backtests/XAUUSD_15m_replay_2026-08-10_to_2026-08-14.jsonl"
def utc(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%m-%d %H:%M")
def fnum(x):
    try: return float(str(x).replace("−","-").replace(",",""))
    except: return None
cap={}
for l in open(CAP):
    if not l.strip(): continue
    r=json.loads(l); oh=r.get("ohlcv"); b=oh.get("bars") if isinstance(oh,dict) else oh
    if b: cap[int(b[-1].get("t") or b[-1].get("time"))]=r
def cap_asof(t):
    ks=[x for x in cap if x<=t]; return cap[max(ks)] if ks else None
def ob_zones(r):
    out=[]; pb=(r or {}).get("pine_boxes",{})
    for s in (pb.get("studies") if isinstance(pb,dict) else pb) or []:
        if "OB Detector" in s.get("name",""):
            for b in (s.get("all_boxes") or []):
                if b.get("text"): out.append((b["text"],float(b["low"]),float(b["high"])))
    return out
def sv(r,sub):
    _sv=(r or {}).get("study_values",{}); st=_sv.get("studies",_sv) if isinstance(_sv,dict) else _sv
    for s in st or []:
        if sub in s.get("name",""): return s.get("values",{})
    return {}
def ema(series,n):
    if len(series)<n: return series[-1]
    k=2/(n+1); e=series[-n]
    for x in series[-n+1:]: e=x*k+e*(1-k)
    return round(e,3)

# --- monkeypatch store_reader.bars -> as-of CUR_T (faz tops/bots e liquidez lerem histórico) ---
CUR_T=[0]; _orig=SR.bars
def _bars_asof(tf,count=None):
    r=_orig(tf,None) or []
    r=[b for b in r if int(b.get("t",b.get("time",0)))<=CUR_T[0]]
    return r[-(count or 100000):]
SR.bars=_bars_asof

def sweep_verdict_asof(t):
    ts=None;sh=None
    for (bt,o,h,l,c) in B4:
        if bt+4*3600>t: break
        if (h-max(o,c))>0.5*abs(c-o): ts=bt+4*3600; sh=round(h,2)
    up=None; seg=[b for b in B15 if b[0]<=t]
    if len(seg)>25:
        H=[b[2] for b in seg];L=[b[3] for b in seg];C=[b[4] for b in seg];ph=[];pl=[]
        for k in range(2,len(seg)-2):
            if H[k]>H[k-1] and H[k]>H[k-2] and H[k]>=H[k+1] and H[k]>=H[k+2]: ph.append((k+2,H[k]))
            if L[k]<L[k-1] and L[k]<L[k-2] and L[k]<=L[k+1] and L[k]<=L[k+2]: pl.append((k+2,L[k]))
        hi=lo=0
        for i in range(len(seg)):
            while hi<len(ph) and ph[hi][0]<=i: hi+=1
            while lo<len(pl) and pl[lo][0]<=i: lo+=1
            if hi>=2 and lo>=2 and ph[hi-1][1]<ph[hi-2][1] and pl[lo-1][1]>pl[lo-2][1] and C[i]>ph[hi-1][1]: up=seg[i][0]
    block=ts is not None and (up is None or ts>up)
    return {"block":bool(block),"why":"sweep4H as-of","sweep_t":ts,"sweep_high":sh,"break15_t":up}

def regime_l1_asof(t):
    daily=[{"ts":dt.datetime.utcfromtimestamp(b[0]).strftime("%Y-%m-%dT00:00:00"),"open":b[1],"high":b[2],"low":b[3],"close":b[4],"volume":0} for b in B1D if b[0]<=t]
    if len(daily)<200: return None
    cls=RL1.build_classifications(daily); s,_=RL1.latest_state_before(cls,t); return s

def build_dsr(t):
    r=cap_asof(t); price=[b for b in B15 if b[0]<=t][-1][4]; zs=ob_zones(r)
    mtf={}
    for tf,bars in (("60",B1),("240",B4),("15",B15),("1D",B1D)):     # (1) 1D usa bars_1d
        seg=[b for b in bars if b[0]<=t]
        if len(seg)<25: mtf[tf]={}; continue
        s=CS.structure([b[2] for b in seg],[b[3] for b in seg],[b[4] for b in seg],len(seg)-1,m=3)
        above=[(lo,hi) for (tx,lo,hi) in zs if lo>price]; below=[(lo,hi) for (tx,lo,hi) in zs if hi<price]
        s["zones"]={"above":({"src":"OB supply","low":min(above)[0],"high":min(above)[1]} if above else None),
                    "below":({"src":"OB demand","low":max(below)[0],"high":max(below)[1]} if below else None)}
        mtf[tf]=s
    C15=[b[4] for b in B15 if b[0]<=t]; dmi=sv(r,"Directional"); nas=sv(r,"NAS"); rsi=sv(r,"Relative"); chop=sv(r,"Choppiness")
    micro={"close":price,"bar_time":t,"ema":{"ema9":ema(C15,9),"ema21":ema(C15,21),"ema50":ema(C15,50),"pos":"above" if price>ema(C15,21) else "below"},
           "rsi":rsi.get("RSI"),"rsi_ma":rsi.get("RSI-based MA"),"chop":chop.get("CHOP"),
           "dmi":{"adx":dmi.get("ADX"),"plus_di":dmi.get("+DI"),"minus_di":dmi.get("-DI")},
           "nas":{"bottom":fnum(nas.get("NAS_BOTTOM_SIGNAL")),"top":fnum(nas.get("NAS_TOP_SIGNAL")),"dist_ema_atr":nas.get("NAS_DISTANCE_FROM_EMA_ATR")}}
    liq=CL.compute([{"t":b[0],"o":b[1],"h":b[2],"l":b[3],"c":b[4]} for b in B15 if b[0]<=t][-480:]) or {}
    # (2) confluence: janela das bubbles TIMESTAMPED as-of
    conf={}
    for s in ((r or {}).get("pine_shapes_bubbles") or []):
        if "Bubbles" in s.get("name",""):
            ap=s.get("activations_per_plot") or {}                         # (2) nível-PERNA (per_plot da captura)
            legb=sum(v for k,v in ap.items() if k in ("plot_0","plot_2","plot_4"))
            legs=sum(v for k,v in ap.items() if k in ("plot_6","plot_8","plot_10"))
            win=[a for a in (s.get("activations") or []) if t-4*900<=(a.get("time") or 0)<=t]
            bn=sum(1 for a in win for k in (a.get("shapes") or {}) if k in ("plot_0","plot_2","plot_4"))
            bw=sum(c for a in win for k,c in (a.get("shapes") or {}).items() if k in ("plot_0","plot_2","plot_4"))
            sn=sum(1 for a in win for k in (a.get("shapes") or {}) if k in ("plot_6","plot_8","plot_10"))
            sw=sum(c for a in win for k,c in (a.get("shapes") or {}).items() if k in ("plot_6","plot_8","plot_10"))
            conf={"15":{"buy_dens":legb,"sell":{"dens":legs},"act_dens":legb+legs,"leg_dur_bars":"perna","leg_sell":legs,"nas_n":0,
                        "window":{"bars":4,"buy":{"n":bn,"weight":bw},"sell":{"n":sn,"weight":sw},"net_side":"buy" if bw>sw else "sell"}}}
    # (4) regime: keys CERTAS (v5_4h/structural_1d); Layer1-1D reconstruível; v5-4H IRREDUCÍVEL
    reg={"v5_4h":{"regime":None,"as_of":"IRREDUCÍVEL(state-file)"},"structural_1d":{"regime":regime_l1_asof(t),"as_of":utc(t)}}
    return {"_meta":{"cycle_ts":t,"price_ref":price},"source_health":{"mtf":{"status":"fresh"},"micro_15m":{"status":"fresh"}},
            "axes":{"mtf":mtf,"micro_15m":micro,"liquidity":liq,"confluence":conf,"magnets":{},"regime":reg,
                    "macro":{"_nota":"IRREDUCÍVEL: yields/DXY/VIX/session não guardados por barra histórica"},"amd_setup":{}}}

def build_prompt(bar):
    t=bar[0]; CUR_T[0]=t; dsr=build_dsr(t); SRG.verdict=lambda: sweep_verdict_asof(t)
    b={"t":t,"o":bar[1],"h":bar[2],"l":bar[3],"c":bar[4]}; cand=CR.obs_candidate("15",b,dsr)
    image=E2.render_composite(dsr,cand)
    r=cap_asof(t); dmi=sv(r,"Directional"); rsi=sv(r,"Relative"); nas=sv(r,"NAS")
    near=[f"{tx} {lo:.0f}-{hi:.0f}" for tx,lo,hi in ob_zones(r) if abs((lo+hi)/2-bar[4])<60][:8]
    indic=("\n\n# INDICADORES REAIS NO FECHO (as-of, captura)\n"
           f"  OB perto: {', '.join(near) or '—'}\n  RSI {rsi.get('RSI')} | +DI {dmi.get('+DI')} -DI {dmi.get('-DI')} | NAS top={nas.get('NAS_TOP_SIGNAL')} bot={nas.get('NAS_BOTTOM_SIGNAL')}")
    tb=""
    try: tb="\n\n"+(CR.seq_tops_block() or "")+"\n"+(CR.seq_bottoms_block() or "")     # (3) as-of via monkeypatch
    except Exception: pass
    polnote="\n\n# (POLARIDADES ATIVAS: IRREDUCÍVEL — estado do polarity_tracker não guardado por barra histórica; ausente neste replay)"
    focus=(f"\n\n# VELA EM FOCO (15M, fecho {utc(t)} UTC): O{bar[1]} H{bar[2]} L{bar[3]} C{bar[4]} — lê ESTA vela na fita acima.")
    return image+indic+tb+polnote+focus+CR.TAPE_SCHEMA

TARGETS=[(2026,8,12,14,15,"TOPO rej upW0.81"),(2026,8,12,16,15,"TOPO rej upW0.77"),(2026,8,13,3,0,"RETEST 4410 upW0.64")]
def bar_at(y,mo,d,h,mi):
    t=int(dt.datetime(y,mo,d,h,mi,tzinfo=dt.timezone.utc).timestamp()); return next((b for b in B15 if b[0]==t),None)
if "--show" in sys.argv:
    bar=bar_at(*TARGETS[0][:5]); print("### PROMPT v3 (%s %s) ###\n"%(TARGETS[0][5],utc(bar[0]))); print(build_prompt(bar)); sys.exit(0)
for *ymd,lab in [(t[0],t[1],t[2],t[3],t[4],t[5]) for t in TARGETS]:
    bar=bar_at(*ymd)
    if not bar: continue
    p=build_prompt(bar); print("="*80); print("ALVO:",lab,"@",utc(bar[0]),"C",bar[4])
    try:
        r=subprocess.run([E2.CLAUDE_EXE,"-p",p,"--append-system-prompt",CR.TAPE_SYS,"--model","claude-opus-4-8"],capture_output=True,text=True,timeout=200)
        import re as _re; mm=_re.search(r"\{.*\}",r.stdout,_re.S); v=json.loads(mm.group(0)) if mm else {}
        print("  DIREÇÃO:",v.get("direction"),"| conf",v.get("conviction"),"| fase",v.get("phase"),"| confirmado",v.get("confirmed_signal"))
        print("  nota:",(v.get("note") or "")[:220])
    except Exception as e: print("  ERRO:",e)
