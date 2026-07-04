#!/usr/bin/env python3
"""DA LAB B r2 — ATAQUE 3: FB2 FUNDO_EARLYLEG do zero.
a) flagged 42 / WR / −6,0 / SIZE_50 +236,6 reproduzidos independentemente (+ WR 28,6 do discovery?);
b) aritmética do SIZE_50: retenção 101,3% é tautologia de flagged_sum<0;
c) size-null WEEK-AWARE (lab usou uniforme) + null episódio-aware;
d) fragilidade: jackknife por semana/episódio dos flagged (>15% delta do prereg);
e) runner-kills 2026 (verificar anos e R);
f) overlap F4 chain_pos recomputado INDEPENDENTE (exits reais, implementação própria)."""
import json, random, hashlib, datetime as dt
from pathlib import Path
import statistics as stt

HERE = Path(__file__).parent
SB = 0.80
CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = [json.loads(l) for l in open(CANON)]
BASE = sorted([r for r in U if r["g_in_base435"] == 1 and r["g_v5h"] != "BEAR"], key=lambda r: r["cj_t"])
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def net(r): return r["g_R"] - SB / r["g_risk"]

fb2 = [i for i, b in enumerate(BASE) if fv(b, "legpos60", 1) <= 0.25 and fv(b, "h1_pos", 1) <= 0.61]
F = set(fb2)
netf = [net(BASE[i]) for i in fb2]
grossf = [BASE[i]["g_R"] for i in fb2]
print(f"a) flagged N{len(fb2)}  sumNET {sum(netf):+.1f}  WR_liq {100*sum(1 for x in netf if x>0)/len(fb2):.1f}%  "
      f"WR_bruto {100*sum(1 for x in grossf if x>0)/len(fb2):.1f}%  (discovery dizia WR 28,6 — de onde?)")
base_sum = sum(net(b) for b in BASE)
size50 = sum(net(BASE[i]) * (0.5 if i in F else 1.0) for i in range(435))
print(f"   base {base_sum:+.1f} · SIZE_50 {size50:+.1f} · SKIP {base_sum - sum(netf):+.1f}")
print(f"\nb) aritmética: SIZE_50 − base = {size50-base_sum:+.2f} = −0,5×flagged_sum ({-0.5*sum(netf):+.2f}) ✓tautologia; "
      f"retenção>100% ⇔ flagged_sum<0. avg flagged {sum(netf)/len(netf):+.3f}/trade (≈{abs(sum(netf))/435:.3f} NET/trade da base)")

# c) size-nulls: uniforme (lab) vs week-aware vs episódio-aware
random.seed(13)
def size_null(picker, reps=2000):
    d = []
    for _ in range(reps):
        pick = picker()
        d.append(sum(net(BASE[i]) * (0.5 if i in pick else 1.0) for i in range(435)))
    return d
dU = size_null(lambda: set(random.sample(range(435), len(fb2))))
bywk = {}
for i in fb2: bywk.setdefault(BASE[i]["g_week"], []).append(i)
pool = {}
for i in range(435): pool.setdefault(BASE[i]["g_week"], []).append(i)
def pick_wk():
    p = set()
    for wk, mem in bywk.items(): p |= set(random.sample(pool[wk], min(len(mem), len(pool[wk]))))
    return p
dW = size_null(pick_wk)
# episódios: cadeia gap<=96 barras (96*900s) na base inteira
eps = []; cur = [0]
for i in range(1, 435):
    if BASE[i]["cj_t"] - BASE[i - 1]["cj_t"] <= 96 * 900: cur.append(i)
    else: eps.append(cur); cur = [i]
eps.append(cur)
epof = {}
for k, e in enumerate(eps):
    for i in e: epof[i] = k
fl_eps = sorted({epof[i] for i in fb2})
def pick_ep():
    ks = random.sample(range(len(eps)), len(fl_eps))
    p = set()
    for k in ks: p |= set(eps[k])
    return p
dE = size_null(pick_ep)
def pctl(obs, d): return 100 * sum(1 for x in d if x < obs) / len(d)
print(f"\nc) nulls SIZE_50 (obs {size50:+.1f}):")
print(f"   uniforme (lab)     pct {pctl(size50,dU):.1f}%  (média {stt.mean(dU):.1f} sd {stt.pstdev(dU):.1f})")
print(f"   week-aware         pct {pctl(size50,dW):.1f}%  (média {stt.mean(dW):.1f} sd {stt.pstdev(dW):.1f})")
print(f"   episódio-aware     pct {pctl(size50,dE):.1f}%  (média {stt.mean(dE):.1f} sd {stt.pstdev(dE):.1f}; {len(fl_eps)} episódios flagged de {len(eps)})")

# d) fragilidade — concentração por semana/episódio do flagged_sum
wsum = {}
for i in fb2: wsum[BASE[i]["g_week"]] = wsum.get(BASE[i]["g_week"], 0) + net(BASE[i])
worst = min(wsum, key=wsum.get); best = max(wsum, key=wsum.get)
print(f"\nd) flagged em {len(wsum)} semanas / {len(fl_eps)} episódios; flagged_sum {sum(netf):+.1f}")
print(f"   sem pior semana {worst} ({wsum[worst]:+.1f}) → {sum(netf)-wsum[worst]:+.1f} | "
      f"sem melhor semana {best} ({wsum[best]:+.1f}) → {sum(netf)-wsum[best]:+.1f}")
esum = {}
for i in fb2: esum[epof[i]] = esum.get(epof[i], 0) + net(BASE[i])
se = sorted(esum.values())
print(f"   episódios: pior {se[0]:+.1f} / 2º {se[1]:+.1f} / melhor {se[-1]:+.1f}; "
      f"episódios com |soma|>15% do efeito(3,0): {sum(1 for v in se if abs(v)>0.45)}")
neg_frac = sum(v for v in se if v < 0)
print(f"   soma dos episódios negativos {neg_frac:+.1f} vs positivos {sum(v for v in se if v>0):+.1f}")
# sinal por ano
for y in (2024, 2025, 2026):
    yy = [net(BASE[i]) for i in fb2 if BASE[i]["yr"] == y]
    print(f"   {y}: N{len(yy)} sum {sum(yy):+.1f}")

# e) runner-kills
rk = [(BASE[i]["yr"], round(BASE[i]["g_R"], 2), dt.datetime.utcfromtimestamp(BASE[i]["cj_t"]).strftime("%Y-%m-%d")) for i in fb2 if BASE[i]["g_R"] >= 3]
print(f"\ne) runners flagged: {rk}  ← 2×2026 = veto SKIP confirmado?")

# f) chain_pos independente
ns = {"__name__": "e2", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "e2", "exec"), ns)
PRIMK, cf_low, HMAX = ns["PRIMK"], ns["cf_low"], ns["HMAX"]
def exit_bar_time(b):
    s = PRIMK[b["block"]]["series"]; tmap = {x["t"]: i for i, x in enumerate(s)}
    j0 = tmap[b["cj_t"]]; entry, sl, atr = b["g_entry"], b["g_sl"], b["g_atr"]
    risk = entry - sl; trail = sl; r1 = False
    end = min(j0 + HMAX, len(s) - 1)
    for k in range(j0 + 1, end + 1):
        if s[k]["l"] <= trail: return s[k]["t"]
        if (s[k]["h"] - entry) / risk >= 1: r1 = True
        if r1:
            sw = cf_low(s, k)
            if sw: trail = max(trail, sw - 0.1 * atr)
    return s[end]["t"]
ext = {b["cj_t"]: exit_bar_time(b) for b in BASE}
chain = [0] * 435
for i in range(1, 435):
    a, b = BASE[i - 1], BASE[i]
    same_zone = abs((b["g_sl"] + 0.1 * b["g_atr"]) - (a["g_sl"] + 0.1 * a["g_atr"])) <= a["g_atr"]
    if (b["cj_t"] - a["cj_t"]) <= 96 * 900 and ext[a["cj_t"]] <= b["cj_t"] and net(a) <= 0 and same_zone:
        chain[i] = chain[i - 1] + 1
dbl = sum(1 for i in fb2 if chain[i] >= 1)
print(f"\nf) chain_pos independente: flagged com chain>=1 = {dbl}/{len(fb2)} = {100*dbl/len(fb2):.0f}% (lab: 12%) | "
      f"base com chain>=1 = {sum(1 for c in chain if c>=1)}/435")
