#!/usr/bin/env python3
"""PAINÉIS COMPLETOS dos kept-sets do veto macro-leg-position (2026-07-05).
Materialização do heredoc (guard de output órfão). Reusa a construção do
macro_leg_position_veto_20260705.py até VETOS e imprime painel canónico + streak distribucional
para: pocket original, kept M6 (vel<0,10), kept M3 (recFrac<0,5), M3∩M6 (info), CTX kept M6."""
import json, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])  # constrói U, R3, CTX, POCKET, _ml

def full(rows, tag):
    rows = sorted(rows, key=lambda u: u["cj_t"])
    nets = [R3[u["cj_t"]]["net3"] for u in rows]
    n = len(rows); h = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3)
    w = sum(1 for x in nets if x > 0); s = sum(nets)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    WEEKS = len({u["g_week"] for u in U})
    yr = {y: round(sum(nets[i] for i, u in enumerate(rows) if u["yr"] == y), 1) for y in (2024, 2025, 2026)}
    random.seed(5); q = []
    for _ in range(2000):
        sq = random.choices(nets, k=n); c2 = m2 = 0
        for x in sq:
            c2 = c2 + 1 if x <= 0 else 0; m2 = max(m2, c2)
        q.append(m2)
    q.sort()
    print(f"{tag}: N{n} hit3R {100*h/n:.1f}% WR {100*w/n:.1f}% sumR {s:+.1f} avgR {s/n:+.3f} DD {dd:.1f} "
          f"r/DD {s/abs(dd) if dd else 0:.1f} stk-{mL} (q95 {q[int(0.95*2000)]}, P>5 {sum(1 for x in q if x>5)/2000:.2f}) "
          f"| {n/WEEKS:.2f}/sem | {yr}")
    return {"n": n, "hit": round(h / n, 3), "sumR": round(s, 1), "dd": round(dd, 1), "stk": mL,
            "stk_q95": q[int(0.95 * 2000)], "p_gt5": sum(1 for x in q if x > 5) / 2000, "yr": yr}

out = {}
out["pocket"] = full(POCKET, "POCKET original      ")
out["kept_M6"] = full([u for u in POCKET if u["_ml"]["vel"] < 0.10], "kept M6 (vel<0.10)   ")
out["kept_M3"] = full([u for u in POCKET if u["_ml"]["recent_frac"] < 0.5], "kept M3 (recFrac<0.5)")
out["kept_M3M6"] = full([u for u in POCKET if u["_ml"]["vel"] < 0.10 and u["_ml"]["recent_frac"] < 0.5],
                        "kept M3∩M6 (info)    ")
out["ctx_kept_M6"] = full([u for u in CTX if u["_ml"]["vel"] < 0.10], "CTX kept M6          ")
json.dump(out, open(HERE / "results" / "macro_leg_kept_panels_20260705.json", "w"), indent=1)
print("OK → results/macro_leg_kept_panels_20260705.json")
