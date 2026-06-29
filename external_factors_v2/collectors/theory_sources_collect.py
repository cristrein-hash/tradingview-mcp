#!/usr/bin/env python3
"""COLETOR DE TEORIAS (núcleo humano credível, FREE + NÃO-DEALER, keyless RSS).
Puxa fontes independentes de alta credibilidade -> grava (1) theory_feed.json (recentes p/ grounding) e
(2) theory_ledger.jsonl (APPEND-ONLY, dedup) = base do FORWARD-SCORING (a realidade dá nota às teorias ao longo
da produção). Cada item vira uma ENTRADA DE TEORIA com campos de claim/horizonte/outcome a serem preenchidos
depois (extração de claim = passo LLM Tier-2; scoring = scorer forward). Determinístico, py3.9.
⚠️ DEALERS DESCARTADOS (Kitco/BullionVault/Heraeus-refiner/Sprott/MoneyMetals/Schiff/Maloney). Só independentes."""
import json,subprocess,re,hashlib,datetime as dt
from email.utils import parsedate_to_datetime
from pathlib import Path
H=Path(__file__).parent.parent; SNAP=H/"snapshots"; SNAP.mkdir(exist_ok=True)
NOWT=int(dt.datetime.now(dt.timezone.utc).timestamp())
LEDGER=SNAP/"theory_ledger.jsonl"
# fontes FREE + NÃO-DEALER (extensível: YouTube RSS de CPM/Bianco = adicionar {url youtube/feeds/videos.xml?channel_id=...})
SOURCES=[
 {"id":"GOLD_OBSERVER","name":"The Gold Observer (Jan Nieuwenhuijs)","url":"https://www.thegoldobserver.com/feed","tier":"T1","bias":"independente; gold-bull-lean","focus":"CB flows / dados primários / COMEX-LBMA"},
 {"id":"LYN_ALDEN","name":"Lyn Alden","url":"https://www.lynalden.com/feed/","tier":"T1","bias":"independente; even-handed","focus":"real-rates / fiscal dominance / liquidez"},
 {"id":"INGWT","name":"In Gold We Trust (Incrementum)","url":"https://ingoldwetrust.report/feed/","tier":"T1","bias":"fund; perma-bull mandato","focus":"valuation / real-rates / monetário"},
 {"id":"MACROVOICES","name":"MacroVoices","url":"https://feeds.feedburner.com/MacroVoices","tier":"T1","bias":"independente; neutro","focus":"macro institucional cross-asset"},
 {"id":"WGC","name":"World Gold Council (Goldhub)","url":"https://www.gold.org/rss.xml","tier":"T3","bias":"miner-funded (dado>narrativa)","focus":"CB demand / ETF flows / supply-demand"},
 {"id":"PETER_BRANDT","name":"Peter Brandt (Factor)","url":"https://www.peterlbrandt.com/feed/","tier":"T4","bias":"independente; técnico (estrutura, não alvos)","focus":"classical charting / risk / cross-market (ouro incluído)"},
 {"id":"TAVI_COSTA","name":"Tavi Costa (Crescat)","url":"https://tavicosta.substack.com/feed","tier":"T5","bias":"fund; fala o próprio book (perma-bull miners)","focus":"macro / charts / juniors"},
]
def curl(u):
    return subprocess.run(["curl","-sSL","--http1.1","--max-time","25","-A","Mozilla/5.0",u],capture_output=True,text=True).stdout
def clean(s):
    s=re.sub(r"<!\[CDATA\[(.*?)\]\]>",r"\1",s,flags=re.S)
    s=re.sub(r"<[^>]+>"," ",s)
    return re.sub(r"\s+"," ",s).strip()
def parse_items(xml):
    out=[]
    for blk in re.findall(r"<item[ >](.*?)</item>",xml,re.S):
        def g(tag):
            m=re.search(rf"<{tag}[^>]*>(.*?)</{tag}>",blk,re.S)
            return clean(m.group(1)) if m else ""
        title=g("title"); link=g("link") or (re.search(r"<link[^>]*>(.*?)</link>",blk,re.S).group(1).strip() if re.search(r"<link",blk) else "")
        out.append({"title":title,"link":link,"pub":g("pubDate"),"author":g("dc:creator") or g("author"),"desc":g("description")})
    return out
def to_ts(s):
    try: return int(parsedate_to_datetime(s).timestamp())
    except Exception: return None
def existing_ids():
    ids=set()
    if LEDGER.exists():
        for ln in LEDGER.read_text().splitlines():
            try: ids.add(json.loads(ln)["theory_id"])
            except Exception: pass
    return ids
def main():
    seen=existing_ids(); new=[]; recent=[]
    for src in SOURCES:
        items=parse_items(curl(src["url"]))[:12]
        for it in items:
            if not it["title"]: continue
            tid=hashlib.md5((src["id"]+it["title"]).encode()).hexdigest()[:12]
            pts=to_ts(it["pub"])
            entry={"theory_id":tid,"source_id":src["id"],"source_name":src["name"],"tier":src["tier"],
                   "bias":src["bias"],"focus":src["focus"],"title":it["title"],"url":it["link"],
                   "author":it["author"],"published_ts":pts,"collected_ts":NOWT,
                   "summary":it["desc"][:500],
                   # --- campos de FORWARD-SCORING (preenchidos depois: claim=LLM Tier-2, outcome=scorer) ---
                   "claim":None,"predicted_gold_dir":None,"horizon_days":None,
                   "scored":False,"outcome":None,"outcome_ts":None}
            if pts and (NOWT-pts)<=45*86400:
                recent.append({k:entry[k] for k in ("source_id","source_name","tier","bias","title","url","published_ts","summary")})
            if tid not in seen:
                new.append(entry); seen.add(tid)
    # append-only no ledger
    if new:
        with open(LEDGER,"a") as fh:
            for e in new: fh.write(json.dumps(e,ensure_ascii=False)+"\n")
    recent.sort(key=lambda x:x["published_ts"] or 0,reverse=True)
    feed={"_meta":{"built_ts":NOWT,"sources":[s["id"] for s in SOURCES],"ledger":str(LEDGER.name),
           "purpose":"núcleo humano credível (não-dealer) p/ análise comparativa realtime vs EF técnico; base forward-scoring"},
          "recent":recent[:25],"ledger_total":len(seen),"new_this_cycle":len(new)}
    (SNAP/"theory_feed.json").write_text(json.dumps(feed,indent=1,ensure_ascii=False))
    print(f"TEORIAS (núcleo não-dealer): {len(recent)} recentes ≤45d | novas no ledger: {len(new)} | ledger total: {len(seen)}")
    for r in recent[:6]:
        age=round((NOWT-(r['published_ts'] or NOWT))/86400,1)
        print(f"  [{r['source_id']}] {age}d | {r['title'][:66]}")
    print(f"-> {SNAP/'theory_feed.json'} + {LEDGER.name}")
if __name__=="__main__": main()
