#!/usr/bin/env python3
"""WATCHER DE NÍVEIS AO VIVO (Cris 2026-07-23, trade ao vivo). Fontes EXATAS do teu Pepperstone:
  • OURO: bar-store bars_5m.jsonl (sempre ouro, exato, sem MCP).
  • EUR: MCP PINADO à tab EURUSD (TVMCP_TARGET_CHART_ID setado ANTES do arranque = lê a tab certa,
    independente da tab ativa; foi o meu erro antes ter setado depois → lia a ativa). Preço exato do broker.
Dispara Telegram no cruzamento. One-shot por nível. Auto-off 4h.
Níveis: OURO 4138 parcial(cima)/4116 defesa(baixo) · EUR 1.14044 SAÍDA(baixo)."""
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

# SELL-SETUP (Cris 2026-07-23): venda a configurar-se → avisar quando o pullback ATINGE cada supply
# (para vigiar a REJEIÇÃO e entrar short). Cruzamento p/ CIMA = pullback chegou à zona de venda.
SELL_ZONES = [
    (4099.0, "🔻 OURO 4099 — bounce à 1ª resistência-partida (4099-4106) · zona de entry parcial short"),
    (4115.0, "🎯 OURO 4115 — ENTRY do teu SHORT limit atingido · vigia rejeição"),
    (4128.0, "⚠️ OURO 4128 — a APROXIMAR-SE do SL 4131.7 (supply institucional) · atenção"),
]
GOLD_DEFENSE = 4068.0  # TP-parcial: demanda institucional 4044-4052 (1º alvo do short)
EUR_EXIT = 1.14044; EUR_HEADSUP = 1.14100
POLL_S = 20; MAX_RUN_S = 14 * 3600   # overnight (Cris 2026-07-23: manter a noite toda)


def _log(o):
    with open(LOG, "a") as fh: fh.write(json.dumps(o, ensure_ascii=False) + "\n")


def _send(t):
    try: return TN.send_telegram(t)
    except Exception as e: return f"ERR {str(e)[:50]}"


def gold_price():
    try: return json.loads(BARS5.read_text().splitlines()[-1])["c"]
    except Exception: return None


def _connect_eur():
    """MCP pinado à tab EURUSD — env setado ANTES do start (senão lê a tab ativa). Devolve (client, tab_id)."""
    eid = tab_pin.discover_tab("15", symbol_suffix="EURUSD")
    if not eid: return None, None
    os.environ["TVMCP_TARGET_CHART_ID"] = eid
    c = MCPClient(); c.start()
    return c, eid


def main():
    try: state = json.loads(STATE_F.read_text())
    except Exception: state = {}
    ceur, eid = _connect_eur()
    src = "MCP pinado (exato broker)" if ceur else "🔴 tab EUR não encontrada"
    _send(f"🎯 <b>Alertas de nível ARMADOS</b>\n🔻 SHORT: entry 4115 · resist-parcial 4099 · SL-aviso 4128 · TP-parcial 4052 (bar-store exato)\n🚨 EUR 1.14044 saída [{src}] + aviso 1.1410\nPoll 20s · auto-off 4h")
    t0 = time.time()
    try:
        while time.time() - t0 < MAX_RUN_S:
            now = dt.datetime.now(LX).strftime("%H:%M:%S")
            g = gold_price()
            if g is not None:
                for lvl, label in SELL_ZONES:                  # pullback ATINGIU a supply (cross p/ cima)
                    k = f"sell_{lvl:.0f}"
                    if g >= lvl and not state.get(k):
                        _send(f"{label}\npreço {g:.1f} · {now} Lisboa"); state[k] = 1
                if g <= GOLD_DEFENSE and not state.get("gold_def"):
                    _send(f"⚠️ <b>OURO tocou 4068</b> — TP #A 4068 (demanda local) — parcial; runner p/ institucional 4044-4052\npreço {g:.1f} · {now} Lisboa"); state["gold_def"] = 1
            # EUR via MCP pinado
            e = None
            if ceur:
                try:
                    q = ceur.call_tool("quote_get") or {}
                    if str(q.get("symbol", "")).endswith("EURUSD"):
                        e = q.get("last") or q.get("close")
                except Exception:
                    try: ceur.stop()
                    except Exception: pass
                    ceur, eid = _connect_eur()      # reconecta se caiu
            if e is not None:
                if e <= EUR_HEADSUP and not state.get("eur_head"):
                    _send(f"⚠️ <b>EUR a aproximar-se da saída</b>\n{e:.5f} · alvo 1.14044 · {now}"); state["eur_head"] = 1
                if e <= EUR_EXIT and not state.get("eur_exit"):
                    _send(f"🚨🚨 <b>URGENTE — EUR NA SAÍDA 1.14044</b>\n{e:.5f} · {now} Lisboa · SAIR com perda pequena"); state["eur_exit"] = 1
            STATE_F.write_text(json.dumps(state, ensure_ascii=False))
            _log({"ts": now, "gold": g, "eur": e})
            if state.get("gold_up") and state.get("gold_dn") and state.get("eur_exit"): break
            time.sleep(POLL_S)
    finally:
        try:
            if ceur: ceur.stop()
        except Exception: pass
        _send("⏹️ Watcher de níveis DESLIGADO. Religa se ainda estiveres nas operações.")


if __name__ == "__main__":
    main()
