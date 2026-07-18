#!/usr/bin/env python3
"""COLETOR FINNHUB NEWS (Cris 2026-07-18) — lane de contexto FRESCA (Reuters-tier, mais fresca que GDELT).
REST /news?category=general (free, 60/min). Filtra por keywords que movem XAU (guerra/Fed/petróleo/dólar),
pontua urgência, escreve snapshots/finnhub_news.json no shape do news_gate. Contexto (o *porquê*), não gatilho
— o gatilho é o preço (price_shock). Determinístico, py3.9, graceful. NUNCA loga a key."""
import json, os, sys, hashlib, subprocess, datetime as dt
from pathlib import Path
H = Path(__file__).resolve().parent.parent; SNAP = H / "snapshots"; SNAP.mkdir(exist_ok=True)
sys.path.insert(0, str(H / "runtime"))
try: from load_env import load_env; load_env()
except Exception: pass
NOWT = int(dt.datetime.now(dt.timezone.utc).timestamp())
KEY = os.environ.get("FINNHUB_API_KEY")
OUT = SNAP / "finnhub_news.json"
WINDOW_S = 6 * 3600     # inclusão de contexto = 6h (news lenta em fim-de-semana); high-impact/escalada apertados
HIGH_FRESH_MIN = 90     # high_impact só se headline TOP-tier ≤90min (breaking, não contexto velho)
TOP = ["hormuz", "tanker", "missile", "strike", "killed", "escalat", "ceasefire", "nuclear", "blockade",
       "attack", "opec", "sanction", "war", "rate cut", "rate hike", "fomc", "cpi", "inflation", "jobs report"]
MED = ["iran", "israel", "oil", "brent", "crude", "gold", "dollar", "fed", "powell", "trump", "tariff", "yields"]


def curl(url):
    return subprocess.run(["curl", "-sS", "--max-time", "25", url], capture_output=True, text=True).stdout


def score(title, summary=""):
    t = (title + " " + summary).lower()
    top = [k for k in TOP if k in t]; med = [k for k in MED if k in t]
    return ("high" if top else ("med" if med else "low")), (top + med)


def main():
    out = {"_meta": {"built_ts": NOWT, "source": "Finnhub /news general (free)", "purpose": "contexto XAU fresco"},
           "fetch_ok": False, "fetch_ts": NOWT, "n_relevant": 0, "n_high": 0,
           "high_impact_now": False, "urgency": "none", "items": [], "gate": {}}
    if not KEY:
        out["error"] = "FINNHUB_API_KEY ausente"; _write(out); print("finnhub_news: sem key"); return
    raw = curl(f"https://finnhub.io/api/v1/news?category=general&token={KEY}")
    try:
        arts = json.loads(raw); out["fetch_ok"] = isinstance(arts, list)
    except Exception:
        out["error"] = f"não-JSON: {raw[:80]}"; _write(out); print("finnhub_news: parse-fail"); return
    items = []
    for a in (arts or [])[:60]:
        ts = a.get("datetime")
        age_min = round((NOWT - ts) / 60) if ts else None
        if age_min is not None and age_min > WINDOW_S / 60:
            continue
        urg, kws = score(a.get("headline", ""), a.get("summary", ""))
        if urg == "low":
            continue
        items.append({"id": hashlib.md5((a.get("headline") or "").encode()).hexdigest()[:12],
                      "title": (a.get("headline") or "")[:200], "keywords": kws, "urgency": urg,
                      "age_min": age_min, "url": a.get("url"), "source": a.get("source")})
    items.sort(key=lambda x: (0 if x["urgency"] == "high" else 1, x["age_min"] if x["age_min"] is not None else 999))
    n_high = sum(1 for it in items if it["urgency"] == "high")
    fresh_high = [it for it in items if it["urgency"] == "high" and (it["age_min"] is None or it["age_min"] <= HIGH_FRESH_MIN)]
    fresh_top = [it for it in items if it["urgency"] == "high" and (it["age_min"] is None or it["age_min"] <= 30)]
    high_impact = len(fresh_high) >= 1        # ≥1 TOP-tier ≤90min = alto-impacto (breaking), não contexto velho
    top = items[0] if items else None
    out.update({"n_relevant": len(items), "n_high": n_high, "high_impact_now": bool(high_impact),
                "urgency": ("high" if high_impact else ("med" if items else "none")), "items": items[:15],
                "gate": {"high_impact_headline": bool(high_impact),
                         "escalate": bool(high_impact and top and (top.get("age_min") is None or top["age_min"] <= 30)),
                         "reason": f"{n_high} headlines TOP-tier frescas" if high_impact else "sem headline alto-impacto",
                         "since_ts": NOWT if high_impact else None, "session": None, "ff_event_le_min": None}})
    _write(out)
    print(f"finnhub_news: {len(items)} relevantes, {n_high} TOP, high_impact={high_impact}")


def _write(o):
    tmp = OUT.with_suffix(".json.tmp"); tmp.write_text(json.dumps(o, indent=1, ensure_ascii=False)); os.replace(tmp, OUT)


if __name__ == "__main__":
    main()
