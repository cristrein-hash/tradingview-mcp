#!/usr/bin/env python3
"""L1 — le via MCP (read-only) as extensoes de TP que o Cris fez nos long_positions do chart 4H (profitLevel).
Casa cada long_position ao trade L1 (por entry_time) e calcula o TP ideal + R_ideal vs baseline 3R.
Ground-truth para o L1_EXIT_REVIEW_PREREG (qual o TP estrutural que o exit causal deve atingir).
NAO plota, NAO clear, NAO screenshot. Output: l1_cris_tp_extensions.json."""
import sys, json
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); sys.path.insert(0,str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient
HERE=Path(__file__).resolve().parent
TRD={int(t["entry_time"]):t for t in json.load(open(HERE/"l1_all_canonical_plotting_result.json"))["trades"]}
TICK=0.01
def nt(x):
    try:x=float(x)
    except:return None
    return x/1000.0 if x and x>1e12 else x
def near(t):
    b=None;bd=1e18
    for et in TRD:
        if abs(t-et)<bd:bd=abs(t-et);b=et
    return b,bd
def pr(c,eid):
    for _ in range(4):
        p=c.call_tool("draw_get_properties",{"entity_id":eid})
        if isinstance(p,dict) and (p.get("points") or p.get("properties")):return p
    return p if isinstance(p,dict) else {}
def main():
    c=MCPClient();c.start();rows=[];extended=0
    try:
        st=c.call_tool("chart_get_state");print("chart",st.get("symbol"),st.get("resolution"))
        dl=c.call_tool("draw_list");shapes=dl.get("shapes",[]) if isinstance(dl,dict) else []
        print("shapes",len(shapes))
        for s in shapes:
            if s.get("name")!="long_position":continue
            p=pr(c,s.get("id"));pts=p.get("points") or [];props=p.get("properties") or {}
            if not pts:continue
            t0=nt(pts[0].get("time"))
            et,dd=near(t0) if t0 else (None,9e9)
            if dd>7200 or et is None:continue   # dentro de 2h do entry
            tr=TRD[et];entry=tr["entry"];sl=tr["sl"];risk=entry-sl;base_tp=tr["target"]
            prof=props.get("profitLevel")
            his_tp=round(entry+float(prof)*TICK,2) if prof is not None else None
            p2=pts[1].get("price") if len(pts)>1 else None
            tp=his_tp if his_tp else (round(p2,2) if p2 else None)
            R_ideal=round((tp-entry)/risk,2) if (tp and risk>0) else None
            ext = (tp is not None and base_tp is not None and tp>base_tp+0.5)
            if ext: extended+=1
            rows.append(dict(n=tr["n"],ts=tr["ts"],win=tr["win"],entry=entry,sl=round(sl,2),base_target_3R=base_tp,
                             cris_tp=tp,R_ideal=R_ideal,extended=ext))
    finally:
        try:c.stop()
        except Exception:pass
    rows.sort(key=lambda x:x["n"])
    ext_rows=[r for r in rows if r["extended"]]
    print(f"\nlidos {len(rows)} long_positions | EXTENDIDOS pelo Cris: {extended}")
    print(f"{'#':>3}{'win':>5}{'entry':>9}{'3R_tp':>9}{'cris_tp':>9}{'R_ideal':>8}{'ext':>5}")
    for r in rows:
        print(f"{r['n']:>3}{str(r['win']):>5}{r['entry']:>9}{str(r['base_target_3R']):>9}{str(r['cris_tp']):>9}{str(r['R_ideal']):>8}{'SIM' if r['extended'] else '-':>5}")
    if ext_rows:
        print(f"\nEXTENDIDOS: R_ideal medio={sum(r['R_ideal'] for r in ext_rows)/len(ext_rows):.1f} max={max(r['R_ideal'] for r in ext_rows)}")
    json.dump(rows,open(HERE/"l1_cris_tp_extensions.json","w"),indent=1,default=str)
    print("saved l1_cris_tp_extensions.json")
    return 0
if __name__=="__main__":sys.exit(main())
