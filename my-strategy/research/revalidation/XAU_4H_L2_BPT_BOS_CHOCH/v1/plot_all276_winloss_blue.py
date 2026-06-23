#!/usr/bin/env python3
"""Plota os episódios L2/BPT com decisão TAKE ou REVIEW (NÃO plota SKIP) — avaliar a leitura real.
Plotagem CANÔNICA SIMPLES (long_position + label #id):
  - label VERDE  (#1a8917) = winner (capped_realR > 0)
  - label VERMELHO (#cc0000) = loser  (capped_realR <= 0)
  - label AZUL  (#2962ff) = casos CRÍTICOS dentro de TAKE/REVIEW (sobrepõe verde/vermelho)
Exit canônico p/ geometria: stop −1.0 ATR / target +2.7 ATR (todos LONG). ADITIVO (NÃO draw_clear,
NÃO troca symbol/timeframe, NÃO screenshot). Segura chart_op.lock do daemon L1; remove no finally.
HARD STOP se chart != PEPPERSTONE:XAUUSD/240 ou trade inválido."""
import json, math, subprocess, sys, time, csv, os
from pathlib import Path

V1 = Path(__file__).resolve().parent
for d in (V1, *V1.parents):
    if (d / "src" / "server.js").exists():
        ROOT = d; break
MCP_SERVER_PATH = ROOT / "src" / "server.js"
NODE_BIN = "/opt/homebrew/bin/node"
SYMBOL, TIMEFRAME, MINTICK = "PEPPERSTONE:XAUUSD", "240", 0.01
GREEN, RED, BLUE = "#1a8917", "#cc0000", "#2962ff"
CHART_LOCK = ROOT / "my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION/.runtime_state/chart_op.lock"
RAW = V1 / "repro_recovery/raw_features_2020_2026.jsonl"
READINGS = V1 / "results/l2_bpt_episode_readings_276.jsonl"
OUTCOMES = V1 / "results/l2_bpt_uncapped_or_proxy_outcomes_276.csv"
CRIT32 = V1 / "results/l2_bpt_episode_reading_plot_list.csv"   # os 32 críticos
HORIZON_S = 40 * 4 * 3600


def price_to_ticks_offset(entry, level, mintick=MINTICK):
    return int(round(abs(level - entry) / mintick))


class MCPClient:
    def __init__(self): self.proc=None; self._id=0
    def start(self):
        self.proc=subprocess.Popen([NODE_BIN,str(MCP_SERVER_PATH)],stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
        r=self._raw("initialize",{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"plot-276","version":"1.0"}})
        if "error" in r: raise RuntimeError(f"MCP init: {r['error']}")
        self._notify("notifications/initialized",{})
    def stop(self):
        if self.proc:
            try: self.proc.stdin.close()
            except Exception: pass
            try: self.proc.terminate(); self.proc.wait(timeout=5)
            except Exception: self.proc.kill()
    def _notify(self,m,p):
        self.proc.stdin.write(json.dumps({"jsonrpc":"2.0","method":m,"params":p})+"\n"); self.proc.stdin.flush()
    def _raw(self,m,p,timeout=60):
        self._id+=1; rid=self._id
        self.proc.stdin.write(json.dumps({"jsonrpc":"2.0","id":rid,"method":m,"params":p})+"\n"); self.proc.stdin.flush()
        dl=time.monotonic()+timeout
        while time.monotonic()<dl:
            line=self.proc.stdout.readline()
            if not line: raise RuntimeError("MCP closed stdout")
            try:
                r=json.loads(line)
                if r.get("id")==rid: return r
            except json.JSONDecodeError: continue
        raise TimeoutError(f"MCP {m} timeout")
    def call(self,name,args=None,timeout=60):
        r=self._raw("tools/call",{"name":name,"arguments":args or {}},timeout=timeout)
        if "error" in r: return {"_error":r["error"]}
        c=r.get("result",{}).get("content",[])
        if c and c[0].get("type")=="text":
            try: return json.loads(c[0]["text"])
            except Exception: return {"_raw":c[0]["text"]}
        return r.get("result",{})


def fn(v):
    try: return float(v)
    except: return None


def build_trades():
    F=[json.loads(l) for l in open(RAW)]
    H=[r['high'] for r in F]; L=[r['low'] for r in F]; C=[r['close'] for r in F]; TS=[r['ts_epoch'] for r in F]
    ATR=[None]*len(F); trs=[]
    for i in range(1,len(F)):
        trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
        if i>=14: ATR[i]=sum(trs[i-14:i])/14
    O={int(r['bar_idx']):r for r in csv.DictReader(open(OUTCOMES))}
    crit={int(r['bar_idx']) for r in csv.DictReader(open(CRIT32))}
    dec={int(json.loads(l)['episode_id']):json.loads(l)['provisional_decision'] for l in open(READINGS)}
    eps=[b for b,d in dec.items() if d in ('TAKE','REVIEW')]   # NÃO plota SKIP
    trades=[]; nW=nL=nB=0
    for b in sorted(eps):
        atr=ATR[b]
        if atr is None or b not in O: continue
        entry=C[b]; stop=entry-1.0*atr; tgt=entry+2.7*atr
        realR=fn(O[b]['capped_realR'])
        if b in crit: color=BLUE; nB+=1
        elif realR is not None and realR>0: color=GREEN; nW+=1
        else: color=RED; nL+=1
        trades.append(dict(id=b,entry_price=round(entry,2),stop_price=round(stop,2),target_price=round(tgt,2),
            entry_time=TS[b],exit_time=TS[b]+HORIZON_S,color=color,realR=realR))
    return trades,nW,nL,nB


def main():
    trades,nW,nL,nB=build_trades()
    for t in trades:
        e,s,tg=t["entry_price"],t["stop_price"],t["target_price"]
        if not (e>s and tg>e) or price_to_ticks_offset(e,s)<=0 or price_to_ticks_offset(e,tg)<=0:
            print(f"HARD STOP: #{t['id']} inválido e={e} s={s} tg={tg}",file=sys.stderr); return 1
    print(f"trades válidos: {len(trades)} | verde(W)={nW} vermelho(L)={nL} azul(crit32)={nB} | aditivo")
    CHART_LOCK.parent.mkdir(parents=True,exist_ok=True)
    CHART_LOCK.write_text(f"plot_all276_winloss_blue pid={os.getpid()} {time.time()}\n")
    client=MCPClient(); client.start()
    try:
        st=client.call("chart_get_state")
        if st.get("symbol")!=SYMBOL or str(st.get("resolution"))!=TIMEFRAME:
            print(f"HARD STOP: chart {st.get('symbol')}/{st.get('resolution')} != {SYMBOL}/{TIMEFRAME}",file=sys.stderr); return 1
        print(f"chart OK: {st.get('symbol')}/{st.get('resolution')} | plotando {len(trades)}")
        ok_pos=ok_lbl=fail=0
        for k,t in enumerate(trades):
            Rd=t["entry_price"]-t["stop_price"]
            r1=client.call("draw_shape",{"shape":"long_position",
                "point":{"time":t["entry_time"],"price":t["entry_price"]},
                "point2":{"time":t["exit_time"],"price":t["target_price"]},
                "overrides":json.dumps({"stopLevel":price_to_ticks_offset(t["entry_price"],t["stop_price"]),
                    "profitLevel":price_to_ticks_offset(t["entry_price"],t["target_price"])})})
            ok_pos+=1 if r1.get("success") else 0; fail+=0 if r1.get("success") else 1
            if not r1.get("success"): print(f"  #{t['id']} pos FAIL: {r1}")
            r2=client.call("draw_shape",{"shape":"text",
                "point":{"time":t["entry_time"],"price":round(t["entry_price"]+0.5*Rd,2)},
                "text":f"#{t['id']}",
                "overrides":json.dumps({"color":t["color"],"bold":True,"fontsize":12})})
            ok_lbl+=1 if r2.get("success") else 0; fail+=0 if r2.get("success") else 1
            if not r2.get("success"): print(f"  #{t['id']} label FAIL: {r2}")
            if (k+1)%50==0: print(f"  [{k+1}/{len(trades)}] pos={ok_pos} lbl={ok_lbl} fail={fail}")
        dl=client.call("draw_list")
        n=len(dl.get("drawings") or dl.get("shapes") or []) if isinstance(dl,dict) else None
        print(json.dumps({"trades":len(trades),"long_position_ok":ok_pos,"label_ok":ok_lbl,
            "failures":fail,"expected_shapes":2*len(trades),"draw_list_total":n,
            "green_W":nW,"red_L":nL,"blue_crit":nB},indent=2))
    finally:
        client.stop()
        try: CHART_LOCK.unlink()
        except FileNotFoundError: pass
        print("chart_op.lock removido.")
    return 0


if __name__=="__main__":
    sys.exit(main())
