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


def build_msg(name, top, advisory):
    return ("📰⚠️ <b>NEWS ALTO IMPACTO — XAUUSD</b>\n\n"
            f"[{name}] \"{(top.get('title') or '')[:130]}\"\n"
            f"({', '.join(top.get('keywords', []) or [])} · -{top.get('age_min')}m)\n\n"
            f"Contexto: {advisory[:180]}\n"
            "▶️ Contexto para decisão (não é sinal de trade).")


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
