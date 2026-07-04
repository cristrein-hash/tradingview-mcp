#!/usr/bin/env python3
"""DA independente — RAW_15M_EXTENSION_COLLECT_TO_TODAY (2026-07-04).
(1) Kill-check N=0: 240 candidatos virgens todos BEAR? recompute regime_hourcausal via exec do engine
    (3 spot + full sweep 240). (2) Sanity de preço no 9º bloco primitives (~4560→~4000).
(3) Densidade de primitivas 9º vs 8º bloco. (4) Spec congelada do kill-check vs Lab G frozen spec."""
import json, datetime as dt
from pathlib import Path
HERE = Path(__file__).parent
PREV_END = 1779667200

# ---- (1) candidatos virgens ----
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
V = sorted([r for r in U if r["cj_t"] > PREV_END], key=lambda r: r["cj_t"])
from collections import Counter
reg = Counter(r["g_v5h"] for r in V)
print(f"[1] total {len(U)} · virgens {len(V)} · regimes {dict(reg)}")
assert len(V) == 240 and reg.get("BEAR") == 240 and len(reg) == 1, "nem todos BEAR / N!=240"

ns = {"__name__": "engine", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "engine", "exec"), ns)
rh = ns["regime_hourcausal"]
for r in (V[0], V[len(V) // 2], V[-1]):
    rc = rh(r["cj_t"])
    print(f"    spot {dt.datetime.utcfromtimestamp(r['cj_t'])} stored={r['g_v5h']} recomputed={rc}")
    assert rc == r["g_v5h"]
mism = sum(1 for r in V if rh(r["cj_t"]) != r["g_v5h"])
print(f"    full-sweep 240: mismatches={mism}"); assert mism == 0

# ---- (2) sanity preço 9º bloco ----
p9 = json.load(open(HERE / "primitives" / "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.primitives.json"))
s9 = p9["series"]
print(f"[2] 9º bloco: {len(s9)} bars · first {dt.datetime.utcfromtimestamp(s9[0]['t'])} c={s9[0]['c']}"
      f" · last {dt.datetime.utcfromtimestamp(s9[-1]['t'])} c={s9[-1]['c']}"
      f" · hi {max(b['h'] for b in s9)} lo {min(b['l'] for b in s9)}")
assert s9[0]["c"] > 4500 and min(b["l"] for b in s9) < 4050, "queda ~4560→~4000 não confere"

# ---- (3) densidade 9º vs 8º ----
p8 = json.load(open(HERE / "primitives" / "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.primitives.json"))
for tag, p in (("8º", p8), ("9º", p9)):
    nb = len(p["series"])
    print(f"[3] {tag}: bars {nb} · NAS {len(p['nas_events'])} ({len(p['nas_events'])/nb*1000:.1f}/kbar)"
          f" · SMC {len(p['smc_events'])} ({len(p['smc_events'])/nb*1000:.1f}/kbar)"
          f" · OB {len(p['zones'])} ({len(p['zones'])/nb*1000:.1f}/kbar)")

# ---- (4) spec congelada vs Lab G ----
lg = json.load(open(HERE / "results" / "lab_g_systems_results.json"))
def find_spec(o, out):
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)): find_spec(v, out)
            elif isinstance(v, str) and ("wf_15184946" in str(k) + v or "SHAKEOUT" in v.upper()): out.append((k, v))
        if "spec" in o or "rule" in o or "gates" in o: out.append(("NODE", json.dumps(o)[:400]))
    elif isinstance(o, list):
        for v in o: find_spec(v, out)
hits = []
find_spec(lg, hits)
for k, v in hits[:6]: print(f"[4] labG hit: {k}: {v[:300]}")
