#!/usr/bin/env python3
"""GATE DE NEWS UNIFICADO (advisory) — helper PARTILHADO lido pelo E0 (context_macro) e monitor live.
AVISO CONTEXTUAL: informa, NUNCA bloqueia. Funde TODAS as fontes rápidas/contexto numa só leitura
(des-buraco geopolítico, Cris 2026-07-18):
  GATILHO (rápido)  : price_shock (tape, sub-minuto — o mais rápido, precede news)
  CONTEXTO (fresco) : finnhub_news (Reuters-tier) · geopolitical (GDELT) · investinglive (RSS) · oil (Brent shock)
  AGENDADO          : ff_calendar (evento US alto-impacto iminente/just-released)
high_impact_now = OR de todas. Determinístico, py3.9, NUNCA lança. Não é backtest (news live não existe no
passado). Horas humanas em Lisboa. Uso: from news_gate import read_gate; g = read_gate()"""
import json, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parent.parent
SNAP = REPO / "external_factors_v2" / "snapshots"
IL = SNAP / "investinglive_news.json"
GEO = SNAP / "geopolitical_news.json"
FH = SNAP / "finnhub_news.json"
FJ = SNAP / "fj_news.json"          # FinancialJuice (10min atraso) = contexto/curadoria, NÃO breaking
PM = SNAP / "polymarket.json"       # Polymarket odds (drivers do ouro) = contexto lento; SHIFT = sinal
OIL = SNAP / "oil_data.json"
FFCAL = SNAP / "ff_calendar.json"
SHOCK = REPO / "my-strategy/core/price_shock/.shock_state/shock.json"
GLD_SHOCK = REPO / "my-strategy/core/price_shock/.shock_state/gld_shock.json"
LX = ZoneInfo("Europe/Lisbon")
STALE_S = 900


def _load(p):
    try: return json.loads(Path(p).read_text())
    except Exception: return None


def _now(): return int(dt.datetime.now(dt.timezone.utc).timestamp())


def _news_source(d):
    """Extrai (high_impact, top_headline, age_s, escalate) de um snapshot no shape padrão."""
    if not isinstance(d, dict): return (False, None, None, False)
    g = d.get("gate", {}) or {}
    items = d.get("items", []) or []
    top = items[0] if items else None
    age = (_now() - (d.get("fetch_ts") or d.get("_meta", {}).get("built_ts") or 0))
    return (bool(d.get("high_impact_now") or g.get("high_impact_headline")), top, age, bool(g.get("escalate")))


def _imminent_ffevent():
    """Evento US alto-impacto mais próximo do ff_calendar: (mins_until, event, actual, just_released)."""
    d = _load(FFCAL)
    ev = (d or {}).get("events") or (d if isinstance(d, list) else [])
    now = _now(); best = None
    for e in ev:
        if str(e.get("impact", "")).upper() != "HIGH": continue
        ts = e.get("release_ts")
        if not ts: continue
        mins = round((ts - now) / 60)
        if mins < -15: continue                    # já passou há muito
        # AUDIT-FIX 19/08 (D8): preferir SEMPRE o próximo evento FUTURO; just-released (<0) só ganha
        # se não houver nenhum upcoming — antes |Δt| podia apontar p/ um evento já saído com outro à porta.
        key = (0 if mins >= 0 else 1, abs(mins))
        cur = (0 if best[0] >= 0 else 1, abs(best[0])) if best else None
        if best is None or key < cur:
            best = (mins, e.get("event"), e.get("actual"), (-15 <= mins < 5 and e.get("actual") not in (None, "")))
    return best


def read_gate(path=IL):
    now = _now()
    base = {"ok": False, "stale": True, "fetch_age_s": None, "session": None,
            "high_impact_now": False, "escalate": False, "ff_event_le_min": None, "headline": None,
            "price_shock": None, "sources": {}, "reason": "sem snapshots", "advisory": "ℹ️ news lane indisponível"}
    il = _load(path)
    if il is None:
        # sem investinglive; ainda assim funde as outras fontes (podem estar frescas)
        il = {"gate": {}, "fetch_ts": 0, "fetch_ok": False}
    base["ok"] = True
    g_il = il.get("gate", {}) or {}
    sess = g_il.get("session")
    il_age = now - (il.get("fetch_ts") or 0)
    stale_il = (il_age > STALE_S) or (not il.get("fetch_ok", False))

    # --- funde fontes ---
    src = {}
    hi_il, top_il, age_il, esc_il = _news_source(il)
    src["investinglive"] = {"high": hi_il, "age_s": age_il}
    hi_geo, top_geo, age_geo, esc_geo = _news_source(_load(GEO))
    src["geopolitical"] = {"high": hi_geo, "age_s": age_geo, "headline": (top_geo or {}).get("title") if top_geo else None}
    hi_fh, top_fh, age_fh, esc_fh = _news_source(_load(FH))
    src["finnhub"] = {"high": hi_fh, "age_s": age_fh, "headline": (top_fh or {}).get("title") if top_fh else None}
    # FinancialJuice = contexto/curadoria ATRASADO 10min — NÃO entra no high_impact/breaking, só enriquece
    fj = _load(FJ) or {}
    fj_items = fj.get("items", []) or []
    src["fj"] = {"delayed_10min": True, "n": len(fj_items),
                 "headline": (fj_items[0].get("title") if fj_items else None)}
    oil = _load(OIL) or {}
    oil_shock = bool(oil.get("shock"))
    src["oil"] = {"shock": oil_shock, "read": oil.get("read")}
    # Polymarket = odds forward-looking dos drivers (Fed/guerra/Ormuz). Contexto LENTO, NÃO breaking.
    # Um SHIFT ≥5pp = a multidão a re-precificar um evento antes do preço → enriquece a leitura E2.
    pm = _load(PM) or {}
    pm_shifts = pm.get("shifts", []) or []
    src["polymarket"] = {"key_probs": pm.get("key_probs"), "read": pm.get("read"),
                         "shift": (pm_shifts[0] if pm_shifts else None), "n_shifts": len(pm_shifts)}
    # price shock (gatilho rápido) — funde TV-tape (24h/30s) + GLD-tick (sub-segundo, horas US); <5min
    ps = None
    cands = []
    sh = _load(SHOCK)
    if isinstance(sh, dict) and (now - sh.get("ts", 0) <= 300):
        cands.append({"src": "tv_tape", "unit": "ATR", "mag": sh.get("move_atr"), "dir": sh.get("dir"),
                      "major": sh.get("major"), "window_min": sh.get("window_min"), "ts": sh.get("ts", 0)})
    gld = _load(GLD_SHOCK)
    if isinstance(gld, dict) and (now - gld.get("ts", 0) <= 300):
        cands.append({"src": "gld_tick", "unit": "%", "mag": gld.get("pct"), "dir": gld.get("dir"),
                      "major": gld.get("major"), "window_min": gld.get("window_min"), "ts": gld.get("ts", 0)})
    if cands:
        c = max(cands, key=lambda x: x["ts"])                # o mais recente (GLD-tick vence em horas US)
        ps = {"source": c["src"], "unit": c["unit"], "mag": c["mag"], "dir": c["dir"], "major": c["major"],
              "window_min": c["window_min"], "age_s": now - c["ts"]}
    src["price_shock"] = ps
    # evento agendado
    imm = _imminent_ffevent()
    ff_mins = imm[0] if imm else None
    src["ff_event"] = {"mins_until": ff_mins, "event": imm[1] if imm else None,
                       "just_released": imm[3] if imm else False}

    # high_impact = BREAKING (news fresca / choque de preço / release agendado). CONTEXTO PERSISTENTE
    # (NÃO liga breaking): oil_shock (dura dias) E geopolítico/GDELT (guerra Irão/Israel em curso tem SEMPRE
    # headline TOP-tier fresca → seria breaking 24/7). Ambos ficam nos sources/advisory como contexto para a
    # leitura E2, mas não marcam breaking. Choque geopolítico REAL move o preço → ps apanha-o (price-first).
    # (Coerência com news_escalate, ordem Cris 2026-07-19: geopolítico = contexto, não breaking.)
    high_impact = bool(hi_il or hi_fh or ps or (imm and imm[3]))
    escalate = bool(esc_il or esc_fh or (ps and ps.get("major")) or (imm and imm[3]))

    # advisory humano (o mais forte primeiro)
    parts = []
    if ps:
        u = "×ATR" if ps["unit"] == "ATR" else "%"
        parts.append(f"⚡ CHOQUE PREÇO {ps['dir']} {ps['mag']}{u} ({ps['source']}) em {ps['window_min']}min")
    if imm and 0 <= (imm[0] or 99) <= 60:
        parts.append(f"⏰ {imm[1]} em {imm[0]}min (alto-impacto agendado)")
    if imm and imm[3]:
        parts.append(f"📊 {imm[1]} SAIU: actual {imm[2]}")
    for name, hi, top in (("Finnhub", hi_fh, top_fh), ("geopolítico", hi_geo, top_geo), ("InvestingLive", hi_il, top_il)):
        if hi and top:
            parts.append(f"⚠️ {name}: \"{(top.get('title','') or '')[:70]}\" (-{top.get('age_min')}m)")
    if oil_shock:
        parts.append(f"🛢️ {(oil.get('read') or '')[:80]}")
    if pm_shifts:                                          # movimento de probabilidade = evento a ser precificado
        s = pm_shifts[0]
        parts.append(f"🎲 Polymarket: \"{s['q'][:48]}\" {s['delta']:+.0f}pp→{s['to']}% ({s['driver']})")
    if fj_items:
        parts.append(f"📰 FJ (10min): \"{(fj_items[0].get('title') or '')[:60]}\"")
    if sess == "dead_zone":
        parts.append("🕐 zona morta")
    elif sess in ("london_strong", "ny_open", "ny"):
        parts.append(f"✅ sessão {sess}")
    if stale_il and not (hi_geo or hi_fh or ps):
        parts.append(f"⚠️ RSS lane stale ({il_age}s)")
    advisory = " · ".join(parts) if parts else "ℹ️ sem contexto de news relevante"

    base.update({"stale": stale_il, "fetch_age_s": il_age, "session": sess,
                 "high_impact_now": high_impact, "escalate": escalate,
                 "ff_event_le_min": (ff_mins if (ff_mins is not None and 0 <= ff_mins <= 120) else None),
                 "headline": top_fh or top_geo or top_il, "price_shock": ps, "sources": src,
                 "reason": g_il.get("reason"), "advisory": advisory})
    return base


if __name__ == "__main__":
    print(json.dumps(read_gate(), indent=1, ensure_ascii=False))
