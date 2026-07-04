#!/usr/bin/env python3
"""DA LAB B r2 — ATAQUE 4: sanidade FB4/FB5 (contagens, overlaps, listas congeladas no summary)."""
import json, hashlib
from pathlib import Path
HERE = Path(__file__).parent
SB = 0.80
CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = [json.loads(l) for l in open(CANON)]
BASE = sorted([r for r in U if r["g_in_base435"] == 1 and r["g_v5h"] != "BEAR"], key=lambda r: r["cj_t"])
MAT = {m["t"]: m for m in json.load(open(HERE / "base4_maturation_features.json"))}
FEATS = {f["cj_t"]: f for f in json.load(open(HERE / "results" / "_labB_r2_regime_box_feats.json"))}
S = json.load(open(HERE / "results" / "lab_b_r2_structural_context_summary.json"))
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def net(r): return r["g_R"] - SB / r["g_risk"]

# FB4
qp = [i for i, b in enumerate(BASE) if MAT[b["cj_t"]].get("room_above", 9) <= 1.11]
kn = [i for i, b in enumerate(BASE) if b["g_ema21_dist"] <= 0.16 and i not in set(qp)]
C = {}
C["conv4"] = {i for i, b in enumerate(BASE) if fv(b, "h1n_clean_sky_atr", 99) <= 0.29 and fv(b, "h4n_clean_sky_atr", 99) <= 0.12}
C["box96top"] = {i for i, b in enumerate(BASE) if 0.906 <= b["g_box96"] < 0.947}
C["legtop"] = {i for i, b in enumerate(BASE) if fv(b, "legpos90") >= 0.804}
C["htfceil"] = {i for i, b in enumerate(BASE) if fv(b, "h1n_clean_sky_atr", 99) <= 0.39 and fv(b, "h4n_clean_sky_atr", 99) <= 0.17}
C["rb_p1"] = {i for i, b in enumerate(BASE) if b["g_v5h"] == "BULL" and FEATS[b["cj_t"]]["prev_hi_dist_atr"] is not None and FEATS[b["cj_t"]]["prev_hi_dist_atr"] >= -2 and FEATS[b["cj_t"]]["rbox_age_h"] <= 178}
C["rb_p2"] = {i for i, b in enumerate(BASE) if b["g_v5h"] == "RANGE" and FEATS[b["cj_t"]]["rbox_pos"] >= 0.9 and FEATS[b["cj_t"]]["prev_state"] == "BULL" and (FEATS[b["cj_t"]]["prev_hi_dist_atr"] or 0) > 0}
C["rb_p3"] = {i for i, b in enumerate(BASE) if b["g_v5h"] == "BULL" and 3 < FEATS[b["cj_t"]]["rbox_hi_dist_atr"] <= 8}
prot = set().union(*C.values())
def wr(idxs):
    s = [net(BASE[i]) for i in idxs]; return round(100 * sum(1 for x in s if x > 0) / len(s), 1)
print(f"FB4 QUICKPOP n{len(qp)} (summary {S['fb4']['quickpop']}) WR{wr(qp)} run{sum(1 for i in qp if BASE[i]['g_R']>=3)} "
      f"(summary {S['fb4']['quickpop_runners']}) overlapFB1 {len(set(qp)&prot)}")
print(f"FB4 KNIFE    n{len(kn)} (summary {S['fb4']['knife']}) WR{wr(kn)} run{sum(1 for i in kn if BASE[i]['g_R']>=3)} "
      f"(summary {S['fb4']['knife_runners']}) overlapFB1 {len(set(kn)&prot)} | qp∩kn {len(set(qp)&set(kn))} (deve ser 0)")
mat_missing = sum(1 for b in BASE if "room_above" not in MAT[b["cj_t"]])
print(f"   room_above ausente em {mat_missing}/435 (default 9 → nunca QUICKPOP); "
      f"KNIFE runners = {sum(1 for i in kn if BASE[i]['g_R']>=3)}/53 runners da base ({100*sum(1 for i in kn if BASE[i]['g_R']>=3)/53:.0f}%)")

# FB5 — listas congeladas batem com recompute?
LEDGER = {
    "CONV1": lambda b: fv(b, "clean_sky_atr", 99) <= 0.05 and fv(b, "n_supply_overhead") >= 48,
    "EXT": lambda b: b["g_ema21_dist"] >= 2.18 or b["g_ema50_dist"] >= 3.46,
    "CAL3_DVOID": lambda b: fv(b, "dist_demand_atr", 0) >= 1.37,
    "CAL4_B480": lambda b: 0.943 <= b["g_box480"] < 0.968,
    "H4_MIDLID": lambda b: fv(b, "h4n_clean_sky_atr", 99) != 99 and 0.38 <= fv(b, "h4n_clean_sky_atr", 99) < 0.92,
}
ok_all = True
for k, fn in LEDGER.items():
    mem = [b["cj_t"] for b in BASE if fn(b)]
    stored = S["forward_ledger_members"][k]
    match = mem == stored
    ok_all &= match
    flg = [net(b) for b in BASE if fn(b)]
    print(f"FB5 {k:<10} n{len(mem)} recompute==summary: {match} | flagged sumNET {sum(flg):+.1f} WR {100*sum(1 for x in flg if x>0)/len(flg):.0f}%")
fb2m = [b["cj_t"] for b in BASE if fv(b, "legpos60", 1) <= 0.25 and fv(b, "h1_pos", 1) <= 0.61]
print(f"FB2 members list em summary: {fb2m == S['fb2_members_cjt']}")
print(f"TODAS listas congeladas verificadas: {ok_all}")
# regra de promoção FB5 exige N>=15 forward — sanity: qual N forward esperado? (extensão ~5,5 semanas)
import collections
wk = collections.Counter()
for b in BASE: wk[b["g_week"]] += 1
rate = 435 / len(wk)
for k, fn in LEDGER.items():
    n = sum(1 for b in BASE if fn(b))
    print(f"   {k:<10} taxa {n/435:.2f} → em ~5,5 sem (~{rate*5.5:.0f} trades) espera ~{n/435*rate*5.5:.1f} flags (regra pede N>=15!)")
