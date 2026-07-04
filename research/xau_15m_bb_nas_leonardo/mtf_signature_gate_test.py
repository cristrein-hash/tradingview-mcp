#!/usr/bin/env python3
"""MTF SIGNATURE GATE TEST (2026-07-04) — assinatura CONGELADA do discovery:
GATE = supply_far_3atr(15M) AND demand_near_1atr(1H), avaliado no cj (price=close@cj).
Prereg: XAU_15M_LONG_MTF_SIGNATURE_GATE_PREREG_20260704.md. Zero re-tuning (3ATR/1ATR imutáveis).
E1 = BASE∩GATE vs baseline · E2 = UNIVERSE∩GATE standalone (células por regime, nada escondido).
Nulls: random-gate N / year-aware / episode-aware (500 cada; seed 42). Fail-loud no baseline e no selo."""
import json, csv, bisect, random, hashlib
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SBX = Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/d1341f00-be87-4e4d-a046-9208ee4563a5/scratchpad/mtf_sandbox")
SB = 0.80
random.seed(42)

CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = sorted([json.loads(l) for l in open(CANON)], key=lambda r: r["cj_t"])
assert len(U) == 4739

# ---- zonas + séries 15M (oficiais, 9 blocos) e 1H (sandbox, 3 blocos) ----
def load_zones_series(paths):
    zones = []; series = {}
    for p in paths:
        d = json.load(open(p))
        zs = d["zones"].values() if isinstance(d["zones"], dict) else d["zones"]
        zones += list(zs)
        for b in d["series"]: series.setdefault(b["t"], b)
    S = sorted(series.values(), key=lambda b: b["t"])
    return zones, S, [b["t"] for b in S]
Z15, S15, T15 = load_zones_series(sorted((HERE / "primitives").glob("*.primitives.json")))
Z60, S60, T60 = load_zones_series(sorted(SBX.glob("prim60/*.primitives.json")))
H_END = T60[-1]
print(f"zonas 15M {len(Z15)} · zonas 1H {len(Z60)} · cobertura 1H até {dt.datetime.utcfromtimestamp(H_END)}")
DEM60 = sorted([z for z in Z60 if "DEMAND" in str(z.get("text", "")).upper()], key=lambda z: z["born_t"])
SUP15 = sorted([z for z in Z15 if "SUPPLY" in str(z.get("text", "")).upper()], key=lambda z: z["born_t"])

def atr_asof(S, T, t0):
    j = bisect.bisect_right(T, t0) - 1
    return (S[j].get("atr") or 1.0) if j >= 0 else 1.0
def supply_far_3atr_15m(t0, price):
    a = atr_asof(S15, T15, t0)
    for z in SUP15:
        if z["born_t"] > t0: break
        if z["born_t"] <= t0 <= z.get("last_t", z["born_t"]) and z["low"] >= price and (z["low"] - price) / a < 3.0:
            return False
    return True
def demand_near_1atr_1h(t0, price):
    a = atr_asof(S60, T60, t0)
    for z in DEM60:
        if z["born_t"] > t0: break
        if z["born_t"] <= t0 <= z.get("last_t", z["born_t"]):
            if z["low"] <= price <= z["high"]: return True
            if z["high"] <= price and (price - z["high"]) / a <= 1.0: return True
    return False

def net(r): return r["g_R"] - SB / r["g_risk"]
def panel(rows):
    rows = sorted(rows, key=lambda r: r["cj_t"]); n = len(rows)
    if not n: return None
    out = {"N": n}
    for tag, R in (("g", [r["g_R"] for r in rows]), ("q", [net(r) for r in rows])):
        eq = pk = dd = 0.0; mL = cl = 0
        for x in R:
            eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
            if x <= 0: cl += 1; mL = max(mL, cl)
            else: cl = 0
        w = sum(1 for x in R if x > 0)
        out[tag] = dict(sum=round(sum(R), 1), wr=round(100 * w / n, 1), avg=round(sum(R) / n, 3),
                        dd=round(dd, 1), rdd=round(abs(sum(R) / dd), 2) if dd < 0 else 99, stk=mL)
    out["yrs"] = {y: round(sum(net(r) for r in rows if r["yr"] == y), 1) for y in (2024, 2025, 2026)}
    out["runners"] = sum(1 for r in rows if r["g_R"] >= 3)
    mo, wk = {}, {}
    for r in rows:
        d = dt.datetime.utcfromtimestamp(r["cj_t"])
        mo[d.strftime("%Y-%m")] = mo.get(d.strftime("%Y-%m"), 0) + net(r)
        wk[d.strftime("%G-%V")] = wk.get(d.strftime("%G-%V"), 0) + net(r)
    out["mo_worst"] = round(min(mo.values()), 1); out["wk_worst"] = round(min(wk.values()), 1)
    out["weeks_active"] = len(wk)
    return out
def show(tag, st, extra=""):
    if st is None: print(f"  {tag:<26} vazio"); return
    q = st["q"]; g = st["g"]
    print(f"  {tag:<26} N{st['N']:>4} WR{q['wr']:>5.1f} NET{q['sum']:>7.1f} (bruto {g['sum']:>7.1f}) DD{q['dd']:>6.1f} "
          f"r/DD{q['rdd']:>5.2f} stk-{q['stk']} run{st['runners']} | anos {st['yrs'][2024]}/{st['yrs'][2025]}/{st['yrs'][2026]} "
          f"| piorM {st['mo_worst']} piorS {st['wk_worst']} {extra}")

BASE = [r for r in U if r["g_in_base435"] == 1 and r["g_v5h"] != "BEAR"]
bs = panel(BASE)
assert bs["N"] == 435 and abs(bs["g"]["sum"] - 291.5) < 0.5 and abs(bs["q"]["sum"] - 233.6) < 0.1 and bs["runners"] == 53
print("=" * 114)
print("MTF SIGNATURE GATE TEST — assinatura congelada (supply_far_3atr 15M & demand_near_1atr 1H) — CALIBRAÇÃO")
print("=" * 114)
show("BASELINE base#4", bs)

# gate em todo o universo (1H coberto)
print("computando gate em 4739 candidatos…")
GATE = {}
for r in U:
    if r["cj_t"] > H_END: GATE[r["cj_t"]] = None; continue
    GATE[r["cj_t"]] = supply_far_3atr_15m(r["cj_t"], r["g_entry"]) and demand_near_1atr_1h(r["cj_t"], r["g_entry"])
n_na = sum(1 for v in GATE.values() if v is None)
n_pass = sum(1 for v in GATE.values() if v)
print(f"gate PASS {n_pass}/{len(U)-n_na} candidatos cobertos ({100*n_pass/(len(U)-n_na):.1f}%) · sem cobertura 1H: {n_na} (extensão, todos BEAR)")

# ---- E1: BASE ∩ GATE ----
print("\nE1 — GATE como filtro da base #4:")
g1 = [r for r in BASE if GATE[r["cj_t"]]]
st1 = panel(g1)
show("BASE∩GATE", st1, f"retenção {100*st1['q']['sum']/bs['q']['sum']:.1f}% · corta {435-st1['N']}")
cut = [r for r in BASE if not GATE[r["cj_t"]]]
rk = sum(1 for r in cut if r["g_R"] >= 3)
print(f"  runner-kill: {rk}/53 cortados · losers cortados: {sum(1 for r in cut if net(r) <= 0)}/{len(cut)}")
# nulls E1
eps = []; last = None
for i, r in enumerate(BASE):
    if last is not None and r["cj_t"] - last <= 96 * 900: eps[-1].append(i)
    else: eps.append([i])
    last = r["cj_t"]
def pct(obs, dist): return round(100 * sum(1 for d in dist if d < obs) / len(dist), 1)
k = len(g1)
nd_r = []; nd_y = []; nd_e = []
by_yr = {}
for i, r in enumerate(BASE): by_yr.setdefault(r["yr"], []).append(i)
kyr = {y: sum(1 for r in g1 if r["yr"] == y) for y in (2024, 2025, 2026)}
from collections import Counter
epool = [i for e in eps for i in e]
for _ in range(500):
    pick = random.sample(range(435), k)
    nd_r.append(sum(net(BASE[i]) for i in pick))
    picky = [i for y in kyr for i in random.sample(by_yr[y], min(kyr[y], len(by_yr[y])))]
    nd_y.append(sum(net(BASE[i]) for i in picky))
    # episode-aware: sorteia episódios inteiros até atingir ~k trades
    random.shuffle(eps); acc = []
    for e in eps:
        if len(acc) >= k: break
        acc += e
    nd_e.append(sum(net(BASE[i]) for i in acc[:k]))
print(f"  nulls (percentil do NET gated {st1['q']['sum']}): random {pct(st1['q']['sum'], nd_r)}% · "
      f"year-aware {pct(st1['q']['sum'], nd_y)}% · episode-aware {pct(st1['q']['sum'], nd_e)}%")
# jackknife-episódio: concentração do delta (se delta>0)
delta = st1["q"]["sum"] - bs["q"]["sum"]

# ---- E2: UNIVERSE ∩ GATE (standalone) ----
print("\nE2 — GATE standalone no universo (sem outros filtros; todas as células reportadas):")
g2 = [r for r in U if GATE.get(r["cj_t"])]
st2 = panel(g2)
show("UNIVERSE∩GATE", st2, f"freq {st2['N']/st2['weeks_active']:.2f}/sem")
for rg in ("BULL", "RANGE", "BEAR"):
    cell = [r for r in g2 if r["g_v5h"] == rg]
    stc = panel(cell)
    if stc: show(f"  célula {rg}", stc, "(SEM PODER)" if stc["N"] < 25 else "")
ov_base = sum(1 for r in g2 if r["g_in_base435"] == 1 and r["g_v5h"] != "BEAR")
print(f"  overlap com base#4: {ov_base}/{st2['N']}")

# ---- cobertura dos alvos ----
AN = json.load(open(HERE / "results" / "cris_trades_analysis_20260704.json"))
tr35 = [(r["t"], r["entry"]) for r in AN]
cov35 = 0; m35 = 0
Ut = [r["cj_t"] for r in U]
for t0, px in tr35:
    i = bisect.bisect_right(Ut, t0) - 1
    if i >= 0 and t0 - U[i]["cj_t"] <= 24 * 900:
        m35 += 1
        if GATE.get(U[i]["cj_t"]): cov35 += 1
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def sysA(r):
    return (r["g_v5h"] == "BULL" and fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.33
            and (fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 3)
            and (fv(r, "g_atr_spike") >= 1.27 or fv(r, "g_downrun") >= 3)
            and (fv(r, "in_demand") == 1 or fv(r, "htf_demand_any") == 1)
            and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0) and r["g_knife"] == 0)
sysA21 = [r for r in U if sysA(r) and not r["g_in_base435"]]
g21 = [r for r in sysA21 if GATE.get(r["cj_t"])]
st21 = panel(sysA21); st21g = panel(g21)
print(f"\nALVOS: 35 manuais → matched {m35}, gate-pass no candidato {cov35} · "
      f"21 fora-da-base do Sistema A → gate-pass {len(g21)}/21 (NET dos 21: {st21['q']['sum'] if st21 else 0} · dos que passam: {st21g['q']['sum'] if st21g else 0})")

# ---- outputs ----
rows = []
def addrow(name, st, note=""):
    if st is None: return
    rows.append(dict(variant=name, N=st["N"], WR_liq=st["q"]["wr"], sumNET=st["q"]["sum"], bruto=st["g"]["sum"],
                     DD=st["q"]["dd"], rDD=st["q"]["rdd"], streak=st["q"]["stk"], runners=st["runners"],
                     yr2024=st["yrs"][2024], yr2025=st["yrs"][2025], yr2026=st["yrs"][2026],
                     worst_month=st["mo_worst"], worst_week=st["wk_worst"], note=note))
addrow("BASELINE", bs); addrow("BASE_AND_GATE", st1, f"cut {435-st1['N']}, runner-kill {rk}")
addrow("UNIVERSE_AND_GATE", st2, f"freq {st2['N']/st2['weeks_active']:.2f}/sem")
for rg in ("BULL", "RANGE", "BEAR"):
    addrow(f"E2_{rg}", panel([r for r in g2 if r["g_v5h"] == rg]))
addrow("SYSA_21_outbase", st21); addrow("SYSA_21_gatepass", st21g)
with open(HERE / "results" / "mtf_signature_gate_results.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader()
    for r in rows: w.writerow(r)
json.dump({"gate_pass_universe": n_pass, "universe_covered": len(U) - n_na, "no_1h_coverage": n_na,
           "E1": {"N": st1["N"], "net": st1["q"]["sum"], "runner_kill": rk,
                  "pct_random": pct(st1["q"]["sum"], nd_r), "pct_year": pct(st1["q"]["sum"], nd_y),
                  "pct_episode": pct(st1["q"]["sum"], nd_e)},
           "E2": {"N": st2["N"], "net": st2["q"]["sum"], "freq_wk": round(st2["N"] / st2["weeks_active"], 2),
                  "overlap_base": ov_base},
           "targets": {"m35": m35, "gate35": cov35, "sysA21_pass": len(g21)},
           "status": "EXPLORATORY_CALIBRATION"}, open(HERE / "results" / "mtf_signature_gate_summary.json", "w"), indent=1)
print("\nOK → results/mtf_signature_gate_{results.csv,summary.json}")
