#!/usr/bin/env python3
"""COLETOR CALENDÁRIO — ForexFactory weekly JSON feed (FairEconomy, oficial, KEYLESS, NÃO scraping).
Substitui o gerador determinístico 1ª-sexta (bug de shift de feriado) + o fetch manual de consenso +
a captura de actual. Traz previous + forecast(consenso) + actual num só feed, com a data REAL (já com
shift de feriado). Normaliza p/ o schema de eventos da Camada A e calcula direção NFP (surpresa->ouro).
Determinístico, py3.9. Saída: snapshots/ff_calendar.json. Fonte canônica (whitelist), só leitura."""
import json,sys,subprocess,datetime as dt,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from _resilient import write_resilient   # keep-last-good: fetch vazio NÃO apaga o calendário (countdown crítico)
H=Path(__file__).parent.parent; SNAP=H/"snapshots"; SNAP.mkdir(exist_ok=True)
URL="https://nfs.faireconomy.media/ff_calendar_thisweek.json"
NOWT=int(dt.datetime.now(dt.timezone.utc).timestamp())
# mapa título FF -> {canonical, layer, driver, hi} (alto impacto USD que move o ouro)
CANON={
 "Non-Farm Employment Change":("Nonfarm Payrolls (NFP)","A","USD->GOLD",True),
 "ADP Non-Farm Employment Change":("ADP Private Payrolls","A","USD/labor preview",False),
 "Unemployment Claims":("Initial Jobless Claims","A","USD/labor",False),
 "Average Hourly Earnings m/m":("Average Hourly Earnings","A","USD/wages",False),
 "Unemployment Rate":("Unemployment Rate","A","USD/labor",False),
 "CPI m/m":("CPI","A","inflação->GOLD",True),"Core CPI m/m":("Core CPI","A","inflação->GOLD",True),
 "CPI y/y":("CPI y/y","A","inflação->GOLD",True),
 "PPI m/m":("PPI","A","inflação",False),"Core PCE Price Index m/m":("Core PCE","A","inflação Fed-pref",True),
 "Federal Funds Rate":("FOMC Rate Decision","A","Fed->USD->GOLD",True),
 "FOMC Statement":("FOMC Statement","A","Fed->USD->GOLD",True),
 "FOMC Press Conference":("FOMC Press Conf","A","Fed tom",True),
 "FOMC Meeting Minutes":("FOMC Minutes","A","Fed tom",False),
 "ISM Manufacturing PMI":("ISM Manufacturing","A","atividade",False),
 "ISM Services PMI":("ISM Services","A","atividade",False),
 "Retail Sales m/m":("Retail Sales","A","consumo/USD",False),
 "Advance GDP q/q":("GDP (Advance)","A","crescimento",False),
}
def num(s):
    if s is None or s=="": return None
    m=re.search(r'-?\d+\.?\d*',str(s).replace(",",""))
    return float(m.group()) if m else None
def fetch():
    r=subprocess.run(["curl","-sS","--http1.1","--max-time","30",URL],capture_output=True,text=True)
    return json.loads(r.stdout) if r.stdout.strip().startswith("[") else []
def nfp_direction(prev,fc,act):
    c=num(fc)
    if c is None: return {"bias":"pending","rule":"surpresa=actual-consenso; jobs fortes(>0)->USD↑->ouro bearish","awaiting":"consenso/actual"}
    a=num(act)
    if a is None: return {"bias":"pending","consensus_k":c,"previous_k":num(prev),"rule":"actual>consenso=ouro bearish; <consenso=bullish","awaiting":"actual no release"}
    s=a-c
    return {"bias":"bearish" if s>0 else ("bullish" if s<0 else "neutral"),"surprise_k":round(s,1),"actual_k":a,"consensus_k":c,
            "rule":"NFP forte(actual>consenso)->USD↑->ouro↓","resolved_ts":NOWT}
def main():
    raw=fetch(); events=[]
    for e in raw:
        if e.get("country")!="USD": continue
        title=e.get("title",""); imp=e.get("impact","")
        canon=CANON.get(title)
        if not canon and imp not in("High",): continue  # só USD high-impact + os mapeados
        name,layer,driver,hi=canon if canon else (title,"A","USD",imp=="High")
        try: ts=int(dt.datetime.fromisoformat(e["date"]).timestamp())
        except Exception: continue
        ev={"event":name,"ff_title":title,"date":e["date"][:10],"release_ts":ts,
            "impact":"HIGH" if (hi or imp=="High") else "med","layer":layer,"driver":driver,
            "previous":e.get("previous"),"consensus":e.get("forecast"),"actual":e.get("actual"),
            "source":"ForexFactory/FairEconomy JSON (keyless)"}
        if name.startswith("Nonfarm"):
            d=nfp_direction(e.get("previous"),e.get("forecast"),e.get("actual"))
            ev["consensus_k"]=num(e.get("forecast")); ev["previous_k"]=num(e.get("previous")); ev["actual_k"]=num(e.get("actual"))
            ev["direction"]=d
        events.append(ev)
    events.sort(key=lambda x:x["release_ts"])
    for ev in events: ev["hours_until"]=round((ev["release_ts"]-NOWT)/3600,1)
    state={"_meta":{"built_ts":NOWT,"source":URL,"purpose":"Camada A calendário keyless (substitui gerador+consenso manual+captura)"},
           "events":events,"imminent_le96h":[e for e in events if 0<=e["hours_until"]<=96]}
    # SAUDÁVEL = o feed devolveu linhas cruas (raw). Fetch vazio/falhado (o que disparou o auditor 30/07:
    # calendário sem eventos) NÃO deve apagar o calendário bom — o countdown de eventos (FOMC/GDP/PCE) é
    # crítico. Recompute-mos hours_until na leitura, por isso servir o calendário anterior é seguro.
    healthy = bool(raw)
    _w, served_stale = write_resilient(SNAP/"ff_calendar.json", state, healthy)
    if served_stale:
        print(f"ForexFactory: FETCH VAZIO -> mantido calendário anterior (falhas seguidas={_w.get('_meta',{}).get('consecutive_fail')}); countdown preservado")
        return
    print(f"ForexFactory: {len(events)} eventos USD (high+mapeados) | imminent ≤96h: {len(state['imminent_le96h'])}")
    for e in state["imminent_le96h"]:
        ex=f" | cons={e['consensus']} prev={e['previous']} act={e['actual']} dir={e.get('direction',{}).get('bias')}" if e.get('consensus_k') is not None else f" | cons={e['consensus']}"
        print(f"  [{e['impact']}] {e['event']} — {e['date']} (em {e['hours_until']}h){ex}")
    print(f"-> {SNAP/'ff_calendar.json'}")
if __name__=="__main__": main()
