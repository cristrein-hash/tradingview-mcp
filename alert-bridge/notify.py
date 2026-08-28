#!/usr/bin/env python3
"""NOTIFY — sender Telegram ÚNICO do sistema (Cris 2026-08-19, auditoria SIGNAL_SEMANTICS_AUDIT_20260819).

Regras (parametrização aprovada):
- 4 canais fixos: 🎯 ENTRADA · 🧠 LEITURA · ⚡ AVISO · 🩺 INFRA — nada fora disto.
- UM formato (opção A, vertical alinhado), texto plano SEMPRE (sem parse_mode/<b>), hora Lisboa.
- .telegram_muted cala TUDO, sem exceção.
- audience explícito: "group" (TELEGRAM_CHAT_IDS/TELEGRAM_CHAT_ID) ou "personal" (AUTHORIZED_CHAT_ID).
- Sem dados que não ajudem a decidir: entry/SL/alvo(R) + no máx. 1 tag de evento. O resto vive nos ledgers.

API:
  signal(channel, name, tf, side, entry, sl, alvo, r=None, event=None, tag=None, audience="group")
  info(channel, name, body, audience="personal")     # AVISO/INFRA sem níveis (corpo 1-2 linhas)
Ambos devolvem True/False (enviado) ou str "ERR ...".
"""
import os, sys, datetime as dt
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

REPO = "/Users/cristrein/tradingview-mcp"
MUTE = os.path.join(REPO, ".telegram_muted")
ENV = os.path.join(REPO, "alert-bridge", ".env")
SEP = "──────────────"
CH = {"ENTRADA": "🎯", "LEITURA": "🧠", "AVISO": "⚡", "INFRA": "🩺"}
SIDE = {"LONG": "🟢 LONG", "SHORT": "🔴 SHORT"}


def _env():
    e = {}
    try:
        for ln in open(ENV):
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                e[k] = v.strip().strip('"')
    except Exception:
        pass
    return e


def _now_lisboa():
    return dt.datetime.now(ZoneInfo("Europe/Lisbon")).strftime("%H:%M Lisboa")


INFRA_LOG = os.path.join(REPO, "my-strategy/core/health_check/.health_state/infra_events.jsonl")


AVISO_SHADOW = os.path.join(REPO, "alert-bridge", "logs", "aviso_shadow.jsonl")


def _route_to_file(path, text):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as fh:
            import json as _j, time as _t
            fh.write(_j.dumps({"ts": int(_t.time()), "msg": text}, ensure_ascii=False) + "\n")
    except Exception as e:
        # AUDIT-FIX 19/08: falha de escrita do shadow/infra ledger deixava o evento sem rasto nenhum
        print(f"notify._route_to_file ERR {type(e).__name__}: {str(e)[:80]}", file=sys.stderr)


def _send(text, audience):
    # 🩺 INFRA NUNCA vai ao Telegram (ordem Cris 2026-08-19: "não quero receber INFRA — é para o Claude
    # monitorar"). Vai para infra_events.jsonl, que o Claude lê ao auditar saúde (par do PENDING.json).
    if text.startswith(CH["INFRA"]):
        _route_to_file(INFRA_LOG, text)
        return "infra-logged(no-telegram)"
    # ⚡ AVISO em SHADOW (decisão Cris 2026-08-19): Telegram fica SÓ com 🎯 ENTRADA + 🧠 LEITURA.
    # Avisos continuam a correr e ficam em aviso_shadow.jsonl p/ avaliação futura (validar ou descartar).
    # EXCEÇÃO (ordem Cris 2026-08-28): AVISO com audience="personal" vai TAMBÉM ao TG pessoal dele
    # (AUTHORIZED_CHAT_ID) — nunca ao grupo. Caso de uso: pool-limit watch antecipado.
    if text.startswith(CH["AVISO"]):
        _route_to_file(AVISO_SHADOW, text)
        if audience != "personal":
            return "aviso-shadow(no-telegram)"
    if os.path.exists(MUTE):
        return False
    env = _env()
    token = env.get("TELEGRAM_BOT_TOKEN")
    if audience == "personal":
        chats = [env.get("AUTHORIZED_CHAT_ID") or ""]
    else:
        chats = [x.strip() for x in (env.get("TELEGRAM_CHAT_IDS") or env.get("TELEGRAM_CHAT_ID") or "").split(",")]
    chats = [c for c in chats if c]
    if not token or not chats:
        return "ERR telegram nao configurado"
    ok = True
    for cid in chats:
        data = urlencode({"chat_id": cid, "text": text, "disable_web_page_preview": "true"}).encode()
        try:
            with urlopen(Request(f"https://api.telegram.org/bot{token}/sendMessage",
                                 data=data, method="POST"), timeout=20) as r:
                ok = ok and (r.status == 200)
        except Exception:
            ok = False
    return ok


def _num(x):
    try:
        return f"{float(x):g}"
    except (TypeError, ValueError):
        return "?"


def build_signal(channel, name, tf, side, entry, sl, alvo, r=None, event=None, symbol="XAUUSD"):
    head = f"{CH[channel]} {channel} · {name} · {tf}"
    dline = f"{SIDE[side]} {symbol}" + (f" — {event}" if event else "")
    rtxt = f"  ({_num(r)}R)" if r is not None else ""
    body = [head, SEP, dline,
            f"entry   {_num(entry)}",
            f"SL      {_num(sl)}",
            f"alvo    {_num(alvo)}{rtxt}",
            SEP, f"{_now_lisboa()} · decisão humana · #N"]
    return "\n".join(body)


def signal(channel, name, tf, side, entry, sl, alvo, r=None, event=None, symbol="XAUUSD", audience="group"):
    return _send(build_signal(channel, name, tf, side, entry, sl, alvo, r, event, symbol), audience)


def info(channel, name, body, audience="personal"):
    head = f"{CH[channel]} {channel} · {name}"
    return _send("\n".join([head, SEP, body.strip(), SEP, _now_lisboa()]), audience)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        m = build_signal("ENTRADA", "CP CAPITULAÇÃO", "15M", "LONG", 4318.4, 4309.2, 4345.9, 3, None)
        assert m.startswith("🎯 ENTRADA · CP CAPITULAÇÃO · 15M"), m
        assert "entry   4318.4" in m and "(3R)" in m and "decisão humana" in m
        m2 = build_signal("LEITURA", "READER E2", "15M", "SHORT", 4411.5, 4419.4, 4386.0, 2.9, "rejeição no íman")
        assert "🔴 SHORT XAUUSD — rejeição no íman" in m2 and "(2.9R)" in m2
        # AUDIT-FIX 19/08 (I): ROUTING é a invariante crítica — ⚡/🩺 NUNCA tocam Telegram
        r_av = _send("⚡ AVISO · SELFTEST\nx", "group")
        assert r_av == "aviso-shadow(no-telegram)", r_av
        r_in = _send("🩺 INFRA · SELFTEST\nx", "personal")
        assert r_in == "infra-logged(no-telegram)", r_in
        import json as _j
        last = open(AVISO_SHADOW).read().splitlines()[-1]
        assert "SELFTEST" in _j.loads(last)["msg"]
        print(m); print(); print(m2); print("\nselftest PASS (formato + routing shadow/infra)")
    elif "--test-send" in sys.argv:
        print(signal("ENTRADA", "TESTE FORMATO", "15M", "LONG", 4318.4, 4309.2, 4345.9, 3,
                     audience="personal"))
