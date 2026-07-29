#!/usr/bin/env python3
"""COLETOR GEOPOLÍTICO (Cris 2026-07-18) — o buraco que a auditoria expôs: o EF era cego ao Médio Oriente/
Irão/energia, que hoje DOMINAM o ouro. Fonte GDELT DOC 2.0 (keyless, grátis, real-time global news+tone).
Filtra por keywords de alto-impacto para XAU (guerra/Ormuz/petróleo/sanções/Fed-geopolítico), pontua urgência,
e escreve snapshots/geopolitical_news.json no MESMO shape que o news_gate/news_escalate consomem — para
ACIONAR RÁPIDO (lane 4min → news_gate → E0 → E2 + escalada Telegram). Determinístico, py3.9, graceful.
NÃO é sinal de trade — é contexto/gate de alto-impacto."""
import json, os, sys, hashlib, subprocess, datetime as dt, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _resilient import write_resilient   # keep-last-good em vazio intermitente (anti-flapping)
H = Path(__file__).resolve().parent.parent; SNAP = H / "snapshots"; SNAP.mkdir(exist_ok=True)
NOWT = int(dt.datetime.now(dt.timezone.utc).timestamp())
OUT = SNAP / "geopolitical_news.json"
WINDOW_MIN = 180        # janela de relevância (3h)

# query GDELT: temas que movem XAU. sourcelang eng, ordenado por data desc.
QUERY = '(Iran OR Hormuz OR Israel OR "oil price" OR OPEC OR "gold price" OR sanctions OR tanker OR strike) sourcelang:eng'
# keywords TOP-tier (choque de preço quase certo) e MED-tier (contexto)
TOP = ["hormuz", "tanker", "missile", "strike", "killed", "escalat", "ceasefire", "nuclear",
       "blockade", "attack", "invasion", "opec", "sanction", "war", "retaliat"]
MED = ["iran", "israel", "oil", "brent", "crude", "gaza", "trump", "fed", "tariff", "gold"]


def curl(url):
    return subprocess.run(["curl", "-sS", "--http1.1", "--max-time", "40",
                           "-A", "ef-geopolitical-poller/1.0", url], capture_output=True, text=True).stdout


def parse_dt(s):
    try:
        return int(dt.datetime.strptime(s, "%Y%m%dT%H%M%SZ").replace(tzinfo=dt.timezone.utc).timestamp())
    except Exception:
        return None


def score(title):
    t = (title or "").lower()
    top = [k for k in TOP if k in t]
    med = [k for k in MED if k in t]
    return ("high" if top else ("med" if med else "low")), (top + med)


def main():
    q = urllib.parse.quote(QUERY)
    # GDELT timespan minute-format é instável; uso 24h (known-good) e FILTRO por age_min no código.
    url = (f"https://api.gdeltproject.org/api/v2/doc/doc?query={q}&mode=artlist"
           f"&maxrecords=50&sort=datedesc&format=json&timespan=24h")
    raw = curl(url)
    fetch_ok = True; arts = []
    try:
        d = json.loads(raw or "{}"); arts = d.get("articles", []) or []
    except Exception:
        fetch_ok = False
    items = []
    for a in arts:
        title = a.get("title") or ""
        ts = parse_dt(a.get("seendate", ""))
        age_min = round((NOWT - ts) / 60) if ts else None
        if age_min is not None and age_min > WINDOW_MIN:
            continue
        urg, kws = score(title)
        if urg == "low":
            continue
        items.append({"id": hashlib.md5(title.encode()).hexdigest()[:12], "title": title[:200],
                      "keywords": kws, "urgency": urg, "age_min": age_min,
                      "url": a.get("url"), "domain": a.get("domain")})
    # dedup por id, ordena por urgência+frescura
    seen = set(); uniq = []
    for it in sorted(items, key=lambda x: (0 if x["urgency"] == "high" else 1, x["age_min"] if x["age_min"] is not None else 999)):
        if it["id"] in seen: continue
        seen.add(it["id"]); uniq.append(it)
    n_high = sum(1 for it in uniq if it["urgency"] == "high")
    # ALTO-IMPACTO = BREAKING: ≥1 headline TOP-tier FRESCA (≤45min). Guerra em curso tem sempre TOP na
    # janela (contexto persistente) — só uma headline NOVA liga o flag; o resto fica em items/advisory.
    fresh_top = [it for it in uniq if it["urgency"] == "high" and (it["age_min"] is None or it["age_min"] <= 45)]
    high_impact = len(fresh_top) >= 1
    top = uniq[0] if uniq else None
    gate = {"high_impact_headline": bool(high_impact),
            "escalate": bool(high_impact and top and (top.get("age_min") is None or top["age_min"] <= 60)),
            "reason": (f"{n_high} headlines TOP-tier geopolíticas frescas" if high_impact else "sem headline geopolítica de alto impacto"),
            "since_ts": (NOWT if high_impact else None), "session": None, "ff_event_le_min": None}
    out = {"_meta": {"built_ts": NOWT, "source": "GDELT DOC 2.0 (keyless)", "purpose": "geopolítica/energia p/ XAU",
                     "window_min": WINDOW_MIN},
           "fetch_ok": fetch_ok, "fetch_ts": NOWT, "fetch_age_s": 0,
           "n_total": len(arts), "n_relevant": len(uniq), "n_high": n_high,
           "high_impact_now": bool(high_impact), "urgency": ("high" if high_impact else ("med" if uniq else "none")),
           "items": uniq[:15], "gate": gate}
    # SAUDÁVEL = fetch OK e o GDELT devolveu artigos brutos (a query ampla de 24h SEMPRE traz ~50; 0 = falha
    # de fetch, não ausência real). Vazio -> preserva o último bom snapshot (não grava buraco) e neutraliza
    # gatilhos de alarme para não escalar Telegram em dados velhos.
    healthy = bool(fetch_ok and len(arts) > 0)
    _written, served_stale = write_resilient(
        OUT, out, healthy,
        neutralize=["high_impact_now", "gate.high_impact_headline", "gate.escalate"])
    if served_stale:
        cf = _written.get("_meta", {}).get("consecutive_fail")
        print(f"geopolitical: FETCH VAZIO (fetch_ok={fetch_ok} arts={len(arts)}) -> mantido último bom "
              f"snapshot (falhas seguidas={cf}, alarmes neutralizados)")
    else:
        print(f"geopolitical: {len(arts)} arts, {len(uniq)} relevantes, {n_high} TOP, high_impact={high_impact}")


if __name__ == "__main__":
    main()
