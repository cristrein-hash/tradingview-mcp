#!/usr/bin/env python3
"""Le via MCP o ALVO que o Cris colocou EXTENDENDO cada long_position (profitLevel/point2) no chart 4H.
Mapeia cada long_position ao trade por tempo de entry, extrai profitLevel(ticks)+point2(price)+stopLevel,
calcula alvo_price e Cris_R = (alvo-entry)/risco, compara com o let-run. Read-only. Salva l2_bpt_cris_targets.csv."""
import sys, json, csv, datetime as dt
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); sys.path.insert(0,str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient
TICK=0.01
MY={int(r["num"]):r for r in csv.DictReader(open(REPO/"research/results/l2_bpt_17_trades.csv"))}
BYT=sorted((int(v["entry_t"]),int(n)) for n,v in MY.items())
def near(t):
    b=None;bd=1e18
    for et,n in BYT:
        if abs(t-et)<bd:bd=abs(t-et);b=n
    return b,bd
def nt(x):
    try:x=float(x)
    except:return None
    return x/1000.0 if x and x>1e12 else x
def pr(c,eid):
    for _ in range(4):
        p=c.call_tool("draw_get_properties",{"entity_id":eid})
        if isinstance(p,dict) and (p.get("points") or p.get("properties")):return p
    return p if isinstance(p,dict) else {}
def main():
    c=MCPClient();c.start();rows=[]
    try:
        dl=c.call_tool("draw_list");shapes=dl.get("shapes",[]) if isinstance(dl,dict) else []
        for s in shapes:
            if s.get("name")!="long_position":continue
            p=pr(c,s.get("id"));pts=p.get("points") or [];props=p.get("properties") or {}
            if not pts:continue
            t0=nt(pts[0].get("time"));p0=pts[0].get("price")
            n,dd=near(t0) if t0 else (None,9e9)
            if dd>450 or n is None:continue
            m=MY[n];entry=float(m["entry"]);sl=float(m["sl"]);risk=abs(entry-sl);letrun_ex=float(m["exit"]);Rlet=float(m["R"])
            prof=props.get("profitLevel");stop=props.get("stopLevel")
            p2=pts[1].get("price") if len(pts)>1 else None
            tgt_from_level=round(entry+float(prof)*TICK,2) if prof is not None else None
            tgt=tgt_from_level if tgt_from_level else (round(p2,2) if p2 else None)
            crisR=round((tgt-entry)/risk-0.35,2) if tgt else None
            rows.append(dict(num=n,date=m["date"],regime=m["regime"],entry=entry,sl=sl,risk=round(risk,1),
                             letrun_exit=letrun_ex,R_letrun=Rlet,profitLevel=prof,point2=round(p2,2) if p2 else None,
                             alvo_cris=tgt,R_cris=crisR,delta_R=round(crisR-Rlet,2) if crisR is not None else None))
    finally:
        try:c.stop()
        except Exception:pass
    rows.sort(key=lambda r:r["num"])
    print("="*112);print("ALVOS DO CRIS (extendidos via MCP) vs LET-RUN oficial — por trade");print("="*112)
    print(f"{'#':>2} {'data':<11}{'reg':<6}{'entry':>9}{'sl':>9}{'risk':>7}{'let_exit':>9}{'R_let':>7}{'alvo_Cris':>10}{'R_Cris':>8}{'ΔR':>7}")
    sl=sc=0
    for r in rows:
        sl+=r["R_letrun"];sc+=(r["R_cris"] or r["R_letrun"])
        print(f"#{r['num']:>2} {r['date']:<11}{r['regime']:<6}{r['entry']:>9}{r['sl']:>9}{r['risk']:>7}{r['letrun_exit']:>9}{r['R_letrun']:>+7}{str(r['alvo_cris']):>10}{str(r['R_cris']):>8}{str(r['delta_R']):>7}")
    print("-"*112)
    print(f"  sumR let-run = {sl:+.1f}   |   sumR ALVOS-CRIS = {sc:+.1f}   |   delta total = {sc-sl:+.1f}R")
    print(f"  losers let-run = {sum(1 for r in rows if r['R_letrun']<=0)}  |  losers c/ alvo-Cris = {sum(1 for r in rows if (r['R_cris'] or r['R_letrun'])<=0)}  (de {len(rows)})")
    json.dump(rows,open(REPO/"research/results/l2_bpt_cris_targets.json","w"),indent=1)
    with open(REPO/"research/results/l2_bpt_cris_targets.csv","w",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("saved research/results/l2_bpt_cris_targets.{json,csv}")
    return 0
if __name__=="__main__":sys.exit(main())
