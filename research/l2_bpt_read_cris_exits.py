#!/usr/bin/env python3
"""Le via MCP (CDP) TODOS os desenhos do chart 4H e extrai os ALVOS/EXITS que o Cris colocou.
Separa os MEUS 17 (long_position nos 17 entry_t + labels #num) dos desenhos do CRIS (boxes/lines/long_position
com alvos proprios). Para cada shape: name, pontos (time,price), propriedades-chave (text, cor, stop/profit).
Mapeia cada exit do Cris ao trade mais proximo por tempo. Read-only (draw_list + draw_get_properties)."""
import sys, json, csv, datetime as dt
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); sys.path.insert(0,str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient
ENT={int(r["num"]):{"t":int(r["entry_t"]),"entry":float(r["entry"]),"sl":float(r["sl"]),
                    "exit_letrun":float(r["exit"]),"R":float(r["R"]),"date":r["date"]}
     for r in csv.DictReader(open(REPO/"research/results/l2_bpt_17_trades.csv"))}
ENT_T=sorted((v["t"],n) for n,v in ENT.items())
def nearest_trade(t):
    best=None;bd=1e18
    for et,n in ENT_T:
        if abs(t-et)<bd: bd=abs(t-et);best=n
    return best,bd
def norm_t(x):
    try:x=float(x)
    except:return None
    return x/1000.0 if x>1e12 else x
def props_retry(c,eid,tries=4):
    for _ in range(tries):
        pr=c.call_tool("draw_get_properties",{"entity_id":eid})
        if isinstance(pr,dict) and (pr.get("points") or pr.get("properties")): return pr
    return pr if isinstance(pr,dict) else {}
def main():
    c=MCPClient(); c.start()
    try:
        st=c.call_tool("chart_get_state"); print("chart:",st.get("symbol"),st.get("resolution"))
        dl=c.call_tool("draw_list"); shapes=dl.get("shapes",[]) if isinstance(dl,dict) else []
        from collections import Counter
        print("total shapes:",len(shapes),"| por tipo:",dict(Counter(s.get("name") for s in shapes)))
        mine=[]; cris=[]
        for s in shapes:
            eid=s.get("id"); nm=s.get("name")
            if not eid: continue
            pr=props_retry(c,eid); pts=pr.get("points") or []; props=pr.get("properties") or {}
            P=[(norm_t(p.get("time")),p.get("price")) for p in pts if isinstance(p,dict)]
            text=props.get("text"); col=props.get("color") or props.get("linecolor") or props.get("backgroundColor")
            rec={"name":nm,"pts":P,"text":text,"color":col,
                 "stopLevel":props.get("stopLevel"),"profitLevel":props.get("profitLevel")}
            # MEU: long_position/text ancorado exatamente num entry_t (|dt|<450s) e label #num
            is_mine=False
            if P:
                t0=P[0][0]; tn,dd=nearest_trade(t0) if t0 else (None,9e9)
                if nm=="text" and text and str(text).lstrip("#").rstrip("R").isdigit(): is_mine=True
                elif nm=="long_position" and dd<450 and props.get("stopLevel") is not None: is_mine=True
            (mine if is_mine else cris).append(rec)
        print(f"\nMEUS (auto): {len(mine)}  |  DO CRIS (a inspecionar): {len(cris)}")
        print("\n=== DESENHOS DO CRIS (candidatos a alvos/exit) ===")
        out=[]
        for r in cris:
            P=r["pts"];
            if not P:
                print(f"  {r['name']} (sem pontos) text={r['text']} cor={r['color']}"); continue
            # tempo/preco de referencia
            t0=P[0][0]; tn,dd=nearest_trade(t0) if t0 else (None,9e9)
            prices=[p[1] for p in P if p[1] is not None]
            hi=max(prices) if prices else None; lo=min(prices) if prices else None
            info={"name":r["name"],"text":r["text"],"color":r["color"],"pts":[(int(p[0]) if p[0] else None,p[1]) for p in P],
                  "price_hi":hi,"price_lo":lo,"near_trade":tn,"dt_days":round(dd/86400,1) if dd<9e8 else None}
            out.append(info)
            when=dt.datetime.utcfromtimestamp(int(t0)).strftime("%Y-%m-%d") if t0 else "?"
            print(f"  {r['name']:14} {when} text={str(r['text'])[:16]:16} hi={hi} lo={lo}  ~trade#{tn}(Δ{info['dt_days']}d)")
        json.dump({"cris":out,"my_entries":{str(n):ENT[n] for n in ENT}}, open(REPO/"research/results/l2_bpt_cris_exits_raw.json","w"), indent=1)
        print("\nsaved research/results/l2_bpt_cris_exits_raw.json")
    finally:
        try:c.stop()
        except Exception:pass
    return 0
if __name__=="__main__": sys.exit(main())
