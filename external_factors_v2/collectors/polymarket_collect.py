#!/usr/bin/env python3
"""COLETOR POLYMARKET (Cris 2026-07-18, ideia do Fincept mas API PRÓPRIA grátis/keyless — sem código deles).
Odds de mercados de previsão sobre os DRIVERS do ouro: guerra Irão/Ormuz (geopolítico), Fed/juros/recessão
(macro). Sinal forward-looking único: a multidão precifica o evento ANTES do preço. Edge real = o DELTA
(uma probabilidade a mover = evento a ser precificado). Gamma API (gamma-api.polymarket.com), determinístico,
py3.9, graceful. Saída: polymarket.json {markets, key_probs, shifts, read}. Contexto (não gatilho), lido pelo
news_gate. NÃO copia nada do Fincept (só a ideia; API pública do Polymarket)."""
import json, os, subprocess, datetime as dt
from pathlib import Path
H = Path(__file__).resolve().parent.parent; SNAP = H / "snapshots"; SNAP.mkdir(exist_ok=True)
NOWT = int(dt.datetime.now(dt.timezone.utc).timestamp())
OUT = SNAP / "polymarket.json"
GAMMA = "https://gamma-api.polymarket.com/markets?closed=false&active=true&order=volumeNum&ascending=false&limit=100"
KW = ["fed", "rate", "recession", "inflation", "iran", "israel", "war", "gold", "oil", "trump", "tariff",
      "powell", "cpi", "gdp", "nuclear", "hormuz", "ceasefire", "opec", "jobs", "unemployment", "regime"]
GEO = ["iran", "israel", "war", "nuclear", "hormuz", "ceasefire", "regime", "invade", "strait"]
MACRO = ["fed", "rate", "recession", "inflation", "powell", "cpi", "gdp", "jobs", "unemployment", "tariff"]
OIL = ["oil", "opec", "hormuz", "crude", "brent"]
SHIFT_PP = 5.0          # |Δ| ≥ 5 pontos percentuais = movimento relevante


def curl(url):
    return subprocess.run(["curl", "-sS", "--http1.1", "--max-time", "30", url], capture_output=True, text=True).stdout


def driver(q):
    ql = q.lower()
    if any(k in ql for k in GEO): return "geopolítico"
    if any(k in ql for k in OIL): return "petróleo"
    if any(k in ql for k in MACRO): return "macro/Fed"
    return "outro"


def _prev():
    try: return {m["id"]: m["yes"] for m in json.loads(OUT.read_text()).get("markets", [])}
    except Exception: return {}


def main():
    markets = []
    for offset in (0, 100):                     # 2 páginas p/ cobertura (drivers são alto-volume, ficam no topo)
        raw = curl(GAMMA + f"&offset={offset}")
        try:
            d = json.loads(raw or "[]"); ms = d if isinstance(d, list) else d.get("data", [])
        except Exception:
            ms = []
        for m in ms:
            q = m.get("question") or ""
            if not any(k in q.lower() for k in KW):
                continue
            try:
                pr = m.get("outcomePrices"); pr = json.loads(pr) if isinstance(pr, str) else pr
                oc = m.get("outcomes"); oc = json.loads(oc) if isinstance(oc, str) else oc
                yes = round(float(pr[0]) * 100, 1) if pr else None      # % do 1º outcome (Yes)
            except Exception:
                yes = None
            if yes is None:
                continue
            markets.append({"id": m.get("id") or q[:40], "q": q[:100], "yes": yes,
                            "outcome": oc[0] if oc else "Yes", "driver": driver(q),
                            "vol": round(float(m.get("volumeNum") or m.get("volume") or 0))})
    # dedup por id, ordena por volume
    seen = {}; uniq = []
    for m in sorted(markets, key=lambda x: -x["vol"]):
        if m["id"] in seen: continue
        seen[m["id"]] = 1; uniq.append(m)
    # shifts vs snapshot anterior
    prev = _prev(); shifts = []
    for m in uniq:
        if m["id"] in prev:
            delta = round(m["yes"] - prev[m["id"]], 1)
            if abs(delta) >= SHIFT_PP:
                shifts.append({"q": m["q"], "driver": m["driver"], "from": prev[m["id"]], "to": m["yes"], "delta": delta})
    shifts.sort(key=lambda x: -abs(x["delta"]))
    # key_probs curados (os que mais movem o ouro)
    def find(pat):
        for m in uniq:
            if all(w in m["q"].lower() for w in pat): return m
        return None
    kp = {"fed_no_change_jul": find(["fed", "no change"]) or find(["no change", "fed"]),
          "us_invade_iran": find(["invade", "iran"]), "hormuz_normal": find(["hormuz", "normal"]),
          "iran_regime_fall": find(["regime", "fall"])}
    key_probs = {k: (v["yes"] if v else None) for k, v in kp.items()}
    out = {"_meta": {"built_ts": NOWT, "source": "Polymarket Gamma API (keyless, grátis)",
                     "purpose": "odds forward-looking dos drivers do ouro; edge = DELTA"},
           "fetch_ok": bool(uniq), "fetch_ts": NOWT, "n_markets": len(uniq),
           "markets": uniq[:20], "key_probs": key_probs, "shifts": shifts[:6],
           "read": (f"Fed no-change {key_probs.get('fed_no_change_jul')}% · invasão Irão {key_probs.get('us_invade_iran')}% · "
                    f"Ormuz normaliza {key_probs.get('hormuz_normal')}%" +
                    (f" · ⚠️ SHIFT: {shifts[0]['q'][:50]} {shifts[0]['delta']:+.0f}pp" if shifts else ""))}
    tmp = OUT.with_suffix(".json.tmp"); tmp.write_text(json.dumps(out, indent=1, ensure_ascii=False)); os.replace(tmp, OUT)
    print(f"polymarket: {len(uniq)} mercados relevantes | shifts: {len(shifts)} | {out['read'][:90]}")


if __name__ == "__main__":
    main()
