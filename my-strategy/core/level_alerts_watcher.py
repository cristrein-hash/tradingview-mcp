#!/usr/bin/env python3
"""WATCHER DE NÍVEIS AO VIVO (Cris 2026-07-23, trade ao vivo). Fontes EXATAS do Pepperstone:
  • OURO: bar-store bars_5m.jsonl (sempre ouro, exato, sem MCP).
  • EUR: MCP PINADO à tab EURUSD (env ANTES do arranque; None se a tab não existir = ok).
Dispara Telegram no cruzamento. One-shot por nível. Robusto (try/except por ciclo — nunca morre num erro
transitório). Overnight 14h.

CONCEITO (Cris): POLARIDADE DE FUNDO = regiões de FUNDOS ANTERIORES que agora coincidem com supply e formam
RESISTÊNCIA (não é o fundo de capitulação). No bounce, o preço testa essas zonas e rejeita → SHORT.
Zonas de venda (bounce+rejeição): supply/polaridade-flip acima do preço."""
import os, sys, json, time, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION"))
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import tab_pin
from draw_xau_4h_trades import MCPClient
import telegram_notify as TN
LX = ZoneInfo("Europe/Lisbon")
ST = HERE / ".level_alerts_state"; ST.mkdir(exist_ok=True)
STATE_F = ST / "state.json"; LOG = ST / "watch.log"
BARS5 = HERE / "bar_store/store/bars_5m.jsonl"

# SELL: bounce a supply / polaridade-de-fundo (fundos antigos agora resistência) → vigiar REJEIÇÃO p/ short
SELL_ZONES = [
    (4076.0, "🔻 OURO 4076 — bounce à 1ª resistência (fundo antigo 4076-4084=resist) · vigia REJEIÇÃO p/ short"),
    (4088.0, "🔻 OURO 4088 — bounce à polaridade-flip (4088-4095, fundo antigo=resistência) · vigia REJEIÇÃO p/ short"),
    (4123.0, "🔻 OURO 4123 — bounce ao SUPPLY institucional (4123-4130, POC multi-TF) · vigia REJEIÇÃO p/ short"),
    (4134.0, "🔻 OURO 4134 — bounce ao SUPPLY institucional (4134-4141) · vigia REJEIÇÃO p/ short"),
]
GOLD_FLUSH = 4006.0   # se flushar à demanda institucional 3998-4006 sem bounce = continuação-baixa (avisa)
EUR_EXIT = 1.14044; EUR_HEADSUP = 1.14100
POLL_S = 20; MAX_RUN_S = 14 * 3600


def _log(o):
    try:
        with open(LOG, "a") as fh: fh.write(json.dumps(o, ensure_ascii=False) + "\n")
    except Exception: pass


def _send(t):
    try: return TN.send_telegram(t)
    except Exception as e: return f"ERR {str(e)[:50]}"


def gold_price():
    try: return json.loads(BARS5.read_text().splitlines()[-1])["c"]
    except Exception: return None


def _connect_eur():
    try:
        eid = tab_pin.discover_tab("15", symbol_suffix="EURUSD")
        if not eid: return None
        os.environ["TVMCP_TARGET_CHART_ID"] = eid
        c = MCPClient(); c.start(); return c
    except Exception:
        return None


def main():
    try: state = json.loads(STATE_F.read_text())
    except Exception: state = {}
    ceur = _connect_eur()
    src = "MCP pinado (exato)" if ceur else "tab EUR ausente (só ouro)"
    _send(f"🎯 <b>Alertas de nível ARMADOS</b>\n🔻 OURO short em bounce: 4088/4123/4134 (rejeição) · flush 4006\n🚨 EUR 1.14044 saída [{src}]\nPoll 20s · overnight")
    t0 = time.time()
    try:
        while time.time() - t0 < MAX_RUN_S:
            try:
                now = dt.datetime.now(LX).strftime("%H:%M:%S")
                g = gold_price()
                if g is not None:
                    for lvl, label in SELL_ZONES:
                        k = f"sell_{lvl:.0f}"
                        if g >= lvl and not state.get(k):
                            _send(f"{label}\npreço {g:.1f} · {now} Lisboa"); state[k] = 1
                    if g <= GOLD_FLUSH and not state.get("gold_flush"):
                        _send(f"⚠️ <b>OURO na demanda institucional 3998-4006</b> (flush sem bounce = continuação-baixa)\npreço {g:.1f} · {now}"); state["gold_flush"] = 1
                e = None
                if ceur:
                    try:
                        q = ceur.call_tool("quote_get") or {}
                        if str(q.get("symbol", "")).endswith("EURUSD"):
                            e = q.get("last") or q.get("close")
                    except Exception:
                        try: ceur.stop()
                        except Exception: pass
                        ceur2 = _connect_eur()
                        if ceur2: ceur = ceur2
                if e is not None:
                    if e <= EUR_HEADSUP and not state.get("eur_head"):
                        _send(f"⚠️ <b>EUR a aproximar-se da saída</b>\n{e:.5f} · alvo 1.14044 · {now}"); state["eur_head"] = 1
                    if e <= EUR_EXIT and not state.get("eur_exit"):
                        _send(f"🚨🚨 <b>URGENTE — EUR NA SAÍDA 1.14044</b>\n{e:.5f} · {now} Lisboa"); state["eur_exit"] = 1
                STATE_F.write_text(json.dumps(state, ensure_ascii=False))
                _log({"ts": now, "gold": g, "eur": e})
            except Exception as ex:
                _log({"ts": dt.datetime.now(LX).strftime("%H:%M:%S"), "erro_ciclo": str(ex)[:120]})
            time.sleep(POLL_S)
    finally:
        try:
            if ceur: ceur.stop()
        except Exception: pass
        _send("⏹️ Watcher de níveis DESLIGADO. Religa se ainda estiveres nas operações.")


if __name__ == "__main__":
    main()
