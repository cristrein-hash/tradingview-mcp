#!/usr/bin/env python3
"""Avaliação um-a-um dos sinais ENVIADOS ao grupo esta semana (AMD ping2 + A1/A2). Cris 2026-08-28.
Resolve cada sinal contra bars_15m do store (SL-first, 3R). Read-only. py3 stdlib."""
import json
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
LX = dt.timezone(dt.timedelta(hours=1))
WEEK0 = dt.datetime(2026, 8, 24, tzinfo=dt.timezone.utc).timestamp()   # seg 24/08


def jl(p):
    try:
        return [json.loads(l) for l in open(p).read().splitlines() if l.strip()]
    except Exception:
        return []


def hm(t):
    return dt.datetime.fromtimestamp(int(t), LX).strftime("%a %d/%m %H:%M")


bars = jl(REPO / "my-strategy/core/bar_store/store/bars_15m.jsonl")
T = [b["t"] for b in bars]
H = [b["h"] for b in bars]
L = [b["l"] for b in bars]


def resolve(entry_t, e, sl, tgt, long=True):
    """SL-first 3R + MFE. Devolve (outcome, R, mfe_R, bars_alive)."""
    if not (entry_t and e and sl):
        return "SEM-DADOS", None, None, None
    i0 = next((i for i, t in enumerate(T) if t > entry_t), None)
    if i0 is None:
        return "FUTURO/SEM-BARRAS", None, None, None
    risk = (e - sl) if long else (sl - e)
    if risk <= 0:
        return "RISK<=0", None, None, None
    mfe = 0.0
    for i in range(i0, len(T)):
        fav = (H[i] - e) / risk if long else (e - L[i]) / risk
        mfe = max(mfe, fav)
        if long:
            if L[i] <= sl:
                return "LOSS", -1.0, round(mfe, 2), i - i0
            if H[i] >= tgt:
                return "WIN", 3.0, round(mfe, 2), i - i0
        else:
            if H[i] >= sl:
                return "LOSS", -1.0, round(mfe, 2), i - i0
            if L[i] <= tgt:
                return "WIN", 3.0, round(mfe, 2), i - i0
    return "OPEN", 0.0, round(mfe, 2), len(T) - i0


rows = []

# --- A1/A2 (alerted.jsonl) ---
for r in jl(REPO / "my-strategy/strategies/xau_15m_long/continuation_A1A2/.a1a2_state/alerted.jsonl"):
    t = r.get("entry_t")
    if not t or t < WEEK0:
        continue
    e, sl, tgt = r.get("ent"), r.get("sl"), r.get("tgt")
    o, R, mfe, ba = resolve(t, e, sl, tgt, long=True)
    rows.append(("A1/A2 " + (r.get("layer") or ""), t, e, sl, tgt, o, R, mfe, ba))

# --- AMD ping2 (candidatos efetivamente PINGADOS ao grupo) ---
for r in jl(REPO / "my-strategy/strategies/xau_amd/amd_live/.amd_state/amd_setups.jsonl"):
    at = r.get("h4_bar_t") or 0
    pinged = set(r.get("candidates_pinged") or [])
    if not pinged:
        continue
    long = r.get("dir") == "long"
    for c in (r.get("candidates_latest") or []):
        cid = c.get("candidate_id")
        # foi realmente pingado? (id:status em candidates_pinged)
        if not any(str(k).startswith(str(cid)) for k in pinged):
            continue
        e, sl, tgt = c.get("ent"), c.get("sl"), c.get("tgt")
        # timestamp do envio = quando o setup armou (ping2 sai na janela); usa h4_bar_t como âncora causal
        et = at
        if et < WEEK0:
            continue
        o, R, mfe, ba = resolve(et, e, sl, tgt, long=long)
        rows.append((f"AMD {r.get('dir')} {r.get('setup_id','')[-8:]}", et, e, sl, tgt, o, R, mfe, ba))

rows.sort(key=lambda x: x[1])
print(f"=== SINAIS ENVIADOS AO GRUPO · semana 24-28/08 · N={len(rows)} ===")
print(f"{'linha':<18}{'quando':<17}{'entry':>8}{'sl':>8}{'tgt':>8}{'res':>7}{'R':>5}{'MFE':>6}{'barras':>7}")
tot = 0.0
w = l = op = 0
for lab, t, e, sl, tgt, o, R, mfe, ba in rows:
    print(f"{lab:<18}{hm(t):<17}{(e or 0):>8.1f}{(sl or 0):>8.1f}{(tgt or 0):>8.1f}{o:>7}"
          f"{(R if R is not None else 0):>5.0f}{(mfe if mfe is not None else 0):>6.2f}{(ba if ba is not None else 0):>7}")
    if R is not None:
        tot += R
        if o == "WIN":
            w += 1
        elif o == "LOSS":
            l += 1
        elif o == "OPEN":
            op += 1
print(f"\nTOTAL resolvidos: {w}W-{l}L-{op}OPEN · sumR {tot:+.0f}R (3R fixo, SL-first)")
