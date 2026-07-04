#!/usr/bin/env python3
"""RECLAIM-QUIETO v1.0 — LEITURA ONE-SHOT DE OUTCOME (GO Cris 2026-07-04).
Protocolo pré-registrado (SPEC §5): selos verificados · entrada no close do sinal · exit let-run
aprovado (trail swing-low −0,1ATR pós +1R, HMAX480, RCAP20) · painel duplo bruto+SB $0,80 ·
null a mesma-frequência por-ano (500) · null b time-matched weekday×hora (500) · null c circular-shift
semanal (100 shifts ×480 barras) · jackknife mês/ano · ablação leave-one-lens (6 leituras declaradas,
gerador replicado fail-loud 157/157) · runners (sem top-5; anos sem top-2) · FN-proxy (streak≤5).
ONE-SHOT: números publicados como saírem; mudança posterior = sistema novo + re-null. Seed 42."""
import json, csv, glob, bisect, random, hashlib, collections
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SB = 0.80
random.seed(42)

# ---- selos ----
for f, exp in [l.split()[::-1] for l in open(HERE / "results" / "reclaim_quieto_v1_seal.sha256")]:
    f = f.strip()
    p = HERE / f if not f.startswith("results") else HERE / f
    assert hashlib.sha256((HERE / f).read_bytes()).hexdigest() == exp, f"SELO VIOLADO: {f}"
print("selos OK (sinais + gerador)")

# ---- timeline global idêntica ao gerador selado ----
series, smc = {}, {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"], b)
    for e in d["smc_events"]:
        if "CHOCH" in str(e.get("text", "")).upper(): smc.setdefault((e["t"], e.get("id")), e)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]
N = len(S)
L = [b["l"] for b in S]; H = [b["h"] for b in S]; C = [b["c"] for b in S]
SIGS = json.load(open(HERE / "results" / "reclaim_quieto_v1_signals_20260704.json"))
assert len(SIGS) == 157
for s in SIGS:
    assert S[s["i"]]["t"] == s["t"] and abs(S[s["i"]]["c"] - s["c"]) < 1e-9, f"sinal não replica {s['t']}"
print("157 sinais replicam na timeline global")

# ---- letrun aprovado, otimizado (fractais pré-computados) ----
ISLOW = [False] * N
for p in range(2, N - 2):
    if L[p] == min(L[p - 2:p + 3]): ISLOW[p] = True
PREV_FR = [None] * N  # fractal mais recente p <= k-2 (janela 120, semântica do cf_low do engine)
last = None
for k in range(N):
    p = k - 2
    if p >= 2 and ISLOW[p]: last = p
    PREV_FR[k] = last
def letrun(i, entry, sl, atr):
    risk = entry - sl; trail = sl; r1 = False; end = min(i + 480, N - 1)
    for k in range(i + 1, end + 1):
        if L[k] <= trail: return max(-1.0, min(20.0, (trail - entry) / risk))
        if (H[k] - entry) / risk >= 1: r1 = True
        if r1:
            p = PREV_FR[k]
            if p is not None and p >= k - 120: trail = max(trail, L[p] - 0.1 * atr)
    return max(-1.0, min(20.0, (C[end] - entry) / risk))

def sl_rule(i):
    """regra de SL selada aplicada num bar i (para nulls). Retorna (sl, risk) ou None (rejeitado)."""
    b = S[i]; atr = b.get("atr") or 1.0
    if i < 98 or b.get("ema21") is None: return None
    lows52 = L[i - 52:i + 1]
    swl52 = [k for k in range(2, len(lows52) - 2) if lows52[k] == min(lows52[k - 2:k + 3])]
    win = S[i - 96:i + 1]
    jh = max(range(len(win)), key=lambda k: win[k]["h"])
    dip96 = min(x["l"] for x in win[jh:])
    anch = min(lows52[swl52[-1]] if swl52 else dip96, min(lows52[-8:]))
    sl = anch - 0.25 * atr; d = (b["c"] - sl) / atr
    if d > 4.0: return None
    if d < 1.2:
        sl = dip96 - 0.25 * atr; d = (b["c"] - sl) / atr
        if not (1.2 <= d <= 4.0): return None
    if b["c"] - sl > 40.0: return None
    return sl, b["c"] - sl

def panel(trades):
    """trades = [(t, R, risk)] → painel duplo."""
    trades = sorted(trades); n = len(trades)
    if not n: return None
    out = {"N": n}
    for tag, R in (("g", [x[1] for x in trades]), ("q", [x[1] - SB / x[2] for x in trades])):
        eq = pk = dd = 0.0; mL = cl = 0
        for x in R:
            eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
            if x <= 0: cl += 1; mL = max(mL, cl)
            else: cl = 0
        w = sum(1 for x in R if x > 0)
        out[tag] = dict(sum=round(sum(R), 1), wr=round(100 * w / n, 1), avg=round(sum(R) / n, 3),
                        dd=round(dd, 1), rdd=round(abs(sum(R) / dd), 2) if dd < 0 else 99, stk=mL)
    out["yrs"] = {}
    for t, R, rk in trades:
        y = dt.datetime.utcfromtimestamp(t).year
        out["yrs"][y] = round(out["yrs"].get(y, 0) + R - SB / rk, 1)
    mo = {}
    for t, R, rk in trades:
        k = dt.datetime.utcfromtimestamp(t).strftime("%Y-%m"); mo[k] = mo.get(k, 0) + R - SB / rk
    out["mo_worst"] = round(min(mo.values()), 1); out["mo"] = mo
    return out
def show(tag, st, extra=""):
    if st is None: print(f"  {tag:<24} vazio"); return
    q, g = st["q"], st["g"]
    yrs = "/".join(f"{st['yrs'].get(y, 0)}" for y in (2024, 2025, 2026))
    print(f"  {tag:<24} N{st['N']:>3} | BRUTO {g['sum']:>7.1f} WR{g['wr']:>5.1f} | NET {q['sum']:>7.1f} WR{q['wr']:>5.1f} "
          f"avg{q['avg']:>6.3f} DD{q['dd']:>6.1f} r/DD{q['rdd']:>5.2f} stk-{q['stk']} | anos {yrs} | piorM {st['mo_worst']} {extra}")

# ================= ABERTURA DO ENVELOPE =================
OBS = []
for s in SIGS:
    R = letrun(s["i"], s["c"], s["sl"], S[s["i"]].get("atr") or 1.0)
    OBS.append((s["t"], R, s["d_usd"]))
st = panel(OBS)
print("\n" + "=" * 112)
print("RECLAIM-QUIETO v1.0 — OUTCOME ONE-SHOT (157 sinais selados; exit let-run aprovado; SB $0,80)")
print("=" * 112)
show("OBSERVADO", st)
runners = sorted([x[1] for x in OBS], reverse=True)
net_sorted = sorted([x[1] - SB / x[2] for x in OBS], reverse=True)
print(f"  runners R>=3: {sum(1 for x in OBS if x[1] >= 3)} · R>=5: {sum(1 for x in OBS if x[1] >= 5)} · máx {max(runners):.2f}")
print(f"  sem top-5 (NET): {round(st['q']['sum'] - sum(net_sorted[:5]), 1)}  (gate: >0)")
for y in (2024, 2025, 2026):
    yr_tr = sorted([x[1] - SB / x[2] for x in OBS if dt.datetime.utcfromtimestamp(x[0]).year == y], reverse=True)
    print(f"  {y} sem top-2: {round(sum(yr_tr) - sum(yr_tr[:2]), 1)}  (gate: >0)")
print(f"  FN: streak {st['q']['stk']} (hard <=5: {'PASS' if st['q']['stk'] <= 5 else 'FAIL'}) · DD {st['q']['dd']}R @1% = {st['q']['dd']:.1f}%")

# ---- nulls ----
ELIG = [i for i in range(98, N - 481) if S[i].get("ema21") is not None]
by_year = collections.defaultdict(list)
for i in ELIG: by_year[dt.datetime.utcfromtimestamp(S[i]["t"]).year].append(i)
obs_years = collections.Counter(dt.datetime.utcfromtimestamp(x[0]).year for x in OBS)
MEMO = {}
def eval_bar(i):
    if i not in MEMO:
        r = sl_rule(i)
        MEMO[i] = None if r is None else (letrun(i, S[i]["c"], r[0], S[i].get("atr") or 1.0), r[1])
    return MEMO[i]
def draw_null(pool_by_key, counts):
    tot_net = 0.0; got = 0
    for key, k in counts.items():
        pool = pool_by_key[key]; tries = 0
        need = k
        while need and tries < 50 * k:
            i = random.choice(pool); tries += 1
            ev = eval_bar(i)
            if ev is None: continue
            tot_net += ev[0] - SB / ev[1]; need -= 1; got += 1
    return tot_net, got
print("\nNULLS (500 reps a/b · 100 shifts c):")
na = [draw_null(by_year, obs_years)[0] for _ in range(500)]
p_a = round(100 * sum(1 for x in na if x < st["q"]["sum"]) / len(na), 1)
by_wh = collections.defaultdict(list)
for i in ELIG:
    d = dt.datetime.utcfromtimestamp(S[i]["t"]); by_wh[(d.weekday(), d.hour)].append(i)
obs_wh = collections.Counter((dt.datetime.utcfromtimestamp(x[0]).weekday(), dt.datetime.utcfromtimestamp(x[0]).hour) for x in OBS)
nb = [draw_null(by_wh, obs_wh)[0] for _ in range(500)]
p_b = round(100 * sum(1 for x in nb if x < st["q"]["sum"]) / len(nb), 1)
nc = []
for k in range(1, 101):
    tot = 0.0; got = 0
    for s in SIGS:
        j = (s["i"] + k * 480)
        if j >= N - 481: j = 98 + (j % (N - 579))
        ev = eval_bar(j)
        if ev: tot += ev[0] - SB / ev[1]; got += 1
    nc.append(tot * (157 / max(1, got)))
p_c = round(100 * sum(1 for x in nc if x < st["q"]["sum"]) / len(nc), 1)
med = lambda a: sorted(a)[len(a) // 2]
print(f"  a mesma-freq/ano: med {med(na):+.1f} → obs pct {p_a}%")
print(f"  b time-matched:   med {med(nb):+.1f} → obs pct {p_b}%")
print(f"  c circular-shift: med {med(nc):+.1f} → obs pct {p_c}%")

# ---- jackknife ----
mo = st["mo"]; tot = st["q"]["sum"]
mx = max(mo.items(), key=lambda kv: kv[1])
print(f"\nJACKKNIFE: pior remoção de mês deixa {round(tot - mx[1], 1)} (mês {mx[0]} = {round(mx[1], 1)} = {round(100 * mx[1] / tot, 0) if tot else 0}% — gate <=35%)")
for y in (2024, 2025, 2026):
    print(f"  leave-{y}-out: {round(tot - st['yrs'].get(y, 0), 1)}")

# ---- ablação leave-one-lens (gerador replicado; full-mask deve reproduzir 157/157) ----
CLOSE_T = {b["t"]: b["c"] for b in S}
def sign(x): return 1 if x > 0 else (-1 if x < 0 else 0)
CH = []
for e in smc.values():
    ta, pr = e["t"], e.get("price")
    j0 = bisect.bisect_right(TS, ta) - 1
    if j0 < 0 or pr is None: continue
    s0 = sign(S[j0]["c"] - pr); known = None
    if s0 != 0:
        for k in range(j0 + 1, min(j0 + 41, N)):
            if sign(S[k]["c"] - pr) == -s0: known = S[k]["t"]; break
    if known is None: known = ta + 6 * 900
    CH.append((ta, known))
CH.sort(); CH_TA = [c[0] for c in CH]
def choch_ok(t_i):
    j = bisect.bisect_right(CH_TA, t_i) - 1
    while j >= 0 and (t_i - CH_TA[j]) // 900 <= 24:
        if CH[j][1] <= t_i: return True
        j -= 1
    return False
b30 = {}
for b in S:
    key = b["t"] // 1800
    r = b30.setdefault(key, {"h": b["h"], "l": b["l"], "t_close": b["t"]})
    r["h"] = max(r["h"], b["h"]); r["l"] = min(r["l"], b["l"]); r["t_close"] = max(r["t_close"], b["t"])
B30 = sorted(b30.values(), key=lambda r: r["t_close"])
B30_CLOSE = [r["t_close"] for r in B30]; TR30 = [r["h"] - r["l"] for r in B30]
ATR30 = []; a = None
for tr in TR30:
    a = tr if a is None else (a * 13 + tr) / 14.0; ATR30.append(a)
def quiet30_at(t0):
    j = bisect.bisect_right(B30_CLOSE, t0) - 1
    return None if j < 20 else sum(TR30[j - 3:j + 1]) / 4.0 / max(1e-9, ATR30[j])
def generate(skip=None):
    out = []; last_i = -10**9; last_jh_t = None
    W, BUF = 96, 0.15
    for i in range(W + 2, N):
        b, pb = S[i], S[i - 1]
        if b.get("ema21") is None or pb.get("ema21") is None: continue
        atr = b["atr"] or 1.0
        if not (b["c"] >= b["ema21"] + BUF * atr): continue
        if not (pb["c"] < pb["ema21"] + BUF * (pb["atr"] or atr)): continue
        if (b["c"] - b["ema21"]) / atr > 1.2: continue
        if skip != "E2" and not any(S[k]["c"] < S[k]["ema21"] for k in range(i - 24, i) if S[k].get("ema21")): continue
        win = S[i - W:i + 1]; lows = [x["l"] for x in win]; highs = [x["h"] for x in win]
        jh = max(range(len(win)), key=lambda k: win[k]["h"])
        if skip != "M" and len(win) - 1 - jh < 24: continue
        swl = [k for k in range(2, len(lows) - 2) if lows[k] == min(lows[k - 2:k + 3])]
        if skip != "C1" and not (len(swl) >= 2 and lows[swl[-1]] > lows[swl[-2]]): continue
        if skip != "C2" and not choch_ok(b["t"]): continue
        hi96, lo96 = max(highs), min(lows)
        ret = (hi96 - b["c"]) / ((hi96 - lo96) or atr)
        if skip != "C3" and not (0.25 <= ret <= 0.75): continue
        q = quiet30_at(b["t"])
        if skip != "C4" and (q is None or q > 1.0): continue
        r = sl_rule(i)
        if r is None: continue
        if i - last_i <= 48: continue
        if last_jh_t is not None and win[jh]["t"] == last_jh_t: continue
        out.append((i, b["c"], r[0], r[1], b["t"]))
        last_i = i; last_jh_t = win[jh]["t"]
    return out
full = generate()
assert len(full) == 157 and all(f[0] == s["i"] for f, s in zip(full, SIGS)), f"replicação falhou: {len(full)}"
print("\nABLAÇÃO leave-one-lens (6 leituras declaradas; full-mask replica 157/157 ✓):")
for lens in ("E2", "M", "C1", "C2", "C3", "C4"):
    g = generate(skip=lens)
    tr = [(t, letrun(i, c, sl, S[i].get("atr") or 1.0), rk) for i, c, sl, rk, t in g]
    stl = panel(tr)
    dN = stl["N"] - 157
    print(f"  sem {lens:<3} N{stl['N']:>4} ({dN:+d}) NET {stl['q']['sum']:>7.1f} WR {stl['q']['wr']:>5.1f} stk-{stl['q']['stk']}")

rows = [dict(t=x[0], utc=dt.datetime.utcfromtimestamp(x[0]).isoformat(), R=round(x[1], 3),
             risk=x[2], net=round(x[1] - SB / x[2], 3)) for x in OBS]
with open(HERE / "results" / "reclaim_quieto_v1_outcome_20260704.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader()
    for r in rows: w.writerow(r)
json.dump({"panel": {k: v for k, v in st.items() if k != "mo"},
           "nulls_pct": {"a_freq_ano": p_a, "b_time_matched": p_b, "c_circular": p_c},
           "runners_ge3": sum(1 for x in OBS if x[1] >= 3),
           "one_shot": True, "seed": 42},
          open(HERE / "results" / "reclaim_quieto_v1_outcome_summary_20260704.json", "w"), indent=1)
print("\nOK → results/reclaim_quieto_v1_outcome_{20260704.csv,summary_20260704.json}")
