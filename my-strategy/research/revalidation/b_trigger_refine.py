#!/usr/bin/env python3
"""REFINO DO GATILHO DE B (Cris 2026-07-15) — exigir SPRING/ABSORÇÃO no suporte e testar contra o NULL.
Em vez de decidir por N=4, enumera TODOS os dips (swing-lows) na porção BAIXA (gated: ORDERLY + pos<=40%
da banda causal) do range plano de 2025 e compara a taxa de 3R:
  baseline (todos os dips gated = o null)  vs  SPRING  vs  ABSORÇÃO  vs  SPRING|ABSORÇÃO.
Definições causais (no low-âncora do dip):
  SPRING    = o low varreu ABAIXO do suporte imediato (penúltimo swing-low) e o MB3 RECUPEROU acima dele.
  ABSORÇÃO  = vela do low-âncora com mecha inferior >=0.4 do range E close na metade de cima (>=0.5).
Entrada/SL/alvo = MB3 + SL low-real + 3R (a1_causal_entry). Se spring/absorção > baseline => refino vale.
RAW 15M. Marca onde caem os 4 GT fundos."""
import json, bisect, statistics, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import b_engine_v1 as BE
from a1_causal_entry import load_series, causal_entry, _is_swinglow, M_FRAC
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
BLK = ["XAUUSD_15m_replay_2025-02-25_to_2025-05-25.jsonl.gz", "XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz",
       "XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz"]
S = load_series(BLK); T, O, H, L, C, ATR, N = S["T"], S["O"], S["H"], S["L"], S["C"], S["ATR"], S["N"]
# janela do range plano de 2025 (ORDERLY): 2025-05-14 .. 2025-09-03
t_lo = int(dt.datetime(2025, 5, 14, tzinfo=dt.timezone.utc).timestamp())
t_hi = int(dt.datetime(2025, 9, 4, tzinfo=dt.timezone.utc).timestamp())

def gated(t0):
    g = BE.BG.gate_at(t0)
    if not g["b_long_allowed"]: return False
    band = BE.causal_band(t0, S)
    if band is None: return False
    return band  # (sup,res)

def flags(e):
    """spring / absorção no low-âncora do dip e."""
    ab = e["anchor_bar"]; atr = ATR[ab] or 5.0
    # suporte imediato = penúltimo swing-low antes de ab
    lows = [(p, L[p]) for p in range(max(M_FRAC, ab-64), ab) if _is_swinglow(L, p, M_FRAC)]
    support = lows[-1][1] if lows else None
    spring = support is not None and L[ab] < support-0.1*atr and e["ent"] > support
    rng = max(1e-9, H[ab]-L[ab])
    lw = (min(O[ab], C[ab])-L[ab])/rng; cp = (C[ab]-L[ab])/rng
    absorb = lw >= 0.4 and cp >= 0.5
    return spring, absorb

# enumera dips (swing-lows) gated e classifica
seen = set(); rows = []
for p in range(M_FRAC, N-M_FRAC):
    if not (t_lo <= T[p] <= t_hi): continue
    if not _is_swinglow(L, p, M_FRAC): continue
    e = causal_entry(S, p, "MB3")
    if not e or e["ei"] in seen: continue
    seen.add(e["ei"])
    band = gated(T[p])
    if not band: continue
    sup, res = band; pos = 100*(L[e["anchor_bar"]]-sup)/max(1e-9, res-sup)
    if pos > BE.POS_MAX: continue
    spr, ab = flags(e)
    rows.append({"ei": e["ei"], "t": T[e["ei"]], "o": e["o"], "spring": spr, "absorb": ab, "pos": round(pos)})

def hit(sub):
    v = [r for r in sub if r["o"] in ("WIN", "LOSS")]
    w = sum(1 for r in v if r["o"] == "WIN")
    return w, len(v), (100*w/len(v) if v else 0)

print(f"Dips GATED (ORDERLY + pos<=40%) no range plano 2025: N={len(rows)}")
for lab, sub in [("baseline (todos=null)", rows),
                 ("SPRING", [r for r in rows if r["spring"]]),
                 ("ABSORÇÃO", [r for r in rows if r["absorb"]]),
                 ("SPRING|ABSORÇÃO", [r for r in rows if r["spring"] or r["absorb"]]),
                 ("SEM spring/absorção", [r for r in rows if not (r["spring"] or r["absorb"])])]:
    w, n, hr = hit(sub); op = sum(1 for r in sub if r["o"] == "OPEN")
    print(f"  {lab:24} N={len(sub):3d}  hit-3R {hr:4.0f}% ({w}/{n})  OPEN {op}")
# onde caem os 4 GT fundos
GT = json.load(open(HERE/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
B4 = sorted([f for f in GT["fundos"] if f.get("subclasse") == "B_range"], key=lambda x: x["t"])[:4]
print("\n4 GT fundos B#1-4 (têm spring/absorção?):")
for n, f in enumerate(B4, 1):
    e = causal_entry(S, bisect.bisect_right(T, int(f["t"]))-1, "MB3")
    if e: spr, ab = flags(e); print(f"  B#{n} {ds(int(f['t']))}  {e['o']:5} spring={spr} absorb={ab}")