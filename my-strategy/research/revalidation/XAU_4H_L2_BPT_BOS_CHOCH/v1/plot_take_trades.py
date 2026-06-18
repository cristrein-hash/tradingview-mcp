#!/usr/bin/env python3
"""Plota os 32 TAKE do Trade Qualification Engine no chart XAU 4H — CONVENÇÃO CANÔNICA
(docs/CANONICAL_TRADE_PLOTTING.md): long_position (largura 20 barras, stop/profit em TICKS via
mintick 0.01) + label #ID verde(close_R>0)/vermelho. point2 NO TARGET. Verificação por draw_list
(SEM screenshot). SL = demand-anchored (real do trade); TARGET = +2R (primário do partial50) — DECLARADO.
NÃO limpa desenhos (Cris limpa manual). Deixa o chart em XAU 4H p/ revisão. Reusa MCPClient canônico."""
import json,math,subprocess,sys,time
from pathlib import Path
BASE=Path("/Users/cristrein/tradingview-mcp")
NODE="/opt/homebrew/bin/node";SERVER=BASE/"src"/"server.js"
MINTICK=0.01;BAR=14400;WIDTH_BARS=20
TRADES=json.load(open("/tmp/take_trades_plot.json"))
def ticks(entry,level): return int(round(abs(level-entry)/MINTICK))
class MCP:
    def __init__(self):self.p=None;self.i=0
    def start(self):
        self.p=subprocess.Popen([NODE,str(SERVER)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
        self._raw("initialize",{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"plot-take","version":"1.0"}})
        self.p.stdin.write(json.dumps({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})+"\n");self.p.stdin.flush()
    def _raw(self,m,pr,to=60):
        self.i+=1;rid=self.i
        self.p.stdin.write(json.dumps({"jsonrpc":"2.0","id":rid,"method":m,"params":pr})+"\n");self.p.stdin.flush()
        dl=time.monotonic()+to
        while time.monotonic()<dl:
            ln=self.p.stdout.readline()
            if not ln:raise RuntimeError("server closed")
            try:
                r=json.loads(ln)
                if r.get("id")==rid:return r
            except:continue
        raise TimeoutError(m)
    def call(self,n,a=None,to=60):
        r=self._raw("tools/call",{"name":n,"arguments":a or {}},to)
        if "error" in r:return {"_error":r["error"]}
        c=r.get("result",{}).get("content",[])
        if c and c[0].get("type")=="text":
            try:return json.loads(c[0]["text"])
            except:return {"_raw":c[0]["text"]}
        return r.get("result",{})
    def stop(self):
        try:self.p.stdin.close();self.p.terminate();self.p.wait(timeout=5)
        except:self.p.kill()
m=MCP();print("spawn MCP...");m.start();print("ok")
st=m.call("chart_get_state");sym=(st.get('symbol') or '');tf=str(st.get('resolution') or st.get('timeframe') or '')
print(f"chart atual: {sym} {tf}")
if 'XAUUSD' not in sym.upper():
    print("set PEPPERSTONE:XAUUSD ...");m.call("chart_set_symbol",{"symbol":"PEPPERSTONE:XAUUSD"});time.sleep(1.5)
if tf not in ('240','4H','4h'):
    print("set tf 240 ...");m.call("chart_set_timeframe",{"timeframe":"240"});time.sleep(1.5)
ok=0;fail=0
for t in TRADES:
    entry=t['entry'];stop=t['stop'];tgt=t['target'];et=t['ts'];R=t['close_R']
    if not(entry>stop and tgt>entry):print(f"  #{t['id']} skip (validação)");fail+=1;continue
    r1=m.call("draw_shape",{"shape":"long_position","point":{"time":et,"price":entry},
        "point2":{"time":et+WIDTH_BARS*BAR,"price":tgt},
        "overrides":json.dumps({"stopLevel":ticks(entry,stop),"profitLevel":ticks(entry,tgt)})})
    rd=entry-stop
    r2=m.call("draw_shape",{"shape":"text","point":{"time":et,"price":entry+0.5*rd},
        "text":f"#{t['id']}","overrides":json.dumps({"color":"#1a8917" if R>0 else "#cc0000","bold":True,"fontsize":12})})
    if r1.get("success"):ok+=1
    else:print(f"  #{t['id']} long_position FALHOU: {r1}");fail+=1
print(f"\nlong_position desenhados: {ok}/{len(TRADES)} (falhas {fail})")
dl=m.call("draw_list")
ents=dl.get('drawings') or dl.get('entities') or dl.get('list') or []
print(f"draw_list count: {dl.get('count', len(ents) if isinstance(ents,list) else '?')}")
print(f"chart deixado em XAU 4H p/ revisão. Símbolo/TF NÃO restaurados (daemon gerencia no próximo ciclo).")
m.stop();print("MCP stopped.")
