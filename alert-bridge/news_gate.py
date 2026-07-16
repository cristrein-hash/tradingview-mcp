#!/usr/bin/env python3
"""GATE DE NEWS (advisory) — helper PARTILHADO lido pelo workflow de monitorização live (proxy trades)
e, no futuro, pelos engines quando forem live-runtime. AVISO CONTEXTUAL: informa, NUNCA bloqueia.
Lê o snapshot fresco da news lane (external_factors_v2/snapshots/investinglive_news.json, ≤4min) e
devolve contexto advisory: sessão, headline de alto impacto, evento FF iminente, staleness. Determinístico.
NÃO é para backtest (news live não existe no passado). py3.9. Uso:
  from news_gate import read_gate; g = read_gate(); print(g['advisory'])"""
import json, datetime as dt
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SNAP = REPO / "external_factors_v2" / "snapshots" / "investinglive_news.json"
STALE_S = 900  # >15min (1 barra 15M) sem fetch OK = news lane atrasada -> sinalizar


def read_gate(path=SNAP):
    """Devolve dict advisory. NUNCA lança; se não houver snapshot, devolve estado 'unknown' seguro."""
    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    base = {"ok": False, "stale": True, "fetch_age_s": None, "session": None,
            "high_impact_now": False, "escalate": False, "ff_event_le_min": None,
            "headline": None, "reason": "sem snapshot de news", "advisory": "ℹ️ news lane indisponível (sem snapshot)"}
    try:
        d = json.loads(Path(path).read_text())
    except Exception as e:
        base["reason"] = f"snapshot ilegível: {type(e).__name__}"
        return base

    fetch_ts = d.get("fetch_ts") or d.get("_meta", {}).get("built_ts")
    age = (now - fetch_ts) if fetch_ts else None
    stale = (age is None) or (age > STALE_S) or (not d.get("fetch_ok", False))
    g = d.get("gate", {})
    items = d.get("items", [])
    top = items[0] if items else None
    hi = bool(g.get("high_impact_headline"))
    sess = g.get("session")
    ff = g.get("ff_event_le_min")

    # advisory humano (contextual, não-bloqueante)
    parts = []
    if hi and top:
        parts.append(f"⚠️ HEADLINE HI: \"{top.get('title','')[:70]}\" ({top.get('keywords')}, -{top.get('age_min')}m)")
    if ff is not None:
        parts.append(f"⚠️ evento FF alto-impacto em ~{ff}min")
    if sess == "dead_zone":
        parts.append("🕐 zona morta (baixa liquidez — sem catalisador, cautela p/ mean-reversion)")
    elif sess in ("london_strong", "ny_open", "ny"):
        parts.append(f"✅ sessão {sess} (liquidez forte)")
    elif sess:
        parts.append(f"🕐 sessão {sess}")
    if stale:
        parts.append(f"⚠️ news lane STALE (fetch_age={age}s)")
    advisory = " · ".join(parts) if parts else "ℹ️ sem contexto de news relevante"

    return {"ok": True, "stale": stale, "fetch_age_s": age, "session": sess,
            "high_impact_now": hi, "escalate": bool(g.get("escalate")),
            "ff_event_le_min": ff, "headline": top, "reason": g.get("reason"),
            "advisory": advisory}


if __name__ == "__main__":
    import json as _j
    print(_j.dumps(read_gate(), indent=1, ensure_ascii=False))
