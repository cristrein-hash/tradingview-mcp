#!/usr/bin/env python3
"""L2/BPT XAU 4H — reproduz os 17 trades APROVADOS (painel canonico phase48) + painel COMPLETO de metricas
+ analise MFE ('dinheiro na mesa'). Regua oficial: SL_CONTEXT + let-run HZ120, R=letrun_struct-0.35.
NAO reinventa: importa phase48_bear_deep_zone (tr + keep) e junta sl/risk/letrun/mfe da regua por bar_idx.
Salva fonte de plot canonica 4H: results/l2_bpt_17_trades.csv (num,entry_t,entry,sl,exit,R,win,regime,mfe)."""
import sys, io, contextlib, csv, json, datetime as dt, statistics as st
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO/"regime_turnstate_engine/validation"))
sys.path.insert(0, str(REPO))
# import canonico (redireciona stdout do painel)
with contextlib.redirect_stdout(io.StringIO()):
    import phase48_bear_deep_zone as Q
tr=Q.tr; keep=Q.keep
# raw 4H p/ mapear bar_idx -> tempo unix
RAW=REPO/"my-strategy/research/revalidation/raw_4h_ohlc.jsonl"
bars=[json.loads(l) for l in open(RAW) if l.strip()]
def btime(b): return int(b.get("t") or b.get("time") or b.get("ts"))
T=[btime(b) for b in bars]
# regua por bar_idx
REGUA=REPO/"my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_regua_structural.csv"
REG={int(r["bar_idx"]):r for r in csv.DictReader(open(REGUA))}
def f(r,k):
    try: return float(r[k])
    except: return None

sel=sorted([x for x in tr if keep(x)], key=lambda z:z["bi"])
assert len(sel)==17, f"esperado 17, obtido {len(sel)}"
rows=[]
for i,x in enumerate(sel,1):
    bi=x["bi"]; rr=REG[bi]; entry=f(rr,"entry"); sl=f(rr,"sl"); risk=f(rr,"risk")
    letrun=f(rr,"letrun_struct"); mfe=f(rr,"mfe_struct"); R=x["R"]
    exit_px=entry+letrun*risk           # long: exit = entry + letrun(R)*risco_pts
    rows.append({"num":i,"bar_idx":bi,"entry_t":T[bi],"date":x["date"],"regime":x["reg"],
                 "entry":round(entry,2),"sl":round(sl,2),"exit":round(exit_px,2),"risk_pts":round(risk,1),
                 "R":R,"letrun":letrun,"mfe":mfe,"win":1 if R>0 else 0})
# salvar fonte de plot
out=REPO/"research/results"; out.mkdir(exist_ok=True)
with open(out/"l2_bpt_17_trades.csv","w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=["num","entry_t","entry","sl","exit","R","win","regime","mfe","risk_pts","bar_idx","date"])
    w.writeheader()
    for r in rows: w.writerow({k:r[k] for k in w.fieldnames})

# ---------- PAINEL COMPLETO ----------
def panel(rs):
    n=len(rs); w=sum(r["win"] for r in rs); s=sum(r["R"] for r in rs)
    cum=peak=dd=0; stk=mx=0
    for r in sorted(rs,key=lambda z:z["bar_idx"]):
        cum+=r["R"]; peak=max(peak,cum); dd=min(dd,cum-peak); stk=stk+1 if r["R"]<=0 else 0; mx=max(mx,stk)
    return dict(N=n,WR=round(100*w/n,1),sumR=round(s,1),avgR=round(s/n,2),DD=round(dd,1),
               retDD=round(s/abs(dd),1) if dd<0 else None,streak=mx,big=sum(1 for r in rs if r["R"]>=3))
P=panel(rows)
print("="*74); print("L2/BPT XAU 4H — PAINEL COMPLETO (régua oficial: SL_CONTEXT + let-run, custo 0.35R)"); print("="*74)
print(f"  N={P['N']} · WR={P['WR']}% · sumR={P['sumR']:+} · avgR={P['avgR']:+} · maxDD={P['DD']}R · Retorno/DD={P['retDD']}x · streak(perdas)={P['streak']} · big(R>=3)={P['big']}")
print("  por ano:")
for y in sorted({r for r in [dt.datetime.utcfromtimestamp(x['entry_t']).year for x in rows]}):
    g=[r for r in rows if dt.datetime.utcfromtimestamp(r['entry_t']).year==y]
    pg=panel(g); print(f"    {y}: N={pg['N']:2} WR={pg['WR']:>5}% sumR={pg['sumR']:+6} avgR={pg['avgR']:+5} streak={pg['streak']}")
print("  por regime:")
for rg in ("BULL","RANGE","BEAR"):
    g=[r for r in rows if r["regime"]==rg]
    if g: pg=panel(g); print(f"    {rg:5} N={pg['N']:2} WR={pg['WR']:>5}% sumR={pg['sumR']:+6} avgR={pg['avgR']:+5}")

# ---------- MFE: dinheiro na mesa ----------
print("\n"+"="*74); print("ANÁLISE MFE — quanto cada trade CORREU (mfe) vs quanto o let-run CAPTUROU (R)"); print("="*74)
capt=sum(r["R"] for r in rows); mfe_sum=sum((r["mfe"] or 0) for r in rows)
winners=[r for r in rows if r["win"]==1]
print(f"  R capturado (líquido custo): {capt:+.1f}R  ·  MFE total (pico favorável): {mfe_sum:+.1f}R")
print(f"  eficiência de captura = R/MFE = {100*capt/mfe_sum:.0f}%  ·  'na mesa' (MFE-R) = {mfe_sum-capt:+.1f}R")
print(f"  MFE médio/trade: {mfe_sum/len(rows):+.2f}R  ·  R médio/trade: {capt/len(rows):+.2f}R")
print(f"  WINNERS: R capturado {sum(r['R'] for r in winners):+.1f} vs MFE {sum((r['mfe'] or 0) for r in winners):+.1f}  (captura {100*sum(r['R'] for r in winners)/max(1e-9,sum((r['mfe'] or 0) for r in winners)):.0f}%)")
print("\n  trade-a-trade (num · data · regime · entry · SL · risco_pts · R · MFE · gap MFE-R):")
for r in rows:
    print(f"   #{r['num']:2} {r['date']} {r['regime']:5} e{r['entry']:>7} sl{r['sl']:>7} risk{r['risk_pts']:>6} R{r['R']:+5} mfe{(r['mfe'] or 0):+5} gap{(r['mfe'] or 0)-r['R']:+5.1f}")
print("\nsaved research/results/l2_bpt_17_trades.csv (fonte de plot 4H) · SEM veredito — dado para revisão do Cris")
