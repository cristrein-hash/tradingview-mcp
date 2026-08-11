#!/usr/bin/env python3
"""G4 — MCP-SURFACE GUARD (Cris 2026-08-11).
BLOQUEIA (exit 2) ações MCP de alto-impacto/só-por-ordem sem autorização fresca. Fecha buracos do catálogo
que vivem FORA de Bash/Write/Edit (a superfície MCP não tinha guard nenhum):
  - C3 screenshots sem pedido · B4 desenhar não-canónico/sem ordem · B5 replay/chart mexidos descuidados ·
    alertas criados/apagados sem ordem.

Ações guardadas exigem um flag FRESCO ~/.claude/.mcp_action_ok (tocado <FRESH_S quando o Cris autoriza).
Leituras (pine_boxes/ohlcv/quote/study_values...) NÃO são guardadas — precisas delas sempre.
Escape: `touch ~/.claude/.mcp_action_ok` imediatamente antes da ação autorizada.

CAVEAT: depende de os hooks PreToolUse dispararem em matchers `mcp__*`. Se não dispararem nesta versão do
Claude Code, o guard é no-op (seguro) — a verificar ao vivo. Núcleo `decide()` puro. py3 stdlib."""
import sys, json, time
from pathlib import Path

FLAG = Path.home() / ".claude" / ".mcp_action_ok"
FRESH_S = 300   # 5 min

GUARDED = {
    "capture_screenshot", "replay_trade", "replay_start", "replay_stop", "replay_autoplay", "replay_step",
    "alert_create", "alert_delete", "chart_set_symbol", "chart_set_timeframe", "chart_set_type",
    "chart_scroll_to_date", "chart_set_visible_range", "draw_shape", "draw_clear", "draw_remove_one",
    "indicator_toggle_visibility", "indicator_set_inputs", "pine_save", "pine_set_source", "layout_switch",
    "chart_manage_indicator", "tab_new", "tab_close", "watchlist_add",
}


def short_tool(tool_name):
    if not tool_name:
        return ""
    return tool_name.split("__")[-1]   # mcp__tradingview__capture_screenshot -> capture_screenshot


def decide(tool_name, flag_fresh):
    """(ok, msg). Puro."""
    st = short_tool(tool_name)
    if st not in GUARDED:
        return True, ""
    if flag_fresh:
        return True, ""
    return False, (
        f"🛑 G4 — AÇÃO MCP SEM AUTORIZAÇÃO ({st}) (Cris 2026-08-11)\n"
        "  Esta ação MCP mexe no chart/replay/alertas/plots — só por ORDEM explícita do Cris (C3 screenshots,\n"
        "  B4 plot não-canónico, B5 replay/chart descuidados). A superfície MCP não tinha guard nenhum.\n"
        "  → Se o Cris AUTORIZOU: `touch ~/.claude/.mcp_action_ok` (vale 5 min) e repete a ação.\n"
        "  → Se não autorizou: NÃO faças (screenshots/plots/mexer chart sem pedido = erro recorrente).\n")


def _flag_fresh(now):
    try:
        return (now - FLAG.stat().st_mtime) < FRESH_S
    except Exception:
        return False


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    ok, msg = decide(data.get("tool_name") or "", _flag_fresh(time.time()))
    if ok:
        return 0
    sys.stderr.write(msg)
    return 2


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        t = []
        ok, _ = decide("mcp__tradingview__capture_screenshot", False)
        t.append(("screenshot sem flag bloqueia", ok is False))
        ok, _ = decide("mcp__tradingview__capture_screenshot", True)
        t.append(("screenshot com flag passa", ok is True))
        ok, _ = decide("mcp__tradingview__replay_trade", False)
        t.append(("replay_trade sem flag bloqueia", ok is False))
        ok, _ = decide("mcp__tradingview__data_get_pine_boxes", False)
        t.append(("leitura pine_boxes passa", ok is True))
        ok, _ = decide("mcp__tradingview__quote_get", False)
        t.append(("quote_get passa", ok is True))
        ok, _ = decide("Bash", False)
        t.append(("nao-MCP passa", ok is True))
        ok, _ = decide("mcp__tradingview__draw_shape", False)
        t.append(("draw_shape sem flag bloqueia", ok is False))
        for lab, r in t:
            print(f"  [{'OK' if r else 'FAIL'}] {lab}")
        allok = all(r for _, r in t)
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    sys.exit(main())
