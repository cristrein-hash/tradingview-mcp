#!/usr/bin/env python3
"""Plota TODOS os trades L2/BPT (BOS/CHoCH bottom) no chart 4H. Entry=close@bar_idx (frozen=RAW), SL estrutural,
exit=entry+R*risk (régua APROVADA: vstair 2024+ / let-run antes). Canônico long_position+label, verde/vermelho.
Requer pause flag + chart já em 4H XAUUSD. NÃO captura screenshot, NÃO limpa (Cris posiciona)."""
import sys,json,csv,datetime as dt
from pathlib import Path
V1=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1")
frozen=[json.loads(l) for l in open(V1/"repro_recovery/raw_features_2020_2026.jsonl")]
N=len(frozen); TSb=[r["ts_epoch"] for r in frozen]; H=[r['high'] for r in frozen]; L=[r['low'] for r in frozen]; C=[r['close'] for r in frozen]
ATR=[None]*N; trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
outc={int(r['bar_idx']):r for r in csv.DictReader(open(V1/"results/l2_bpt_trade_qualification_outcomes.csv"))}
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(V1/"repro_recovery/qual_packets.jsonl")}
RW=6; R_FLOOR=0.3; R_CEIL=1.5
def structural_sl(i,p,atr):
    lo=min(L[max(0,i-RW+1):i+1]); sl=lo-0.1*atr; risk=p-sl
    if risk<=0: return None,None
    if risk<R_FLOOR*atr: sl=p-R_FLOOR*atr; risk=R_FLOOR*atr
    if risk>R_CEIL*atr: sl=p-R_CEIL*atr; risk=R_CEIL*atr
    return sl,risk
def walk(i,p,sl,risk,HZ=120):
    end=min(i+HZ,N-1); stopped=None; lock=-1.0; peakR=0.0; vstair_exit=None
    for j in range(i+1,end+1):
        eff=max(sl,p+lock*risk)
        if vstair_exit is None and L[j]<=eff: vstair_exit=(eff-p)/risk
        if L[j]<=sl and stopped is None:
            stopped=j
            if vstair_exit is None: vstair_exit=-1.0
            break
        hr=(H[j]-p)/risk; peakR=max(peakR,hr)
        for trig,lk in [(2,0),(5,2),(8,5),(12,8),(16,12),(20,16)]:
            if peakR>=trig and lk>lock: lock=float(lk)
    letrun=-1.0 if stopped is not None else (C[end]-p)/risk
    vstair=vstair_exit if vstair_exit is not None else (C[end]-p)/risk
    return letrun,vstair
trades=[]
for bi in sorted(outc):
    p=C[bi]; atr=ATR[bi]
    if not atr: continue
    sl,risk=structural_sl(bi,p,atr)
    if sl is None: continue
    lr,vs=walk(bi,p,sl,risk)
    yr=int(pk[bi]['datetime'][:4]); R=vs if yr>=2024 else lr   # régua aprovada por era
    exitp=p+R*risk
    trades.append({"t":TSb[bi],"date":pk[bi]['datetime'][:10],"entry":round(p,2),"sl":round(sl,2),
                   "exit":round(exitp,2),"R":round(R,2),"win":R>0})
trades.sort(key=lambda z:z["t"])
with open("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/l2_plot_trades.csv","w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=["t","date","entry","sl","exit","R","win"]); w.writeheader(); w.writerows(trades)
sm=sum(t["R"] for t in trades); wn=sum(1 for t in trades if t["win"])
print(f"L2/BPT trades: N={len(trades)} WR={100*wn/len(trades):.1f}% sumR={sm:.1f} | {trades[0]['date']} -> {trades[-1]['date']}")
# ---- plot 4H ----
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/alert-bridge")
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
PAUSE=Path("/tmp/claude_recheck.paused"); SYMBOL,TF,BAR_S,WIDTH="PEPPERSTONE:XAUUSD","240",14400,6; GREEN,RED="#1a8917","#cc0000"
if not PAUSE.exists(): print("ERRO: pause flag ausente"); sys.exit(1)
c=MCPClient(); c.start(); drawn=0; fails=[]; chart={}
try:
    st=c.call_tool("chart_get_state"); sym,res=st.get("symbol"),str(st.get("resolution"))
    if not (str(sym).endswith("XAUUSD") and res=="240"):
        c.stop(); print(json.dumps({"HARD_STOP":f"chart={sym}/{res} (esperado XAUUSD/240). Coloque em 4H."})); sys.exit(1)
    dl0=c.call_tool("draw_list"); chart["before"]=dl0.get("count") if isinstance(dl0,dict) else None
    for i,t in enumerate(trades,1):
        entry,sl,ex,tt,win=t["entry"],t["sl"],t["exit"],t["t"],t["win"]; risk=abs(entry-sl); ly=entry+0.5*risk
        r1=c.call_tool("draw_shape",{"shape":"long_position","point":{"time":tt,"price":entry},
            "point2":{"time":tt+WIDTH*BAR_S,"price":ex},
            "overrides":json.dumps({"stopLevel":price_to_ticks_offset(entry,sl),"profitLevel":price_to_ticks_offset(entry,ex)})})
        if r1.get("success"): drawn+=1
        else: fails.append(str(r1)[:80])
        c.call_tool("draw_shape",{"shape":"text","point":{"time":tt,"price":round(ly,2)},
            "text":f"#{i}","overrides":json.dumps({"color":GREEN if win else RED,"bold":True,"fontsize":9})})
    dl=c.call_tool("draw_list"); chart["after"]=dl.get("count") if isinstance(dl,dict) else None
finally:
    try: c.stop()
    except Exception: pass
print(json.dumps({"trades":len(trades),"posicoes":drawn,"falhas":len(fails),"chart":chart},indent=2,ensure_ascii=False))
