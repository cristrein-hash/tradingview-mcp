#!/usr/bin/env python3
"""LAB DE EXIT L2/BPT — ataca WR/streak. Compara políticas de saída disponíveis no 276 (letrun/vstair 60/120,
capped) + derivadas (target2R, target3R, BE-após-1R) das colunas de milestone. WR/streak(loss<0)/sumR. Full + overlap.
streak_loss = R<0 consecutivos (BE=0 quebra). RAW-derived (outcomes do dataset 276)."""
import csv,datetime as dt
from pathlib import Path
L2=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_uncapped_or_proxy_outcomes_276.csv")
rows=list(csv.DictReader(open(L2)))
def fnum(r,k,d=0.0):
    try: return float(r[k])
    except: return d
def fb(r,k):
    v=str(r.get(k,"")).strip().lower(); return v in ("true","1","1.0")
def dep(s): return int(dt.datetime.strptime(s,"%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
OVL=dep("2024-05-24")
def policies(r):
    mfe=fnum(r,"mfe_R"); lr=fnum(r,"realized_letrun_120"); vs=fnum(r,"realized_vstair_120")
    lr60=fnum(r,"realized_letrun_60"); vs60=fnum(r,"realized_vstair_60")
    h2=fb(r,"hit2"); h3=fb(r,"hit3")
    return {
      "letrun120": lr, "vstair120": vs, "letrun60": lr60, "vstair60": vs60,
      "target2R": (2.0 if h2 else -1.1),
      "target3R": (3.0 if h3 else -1.1),
      "BE_apos1R": (lr if lr>0 else (0.0 if mfe>=1.0 else -1.1)),
      "partial_2R_letrun": (1.0 + 0.5*lr if (h2 and lr>0) else (1.0+0.5*-1.1 if h2 else lr)),  # aprox: 50% em +2R, 50% let-run
    }
def panel(R):
    n=len(R);
    if not n: return None
    sm=sum(R); w=sum(1 for x in R if x>0); be=sum(1 for x in R if x==0)
    eq=pk=dd=0
    for x in R: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    mL=mW=cl=cw=0
    for x in R:
        if x>0: cw+=1; cl=0
        elif x<0: cl+=1; cw=0
        else: cl=0; cw=0   # BE quebra ambos
        mW=max(mW,cw); mL=max(mL,cl)
    return n,round(100*w/n,1),round(sm,1),round(sm/n,3),round(dd,1),f"-{mL}/+{mW}",be
def run(rset,tag):
    print(f"\n=== {tag} (N={len(rset)}) ===")
    print(f"{'política':<20}{'WR':>6}{'sumR':>8}{'avgR':>7}{'DD':>7}{'streak':>9}{'BE':>4}")
    keys=["letrun120","vstair120","letrun60","vstair60","target2R","target3R","BE_apos1R","partial_2R_letrun"]
    for k in keys:
        R=[policies(r)[k] for r in rset]; p=panel(R)
        if not p: continue
        n,wr,sm,av,dd,sk,be=p
        print(f"{k:<20}{wr:>5}%{sm:>8}{av:>7}{dd:>7}{sk:>9}{be:>4}")
run(rows,"FULL 276")
run([r for r in rows if dep(r["datetime"])>=OVL],"OVERLAP 2024-05+")
