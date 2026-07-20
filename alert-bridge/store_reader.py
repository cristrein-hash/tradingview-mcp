#!/usr/bin/env python3
"""STORE READER — API única de leitura do bar-store (Fase 1 arquitetura realtime, Cris 2026-07-18).
Consumidores (E0/Cp/regime/backfill) leem AQUI em vez de abrir MCPClient próprio — zero CDP.
Frescura = heartbeat do store (store_meta.poll[tf]), NÃO o tempo da última barra (fim-de-semana o
mercado para mas o store continua a bater). fresh() falso => consumidor decide fallback/no-op. py3.9."""
import json, time, os, random
from pathlib import Path
STORE = Path("/Users/cristrein/tradingview-mcp/my-strategy/core/bar_store/store")
_FALLBACK_GATE = STORE / ".mcp_fallback_gate.json"
FALLBACK_MIN_GAP_S = 20         # no máximo ~1 fallback-MCP a cada 20s no stack inteiro (anti-thundering-herd)
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


def fallback_ok(tag="?", min_gap=FALLBACK_MIN_GAP_S):
    """Gate anti-thundering-herd: quando o bar-store fica STALE, todos os consumidores caem para MCP próprio
    ao mesmo tempo e martelam o :9222 (o oposto do desenho single-reader). Isto permite NO MÁXIMO ~1
    fallback-MCP a cada `min_gap`s no stack inteiro (rate-limit partilhado por ficheiro) + jitter curto para
    desincronizar. Devolve True se PODE cair para MCP agora; False => salta este ciclo (espera o store).
    Fail-OPEN (em dúvida devolve True — nunca bloqueia a leitura por bug do gate)."""
    def _last():
        try: return json.loads(_FALLBACK_GATE.read_text()).get("last_ts", 0)
        except Exception: return 0
    if time.time() - _last() < min_gap:
        return False                                  # outro consumidor caiu para MCP há pouco -> espera o store
    try: time.sleep(random.uniform(0, 0.4))           # jitter: desincroniza quem colide no mesmo instante
    except Exception: pass
    if time.time() - _last() < min_gap:               # re-verifica após jitter (outro pode ter passado)
        return False
    try:
        tmp = _FALLBACK_GATE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({"last_ts": time.time(), "by": tag})); os.replace(tmp, _FALLBACK_GATE)
    except Exception:
        return True                                   # fail-open
    return True


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
