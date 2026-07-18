#!/usr/bin/env python3
"""STORE READER — API única de leitura do bar-store (Fase 1 arquitetura realtime, Cris 2026-07-18).
Consumidores (E0/Cp/regime/backfill) leem AQUI em vez de abrir MCPClient próprio — zero CDP.
Frescura = heartbeat do store (store_meta.poll[tf]), NÃO o tempo da última barra (fim-de-semana o
mercado para mas o store continua a bater). fresh() falso => consumidor decide fallback/no-op. py3.9."""
import json, time
from pathlib import Path
STORE = Path("/Users/cristrein/tradingview-mcp/my-strategy/core/bar_store/store")
REV = Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation")
FILES = {"15": STORE / "bars_15m.jsonl", "60": REV / "raw_1h_ohlc.jsonl",
         "240": REV / "raw_4h_ohlc.jsonl", "1D": STORE / "bars_1d.jsonl"}
POLL = {"15": 60, "60": 300, "240": 900, "1D": 900}


def _jl(f):
    try:
        return [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    except Exception:
        return []


def _snap(name, tf):
    try:
        return json.loads((STORE / f"{name}_{tf}.json").read_text())
    except Exception:
        return None


def fresh(tf, mult=3.0):
    """Heartbeat do store para o TF: último poll há menos de mult×período."""
    try:
        m = json.loads((STORE / "store_meta.json").read_text())
        ts = (m.get("poll") or {}).get(tf) or 0
        return (time.time() - ts) <= mult * POLL.get(tf, 900)
    except Exception:
        return False


def bars(tf, count=None):
    """Barras fechadas validadas do TF (dicts {t,o,h,l,c}, ordenadas). count = últimas N."""
    rows = _jl(FILES[tf])
    return rows[-count:] if count else rows


def bars_ohlc(tf, count=None):
    """(T,O,H,L,C) em listas — formato dos engines."""
    rs = bars(tf, count)
    return ([r["t"] for r in rs], [r["o"] for r in rs], [r["h"] for r in rs],
            [r["l"] for r in rs], [r["c"] for r in rs])


def shape_pairs(kind="bubbles", t0=None, t1=None):
    """Union de activations (kind: bubbles|nas) como (t, plot); opcional janela [t0,t1]."""
    f = STORE / f"{kind}_15m.jsonl"
    out = []
    for r in _jl(f):
        t = r.get("t")
        if t is None: continue
        if t0 is not None and t < t0: continue
        if t1 is not None and t > t1: continue
        out.append((t, r.get("plot")))
    return out


def pine_boxes(tf):
    """Snapshot pine_boxes da tab do TF: (payload_raw, age_s) ou (None, None)."""
    s = _snap("pine_boxes", tf)
    if not s: return None, None
    return s.get("data"), time.time() - (s.get("ts") or 0)


def study_values(tf):
    s = _snap("study_values", tf)
    if not s: return None, None
    return s.get("data"), time.time() - (s.get("ts") or 0)
