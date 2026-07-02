#!/usr/bin/env python3
"""Cris: plotar os 70 trades INTRA-RANGE com SL = PISO da BOX INTEIRA (demanda-origem do range), buffer 0.1ATR.
Convenção canónica long_position: stopLevel/profitLevel em TICKS (mintick 0.01), cor da borda = win(verde)/loss(vermelho).
SL=box_floor−0.1ATR (piso do range da box INTEIRA — o que o Cris pediu; NOTA: hindsight parcial). let-run HZ120 p/ exit.
Saída JSON p/ plotagem via MCP draw_shape."""
import json,csv,io,contextlib,sys,bisect,datetime as dt
from pathlib import Path
COST=0.35;HZ=120;MT=0.01
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=[s for s in json.load(open("/tmp/causal_segments_v10.json")) if s["regime"]=="RANGE"]
def box_of(ts):
    for s in segs:
        if s['start']<=ts<=s['end']: return s
    return None
def letrun_exit(bi,entry,sl):
    risk=entry-sl;end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return j,sl,-1.0
    return end,C[end],(C[end]-entry)/risk
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
WBARS=12   # largura CANÓNICA fixa (12 barras 4h), NÃO o exit real do let-run (evita caixas gigantes)
out=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];box=box_of(t)
    if not box: continue
    i0=bisect.bisect_left(T,box['start']);iE=bisect.bisect_right(T,box['end'])-1
    box_floor=min(L[i0:iE+1]);a=atr(bi);entry=float(r["entry"]);sl=box_floor-0.1*a;risk=entry-sl
    if risk<=0: continue
    xb,xp,R=letrun_exit(bi,entry,sl);Rc=round(R-COST,2)
    target=entry+3*a   # alvo visual MODESTO = 3 ATR fixo (não 3×risk-piso, que inflava)
    out.append({"bar":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),
        "entry_time":t,"exit_time":t+WBARS*14400,"entry":round(entry,2),"target":round(target,2),
        "stopLevel":int(round((entry-sl)/MT)),"profitLevel":int(round(3*a/MT)),
        "R":round(Rc,1),"win":Rc>0})
json.dump(out,open("/tmp/l2_70_boxfloor.json","w"))
w=sum(1 for x in out if x["win"])
print(f"70 intra-range c/ SL=piso-box-inteira: {len(out)} (win {w} / loss {len(out)-w}) sumR {sum(x['R'] for x in out):+.1f}")
print("amostra:",json.dumps(out[0]))
