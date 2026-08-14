#!/usr/bin/env python3
"""FASE 1 (real-indicator) — faca-vs-dip nos 37 LONG-candidatos da semana, ancorado nos INDICADORES REAIS
capturados por replay (OB Detector DEMAND/SUPPLY as-of-bar), NAO em estrutura re-derivada. READ_OB_ZONES:
consome o OB Detector lido (pine_boxes da captura replay), nunca inventa/re-deriva zona.

Universo = candle_reads.jsonl com read.direction==LONG na semana (momentos reais onde um LONG seria emitido
e o guard aplicaria). Rotulo OBJETIVO por resultado forward (MFE/MAE em ATR). Extrai C6 (localizacao vs OB
real) + C4 (vela bidirecional). Fonte fiel = a mesma que a producao consumiria. py3."""
import sys, json, datetime as dt
from pathlib import Path

ROOT = Path("/Users/cristrein/tradingview-mcp")
CAP15 = ROOT / "alert-bridge/logs/backtests/XAUUSD_15m_replay_2026-08-10_to_2026-08-14.jsonl"
READS = ROOT / "alert-bridge/logs/candle_reads.jsonl"
MON = int(dt.datetime(2026, 8, 10, tzinfo=dt.timezone.utc).timestamp())


def utc(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%m-%d %H:%M")


# --- 1) universo: LONG reads da semana ---
longs = []
for l in open(READS):
    if not l.strip():
        continue
    r = json.loads(l)
    bt = r.get("bar_t")
    if bt is None or int(bt) < MON:
        continue
    rd = r.get("read") or {}
    if (rd.get("direction") or "") == "LONG":
        longs.append({"t": int(bt), "bar": r.get("bar") or {}, "conv": rd.get("conviction"),
                      "phase": rd.get("phase"), "at_level": rd.get("at_level")})
# dedup por bar_t (varios reads na mesma barra)
seen = {}
for e in longs:
    seen[e["t"]] = e
longs = sorted(seen.values(), key=lambda x: x["t"])
print(f"LONG-candidatos únicos na semana: {len(longs)}")

# --- 2) indexar a captura replay 15M por barra as-of (stream, só campos necessários) ---
# chave = t da última barra ohlcv de cada linha replay (a barra as-of, causal)
capidx = {}       # t -> {ob_boxes:[(text,low,high)], close}
allbars = []      # série de barras 15M (t,o,h,l,c) para forward-label
for l in open(CAP15):
    if not l.strip():
        continue
    r = json.loads(l)
    oh = r.get("ohlcv")
    bars = oh.get("bars") if isinstance(oh, dict) else oh
    if not bars:
        continue
    last = bars[-1]
    t = int(last.get("t") or last.get("time"))
    # OB Detector all_boxes (com texto DEMAND/SUPPLY)
    obs = []
    pb = r.get("pine_boxes") or {}
    for s in (pb.get("studies") if isinstance(pb, dict) else pb) or []:
        if "OB Detector" in s.get("name", ""):
            for b in (s.get("all_boxes") or []):
                if b.get("text"):
                    obs.append((b["text"], float(b["low"]), float(b["high"])))
    capidx[t] = {"ob": obs, "c": float(last.get("close") or last.get("c"))}
    allbars.append((t, float(last.get("open") or last.get("o")), float(last.get("high") or last.get("h")),
                    float(last.get("low") or last.get("l")), float(last.get("close") or last.get("c"))))
allbars = sorted(set(allbars), key=lambda x: x[0])
bt_list = [b[0] for b in allbars]
print(f"barras replay 15M indexadas: {len(capidx)}")


def atr(idx, n=14):
    if idx < n:
        return 5.0
    s = sum(max(allbars[k][2]-allbars[k][3], abs(allbars[k][2]-allbars[k-1][4]),
                abs(allbars[k][3]-allbars[k-1][4])) for k in range(idx-n+1, idx+1))
    return s/n or 5.0


def outcome(t):
    """faca/dip por resultado forward (8 barras 15M): reclaim/bounce=DIP, breakdown=FACA. Causal."""
    try:
        i = bt_list.index(t)
    except ValueError:
        return None
    a = atr(i)
    fut = allbars[i+1:i+9]
    if not fut:
        return None
    c0 = allbars[i][4]
    mae = (c0 - min(b[3] for b in fut)) / a       # quão fundo (adverso p/ long)
    mfe = (max(b[2] for b in fut) - c0) / a       # quão alto (favor p/ long)
    lab = "DIP" if mfe >= mae else "FACA"
    return {"label": lab, "mfe": round(mfe, 2), "mae": round(mae, 2), "atr": round(a, 2)}


def c4_candle(bar):
    """Absorção bidirecional da vela do read (real)."""
    o, h, l, c = bar.get("o"), bar.get("h"), bar.get("l"), bar.get("c")
    if None in (o, h, l, c):
        return {}
    rng = max(1e-9, h-l)
    return {"close_pos": round((c-l)/rng, 2),
            "lower_wick": round((min(o, c)-l)/rng, 2),   # absorção compradora
            "upper_wick": round((h-max(o, c))/rng, 2)}   # absorção vendedora


def c6_location(t, price):
    """C6 REAL: preço cai para dentro de DEMAND OB por baixo (protege long) ou rompe p/ vazio (faca)?"""
    cap = capidx.get(t)
    if not cap:
        # barra mais próxima <= t
        cand = [tt for tt in capidx if tt <= t]
        cap = capidx[max(cand)] if cand else None
    if not cap:
        return {}
    dem = [(lo, hi) for (tx, lo, hi) in cap["ob"] if "DEMAND" in tx.upper()]
    # zona DEMAND que contém ou está logo abaixo do preço
    below = [(lo, hi) for (lo, hi) in dem if lo <= price <= hi+0.5 or (hi < price and price-hi < 15)]
    inside = any(lo <= price <= hi for (lo, hi) in dem)
    nearest = min((price-hi for (lo, hi) in dem if hi <= price), default=None)
    return {"in_demand": inside, "demand_near_below": bool(below),
            "dist_to_demand": round(nearest, 1) if nearest is not None else None,
            "n_demand": len(dem)}


# --- 3) montar dataset + contingência ---
rows = []
for e in longs:
    oc = outcome(e["t"])
    if not oc:
        continue
    c4 = c4_candle(e["bar"])
    c6 = c6_location(e["t"], e["bar"].get("c") or capidx.get(e["t"], {}).get("c"))
    rows.append({"t": e["t"], "conv": e["conv"], **oc, **c4, **c6})

print(f"\neventos com rótulo: {len(rows)}")
print("="*100)
for r in rows:
    print("%s | %-4s mfe%4.1f mae%4.1f | close_pos%.2f loW%.2f upW%.2f | in_DEM=%-5s dem_below=%-5s dist=%s | conv%s"
          % (utc(r["t"]), r["label"], r["mfe"], r["mae"], r.get("close_pos", 0), r.get("lower_wick", 0),
             r.get("upper_wick", 0), str(r.get("in_demand")), str(r.get("demand_near_below")),
             r.get("dist_to_demand"), r.get("conv")))

print("\n" + "="*100)
print("DISCRIMINAÇÃO C6 (localização vs OB real) — a hipótese-chave")
print("="*100)
for lab in ("FACA", "DIP"):
    g = [r for r in rows if r["label"] == lab]
    if not g:
        continue
    ind = sum(1 for r in g if r.get("in_demand"))
    below = sum(1 for r in g if r.get("demand_near_below"))
    print("%s n=%2d | in_DEMAND=%d (%.0f%%) | demand_near_below=%d (%.0f%%)"
          % (lab, len(g), ind, 100*ind/len(g), below, 100*below/len(g)))
print("\nHipótese: DIPs caem DENTRO/perto de DEMAND OB (protege long); FACAs rompem para vazio. "
      "Amostra pequena — não é prova, é sinal. C2(liquidez) fica para passo seguinte.")
