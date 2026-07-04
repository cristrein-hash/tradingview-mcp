#!/usr/bin/env python3
"""BEAR-PULLBACK · PROBE 5 — diagnóstico outcome-blind: por que o episódio do trade #20
(2025-10-30 07:15) não dispara na CONFIG V3. Avalia sub-fatores barra a barra na janela
da âncora 10-30 03:45 (e âncoras vizinhas). Zero leitura de outcome."""
import json, glob, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; N = len(S)
L = [b["l"] for b in S]; H = [b["h"] for b in S]; C = [b["c"] for b in S]
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def asof(t): return bisect.bisect_right(TS, t) - 1
t0 = int(dt.datetime(2025, 10, 29, 12, 0).replace(tzinfo=dt.timezone.utc).timestamp())
t1 = int(dt.datetime(2025, 10, 30, 12, 0).replace(tzinfo=dt.timezone.utc).timestamp())
print("âncoras candidatas na janela (qualificação V3):")
for r in U:
    if t0 <= r["cj_t"] <= t1:
        q = (fv(r, "swept_prior_low") == 1 and fv(r, "rsi_low", 99) <= 37
             and fv(r, "g_sweep_depth", -9) >= 0.8 and fv(r, "in_demand") == 1)
        print(f"  {dt.datetime.utcfromtimestamp(r['cj_t']).strftime('%m-%d %H:%M')} "
              f"swept={fv(r,'swept_prior_low')} rsi_low={fv(r,'rsi_low')} depth={fv(r,'g_sweep_depth')} "
              f"in_dem={fv(r,'in_demand')} g_sl={r['g_sl']:.2f} → {'QUALIFICA' if q else 'não'}")
        if not q: continue
        cj = asof(r["cj_t"])
        print("    barras pós-âncora (idade 2..32): fatores [intact M P_dist P_hl Fw_rsi Fw_pos]")
        for i in range(cj + 2, min(cj + 33, N)):
            b = S[i]; ema = b.get("ema21"); atr = b.get("atr"); rsi = b.get("rsi")
            if not ema or not atr or rsi is None: continue
            intact = min(L[cj + 1:i + 1]) > r["g_sl"]
            low96 = min(L[i - 95:i + 1]); M = (C[i] - low96) >= 2.5 * atr
            dist = (C[i] - ema) / atr; Pd = C[i] > ema and dist <= 0.6
            Phl = min(L[i - 2:i + 1]) > min(L[i - 10:i - 2])
            lo20 = min(L[i - 19:i + 1]); hi20 = max(H[i - 19:i + 1])
            pos20 = (C[i] - lo20) / ((hi20 - lo20) or atr)
            Fr = 40 <= rsi <= 60; Fp = pos20 <= 0.85
            allok = intact and M and Pd and Phl and Fr and Fp
            if allok or i == asof(t1) or (Pd and Phl):
                print(f"      {dt.datetime.utcfromtimestamp(TS[i]).strftime('%m-%d %H:%M')} "
                      f"intact={int(intact)} M={int(M)}(d={(C[i]-low96)/atr:.2f}) Pd={int(Pd)}(dist={dist:.3f}) "
                      f"hl={int(Phl)} rsi={rsi:.1f}({int(Fr)}) pos20={pos20:.2f}({int(Fp)}) {'<<< CONJUNÇÃO' if allok else ''}")
