#!/usr/bin/env python3
"""Plot the 41 UNKNOWN visual-sample episodes — OUTCOME-BLIND.
Per CANONICAL_TRADE_PLOTTING.md: 2 shapes/episode = long_position (stop/profit in TICKS) + text.
BLIND: label color = neutral blue #1565c0 (never green/red), text = synthetic 'E<id> · BUCKET · CTX'
(NO R, NO outcome). target = entry + 3R VISUAL (geometry only, not outcome). NO draw_clear, NO
screenshot, NO symbol/tf switch. Aborts if chart != PEPPERSTONE:XAUUSD/240. Reads /tmp/plot_geometry.json.
"""
import json, math, subprocess, sys, time
from pathlib import Path
BASE=Path(__file__).resolve()
for d in (BASE.parent,*BASE.parents):
    if (d/"src"/"server.js").exists(): ROOT=d; break
NODE="/opt/homebrew/bin/node"; MCP=ROOT/"src"/"server.js"
SYMBOL="PEPPERSTONE:XAUUSD"; TF="240"; MINTICK=0.01; BLUE="#1565c0"; BARSEC=14400
def ticks(entry,level): return int(round(abs(level-entry)/MINTICK))
class C:
    def __init__(s): s.p=None; s.i=0
    def start(s):
        s.p=subprocess.Popen([NODE,str(MCP)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
        s._raw("initialize",{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"plot-blind","version":"1.0"}})
        s.p.stdin.write(json.dumps({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})+"\n"); s.p.stdin.flush()
    def stop(s):
        if s.p:
            try: s.p.stdin.close()
            except: pass
            try: s.p.terminate(); s.p.wait(timeout=5)
            except: s.p.kill()
    def _raw(s,m,pr,timeout=60):
        s.i+=1; rid=s.i
        s.p.stdin.write(json.dumps({"jsonrpc":"2.0","id":rid,"method":m,"params":pr})+"\n"); s.p.stdin.flush()
        dl=time.monotonic()+timeout
        while time.monotonic()<dl:
            ln=s.p.stdout.readline()
            if not ln: raise RuntimeError("MCP closed")
            try:
                r=json.loads(ln)
                if r.get("id")==rid: return r
            except json.JSONDecodeError: continue
        raise TimeoutError(m)
    def call(s,name,args=None,timeout=60):
        r=s._raw("tools/call",{"name":name,"arguments":args or {}},timeout=timeout)
        if "error" in r: return {"_error":r["error"]}
        c=r.get("result",{}).get("content",[])
        if c and c[0].get("type")=="text":
            try: return json.loads(c[0]["text"])
            except: return {"_raw":c[0]["text"]}
        return r.get("result",{})

def main():
    eps=json.load(open("/tmp/plot_geometry.json"))
    for e in eps:  # pre-validate
        if not (e["entry"]>e["stop"] and e["target"]>e["entry"]): print(f"HARD STOP E{e['episode_id']} invalid",file=sys.stderr); return 1
        if e["stopLevel"]<=0 or e["profitLevel"]<=0: print(f"HARD STOP E{e['episode_id']} ticks<=0",file=sys.stderr); return 1
    cl=C(); cl.start()
    try:
        st=cl.call("chart_get_state")
        if st.get("symbol")!=SYMBOL or str(st.get("resolution"))!=TF:
            print(f"HARD STOP chart {st.get('symbol')}/{st.get('resolution')}",file=sys.stderr); return 1
        before=cl.call("draw_list").get("count"); print(f"chart OK {SYMBOL}/{TF} | drawings before={before} | plotting {len(eps)} episodes BLIND")
        ok_pos=ok_lbl=fail=0; only_label=[]
        for e in eps:
            exit_t=e["time"]+36*BARSEC; R=e["entry"]-e["stop"]
            r1=cl.call("draw_shape",{"shape":"long_position","point":{"time":e["time"],"price":e["entry"]},
                "point2":{"time":exit_t,"price":e["target"]},
                "overrides":json.dumps({"stopLevel":ticks(e["entry"],e["stop"]),"profitLevel":ticks(e["entry"],e["target"])})})
            if r1.get("success") or r1.get("id") or not r1.get("_error"): ok_pos+=1
            else: fail+=1; print(f"  E{e['episode_id']} long_position FAIL: {r1}"); only_label.append(e['episode_id'])
            r2=cl.call("draw_shape",{"shape":"text","point":{"time":e["time"],"price":e["entry"]+0.5*R},
                "text":e["label"],"overrides":json.dumps({"color":BLUE,"bold":True,"fontsize":16})})
            if r2.get("success") or r2.get("id") or not r2.get("_error"): ok_lbl+=1
            else: print(f"  E{e['episode_id']} label FAIL: {r2}")
        after=cl.call("draw_list").get("count")
        print(json.dumps({"episodes":len(eps),"long_position_ok":ok_pos,"label_ok":ok_lbl,"fail":fail,
            "drawings_before":before,"drawings_after":after,"only_label_episodes":only_label}))
    finally: cl.stop()
    return 0
sys.exit(main())
