#!/usr/bin/env python3
"""COLETOR NEWS RÁPIDA — InvestingLive RSS (ex-ForexLive, KEYLESS, feed público). News lane rápida p/
produção XAU 4H+15M: uma headline move o ouro intra-barra (barra 15M=15min), o ciclo macro de 30min é
lento demais p/ isto. Corre em LaunchAgent SEPARADA (~4min). Determinístico, sem LLM, py3.9. Reaproveita
a lógica de alert-bridge/investinglive_news.py + adiciona guid/link p/ dedup estável, urgency/session/gate.
Saída: snapshots/investinglive_news.json (escrita ATÓMICA os.replace; single-writer deste ficheiro).
Falha de rede/parse -> no-op honesto: mantém snapshot anterior, marca fetch_ok=false. NUNCA lança."""
import json, os, sys, hashlib, urllib.request, urllib.error, datetime as dt
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

H = Path(__file__).parent.parent; SNAP = H / "snapshots"; SNAP.mkdir(exist_ok=True)
OUT = SNAP / "investinglive_news.json"
FF = SNAP / "ff_calendar.json"
NOWT = int(dt.datetime.now(dt.timezone.utc).timestamp())

FEED = "https://investinglive.com/feed/"
# relevância ampla ao ouro (espelha investinglive_news.py)
KW = ["gold", "xau", "dollar", "usd", "dxy", "fed", "fomc", "powell", "rate cut", "rate hike", "rates",
      "yield", "treasury", "bond", "inflation", "cpi", "ppi", "pce", "jobs", "payroll", "jobless",
      "claims", "retail sales", "gdp", "risk", "safe haven", "tariff", "war", "geopolit", "china",
      "boj", "ecb", "recession", "vix", "equit", "stock", "nikkei", "kospi", "sell-off", "selloff", "crash"]
# alto impacto (move o ouro forte / decisões macro) -> urgency high
HI = ["fomc", "powell", "rate cut", "rate hike", "fed ", "cpi", "core pce", "pce", "nfp", "payroll",
      "jobless", "tariff", "war", "fomc statement", "rate decision", "inflation"]
WINDOW_MIN = 60      # janela de relevância dos items
KEEP_N = 15          # headlines relevantes guardadas
CADENCE_S = 240


_HDRS = {"User-Agent": "Mozilla/5.0 (Macintosh) ef-news-poller",
         "Accept": "application/rss+xml, application/xml, text/xml, */*"}


def fetch(url=FEED, timeout=15):
    """Robusto ao 301 INTERMITENTE do investinglive (redirect-loop /feed <-> /feed/ que o urllib às vezes
    reporta como HTTPError; o curl dá 200 = conteúdo alcançável). Retry 3× + variante de trailing-slash +
    seguir Location manualmente. Se tudo falhar, levanta (o caller mantém o snapshot anterior — graceful)."""
    import time as _t
    variants = [url, url.rstrip("/") if url.endswith("/") else url + "/"]
    last = None
    for attempt in range(3):
        for u in variants:
            try:
                req = urllib.request.Request(u, headers=_HDRS)
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    return r.read()
            except urllib.error.HTTPError as e:
                last = e
                if e.code in (301, 302, 303, 307, 308):
                    loc = e.headers.get("Location") if e.headers else None
                    if loc and loc not in variants:
                        try:
                            with urllib.request.urlopen(urllib.request.Request(loc, headers=_HDRS), timeout=timeout) as r2:
                                return r2.read()
                        except Exception as e2:
                            last = e2
            except Exception as e:
                last = e
        _t.sleep(1.5 * (attempt + 1))
    raise last if last else RuntimeError("investinglive fetch falhou sem exceção")


def txt(it, *tags):
    for t in tags:
        v = it.findtext(t)
        if v and v.strip():
            return v.strip()
    return None


def urgency_of(low_title, relevant):
    if any(k in low_title for k in HI):
        return "high"
    return "med" if relevant else "low"


def session_utc(now):
    """Bucket de sessão pelo relógio UTC (sem DST). Ver memory reference_session_volatility_windows."""
    h = now.hour + now.minute / 60.0
    if 0 <= h < 1:      return "asia"
    if 1 <= h < 11:     return "dead_zone"
    if 11 <= h < 13.5:  return "london_strong"
    if 13.5 <= h < 14.5: return "ny_open"
    if 14.5 <= h < 17.5: return "ny"
    if 17.5 <= h < 19.5: return "ny_late"
    return "other"


def ff_event_le_min():
    """Menor tempo (min) até evento FF de alto impacto iminente (0..30min), senão None."""
    try:
        d = json.loads(FF.read_text())
    except Exception:
        return None
    best = None
    for e in d.get("events", []):
        if e.get("impact") != "HIGH":
            continue
        hu = e.get("hours_until")
        if hu is None:
            continue
        if 0 <= hu <= 0.5:
            m = round(hu * 60)
            best = m if best is None else min(best, m)
    return best


def prev_snapshot():
    try:
        return json.loads(OUT.read_text())
    except Exception:
        return {}


def atomic_write(path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    os.replace(tmp, path)


def main():
    now = dt.datetime.now(dt.timezone.utc)
    try:
        raw = fetch()
        root = ET.fromstring(raw)
    except Exception as e:
        # no-op honesto: mantém snapshot anterior, marca falha
        prev = prev_snapshot()
        prev.setdefault("_meta", {})["built_ts"] = NOWT
        prev["fetch_ok"] = False
        prev["error"] = f"{type(e).__name__}:{str(e)[:80]}"
        last = prev.get("fetch_ts")
        prev["fetch_age_s"] = (NOWT - last) if last else None
        atomic_write(OUT, prev)
        print(f"InvestingLive fetch FALHOU ({prev['error']}) -> mantém snapshot anterior (fetch_age_s={prev.get('fetch_age_s')})")
        return

    items = []
    for it in root.iter("item"):
        title = txt(it, "title")
        if not title:
            continue
        pd = it.findtext("pubDate")
        try:
            when = parsedate_to_datetime(pd)
            if when.tzinfo is None:
                when = when.replace(tzinfo=dt.timezone.utc)
        except Exception:
            continue
        ts = int(when.timestamp())
        age_min = round((NOWT - ts) / 60)
        if age_min < -5 or age_min > WINDOW_MIN:
            continue
        key = txt(it, "guid", "link") or title
        low = title.lower()
        rel = [k for k in KW if k in low]
        relevant = bool(rel)
        items.append({
            "id": hashlib.md5(key.encode("utf-8")).hexdigest(),
            "ts": ts, "dt": when.strftime("%H:%M"), "age_min": age_min,
            "title": title[:200], "url": txt(it, "link"),
            "keywords": rel[:5], "relevant": relevant,
            "urgency": urgency_of(low, relevant),
        })
    items.sort(key=lambda x: x["ts"], reverse=True)
    relevant_items = [i for i in items if i["relevant"]]

    high_now = any(i["urgency"] == "high" and i["age_min"] <= 15 for i in items)
    urg = "high" if high_now else ("med" if any(i["urgency"] == "med" for i in relevant_items) else ("low" if relevant_items else "none"))
    sess = session_utc(now)
    ff_le = ff_event_le_min()
    escalate = bool(high_now and (sess in ("london_strong", "ny_open", "ny") or ff_le is not None))
    top = next((i for i in items if i["urgency"] == "high"), (relevant_items[0] if relevant_items else None))

    state = {
        "_meta": {"built_ts": NOWT, "source": FEED, "cadence_s": CADENCE_S,
                  "purpose": "news lane rápida XAU 4H+15M"},
        "fetch_ok": True, "fetch_ts": NOWT, "fetch_age_s": 0, "error": None,
        "window_min": WINDOW_MIN,
        "n_total": len(items), "n_relevant": len(relevant_items),
        "high_impact_now": high_now, "urgency": urg,
        "items": relevant_items[:KEEP_N],
        "gate": {
            "high_impact_headline": high_now,
            "escalate": escalate,
            "reason": (f"kw={top['keywords']}; age={top['age_min']}m" if top else "sem headline relevante"),
            "since_ts": (top["ts"] if top and high_now else None),
            "session": sess,
            "ff_event_le_min": ff_le,
        },
    }
    atomic_write(OUT, state)
    print(f"InvestingLive: {len(items)} na janela {WINDOW_MIN}min | relevantes {len(relevant_items)} | "
          f"high_now={high_now} urg={urg} sess={sess} ff_le={ff_le} escalate={escalate}")
    for i in relevant_items[:5]:
        print(f"  [{i['urgency']}] {i['dt']}Z (-{i['age_min']}m) {i['title'][:70]} {i['keywords']}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
