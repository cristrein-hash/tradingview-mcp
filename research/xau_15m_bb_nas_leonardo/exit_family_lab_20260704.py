#!/usr/bin/env python3
"""EXIT FAMILY LAB (2026-07-04) — medição formal dos 4 exits congelados sobre entradas FIXAS.
Prereg: XAU_15M_LONG_EXIT_FAMILY_LAB_PREREG_20260704.md. Zero exits novos. Deltas PAREADOS por trade
vs E0 com IC bootstrap por EPISÓDIO (1000×), sub-janelas por ano, jackknife mês/episódio,
streak/DD distribucionais (block bootstrap 1000×). Painel duplo bruto+SB. Seed 42."""
import json, csv, glob, bisect, random, hashlib
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SB = 0.80
random.seed(42)
series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; N = len(S)
L = [b["l"] for b in S]; H = [b["h"] for b in S]; C = [b["c"] for b in S]
ISLOW = [False] * N
for p in range(2, N - 2):
    if L[p] == min(L[p - 2:p + 3]): ISLOW[p] = True
PREV_FR = [None] * N; last = None
for k in range(N):
    p = k - 2
    if p >= 2 and ISLOW[p]: last = p
    PREV_FR[k] = last

def mk_trail(arm_R):
    def fn(i, entry, sl, atr):
        risk = entry - sl; trail = sl; armed = False; end = min(i + 480, N - 1)
        for k in range(i + 1, end + 1):
            if L[k] <= trail: return max(-1.0, min(20.0, (trail - entry) / risk))
            if (H[k] - entry) / risk >= arm_R: armed = True
            if armed:
                p = PREV_FR[k]
                if p is not None and p >= k - 120: trail = max(trail, L[p] - 0.1 * atr)
        return max(-1.0, min(20.0, (C[end] - entry) / risk))
    return fn
def mk_fixed(mult):
    def fn(i, entry, sl, atr):
        risk = entry - sl; tgt = entry + mult * risk; end = min(i + 480, N - 1)
        for k in range(i + 1, end + 1):
            if L[k] <= sl and H[k] >= tgt: return -1.0
            if L[k] <= sl: return -1.0
            if H[k] >= tgt: return float(mult)
        return max(-1.0, min(20.0, (C[end] - entry) / risk))
    return fn
EXITS = {"E0_trail": mk_trail(1), "E1_trail3R": mk_trail(3), "E2_alvo3R": mk_fixed(3), "E3_alvo5R": mk_fixed(5)}

CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = [json.loads(l) for l in open(CANON)]
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def sysA(r):
    return (r["g_v5h"] == "BULL" and fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.33
            and (fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 3)
            and (fv(r, "g_atr_spike") >= 1.27 or fv(r, "g_downrun") >= 3)
            and (fv(r, "in_demand") == 1 or fv(r, "htf_demand_any") == 1)
            and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0) and r["g_knife"] == 0)
def asof(t): return bisect.bisect_right(TS, t) - 1
SETS = {
    "BASE435": [(asof(r["cj_t"]), r["g_entry"], r["g_sl"], r["g_atr"], r["cj_t"], r["yr"])
                for r in U if r["g_in_base435"] == 1 and r["g_v5h"] != "BEAR"],
    "SISTEMA_A_53": [(asof(r["cj_t"]), r["g_entry"], r["g_sl"], r["g_atr"], r["cj_t"], r["yr"]) for r in U if sysA(r)],
}
# baseline fail-loud: E0 na BASE435 deve reproduzir a stack aprovada (~+291,5/+233,6)
b0 = [(t, mk_trail(1)(i, e, sl, atr), e - sl, yr) for i, e, sl, atr, t, yr in SETS["BASE435"]]
s_g = sum(x[1] for x in b0); s_q = sum(x[1] - SB / x[2] for x in b0)
assert abs(s_g - 291.5) < 1.5 and abs(s_q - 233.6) < 1.5, f"E0 não reproduz aprovado: {s_g:.1f}/{s_q:.1f}"
print(f"E0/BASE435 reproduz stack aprovada: bruto {s_g:.1f} / NET {s_q:.1f} ✓")

def panel(tr):
    tr = sorted(tr); n = len(tr)
    out = {"N": n}
    for tag, R in (("g", [x[1] for x in tr]), ("q", [x[1] - SB / x[2] for x in tr])):
        eq = pk = dd = 0.0; mL = cl = 0
        for x in R:
            eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
            if x <= 0: cl += 1; mL = max(mL, cl)
            else: cl = 0
        w = sum(1 for x in R if x > 0)
        out[tag] = dict(sum=round(sum(R), 1), wr=round(100 * w / n, 1), avg=round(sum(R) / n, 3),
                        dd=round(dd, 1), rdd=round(abs(sum(R) / dd), 2) if dd < 0 else 99, stk=mL)
    out["yrs"] = {}
    for t, R, rk, yr in tr: out["yrs"][yr] = round(out["yrs"].get(yr, 0) + R - SB / rk, 1)
    mo = {}
    for t, R, rk, yr in tr:
        k = dt.datetime.utcfromtimestamp(t).strftime("%Y-%m"); mo[k] = mo.get(k, 0) + R - SB / rk
    out["mo_worst"] = round(min(mo.values()), 1)
    out["run3"] = sum(1 for x in tr if x[1] >= 3); out["run5"] = sum(1 for x in tr if x[1] >= 5)
    out["mo"] = mo
    return out

def episodes(trs):
    eps = []; lastt = None
    for j, x in enumerate(sorted(trs)):
        if lastt is not None and x[0] - lastt <= 96 * 900: eps[-1].append(j)
        else: eps.append([j])
        lastt = x[0]
    return eps

ROWS = []
print("\n" + "=" * 120)
print(f"{'SET':<13} {'EXIT':<11} | {'N':>4} {'WRliq':>6} {'BRUTO':>8} {'NET':>8} {'ret%':>6} {'DD':>7} {'r/DD':>6} {'stk':>4} {'stk_q95':>7} {'R>=3':>5} | anos 24/25/26 | piorM")
print("-" * 120)
SUMM = {}
for sname, sset in SETS.items():
    base_R = None
    for ename, efn in EXITS.items():
        tr = [(t, efn(i, e, sl, atr), e - sl, yr) for i, e, sl, atr, t, yr in sset]
        st = panel(tr)
        nets = [x[1] - SB / x[2] for x in sorted(tr)]
        eps = episodes(tr)
        # streak distribucional (block bootstrap por episódio)
        worst = []
        for _ in range(1000):
            seq = [nets[j] for _ in range(len(eps)) for j in eps[random.randrange(len(eps))]]
            mL = cl = 0
            for x in seq:
                if x <= 0: cl += 1; mL = max(mL, cl)
                else: cl = 0
            worst.append(mL)
        stk95 = sorted(worst)[950]
        q = st["q"]
        if ename == "E0_trail": base_R = nets; base_sum = q["sum"]
        ret = 100 * q["sum"] / base_sum
        yrs = "/".join(str(st["yrs"].get(y, 0)) for y in (2024, 2025, 2026))
        print(f"{sname:<13} {ename:<11} | {st['N']:>4} {q['wr']:>6.1f} {st['g']['sum']:>8.1f} {q['sum']:>8.1f} {ret:>6.1f} "
              f"{q['dd']:>7.1f} {q['rdd']:>6.2f} {q['stk']:>4} {stk95:>7} {st['run3']:>5} | {yrs:>16} | {st['mo_worst']}")
        row = dict(set=sname, exit=ename, N=st["N"], WR_liq=q["wr"], bruto=st["g"]["sum"], NET=q["sum"],
                   retention=round(ret, 1), DD=q["dd"], rDD=q["rdd"], streak=q["stk"], streak_q95=stk95,
                   run3=st["run3"], run5=st["run5"], yr2024=st["yrs"].get(2024, 0), yr2025=st["yrs"].get(2025, 0),
                   yr2026=st["yrs"].get(2026, 0), worst_month=st["mo_worst"])
        # delta pareado vs E0 + IC bootstrap por episódio + jackknife mês
        if ename != "E0_trail":
            deltas = [a - b for a, b in zip(nets, base_R)]
            dsum = sum(deltas)
            boots = []
            for _ in range(1000):
                boots.append(sum(deltas[j] for _ in range(len(eps)) for j in eps[random.randrange(len(eps))]))
            lo, hi = sorted(boots)[25], sorted(boots)[975]
            # por-ano do delta
            dyr = {}
            for (t, R, rk, yr), d in zip(sorted(tr), deltas): dyr[yr] = round(dyr.get(yr, 0) + d, 1)
            # concentração por mês
            dmo = {}
            for (t, R, rk, yr), d in zip(sorted(tr), deltas):
                k = dt.datetime.utcfromtimestamp(t).strftime("%Y-%m"); dmo[k] = dmo.get(k, 0) + d
            mx = max(dmo.items(), key=lambda kv: kv[1])
            conc = round(100 * mx[1] / dsum, 0) if dsum > 0 else None
            print(f"{'':<13} {'':<11}   Δ pareado {dsum:+.1f} [IC95 {lo:+.1f},{hi:+.1f}] · Δ/ano {dyr} · mês máx {mx[0]} {conc}% (gate<=35)")
            row.update(delta=round(dsum, 1), delta_lo=round(lo, 1), delta_hi=round(hi, 1),
                       delta_yr=json.dumps(dyr), delta_conc_pct=conc)
        ROWS.append(row)
    print("-" * 120)

with open(HERE / "results" / "exit_family_lab_results.csv", "w", newline="") as fh:
    allk = sorted({k for r in ROWS for k in r})
    w = csv.DictWriter(fh, fieldnames=allk); w.writeheader()
    for r in ROWS: w.writerow(r)
json.dump({"rows": ROWS, "prereg": "4 exits congelados; 1 look de descoberta declarado (cross)",
           "seed": 42}, open(HERE / "results" / "exit_family_lab_summary.json", "w"), indent=1)
print("OK → results/exit_family_lab_{results.csv,summary.json}")
