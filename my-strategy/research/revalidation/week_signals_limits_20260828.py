#!/usr/bin/env python3
"""Avaliação dos sinais ENVIADOS ao grupo (semana 24-28/08) pelos LIMITS que teriam sido informados
(Cris 2026-08-28). AMD: limite = nível do FVG, fill no retest_t real do candidato (fill-bar SL conta).
A1/A2: limite = retest_zone reconstruído pelo detetor REAL (re-run causal) — a "entrada LIMITE ideal"
que a mensagem publica; mesmo SL, 3R do novo entry. NO-FILL registado. Read-only. py3 stdlib."""
import json
import sys
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "alert-bridge"))
sys.path.insert(0, str(REPO / "my-strategy/strategies/xau_15m_long/continuation_A1A2"))
LX = dt.timezone(dt.timedelta(hours=1))
WEEK0 = dt.datetime(2026, 8, 24, tzinfo=dt.timezone.utc).timestamp()
FILL_WIN = 16          # barras 15M para o limite encher
HORIZON = 480


def jl(p):
    try:
        return [json.loads(l) for l in open(p).read().splitlines() if l.strip()]
    except Exception:
        return []


def hm(t):
    return dt.datetime.fromtimestamp(int(t), LX).strftime("%a %d/%m %H:%M")


bars = jl(REPO / "my-strategy/core/bar_store/store/bars_15m.jsonl")
T = [b["t"] for b in bars]; H = [b["h"] for b in bars]; L = [b["l"] for b in bars]


def outcome(fill_i, e, sl):
    """SL-first 3R a partir da barra de FILL (a própria barra do fill conta — se o low fura o sl, LOSS)."""
    tgt = e + 3 * (e - sl)
    if L[fill_i] <= sl:
        return "LOSS", -1.0, 0.0, 0
    mfe = 0.0
    risk = e - sl
    for i in range(fill_i + 1, min(len(T), fill_i + HORIZON)):
        mfe = max(mfe, (H[i] - e) / risk)
        if L[i] <= sl:
            return "LOSS", -1.0, round(mfe, 2), i - fill_i
        if H[i] >= tgt:
            return "WIN", 3.0, round(mfe, 2), i - fill_i
    return "OPEN", 0.0, round(mfe, 2), len(T) - fill_i


def fill_index(after_t, level, win):
    """1ª barra após after_t cujo low toca o nível-limite, dentro de `win` barras."""
    i0 = next((i for i, t in enumerate(T) if t > after_t), None)
    if i0 is None:
        return None
    for i in range(i0, min(len(T), i0 + win)):
        if L[i] <= level:
            return i
    return None


def a1a2_retest_zone(entry_t):
    """Re-corre o detetor A1/A2 REAL sobre a série até entry_t → devolve retest_zone (o LIMITE informado)."""
    import a1a2_runtime as RT
    idx = next((i for i, t in enumerate(T) if t == entry_t), None)
    if idx is None:
        return None
    rows = [dict(t=bars[i]["t"], o=bars[i]["o"], h=bars[i]["h"], l=bars[i]["l"], c=bars[i]["c"])
            for i in range(max(0, idx - 299), idx + 1)]
    O = [b["o"] for b in rows]; Hh = [b["h"] for b in rows]; Ll = [b["l"] for b in rows]
    Cc = [b["c"] for b in rows]; Tt = [b["t"] for b in rows]
    N = len(rows); EMA = [None] * N; ATR = [None] * N; ema = None; kE = 2 / 22; trs = []
    for i in range(N):
        ema = Cc[i] if ema is None else Cc[i] * kE + ema * (1 - kE); EMA[i] = ema
        if i > 0:
            trs.append(max(Hh[i] - Ll[i], abs(Hh[i] - Cc[i - 1]), abs(Ll[i] - Cc[i - 1])))
        ATR[i] = sum(trs[-14:]) / 14 if len(trs) >= 14 else None
    S = dict(T=Tt, O=O, H=Hh, L=Ll, C=Cc, EMA=EMA, ATR=ATR, N=N)
    r, why = RT.detect(S)
    return r.get("retest_zone") if r else None


rows_out = []

# --- A1/A2 pelo LIMITE (retest_zone reconstruído) ---
for r in jl(REPO / "my-strategy/strategies/xau_15m_long/continuation_A1A2/.a1a2_state/alerted.jsonl"):
    t = r.get("entry_t")
    if not t or t < WEEK0:
        continue
    sl, ent_mkt = r.get("sl"), r.get("ent")
    rz = a1a2_retest_zone(t)
    if not rz:
        rows_out.append(("A1/A2 " + (r.get("layer") or ""), t, ent_mkt, sl, "SEM-ZONA", None, None, None))
        continue
    limit = max(rz)                       # topo do retest = 1º preço tocado por baixo
    fi = fill_index(t, limit, FILL_WIN)
    if fi is None:
        rows_out.append(("A1/A2 " + (r.get("layer") or ""), t, limit, sl, "NO-FILL", None, None, None))
        continue
    o, R, mfe, ba = outcome(fi, limit, sl)
    rows_out.append(("A1/A2 " + (r.get("layer") or ""), t, limit, sl, o, R, mfe, ba))

# --- AMD pelo LIMITE do FVG, fill no retest_t real ---
for r in jl(REPO / "my-strategy/strategies/xau_amd/amd_live/.amd_state/amd_setups.jsonl"):
    at = r.get("h4_bar_t") or 0
    if at < WEEK0:
        continue
    pinged = set(str(k) for k in (r.get("candidates_pinged") or []))
    for c in (r.get("candidates_latest") or []):
        cid = str(c.get("candidate_id"))
        if not any(k.startswith(cid) for k in pinged):
            continue
        e, sl = c.get("ent"), c.get("sl")
        rt = c.get("retest_t")
        if not rt:
            rows_out.append((f"AMD {r.get('dir')}", at, e, sl, "NO-FILL(sem retest)", None, None, None))
            continue
        fi = next((i for i, tt in enumerate(T) if tt >= rt), None)
        if fi is None:
            rows_out.append((f"AMD {r.get('dir')}", rt, e, sl, "SEM-BARRAS", None, None, None))
            continue
        o, R, mfe, ba = outcome(fi, e, sl)
        rows_out.append((f"AMD {r.get('dir')}", rt, e, sl, o, R, mfe, ba))

rows_out.sort(key=lambda x: x[1])
print(f"=== SINAIS DO GRUPO pelos LIMITS informados · semana 24-28/08 · N={len(rows_out)} ===")
print(f"{'linha':<14}{'quando':<17}{'limite':>8}{'sl':>8}{'res':>18}{'R':>5}{'MFE':>6}{'barras':>7}")
tot = 0.0; w = l = op = nf = 0
for lab, t, e, sl, o, R, mfe, ba in rows_out:
    print(f"{lab:<14}{hm(t):<17}{(e or 0):>8.1f}{(sl or 0):>8.1f}{o:>18}"
          f"{(R if R is not None else 0):>5.0f}{(mfe if mfe is not None else 0):>6.2f}{(ba if ba is not None else 0):>7}")
    if R is not None:
        tot += R
        w += o == "WIN"; l += o == "LOSS"; op += o == "OPEN"
    elif "NO-FILL" in o:
        nf += 1
print(f"\nRESUMO limite: {w}W-{l}L-{op}OPEN · NO-FILL {nf} · sumR {tot:+.0f}R (fills; no-fill=trade não aconteceu)")
