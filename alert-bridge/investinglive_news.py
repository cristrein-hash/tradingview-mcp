#!/usr/bin/env python3
"""Poller InvestingLive RSS (ex-ForexLive) — real-time de macro/Fed/ouro para o desafio de trade
(Cris 2026-07-16). Grátis, sem key. Parse RSS -> headlines recentes + flag de relevância p/ ouro
(gold/USD/Fed/rates/yields/risk). Robusto a erros de rede. Integrado na monitorização 5-min.
Uso: python3 investinglive_news.py [minutos]   |   from investinglive_news import recent_news"""
import sys, urllib.request, datetime as dt
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

FEED = "https://investinglive.com/feed/"
KW = ["gold", "xau", "dollar", "usd", "dxy", "fed", "fomc", "powell", "rate cut", "rate hike", "rates",
      "yield", "treasury", "bond", "inflation", "cpi", "ppi", "pce", "jobs", "payroll", "jobless",
      "claims", "retail sales", "gdp", "risk", "safe haven", "tariff", "war", "geopolit", "china",
      "boj", "ecb", "recession", "vix", "equit", "stock", "nikkei", "kospi", "sell-off", "selloff", "crash"]

def fetch(url=FEED, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 news-poller"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def recent_news(minutes=60):
    try:
        raw = fetch()
    except Exception as e:
        return {"ok": False, "error": f"fetch:{e}", "items": []}
    try:
        root = ET.fromstring(raw)
    except Exception as e:
        return {"ok": False, "error": f"parse:{e}", "items": []}
    now = dt.datetime.now(dt.timezone.utc); items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        pd = it.findtext("pubDate")
        try:
            when = parsedate_to_datetime(pd)
            if when.tzinfo is None: when = when.replace(tzinfo=dt.timezone.utc)
        except Exception:
            continue
        age = (now - when).total_seconds()/60
        if age < -5 or age > minutes: continue
        low = title.lower(); rel = [k for k in KW if k in low]
        items.append({"dt": when.strftime("%H:%M"), "age_min": round(age), "title": title, "rel": rel})
    items.sort(key=lambda x: x["age_min"])
    return {"ok": True, "n": len(items), "n_rel": sum(1 for x in items if x["rel"]), "items": items}

if __name__ == "__main__":
    m = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    r = recent_news(m)
    if not r["ok"]:
        print("ERRO:", r["error"]); sys.exit(1)
    print(f"InvestingLive — {r['n']} headlines nos ultimos {m} min ({r['n_rel']} relevantes ao ouro):")
    for it in r["items"]:
        flag = "🔴" if it["rel"] else "  "
        tail = f"  [{','.join(it['rel'][:3])}]" if it["rel"] else ""
        print(f"  {flag} {it['dt']}Z (-{it['age_min']}m) {it['title'][:92]}{tail}")
