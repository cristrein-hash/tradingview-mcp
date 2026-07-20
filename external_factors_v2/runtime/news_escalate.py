#!/usr/bin/env python3
"""ESCALADA DE NEWS UNIFICADA (Telegram) — passo da news lane. Escala UMA vez a headline breaking mais
fresca de fontes de news BREAKING de BAIXO VOLUME (Finnhub Reuters-tier / InvestingLive) + release de
calendário just-out. Dedup por id, cooldown ≥10min. EXCLUI price_shock/GLD (auto-alertam pelos seus daemons).
🚫 GEOPOLÍTICO (GDELT) FORA do Telegram desde 2026-07-19 (ordem Cris): guerra em curso (Irão/Israel) produz
SEMPRE headlines TOP-tier frescas → inundava (10/10 dos pings eram geopolíticos). Coerente com a doutrina do
news_gate: guerra-em-curso/oil-shock = CONTEXTO persistente, NÃO breaking. O GDELT continua a alimentar o
news_gate/E2 como contexto; um choque geopolítico REAL move o preço → o price-shock daemon dispara (price-first).
Só envia se NEWS_ALERTS_AUTHORIZED=1 (senão DRY-RUN). Reusa o merge do news_gate p/ o advisory. py3.9."""
import json, os, sys, datetime as dt
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent.parent
SNAP = REPO / "external_factors_v2" / "snapshots"
STATE = SNAP / "news_alert_state.json"
COOLDOWN_S = 600
NOWT = int(dt.datetime.now(dt.timezone.utc).timestamp())
# fontes BREAKING de baixo volume que escalam ao Telegram (NÃO price_shock=auto-alerta · NÃO geopolítico=contexto)
NEWS_SNAPS = [("Finnhub", SNAP / "finnhub_news.json"),
              ("InvestingLive", SNAP / "investinglive_news.json")]


def _load(p):
    try: return json.loads(Path(p).read_text())
    except Exception: return None


def load_state():
    try: return json.loads(STATE.read_text())
    except Exception: return {"alerted_ids": [], "last_alert_ts": 0}


def save_state(s):
    tmp = STATE.with_suffix(".json.tmp"); tmp.write_text(json.dumps(s, indent=1, ensure_ascii=False)); os.replace(tmp, STATE)


def gather_breaking():
    """Recolhe (fonte, item) de cada snapshot cujo gate.escalate=True + release de calendário just-out."""
    cands = []
    for name, path in NEWS_SNAPS:
        d = _load(path)
        if not d or not (d.get("gate") or {}).get("escalate"):
            continue
        items = d.get("items", []) or []
        top = next((i for i in items if i.get("urgency") == "high"), items[0] if items else None)
        if top:
            cands.append((name, top))
    # calendário just-released (via merge do news_gate)
    try:
        sys.path.insert(0, str(REPO / "alert-bridge"))
        from news_gate import read_gate
        g = read_gate()
        ff = (g.get("sources") or {}).get("ff_event") or {}
        if ff.get("just_released") and ff.get("event"):
            cands.append(("Calendário", {"id": "cal_" + str(ff["event"])[:20], "title": f"{ff['event']} SAIU",
                                         "urgency": "high", "age_min": 0}))
        advisory = g.get("advisory", "")
    except Exception:
        advisory = ""
    return cands, advisory


# Léxico de viés para OURO (gold-specific): ouro sobe com risk-off/dovish/USD-fraco/yields-a-cair e cai com
# hawkish/USD-forte/yields-a-subir/dados-fortes. Heurística RÁPIDA por keywords (não é modelo validado) —
# dá ao Cris leitura contextual imediata; o olho dele decide. Peso 2=forte, 1=fraco.
BULL_XAU = {"dovish":2,"rate cut":2,"cuts rates":2,"cut rates":2,"rate-cut":2,"easing":1,"stimulus":1,
            "weak dollar":2,"dollar falls":2,"dollar slips":2,"dollar drops":2,"dollar weakens":2,"softer dollar":2,"greenback falls":2,
            "yields fall":2,"yields drop":2,"lower yields":2,"falling yields":2,"yields slip":2,
            "safe haven":2,"safe-haven":2,"war":2,"invasion":2,"invade":2,"missile":2,"airstrike":2,"nuclear":2,"conflict":1,"escalat":1,"tension":1,"sanction":1,"crisis":1,
            "recession":2,"slowdown":1,"contraction":1,"weak data":2,"misses":1,"disappointing":1,"downbeat":1,"layoffs":1,"jobless claims rise":2,"unemployment rises":2,
            "disinflation":2,"inflation eases":2,"cooler inflation":2,"cpi cooler":2,"cools":1,
            "gold demand":2,"central bank buying":2,"etf inflows":2}
BEAR_XAU = {"hawkish":2,"rate hike":2,"hikes rates":2,"raise rates":2,"rate-hike":2,"tightening":2,"higher for longer":2,
            "strong dollar":2,"dollar rises":2,"dollar climbs":2,"dollar strengthens":2,"firmer dollar":2,"greenback rises":2,"dollar jumps":2,
            "yields rise":2,"yields climb":2,"higher yields":2,"rising yields":2,"yields jump":2,"yields edge higher":2,"treasury yields rise":2,
            "strong jobs":2,"robust jobs":2,"hot jobs":2,"strong payrolls":2,"strong data":2,"beat estimates":2,"beats estimates":2,"upbeat":1,"solid data":1,
            "risk-on":2,"risk appetite":1,"stocks rally":1,"equities surge":1,
            "hot inflation":1,"inflation accelerates":1,"cpi rises":1,"gold outflows":2,"etf outflows":2,
            # DE-ESCALAÇÃO geopolítica = tira o prémio safe-haven = OURO CAI (ex. queda de hoje no cessar-fogo Irão-EUA)
            "ceasefire":2,"cease-fire":2,"de-escalat":2,"deescalat":2,"truce":2,"peace deal":2,"peace talks":1,
            "diplomatic breakthrough":2,"deal reached":2,"revive":1,"interim deal":2,"agreement reached":2}


def classify_xau_bias(text):
    """Devolve label direcional CURTO p/ XAU. Heurística por keywords; empate/0 = sem viés claro (honesto)."""
    t = (text or "").lower()
    b = sum(w for k, w in BULL_XAU.items() if k in t)
    s = sum(w for k, w in BEAR_XAU.items() if k in t)
    if b > s: return "🟢 <b>BULLISH XAU</b>"
    if s > b: return "🔴 <b>BEARISH XAU</b>"
    return "⚪ <b>SEM VIÉS CLARO (XAU)</b>"


def build_msg(name, top, advisory):
    bias = classify_xau_bias(f"{top.get('title') or ''} {' '.join(top.get('keywords', []) or [])}")
    return (f"{bias}\n"
            "📰⚠️ <b>NEWS ALTO IMPACTO — XAUUSD</b>\n\n"
            f"[{name}] \"{(top.get('title') or '')[:130]}\"\n"
            f"({', '.join(top.get('keywords', []) or [])} · -{top.get('age_min')}m)\n\n"
            f"Contexto: {advisory[:180]}\n"
            "▶️ Viés = heurística rápida (não é sinal); a tua leitura decide.")


def main():
    cands, advisory = gather_breaking()
    if not cands:
        print("news_escalate: nada breaking (nenhuma fonte escala)"); return
    name, top = min(cands, key=lambda c: (c[1].get("age_min") if c[1].get("age_min") is not None else 999))
    st = load_state()
    if top["id"] in st.get("alerted_ids", []):
        print(f"news_escalate: {top['id'][:8]} já alertada -> dedup skip"); return
    if NOWT - st.get("last_alert_ts", 0) < COOLDOWN_S:
        print(f"news_escalate: cooldown ({NOWT - st.get('last_alert_ts',0)}s) -> skip"); return

    msg = build_msg(name, top, advisory)
    if os.environ.get("NEWS_ALERTS_AUTHORIZED") != "1":
        print("news_escalate: [DRY-RUN] NEWS_ALERTS_AUTHORIZED!=1 -> WOULD-ALERT: " + msg.replace("\n", " | ")[:160])
        return
    try:
        from auto_d2r_daily import send_telegram
        r = send_telegram(msg); ok = bool(r.get("ok")) if isinstance(r, dict) else bool(r)
    except Exception as e:
        print(f"news_escalate: envio falhou ({type(e).__name__}:{str(e)[:60]})"); return
    if ok:
        st.setdefault("alerted_ids", []).append(top["id"]); st["alerted_ids"] = st["alerted_ids"][-200:]
        st["last_alert_ts"] = NOWT; save_state(st)
        print(f"news_escalate: ALERTA ENVIADO [{name}] ({top['id'][:8]})")
    else:
        print("news_escalate: send not-ok -> não marca estado")


if __name__ == "__main__":
    main()
