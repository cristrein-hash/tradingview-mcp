#!/usr/bin/env python3
"""COLETOR NEWS DE MERCADO — Alpha Vantage NEWS_SENTIMENT (key grátis ALPHA_VANTAGE_API_KEY no .env).
Complementa o Fed RSS com news AMPLA (mercado/geopolítica/economia) ticker/source-tagged + sentiment.
Abastece geopolitical-impact (a única skill que faltava cobertura ampla) + news-validation/dedup/risk.
⚠️ RATE-LIMIT free 25/dia: só busca se a última coleta foi há >90min (-> ~16/dia). Determinístico, py3.9.
Saída: snapshots/market_news.json. Sem key -> no-op honesto (Fed RSS segue cobrindo o essencial)."""
import json,subprocess,sys,datetime as dt
from pathlib import Path
H=Path(__file__).parent.parent; SNAP=H/"snapshots"; SNAP.mkdir(exist_ok=True)
sys.path.insert(0,str(H/"runtime"));
import os
try: from load_env import load_env; load_env()
except Exception: pass
NOWT=int(dt.datetime.now(dt.timezone.utc).timestamp())
KEY=os.environ.get("ALPHA_VANTAGE_API_KEY")
OUT=SNAP/"market_news.json"
RATE_S=5400  # 90 min entre coletas (respeita 25/dia do free)
def recent_enough():
    if not OUT.exists(): return False
    try: return (NOWT-json.loads(OUT.read_text()).get("_meta",{}).get("built_ts",0))<RATE_S
    except Exception: return False
def get(u):
    return subprocess.run(["curl","-sS","--http1.1","--max-time","30",u],capture_output=True,text=True).stdout
def main():
    if not KEY:
        print("ALPHA_VANTAGE_API_KEY ausente -> no-op (Fed RSS cobre o essencial)."); return
    if recent_enough():
        print("market_news fresco (<90min) -> pula (rate-limit free 25/dia)."); return
    # topics relevantes ao ouro: macro, mercados, finanças, fusões (geopolítica entra via manchetes)
    url=f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&topics=economy_macro,financial_markets,economy_monetary&sort=LATEST&limit=50&apikey={KEY}"
    d=json.loads(get(url) or "{}")
    if "feed" not in d:
        print("AV sem feed (limite diário? msg:",json.dumps(d)[:120],") -> mantém último snapshot."); return
    items=[]
    for n in d["feed"]:
        ts=None
        try: ts=int(dt.datetime.strptime(n["time_published"],"%Y%m%dT%H%M%S").replace(tzinfo=dt.timezone.utc).timestamp())
        except Exception: pass
        items.append({"title":n.get("title"),"source":n.get("source"),"url":n.get("url"),
                      "published_ts":ts,"age_h":round((NOWT-ts)/3600,1) if ts else None,
                      "sentiment":n.get("overall_sentiment_label"),"sentiment_score":n.get("overall_sentiment_score"),
                      "topics":[t.get("topic") for t in n.get("topics",[])],"layer":"A","source_tier":"med"})
    items=[i for i in items if i["published_ts"]]; items.sort(key=lambda x:x["published_ts"],reverse=True)
    recent=[i for i in items if i["age_h"] is not None and i["age_h"]<=72]
    state={"_meta":{"built_ts":NOWT,"source":"Alpha Vantage NEWS_SENTIMENT","rate_limit":"free 25/dia (>90min entre coletas)"},
           "items":items[:50],"recent_le72h":recent[:30],"n":len(items)}
    OUT.write_text(json.dumps(state,indent=1,ensure_ascii=False))
    print(f"Alpha Vantage: {len(items)} news | recentes ≤72h: {len(recent)}")
    for i in recent[:5]: print(f"  [{i['sentiment']}] {i['age_h']}h | {i['source']} | {i['title'][:60]}")
    print(f"-> {OUT}")
if __name__=="__main__": main()
