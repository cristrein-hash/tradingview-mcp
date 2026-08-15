#!/usr/bin/env python3
"""REPLAY FIEL do reader nas barras dos shorts que faltaram, com o PROMPT DE AGORA (pós-recalibração 14/08).
Reconstrói a briefing as-of-bar: mtf/estado-perna (context_structure) + CONTEXTO-4H as-of (sweep/15M-break)
+ indicadores as-of (OB/SMC/NAS/Bubbles/RSI/DMI da captura replay de ontem). Corre Opus com TAPE_SYS atual.
READ_OB_ZONES: consome OB Detector real capturado. NÃO toca produção. py3."""
import sys, json, subprocess, datetime as dt, bisect
from pathlib import Path
ROOT = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(ROOT / "alert-bridge"))
import context_structure as CS
import candle_reader as CR   # TAPE_SYS, TAPE_SCHEMA
import e2_quality as E2       # CLAUDE_EXE, fmt, _swing_state

CAP = ROOT / "alert-bridge/logs/backtests/XAUUSD_15m_replay_2026-08-10_to_2026-08-14.jsonl"
def load(f):
    return sorted([(int(x['t']),float(x['o']),float(x['h']),float(x['l']),float(x['c'])) for x in
                   (json.loads(l) for l in open(f) if l.strip())])
B15 = load(ROOT/"my-strategy/core/bar_store/store/bars_15m.jsonl")
B1 = load(ROOT/"my-strategy/research/revalidation/raw_1h_ohlc.jsonl")
B4 = load(ROOT/"my-strategy/research/revalidation/raw_4h_ohlc.jsonl")
def utc(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%m-%d %H:%M")

# captura replay indexada por as-of bar t (15M)
capidx={}
for l in open(CAP):
    if not l.strip(): continue
    r=json.loads(l); oh=r.get("ohlcv"); bars=oh.get("bars") if isinstance(oh,dict) else oh
    if bars:
        capidx[int(bars[-1].get("t") or bars[-1].get("time"))]=r

def mtf_block(t):
    out={}
    for tf,bars in (("60",B1),("240",B4),("15",B15)):
        H=[b[2] for b in bars if b[0]<=t]; L=[b[3] for b in bars if b[0]<=t]; C=[b[4] for b in bars if b[0]<=t]
        if len(C)<25: out[tf]={}; continue
        out[tf]=CS.structure(H,L,C,len(C)-1,m=3)
    return out

def sweep_ctx(t):
    # 4H sweep-reject (upper_wick>0.5*body) mais recente com fecho<=t
    ts=None; sh=None
    for (bt,o,h,l,c) in B4:
        if bt+4*3600> t: break
        if (h-max(o,c))>0.5*abs(c-o): ts=bt+4*3600; sh=h
    # última quebra-up 15M (HH+HL, close>lower-high) <=t
    up=None
    seg=[b for b in B15 if b[0]<=t]
    if len(seg)>25:
        H=[b[2] for b in seg]; L=[b[3] for b in seg]; C=[b[4] for b in seg]
        ph=[];pl=[]
        for k in range(2,len(seg)-2):
            if H[k]>H[k-1] and H[k]>H[k-2] and H[k]>=H[k+1] and H[k]>=H[k+2]: ph.append((k+2,H[k]))
            if L[k]<L[k-1] and L[k]<L[k-2] and L[k]<=L[k+1] and L[k]<=L[k+2]: pl.append((k+2,L[k]))
        hi=lo=0
        for i in range(len(seg)):
            while hi<len(ph) and ph[hi][0]<=i: hi+=1
            while lo<len(pl) and pl[lo][0]<=i: lo+=1
            if hi>=2 and lo>=2 and ph[hi-1][1]<ph[hi-2][1] and pl[lo-1][1]>pl[lo-2][1] and C[i]>ph[hi-1][1]:
                up=seg[i][0]
    active = ts is not None and (up is None or ts>up)
    return active, ts, sh, up

def indic_block(t):
    r=capidx.get(t) or capidx.get(max([x for x in capidx if x<=t], default=None))
    if not r: return "  (sem captura)"
    L=[]
    sv=r.get("study_values",{}); st=sv.get("studies",sv) if isinstance(sv,dict) else sv
    for s in st or []:
        n=s.get("name",""); v=s.get("values",{})
        if "NAS" in n: L.append(f"  NAS top={v.get('NAS_TOP_SIGNAL')} bot={v.get('NAS_BOTTOM_SIGNAL')} rsi={v.get('NAS_RSI')}")
        if "Directional" in n: L.append(f"  DMI +DI={v.get('+DI')} -DI={v.get('-DI')} ADX={v.get('ADX')}")
        if "Relative" in n: L.append(f"  RSI={v.get('RSI')} MA={v.get('RSI-based MA')}")
    pb=r.get("pine_boxes",{})
    for s in (pb.get("studies") if isinstance(pb,dict) else pb) or []:
        if "OB Detector" in s.get("name",""):
            zs=[(b.get('text'),b['low'],b['high']) for b in (s.get('all_boxes') or []) if b.get('text')][:8]
            L.append("  OB Detector (as-of): "+", ".join(f"{tx} {lo:.0f}-{hi:.0f}" for tx,lo,hi in zs))
    bb=r.get("pine_shapes_bubbles",[])
    for s in (bb if isinstance(bb,list) else []):
        if "Bubbles" in s.get("name",""):
            ap=s.get("activations_per_plot") or {}
            b=sum(v for k,v in ap.items() if k in ("plot_0","plot_2","plot_4")); sl=sum(v for k,v in ap.items() if k in ("plot_6","plot_8","plot_10"))
            L.append(f"  Bubbles (as-of): BUY={b} SELL={sl}")
    return "\n".join(L)

def briefing(t, price):
    mtf=mtf_block(t)
    active,ts,sh,up=sweep_ctx(t)
    L=[f"# LEITURA DE VELA 15M FECHADA @ {utc(t)} UTC · preço {price}"]
    m60=mtf.get("60",{})
    L.append(f"# FRAME (lê TUDO contra isto): PERNA 1H = trend {m60.get('trend')} (leg {(m60.get('leg') or {}).get('dir')})")
    L.append("\n# ESTADO DA PERNA (swings LH/LL, prioridade 1H→4H→15M)")
    for tf,lbl in (("60","1H"),("240","4H"),("15","15M")):
        sw=(mtf.get(tf,{}) or {}).get("swings",{}) or {}
        lh=(sw.get("last_high") or {}).get("price"); ph=(sw.get("prev_high") or {}).get("price")
        ll=(sw.get("last_low") or {}).get("price"); pl=(sw.get("prev_low") or {}).get("price")
        if lh and ll:
            hs="LOWER-HIGH" if ph and lh<ph else ("higher-high" if ph and lh>ph else "=")
            ls="LOWER-LOW" if pl and ll<pl else ("higher-low" if pl and ll>pl else "=")
            stt="DOWN(LH+LL)" if ph and pl and lh<ph and ll<pl else ("UP(HH+HL)" if ph and pl and lh>ph and ll>pl else "RANGE")
            L.append(f"  [{lbl}] {stt} | high {lh} ({hs} vs {ph}) · low {ll} ({ls} vs {pl})")
    L.append("\n# CONTEXTO ESTRUTURAL 4H (sweep-reject/distribuição/retomada)")
    if active:
        L.append(f"  ⚠️ SWEEP-REJECT 4H ATIVO (high {sh}) = DISTRIBUIÇÃO no topo. SHORT na rejeição de lower-high = LEGÍTIMO (não contra-perna). LONG dentro = faca até quebra 15M.")
    else:
        L.append("  sem sweep-reject 4H ativo — sem moldura de distribuição.")
    L.append("\n# INDICADORES (as-of-bar, captura replay)")
    L.append(indic_block(t))
    return "\n".join(L)

TARGETS=[(dt.datetime(2026,8,12,14,15,tzinfo=dt.timezone.utc),"TOPO rejeição upW0.81 (pré-sweep)"),
         (dt.datetime(2026,8,12,16,15,tzinfo=dt.timezone.utc),"TOPO rejeição upW0.77 (pré-sweep)"),
         (dt.datetime(2026,8,13,3,0,tzinfo=dt.timezone.utc),"RETEST 4410 rejeição upW0.64 (pós-sweep)")]
for d,lab in TARGETS:
    t=int(d.timestamp())
    bar=next((b for b in B15 if b[0]==t), None)
    if not bar:
        cand=[b for b in B15 if b[0]<=t]; bar=cand[-1] if cand else None
    price=bar[4] if bar else "?"
    brief=briefing(t,price)
    prompt=brief+"\n"+CR.TAPE_SCHEMA
    print("="*80); print(f"ALVO: {lab} @ {utc(t)} preço {price}")
    try:
        r=subprocess.run([E2.CLAUDE_EXE,"-p",prompt,"--append-system-prompt",CR.TAPE_SYS,"--model","claude-opus-4-8"],
                         capture_output=True,text=True,timeout=180)
        v=E2._extract_json(r.stdout) if hasattr(E2,"_extract_json") else None
        if v is None:
            import re as _re; mm=_re.search(r"\{.*\}",r.stdout,_re.S); v=json.loads(mm.group(0)) if mm else {}
        print(f"  DIREÇÃO: {v.get('direction')} | conf {v.get('conviction')} | fase {v.get('phase')} | confirmado {v.get('confirmed_signal')}")
        print(f"  nota: {(v.get('note') or '')[:200]}")
    except Exception as e:
        print("  ERRO:",e, r.stdout[:300] if 'r' in dir() else '')
