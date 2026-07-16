#!/usr/bin/env python3
"""ESCALADA DE NEWS (Telegram) — passo do wrapper da news lane. Lê o snapshot da news lane; se
gate.escalate (headline HI + sessão forte OU evento FF iminente) E ainda não alertou esta headline
E cooldown respeitado -> envia UM aviso Telegram. Dedup por id, cooldown ≥10min. Só envia se
NEWS_ALERTS_AUTHORIZED=1 (senão dry-run: imprime WOULD-ALERT). Determinístico, py3.9. NÃO spammeia.
Reusa send_telegram de alert-bridge/auto_d2r_daily (tokens do .env, nunca expostos)."""
import json, os, sys, datetime as dt
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SNAP = REPO / "external_factors_v2" / "snapshots" / "investinglive_news.json"
STATE = REPO / "external_factors_v2" / "snapshots" / "investinglive_alert_state.json"
COOLDOWN_S = 600  # ≥10min entre alertas
NOWT = int(dt.datetime.now(dt.timezone.utc).timestamp())


def load_state():
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {"alerted_ids": [], "last_alert_ts": 0}


def save_state(s):
    tmp = STATE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(s, indent=1, ensure_ascii=False))
    os.replace(tmp, STATE)


def build_msg(top, g):
    return ("📰⚠️ <b>NEWS ALTO IMPACTO — XAUUSD</b>\n\n"
            f"\"{top.get('title','')[:120]}\"\n"
            f"({', '.join(top.get('keywords', []))} · -{top.get('age_min')}m)\n\n"
            f"Sessão: {g.get('session')} · evento FF em: {g.get('ff_event_le_min')}min\n"
            "▶️ Contexto para decisão (não é sinal de trade).")


def main():
    try:
        d = json.loads(SNAP.read_text())
    except Exception as e:
        print(f"news_escalate: sem snapshot ({type(e).__name__}) -> nada a fazer")
        return
    g = d.get("gate", {})
    if not g.get("escalate"):
        print("news_escalate: escalate=false -> nada a enviar")
        return
    items = d.get("items", [])
    top = next((i for i in items if i.get("urgency") == "high"), items[0] if items else None)
    if not top:
        print("news_escalate: escalate=true mas sem item -> skip")
        return

    st = load_state()
    if top["id"] in st.get("alerted_ids", []):
        print(f"news_escalate: headline {top['id'][:8]} já alertada -> dedup skip")
        return
    if NOWT - st.get("last_alert_ts", 0) < COOLDOWN_S:
        print(f"news_escalate: cooldown ({NOWT - st.get('last_alert_ts',0)}s < {COOLDOWN_S}s) -> skip")
        return

    msg = build_msg(top, g)
    authorized = os.environ.get("NEWS_ALERTS_AUTHORIZED") == "1"
    if not authorized:
        print("news_escalate: [DRY-RUN] NEWS_ALERTS_AUTHORIZED!=1 -> NÃO envia. WOULD-ALERT:")
        print("  " + msg.replace("\n", " | "))
        return

    try:
        sys.path.insert(0, str(REPO / "alert-bridge"))
        from auto_d2r_daily import send_telegram
        r = send_telegram(msg)
        ok = bool(r.get("ok"))
    except Exception as e:
        print(f"news_escalate: envio falhou ({type(e).__name__}:{str(e)[:60]}) -> não marca estado")
        return
    if ok:
        st.setdefault("alerted_ids", []).append(top["id"])
        st["alerted_ids"] = st["alerted_ids"][-200:]  # cap
        st["last_alert_ts"] = NOWT
        save_state(st)
        print(f"news_escalate: ALERTA ENVIADO ({top['id'][:8]}) -> estado atualizado")
    else:
        print("news_escalate: send_telegram devolveu not-ok -> não marca estado")


if __name__ == "__main__":
    main()
