#!/usr/bin/env python3
"""Reader MTF (P3/E0) — lê estrutura de cada TF na SUA tab dedicada (pin via TVMCP_TARGET_CHART_ID).
Descobre o mapa tab->TF dinamicamente (robusto a reordenar tabs), pina o MCPClient a cada target, lê
OHLCV via MCP e computa estrutura com context_structure (determinístico, close-only causal). NUNCA toca
a tab do P1 nem troca símbolo. Zones OB/SMC = leitura leve de pine_boxes (nearest ao preço). py3.9.
Uso: python3 context_mtf.py            (lê e imprime o bloco MTF live)
"""
import os, sys, json, urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from draw_xau_4h_trades import MCPClient
import context_structure as cs

CDP_LIST = "http://localhost:9222/json/list"
TFS_WANTED = ("15", "60", "240", "1D")
OHLCV_COUNT = 320


def list_chart_targets():
    try:
        with urllib.request.urlopen(CDP_LIST, timeout=8) as r:
            targets = json.loads(r.read())
    except Exception:
        return []
    return [t["id"] for t in targets if t.get("type") == "page"
            and "tradingview.com/chart" in (t.get("url") or "").lower()]


def _bars_hlc(oh):
    bars = (oh or {}).get("bars") or (oh or {}).get("ohlcv") or []
    H = [b.get("high") for b in bars]; L = [b.get("low") for b in bars]; C = [b.get("close") for b in bars]
    if any(x is None for x in H + L + C):
        return None, None, None, 0
    return H, L, C, len(bars)


def _nearest_zones(c, last):
    """Leitura leve de zonas (pine_boxes): a zona OB/demanda/supply mais próxima acima/abaixo do preço."""
    try:
        pb = c.call_tool("data_get_pine_boxes") or {}
    except Exception:
        return None
    zs = []
    for study in pb.get("studies", []):
        for z in study.get("zones", []):
            hi = z.get("high"); lo = z.get("low")
            if hi is None or lo is None:
                continue
            zs.append({"high": round(float(hi), 2), "low": round(float(lo), 2), "src": (study.get("name") or "")[:14]})
    if not zs or last is None:
        return {"n": len(zs), "above": None, "below": None}
    above = min((z for z in zs if z["low"] > last), key=lambda z: z["low"], default=None)
    below = max((z for z in zs if z["high"] < last), key=lambda z: z["high"], default=None)
    return {"n": len(zs), "above": above, "below": below}


def read_mtf(count=OHLCV_COUNT, with_zones=True):
    """Devolve {tf: {target, bars, structure, zones}} para cada TF encontrado. Pin serial por tab."""
    out = {}
    saved = os.environ.get("TVMCP_TARGET_CHART_ID")
    try:
        for tid in list_chart_targets():
            os.environ["TVMCP_TARGET_CHART_ID"] = tid
            c = MCPClient()
            try:
                c.start()
                st = c.call_tool("chart_get_state") or {}
                res = str(st.get("resolution"))
                if res not in TFS_WANTED or res in out:
                    continue
                oh = c.call_tool("data_get_ohlcv", {"count": count})
                H, L, C, n = _bars_hlc(oh)
                struct = cs.structure(H, L, C) if (n and n > 40) else None
                zones = _nearest_zones(c, C[-1] if C else None) if with_zones else None
                sv = c.call_tool("data_get_study_values") or {}
                svp_v = next((s.get("values", {}) for s in sv.get("studies", []) if "Volume Profile" in (s.get("name") or "")), {})

                def _n(x):
                    try: return float(str(x).replace("K", "e3").replace(" ", ""))
                    except Exception: return None
                up, dn = _n(svp_v.get("Up")), _n(svp_v.get("Down"))
                svp = {"up": up, "dn": dn, "total": _n(svp_v.get("Total")),
                       "pressure": ("sell" if (up is not None and dn is not None and dn > up) else "buy") if (up is not None and dn is not None) else None}
                out[res] = {"target": tid[:8], "bars": n, "structure": struct, "zones": zones, "svp": svp}
            except Exception as e:
                out[res if 'res' in dir() else tid[:8]] = {"error": f"{type(e).__name__}:{str(e)[:60]}"}
            finally:
                try: c.stop()
                except Exception: pass
    finally:
        if saved is None:
            os.environ.pop("TVMCP_TARGET_CHART_ID", None)
        else:
            os.environ["TVMCP_TARGET_CHART_ID"] = saved
    return out


if __name__ == "__main__":
    mtf = read_mtf()
    for tf in ("1D", "240", "60", "15"):
        d = mtf.get(tf)
        if not d:
            print(f"[{tf}] (ausente)"); continue
        s = d.get("structure") or {}
        leg = s.get("leg") or {}
        z = d.get("zones") or {}
        print(f"[{tf}] tab {d.get('target')} bars {d.get('bars')} | trend {s.get('trend')} "
              f"| close {s.get('close')} | leg mag {leg.get('mag_atr')} pos {leg.get('pos_in_leg')} "
              f"| CHoCH dn={s.get('choch',{}).get('dn')} up={s.get('choch',{}).get('up')} "
              f"| zones n={z.get('n')} below={ (z.get('below') or {}).get('high') } above={ (z.get('above') or {}).get('low') }")
