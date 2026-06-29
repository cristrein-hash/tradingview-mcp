#!/usr/bin/env python3
"""COLETOR OURO (fontes canônicas específicas — Cris marcou ESSENCIAIS).
- CME/COMEX preço: Gold Futures (FMP /stable/quote?symbol=GCUSD) — funciona no FMP free (XAUUSD/GLD são premium).
- CME/COMEX posicionamento: COT via CFTC public reporting (Socrata, keyless) — non-commercial net = managed money
  proxy (smart money, Camada B lenta do Cris).
- LBMA fixing: FRED descontinuou as séries (GOLDPMGBD228NLBM retorna HTML); preço LBMA-equiv = GCUSD futures.
- WGC (World Gold Council): demanda/ETF/central-bank = relatórios (sem API free) -> context_on_demand (LLM lê).
Determinístico, py3.9, degradação graciosa. Saída: snapshots/gold_data.json. Abastece gold-driver-analyzer + risk/macro-regime."""
import json,subprocess,sys,datetime as dt,urllib.parse
from pathlib import Path
H=Path(__file__).parent.parent; SNAP=H/"snapshots"; SNAP.mkdir(exist_ok=True)
sys.path.insert(0,str(H/"runtime"));
import os
try: from load_env import load_env; load_env()
except Exception: pass
NOWT=int(dt.datetime.now(dt.timezone.utc).timestamp())
FMP=os.environ.get("FMP_API_KEY")
def curl(url):
    return subprocess.run(["curl","-sS","--http1.1","--max-time","45",url],capture_output=True,text=True).stdout
def gold_price():
    if not FMP: return {"error":"FMP_API_KEY ausente; preço de ouro vem do trading system (RAW/TradingView)"}
    raw=curl(f"https://financialmodelingprep.com/stable/quote?symbol=GCUSD&apikey={FMP}")
    try:
        d=json.loads(raw)
        if isinstance(d,list) and d:
            q=d[0]
            return {"symbol":"GCUSD","name":q.get("name"),"price_usd":q.get("price"),
                    "change":q.get("change"),"change_pct":q.get("changePercentage"),"volume":q.get("volume"),
                    "day_low":q.get("dayLow"),"day_high":q.get("dayHigh"),"year_high":q.get("yearHigh"),"year_low":q.get("yearLow"),
                    "source":"CME/COMEX Gold Futures via FMP /stable (key grátis)"}
        return {"error":f"FMP quote inesperado: {str(d)[:120]}"}
    except Exception:
        return {"error":f"FMP não-JSON: {raw[:120]}"}
def cot_gold():
    where=urllib.parse.quote("upper(market_and_exchange_names) like '%GOLD%'")
    order=urllib.parse.quote("report_date_as_yyyy_mm_dd")
    url=("https://publicreporting.cftc.gov/resource/6dca-aqww.json?"
         f"$where={where}&$order={order}+DESC&$limit=15")
    raw=curl(url)
    try:
        d=json.loads(raw or "[]")
        if not isinstance(d,list): return {"error":f"CFTC resposta: {str(d)[:120]}"}
    except Exception:
        return {"error":f"CFTC não-JSON: {raw[:120]}"}
    row=next((r for r in d if "GOLD" in r.get("market_and_exchange_names","") and "COMEX" in r.get("market_and_exchange_names","")), d[0] if d else None)
    if not row: return {"error":"COT sem dados de ouro"}
    def n(k):
        try: return int(float(row.get(k)))
        except: return None
    nl=n("noncomm_positions_long_all"); ns=n("noncomm_positions_short_all")
    net=(nl-ns) if (nl is not None and ns is not None) else None
    return {"market":row.get("market_and_exchange_names"),"report_date":row.get("report_date_as_yyyy_mm_dd","")[:10],
            "noncomm_long":nl,"noncomm_short":ns,"noncomm_net":net,
            "noncomm_net_read":("net_long (managed money comprado)" if (net or 0)>0 else "net_short (managed money vendido)") if net is not None else None,
            "comm_long":n("comm_positions_long_all"),"comm_short":n("comm_positions_short_all"),
            "source":"CFTC COT (keyless) — non-commercial = managed money proxy (smart money)"}
HIST=SNAP/"gold_price_history.jsonl"
def append_history(price):
    """log diário de preço GCUSD (base do forward-scoring de teorias). dedup por dia."""
    if price is None: return
    today=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    if HIST.exists():
        lines=HIST.read_text().splitlines()
        if lines:
            try:
                if json.loads(lines[-1]).get("date")==today: return  # já tem hoje
            except Exception: pass
    with open(HIST,"a") as fh: fh.write(json.dumps({"ts":NOWT,"date":today,"price":price})+"\n")
def backfill_history():
    """seed histórico EOD via FMP (best-effort; se gated, segue forward-only)."""
    if HIST.exists() and HIST.read_text().strip(): return
    if not FMP: return
    raw=curl(f"https://financialmodelingprep.com/stable/historical-price-eod/light?symbol=GCUSD&apikey={FMP}")
    try:
        d=json.loads(raw)
        rows=d if isinstance(d,list) else d.get("historical",[])
        if not rows: print("  (backfill FMP historical gated/vazio -> forward-only)"); return
        seen=set(); out=[]
        for r in rows:
            dd=str(r.get("date",""))[:10]; px=r.get("price") or r.get("close")
            if dd and px and dd not in seen:
                seen.add(dd); out.append({"ts":int(dt.datetime.strptime(dd,"%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp()),"date":dd,"price":px})
        out.sort(key=lambda x:x["date"])
        with open(HIST,"w") as fh:
            for r in out: fh.write(json.dumps(r)+"\n")
        print(f"  backfill FMP historical: {len(out)} dias de GCUSD")
    except Exception: print("  (backfill FMP historical falhou -> forward-only)")
def main():
    backfill_history()
    gold={"_meta":{"built_ts":NOWT,"note":"fontes canônicas de ouro: CME/COMEX preço(FMP GCUSD)+posicionamento(CFTC COT). LBMA fixing descontinuado no FRED. WGC=context_on_demand."},
          "price_comex":gold_price(),"cot_comex":cot_gold(),
          "wgc":{"status":"context_on_demand","note":"World Gold Council: demanda/ETF/central-bank-buying via relatórios; agente lê sob demanda (sem API free)"},
          "lbma":{"status":"price_via_comex_futures","note":"LBMA fixing descontinuado no FRED (HTML); benchmark = GCUSD futures acima"}}
    p=gold["price_comex"]; ct=gold["cot_comex"]
    append_history(p.get("price_usd") if isinstance(p,dict) else None)
    (SNAP/"gold_data.json").write_text(json.dumps(gold,indent=1,ensure_ascii=False))
    print("OURO (fontes canônicas):")
    print(f"  CME/COMEX preço: {p.get('price_usd')} USD ({p.get('change_pct')}%) vol={p.get('volume')}" if "price_usd" in p else f"  preço: {p.get('error')}")
    print(f"  CME/COMEX COT: net non-comm={ct.get('noncomm_net')} -> {ct.get('noncomm_net_read')} (report {ct.get('report_date')})" if "noncomm_net" in ct else f"  COT: {ct.get('error')}")
    print(f"  WGC: context_on_demand | LBMA: via GCUSD futures (FRED descontinuou fixing)")
    print(f"-> {SNAP/'gold_data.json'}")
if __name__=="__main__": main()
