#!/usr/bin/env python3
"""COLETOR NEWS/FED — feeds RSS OFICIAIS do Federal Reserve (press releases + speeches), KEYLESS, NÃO scraping.
Abastece as skills Tier-2 de texto hoje dormentes (fed-tone-interpreter, news-validation, news-deduplication,
source-reliability, geopolitical-impact) com a fonte #1 de tom do ouro. Mesmo padrão do ForexFactory: fonte
oficial via feed limpo > MCP scraper. Determinístico, py3.9. Saída: snapshots/news_feed.json.
Keys (Alpha Vantage) só adicionariam news de MERCADO mais ampla — opcional. Fed/oficial = o driver validado."""
import json,subprocess,re,datetime as dt
from email.utils import parsedate_to_datetime
from pathlib import Path
H=Path(__file__).parent.parent; SNAP=H/"snapshots"; SNAP.mkdir(exist_ok=True)
NOWT=int(dt.datetime.now(dt.timezone.utc).timestamp())
FEEDS=[
 ("Federal Reserve","press","https://www.federalreserve.gov/feeds/press_all.xml","A"),
 ("Federal Reserve","speech","https://www.federalreserve.gov/feeds/speeches.xml","B"),
]
def fetch(url):
    r=subprocess.run(["curl","-sS","--http1.1","--max-time","25",url],capture_output=True,text=True)
    return r.stdout or ""
def items_from(xml):
    out=[]
    for blk in re.findall(r"<item>(.*?)</item>",xml,re.S):
        def g(tag):
            m=re.search(rf"<{tag}>(.*?)</{tag}>",blk,re.S)
            v=m.group(1).strip() if m else ""
            return re.sub(r"<!\[CDATA\[(.*?)\]\]>",r"\1",v,flags=re.S).strip()
        out.append((g("title"),g("link"),g("pubDate"),g("description")))
    return out
def to_ts(pub):
    try: return int(parsedate_to_datetime(pub).timestamp())
    except Exception: return None
def main():
    news=[]; seen=set()
    for src,kind,url,layer in FEEDS:
        for title,link,pub,desc in items_from(fetch(url)):
            if not title: continue
            key=(title.lower()[:80])
            if key in seen: continue   # dedup simples por título (news-deduplication faz o resto)
            seen.add(key)
            ts=to_ts(pub)
            news.append({"title":title,"source":src,"source_tier":"high","kind":kind,"url":link,
                         "published_ts":ts,"age_h":round((NOWT-ts)/3600,1) if ts else None,
                         "layer":layer,"driver":"Fed tom/política -> USD -> ouro"})
    news=[n for n in news if n["published_ts"]]
    news.sort(key=lambda n:n["published_ts"],reverse=True)
    recent=[n for n in news if n["age_h"] is not None and n["age_h"]<=168]  # 7 dias
    state={"_meta":{"built_ts":NOWT,"sources":[f[2] for f in FEEDS],
            "purpose":"abastece skills Tier-2 de texto (fed-tone/news/source-reliability), keyless"},
           "items":news[:60],"recent_le7d":recent[:30],"n_total":len(news)}
    (SNAP/"news_feed.json").write_text(json.dumps(state,indent=1,ensure_ascii=False))
    print(f"Fed RSS: {len(news)} itens ({sum(1 for n in news if n['kind']=='press')} press / {sum(1 for n in news if n['kind']=='speech')} speeches) | recentes ≤7d: {len(recent)}")
    for n in recent[:6]: print(f"  [{n['kind']}] {n['age_h']}h | {n['title'][:78]}")
    print(f"-> {SNAP/'news_feed.json'}")
if __name__=="__main__": main()
