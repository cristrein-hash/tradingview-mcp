#!/usr/bin/env python3
"""Reader CONFLUÊNCIA (P3/E0 enrich) — auction-intensity AO LONGO DA PERNA (descoberta Cp) + NAS, live.
Reusa o mapeamento VALIDADO dos Market Order Bubbles (consistente em 8 scripts Cp):
  BUY (verde)  = plot_0(1) plot_2(2) plot_4(3)   [tamanho small/med/large]
  SELL (vermelho) = plot_6(1) plot_8(2) plot_10(3)
act_dens = order-flow ponderado ativado do início da perna até agora / duração (Cp: GT 0,82 vs losers 0,48).
Extração live via data_get_pine_shapes (não RAW snapshots como no research). Pina a tab do TF. py3.9.
Uso: python3 context_confluence.py
"""
import os, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from draw_xau_4h_trades import MCPClient
from context_mtf import list_chart_targets
import context_structure as cs

BUY = {"plot_0": 1, "plot_2": 2, "plot_4": 3}      # verde (mapeamento validado Cp)
SELL = {"plot_6": 1, "plot_8": 2, "plot_10": 3}    # vermelho
WIN_BARS = 4                                        # janela do sinal (~1h em 15M) — F-A1.3


def _split_sides(pairs):
    """Soma bubbles por lado a partir de pares (t, plot). Puro/testável (F-A1.3)."""
    bw = sw = bn = sn = 0
    for (_t, plot) in pairs:
        if plot in BUY: bw += BUY[plot]; bn += 1
        elif plot in SELL: sw += SELL[plot]; sn += 1
    return bn, bw, sn, sw


def _window_block(pairs, W):
    """Bubbles por lado na JANELA recente do sinal (F-A1.3): resolve o defeito de sexta (o leg-aggregate
    diluía a ausência de iniciativa recente). Descritivo — o read pondera como voz."""
    bn, bw, sn, sw = _split_sides(pairs)
    net = "buy" if bw > sw else ("sell" if sw > bw else "none")
    return {"bars": W, "buy": {"n": bn, "weight": bw}, "sell": {"n": sn, "weight": sw}, "net_side": net}


def _acts(pb):
    out = []
    for s in (pb or {}).get("studies", []):
        for a in s.get("activations", []):
            t = a.get("time")
            for plot in (a.get("shapes") or {}):
                out.append((t, plot))
    return out


def read_confluence_store(tf="15", count=320):
    """STORE-FIRST (Fase 1, 2026-07-18): confluência da perna via bar-store, zero CDP. None se não-fresco."""
    import store_reader as SR
    if tf != "15" or not SR.fresh("15"):
        return None
    rs = SR.bars("15", count)
    if len(rs) < 50:
        return None
    H = [r["h"] for r in rs]; L = [r["l"] for r in rs]; Cc = [r["c"] for r in rs]; T = [r["t"] for r in rs]
    stru = cs.structure(H, L, Cc)
    sw = stru.get("swings", {})
    bars_idx = [sw.get(k, {}).get("bar") for k in ("last_low", "last_high") if sw.get(k)]
    leg_start = min(bars_idx) if bars_idx else max(0, len(T) - 30)
    t0 = T[leg_start] if 0 <= leg_start < len(T) else T[0]
    t1 = T[-1]
    dur_bars = max(1, len(T) - leg_start)
    buy_w = sell_w = buy_n = sell_n = 0
    for (t, plot) in SR.shape_pairs("bubbles", t0, t1):
        if plot in BUY: buy_w += BUY[plot]; buy_n += 1
        elif plot in SELL: sell_w += SELL[plot]; sell_n += 1
    nas_n = len(SR.shape_pairs("nas", t0, t1))
    act_dens = round((buy_w + sell_w) / dur_bars, 3)
    t_win = T[-WIN_BARS] if len(T) >= WIN_BARS else t0
    window = _window_block(SR.shape_pairs("bubbles", t_win, t1), WIN_BARS)   # F-A1.3
    return {
        "tf": tf, "leg_start_bar": leg_start, "leg_dur_bars": dur_bars,
        "leg": stru.get("leg"), "trend": stru.get("trend"),
        "buy": {"n": buy_n, "weight": buy_w, "dens": round(buy_w / dur_bars, 3)},
        "sell": {"n": sell_n, "weight": sell_w, "dens": round(sell_w / dur_bars, 3)},
        "nas_n": nas_n, "act_dens": act_dens,
        "leg_sell": sell_w, "buy_dens": round(buy_w / dur_bars, 3),
        "window": window,
    }


def read_confluence(tf="15", count=320, max_bars=500):
    """Confluência de order-flow na perna corrente do TF dado (default 15M). STORE-FIRST; fallback MCP."""
    try:
        st = read_confluence_store(tf, count)
        if st is not None:
            return st
    except Exception:
        pass
    try:                                                  # anti-herd (auditoria #5): gate o fallback-MCP
        import store_reader as SR
        if not SR.fallback_ok("confluence"):
            return None
    except Exception:
        pass
    saved = os.environ.get("TVMCP_TARGET_CHART_ID")
    try:
        for tid in list_chart_targets():
            os.environ["TVMCP_TARGET_CHART_ID"] = tid
            c = MCPClient()
            try:
                c.start()
                st = c.call_tool("chart_get_state") or {}
                if str(st.get("resolution")) != tf:
                    continue
                oh = c.call_tool("data_get_ohlcv", {"count": count}) or {}
                bars = oh.get("bars") or oh.get("ohlcv") or []
                if len(bars) < 50:
                    return {"error": "poucas barras"}
                H = [b.get("high") for b in bars]; L = [b.get("low") for b in bars]
                Cc = [b.get("close") for b in bars]; T = [b.get("time") for b in bars]
                stru = cs.structure(H, L, Cc)
                sw = stru.get("swings", {})
                # janela da perna = do swing mais antigo (low/high) até agora
                bars_idx = [sw.get(k, {}).get("bar") for k in ("last_low", "last_high") if sw.get(k)]
                leg_start = min(bars_idx) if bars_idx else max(0, len(T) - 30)
                t0 = T[leg_start] if 0 <= leg_start < len(T) else T[0]
                t1 = T[-1]
                dur_bars = max(1, len(T) - leg_start)
                # bubbles + NAS (na tab do TF)
                pb = c.call_tool("data_get_pine_shapes", {"study_filter": "Market Order", "max_bars": max_bars})
                nb = c.call_tool("data_get_pine_shapes", {"study_filter": "NAS", "max_bars": max_bars})
                buy_w = sell_w = buy_n = sell_n = 0
                for (t, plot) in _acts(pb):
                    if t is None or t < t0 or t > t1:
                        continue
                    if plot in BUY: buy_w += BUY[plot]; buy_n += 1
                    elif plot in SELL: sell_w += SELL[plot]; sell_n += 1
                nas_n = sum(1 for (t, _p) in _acts(nb) if t is not None and t0 <= t <= t1)
                act_dens = round((buy_w + sell_w) / dur_bars, 3)
                t_win = T[-WIN_BARS] if len(T) >= WIN_BARS else t0
                wpairs = [(t, plot) for (t, plot) in _acts(pb) if t is not None and t_win <= t <= t1]
                window = _window_block(wpairs, WIN_BARS)                    # F-A1.3
                return {
                    "tf": tf, "leg_start_bar": leg_start, "leg_dur_bars": dur_bars,
                    "leg": stru.get("leg"), "trend": stru.get("trend"),
                    "buy": {"n": buy_n, "weight": buy_w, "dens": round(buy_w / dur_bars, 3)},
                    "sell": {"n": sell_n, "weight": sell_w, "dens": round(sell_w / dur_bars, 3)},
                    "nas_n": nas_n,
                    "act_dens": act_dens,                                    # Cp: GT ~0.82 vs losers ~0.48
                    "leg_sell": sell_w,                                      # Cp gate: leg_sell>=180 (janela grande)
                    "buy_dens": round(buy_w / dur_bars, 3),                  # Cp gate: buy_dens>=0.25
                    "window": window,
                }
            except Exception as e:
                return {"error": f"{type(e).__name__}:{str(e)[:60]}"}
            finally:
                try: c.stop()
                except Exception: pass
    finally:
        if saved is None:
            os.environ.pop("TVMCP_TARGET_CHART_ID", None)
        else:
            os.environ["TVMCP_TARGET_CHART_ID"] = saved
    return {"error": f"tab {tf} nao encontrada"}


def _selftest():
    pairs = [(1, "plot_6"), (2, "plot_8"), (3, "plot_0")]   # sell 1+2=3 (n2) · buy 1 (n1)
    bn, bw, sn, sw = _split_sides(pairs); w = _window_block(pairs, WIN_BARS)
    r = [("split buy", (bn, bw) == (1, 1)), ("split sell", (sn, sw) == (2, 3)),
         ("net sell", w["net_side"] == "sell"), ("vazio -> none", _window_block([], WIN_BARS)["net_side"] == "none")]
    allok = all(ok for _, ok in r)
    for name, ok in r: print(f"  {'OK' if ok else 'FALHA'} {name}")
    print("SELFTEST context_confluence:", "PASS" if allok else "FALHA")
    return 0 if allok else 1


if __name__ == "__main__":
    import json
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    print(json.dumps(read_confluence("15"), indent=1, ensure_ascii=False))
