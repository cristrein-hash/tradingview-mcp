#!/usr/bin/env python3
"""R10 — KILL-CHECK VIRGEM do Sistema A "EMA-SHAKEOUT" (spec congelada do Lab G, wf_15184946-f29).
Janela virgem: candidatos com cj_t > 1779667200 (pós-2026-05-25 00:00 UTC) até 2026-07-03 16:30.
Critérios PRÉ-REGISTRADOS (inegociáveis): WR<50% OU avgR<+0,15 em N>=20 → VIRGIN_FAIL_KILL;
N<20 → VIRGIN_INCONCLUSIVE_N_LT_20 (não aprova nem mata). NET-SB $0,80 reportado. ZERO reotimização.
Bounds declarados: htf_demand_any com staleness (htf_4H até 2026-06-09, htf_1D até 2026-05-24; asof-stale)
→ painel também sob htf_demand_any:=0 e :=1 (dependência histórica: 0/53). Diagnósticos rotulados."""
import json, csv, datetime as dt
from pathlib import Path
HERE = Path(__file__).parent
SB = 0.80
PREV_END = 1779667200

U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
V = sorted([r for r in U if r["cj_t"] > PREV_END], key=lambda r: r["cj_t"])
print(f"janela virgem: {len(V)} candidatos · regimes: "
      f"{ {k: sum(1 for r in V if r['g_v5h']==k) for k in ('RANGE','BULL','BEAR')} }")

def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def sysA(r, htf_override=None):
    dem_htf = fv(r, "htf_demand_any") if htf_override is None else htf_override
    return (r["g_v5h"] == "BULL"
            and fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.33
            and (fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 3)
            and (fv(r, "g_atr_spike") >= 1.27 or fv(r, "g_downrun") >= 3)
            and (fv(r, "in_demand") == 1 or dem_htf == 1)
            and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0)
            and r["g_knife"] == 0)

rows = []
def panel(idxs, tag):
    n = len(idxs)
    if n == 0:
        print(f"  {tag:<28} N0 — sem trades"); return {"tag": tag, "N": 0}
    R = [V[i]["g_R"] for i in idxs]; Rn = [V[i]["g_R"] - SB / V[i]["g_risk"] for i in idxs]
    w = sum(1 for x in Rn if x > 0)
    st = {"tag": tag, "N": n, "WR_liq": round(100 * w / n, 1), "sumR": round(sum(R), 1),
          "sumNET": round(sum(Rn), 1), "avgR_liq": round(sum(Rn) / n, 3)}
    print(f"  {tag:<28} N{n} WR_liq {st['WR_liq']} bruto {st['sumR']} NET {st['sumNET']} avg {st['avgR_liq']}")
    return st

print("SPEC CONGELADA (kill-check):")
picks = [i for i, r in enumerate(V) if sysA(r)]
st0 = panel(picks, "A frozen (asof-stale htf)")
stL = panel([i for i, r in enumerate(V) if sysA(r, htf_override=0)], "bound htf:=0")
stH = panel([i for i, r in enumerate(V) if sysA(r, htf_override=1)], "bound htf:=1")
print("DIAGNÓSTICO (NÃO é kill-check; rotulado):")
core = [i for i, r in enumerate(V) if sysA(dict(r, g_v5h="BULL"))]
panel(core, "diag: A sem gate de regime")
bp = [i for i, r in enumerate(V) if r.get("g_bear_pullback_ok")]
panel(bp, "diag: lane BEAR-pullback")
b4 = [i for i, r in enumerate(V) if r["g_v5h"] != "BEAR" and r.get("g_in_base435") is not None]
print(f"  diag: base #4 na janela (gate ≠BEAR): {sum(1 for i,_ in enumerate(V) if V[i]['g_v5h']!='BEAR')} candidatos elegíveis por regime")

N = st0["N"]
if N >= 20:
    verdict = "VIRGIN_FAIL_KILL" if (st0["WR_liq"] < 50 or st0["avgR_liq"] < 0.15) else "VIRGIN_PASS_PRELIMINARY"
else:
    verdict = "VIRGIN_INCONCLUSIVE_N_LT_20"
print(f"\nVEREDITO: {verdict} (N={N}; critérios congelados: WR<50 OU avgR<+0,15 em N>=20 = KILL; N<20 = inconclusivo)")

with open(HERE / "results" / "system_a_virgin_killcheck_20260704.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["cj_t", "utc", "regime", "R", "risk", "net"])
    for i in picks:
        r = V[i]
        w.writerow([r["cj_t"], dt.datetime.utcfromtimestamp(r["cj_t"]).isoformat(), r["g_v5h"],
                    r["g_R"], r["g_risk"], round(r["g_R"] - SB / r["g_risk"], 3)])
json.dump({"verdict": verdict, "window": "2026-05-25T00:00 -> 2026-07-03T16:30 UTC",
           "candidates_virgin": len(V), "regimes": {k: sum(1 for r in V if r["g_v5h"] == k) for k in ("RANGE", "BULL", "BEAR")},
           "frozen": st0, "bound_htf0": stL, "bound_htf1": stH,
           "note": "janela inteira classificada BEAR pelo v5h (queda ~4560→~4000); Sistema A é BULL-only por construção → stand-aside integral. Lane BEAR-pullback congelada também sem casos. Zero reotimização."},
          open(HERE / "results" / "system_a_virgin_killcheck_summary.json", "w"), indent=1)
print("OK → results/system_a_virgin_killcheck_{csv,summary.json}")
