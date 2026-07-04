#!/usr/bin/env python3
"""DA EXIT FAMILY LAB — ataque 2: bootstrap por episódio REFEITO independente (seed 777, 2000x),
concentração (remover 2025-01 do delta E1), decomposição mecânica do run3, FN axes, custo/exposição.
READ-ONLY."""
import json, glob, bisect, hashlib, random
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
SB = 0.80
HMAX, RCAP, FR_WIN = 480, 20.0, 120
random.seed(777)  # seed DIFERENTE do lab (42)

series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]:
        series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"])
TS = [b["t"] for b in S]; N = len(S)
L = [b["l"] for b in S]; H = [b["h"] for b in S]; C = [b["c"] for b in S]
LASTFR = [None] * N; _last = None
for k in range(N):
    q = k - 2
    if q >= 2 and 2 <= q < N - 2 and L[q] <= min(L[q-2:q+3]):
        _last = q
    LASTFR[k] = _last

def run_trail(i, entry, sl, atr, arm_R):
    risk = entry - sl; stop = sl; armed = False; end = min(i + HMAX, N - 1)
    for k in range(i + 1, end + 1):
        if L[k] <= stop:
            return max(-1.0, min(RCAP, (stop - entry) / risk))
        if not armed and (H[k] - entry) >= arm_R * risk:
            armed = True
        if armed:
            p = LASTFR[k]
            if p is not None and p >= k - FR_WIN:
                stop = max(stop, L[p] - 0.1 * atr)
    return max(-1.0, min(RCAP, (C[end] - entry) / risk))

def run_fixed(i, entry, sl, atr, mult):
    risk = entry - sl; tgt = entry + mult * risk; end = min(i + HMAX, N - 1)
    for k in range(i + 1, end + 1):
        if L[k] <= sl:
            return -1.0
        if H[k] >= tgt:
            return float(mult)
    return max(-1.0, min(RCAP, (C[end] - entry) / risk))

def mfe_R(i, entry, sl):
    """máxima excursão favorável exit-free na janela HMAX (propriedade da ENTRADA, não do exit)."""
    risk = entry - sl; end = min(i + HMAX, N - 1); best = -1.0; alive_best = -1.0
    hit3_before_sl = False; mx = entry
    for k in range(i + 1, end + 1):
        if H[k] > mx: mx = H[k]
        if (mx - entry) >= 3 * risk and not hit3_before_sl:
            hit3_before_sl = True
        if L[k] <= sl:
            break
    return (mx - entry) / risk, hit3_before_sl

CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == \
    (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = [json.loads(l) for l in open(CANON)]
def fv(r, k, d=0):
    v = r.get(k)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def sysA(r):
    return (r["g_v5h"] == "BULL" and fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.33
            and (fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 3)
            and (fv(r, "g_atr_spike") >= 1.27 or fv(r, "g_downrun") >= 3)
            and (fv(r, "in_demand") == 1 or fv(r, "htf_demand_any") == 1)
            and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0) and r["g_knife"] == 0)
def asof(t):
    return bisect.bisect_right(TS, t) - 1
SETS = {
    "BASE435": sorted((asof(r["cj_t"]), r["g_entry"], r["g_sl"], r["g_atr"], r["cj_t"], r["yr"])
                      for r in U if r["g_in_base435"] == 1 and r["g_v5h"] != "BEAR"),
    "SISTEMA_A_53": sorted((asof(r["cj_t"]), r["g_entry"], r["g_sl"], r["g_atr"], r["cj_t"], r["yr"])
                           for r in U if sysA(r)),
}

def episodes(times, gap=96 * 900):
    eps = []; lastt = None
    for j, t in enumerate(times):
        if lastt is not None and t - lastt <= gap:
            eps[-1].append(j)
        else:
            eps.append([j])
        lastt = t
    return eps

def boot_ci(deltas, eps, B=2000):
    sums = []
    ne = len(eps)
    for _ in range(B):
        s = 0.0
        for _e in range(ne):
            for j in eps[random.randrange(ne)]:
                s += deltas[j]
        sums.append(s)
    sums.sort()
    return sums[int(0.025 * B)], sums[int(0.975 * B)]

print("=" * 100)
for sname, sset in SETS.items():
    times = [t for _i, _e, _sl, _a, t, _y in sset]
    eps = episodes(times)
    nets = {}
    for ename, fn in (("E0", lambda i, e, sl, a: run_trail(i, e, sl, a, 1)),
                      ("E1", lambda i, e, sl, a: run_trail(i, e, sl, a, 3)),
                      ("E2", lambda i, e, sl, a: run_fixed(i, e, sl, a, 3)),
                      ("E3", lambda i, e, sl, a: run_fixed(i, e, sl, a, 5))):
        nets[ename] = [fn(i, e, sl, a) - SB / (e - sl) for i, e, sl, a, t, y in sset]
    print(f"\n{sname}: {len(sset)} trades, {len(eps)} episódios "
          f"(máx {max(len(x) for x in eps)} trades/episódio)")
    for ename in ("E1", "E2", "E3"):
        d = [a - b for a, b in zip(nets[ename], nets["E0"])]
        lo, hi = boot_ci(d, eps)
        print(f"  Δ {ename}-E0 = {sum(d):+.1f}  IC95 boot-episódio 2000x seed777: [{lo:+.1f}, {hi:+.1f}]"
              f"  {'EXCLUI 0' if lo > 0 or hi < 0 else 'cruza 0'}")

# ---- concentração: E1/BASE435 sem 2025-01 ----
print("\n" + "=" * 100)
sset = SETS["BASE435"]
times = [t for *_x, t, _y in [(i, e, sl, a, t, y) for i, e, sl, a, t, y in sset]]
monthkey = [dt.datetime.utcfromtimestamp(t).strftime("%Y-%m") for _i, _e, _sl, _a, t, _y in sset]
netsE0 = [run_trail(i, e, sl, a, 1) - SB / (e - sl) for i, e, sl, a, t, y in sset]
netsE1 = [run_trail(i, e, sl, a, 3) - SB / (e - sl) for i, e, sl, a, t, y in sset]
d = [a - b for a, b in zip(netsE1, netsE0)]
mo = {}
for k, dj in zip(monthkey, d):
    mo[k] = mo.get(k, 0) + dj
top = sorted(mo.items(), key=lambda kv: -kv[1])[:5]
print("E1-E0/BASE435 top-5 meses do delta:", [(k, round(v, 1)) for k, v in top])
keep = [j for j, k in enumerate(monthkey) if k != "2025-01"]
d_wo = [d[j] for j in keep]
times_wo = [sset[j][4] for j in keep]
eps_wo = episodes(times_wo)
lo, hi = boot_ci(d_wo, eps_wo)
print(f"SEM 2025-01: Δ = {sum(d_wo):+.1f} (era {sum(d):+.1f})  IC95 [{lo:+.1f}, {hi:+.1f}]"
      f"  {'EXCLUI 0' if lo > 0 else 'CRUZA 0'}")
# jackknife por mês: pior mês removido em geral
jk = []
for m in sorted(set(monthkey)):
    keepm = [dj for j, dj in enumerate(d) if monthkey[j] != m]
    jk.append((sum(keepm), m))
jk.sort()
print(f"jackknife-mês: min Δ sem '{jk[0][1]}' = {jk[0][0]:+.1f} · max Δ sem '{jk[-1][1]}' = {jk[-1][0]:+.1f}")
neg_mo = sum(1 for v in mo.values() if v < 0)
print(f"meses com delta negativo: {neg_mo}/{len(mo)}")

# idem para E2/SISTEMA_A: mês máx
ssetA = SETS["SISTEMA_A_53"]
mkA = [dt.datetime.utcfromtimestamp(t).strftime("%Y-%m") for _i, _e, _sl, _a, t, _y in ssetA]
nA0 = [run_trail(i, e, sl, a, 1) - SB / (e - sl) for i, e, sl, a, t, y in ssetA]
nA2 = [run_fixed(i, e, sl, a, 3) - SB / (e - sl) for i, e, sl, a, t, y in ssetA]
dA = [a - b for a, b in zip(nA2, nA0)]
moA = {}
for k, dj in zip(mkA, dA):
    moA[k] = moA.get(k, 0) + dj
mxA = max(moA.items(), key=lambda kv: kv[1])
keepA = [j for j, k in enumerate(mkA) if k != mxA[0]]
dA_wo = [dA[j] for j in keepA]
epsA_wo = episodes([ssetA[j][4] for j in keepA])
loA, hiA = boot_ci(dA_wo, epsA_wo)
print(f"\nE2-E0/SISTEMA_A: mês máx {mxA[0]} = {mxA[1]:+.1f} ({100*mxA[1]/sum(dA):.0f}% do Δ {sum(dA):+.1f})")
print(f"SEM {mxA[0]}: Δ = {sum(dA_wo):+.1f}  IC95 [{loA:+.1f}, {hiA:+.1f}]  "
      f"{'EXCLUI 0' if loA > 0 else 'CRUZA 0'}")

# ---- run3 mecânico: MFE exit-free (propriedade da entrada) ----
print("\n" + "=" * 100)
grossE0 = [run_trail(i, e, sl, a, 1) for i, e, sl, a, t, y in sset]
grossE1 = [run_trail(i, e, sl, a, 3) for i, e, sl, a, t, y in sset]
mfe = [mfe_R(i, e, sl) for i, e, sl, a, t, y in sset]
touch3 = sum(1 for _m, h3 in mfe if h3)  # tocou 3R antes do SL original
print(f"BASE435: trades que TOCAM 3R antes do SL original (exit-free): {touch3}")
print(f"  E0 fecha >=3R: {sum(1 for g in grossE0 if g >= 3)} · E1 fecha >=3R: {sum(1 for g in grossE1 if g >= 3)}")
both = sum(1 for g0, g1, (m, h3) in zip(grossE0, grossE1, mfe) if h3 and g1 >= 3)
below = sum(1 for g0, g1, (m, h3) in zip(grossE0, grossE1, mfe) if h3 and g1 < 3)
print(f"  dos {touch3} que tocam 3R: E1 fecha >=3R em {both}, fecha <3R em {below} "
      f"(trail devolve após armar)")
e0cut = sum(1 for g0, (m, h3) in zip(grossE0, mfe) if h3 and g0 < 3)
print(f"  E0 fecha <3R em {e0cut} dos {touch3} tocadores (trail 1R corta cedo) → run3 91 vs 53 é "
      f"MECÂNICO (mesmos tocadores, bookkeeping do exit), não 'mais runners de verdade'")
# quanto do delta E1 vem de quem NUNCA toca 3R (só perde mais)?
d_nontouch = sum(dj for dj, (m, h3) in zip(d, mfe) if not h3)
d_touch = sum(dj for dj, (m, h3) in zip(d, mfe) if h3)
print(f"  Δ E1-E0 decomposto: tocadores 3R {d_touch:+.1f} · não-tocadores {d_nontouch:+.1f} "
      f"(não-tocadores = custo puro de segurar sem trail)")

# ---- FN axes ----
print("\n" + "=" * 100)
def dd_of(seq):
    eq = pk = dd = 0.0
    for x in seq:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
    return dd
for nm, seq in (("E0", netsE0), ("E1", netsE1)):
    m = {}
    for k, x in zip(monthkey, seq):
        m[k] = m.get(k, 0) + x
    neg = sorted(v for v in m.values() if v < 0)
    print(f"BASE435 {nm}: DD {dd_of(seq):.1f}R · meses negativos {len(neg)}/{len(m)} piores {['%.1f' % v for v in neg[:3]]}")
print("FN proxy (constraints: streak<=5, WR alvo 50-60%): E0 WR 45.7/stk8/q95 13 JÁ viola; "
      "E1 WR 38.4/stk14/q95 19 viola MUITO mais.")
print("Em risco 0.5%/trade: pior mês E1 -11.2R = -5.6% de conta em um mês; q95 streak 19 = -9.5% "
      "consecutivos possíveis → colide com limites típicos FN (DD total 10%, daily 5%).")
print("OK — DA boot/conc/run3 concluído.")
