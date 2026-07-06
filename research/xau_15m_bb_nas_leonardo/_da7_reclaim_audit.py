#!/usr/bin/env python3
"""DEVIL'S ADVOCATE 7 — auditoria do edge RECLAIM (P0 / R-twoup). NÃO-produção, read-only.
Reconstrói EV/reclaims idêntico a event_reclaim_entry_20260706.py e ataca 6 vetores."""
import json, bisect, hashlib, random, math, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
N = len(S); HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]; OP = [b.get("o", b["c"]) for b in S]
CACHE = {r["cj_t"]: r for r in (json.loads(l) for l in open(HERE / "results" / "raw_feature_cache_20260706.jsonl"))}
UNIV = sorted([u for u in U if u["cj_t"] in R3 and u["cj_t"] in CACHE], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]; WK = len({u["g_week"] for u in U})
for u in UNIV:
    u["_flo"] = u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0); u["_a"] = u.get("g_atr") or 5.0

# ---- eventos (idêntico) ----
EV = []; cur = []
for u in UNIV:
    if cur and u["cj_t"] - cur[-1]["cj_t"] <= 48 * 3600 and abs(u["_flo"] - cur[-1]["_flo"]) <= 3 * u["_a"]:
        cur.append(u)
    else:
        if cur: EV.append(cur)
        cur = [u]
if cur: EV.append(cur)

for ev in EV:
    min_flo = 1e18; prev_close = None; up = 0
    for pos, u in enumerate(ev, 1):
        ci = bisect.bisect_right(TS, u["cj_t"]) - 1; a = u["_a"]
        prevmin = min_flo
        u["_ci"] = ci
        u["_post_low"] = int(pos > 1 and u["_flo"] > prevmin + 0.05 * a)
        min_flo = min(min_flo, u["_flo"])
        rng = max(1e-9, HI[ci] - LO[ci])
        u["_reclaim"] = int(ci >= 1 and CL[ci] > HI[ci - 1])
        u["_body_up"] = int(CL[ci] > OP[ci]); u["_cir"] = (CL[ci] - LO[ci]) / rng
        if prev_close is not None: up = up + 1 if CL[ci] > prev_close else 0
        prev_close = CL[ci]
        u["_two_up"] = int(up >= 2)

def base_reclaim(u): return u["_post_low"] == 1 and u["_reclaim"] == 1 and u["_body_up"] == 1 and u["_cir"] >= 0.5
def first(ev, extra=None):
    for u in ev:
        if base_reclaim(u) and (extra is None or extra(u)): return u
    return None
def hitv(r): return 1 if R3[r["cj_t"]]["R3"] >= 3 else 0
def net(r): return R3[r["cj_t"]]["net3"]

P0 = [u for ev in EV if (u := first(ev))]
TWOUP = [u for ev in EV if (u := first(ev, lambda x: x["_two_up"] == 1))]
RECL_ALL = [u for ev in EV for u in ev if base_reclaim(u)]   # todos reclaims (não 1/evento)
p_univ = sum(hitv(u) for u in UNIV) / len(UNIV)
print(f"UNIV N{len(UNIV)} hit={p_univ:.4f} | P0 N{len(P0)} hit={sum(map(hitv,P0))/len(P0):.4f} | "
      f"R-twoup N{len(TWOUP)} hit={sum(map(hitv,TWOUP))/len(TWOUP):.4f} | reclaim-pool N{len(RECL_ALL)} hit={sum(map(hitv,RECL_ALL))/len(RECL_ALL):.4f}")

# ================= VETOR 1 — LEAK =================
print("\n=== V1 LEAK ===")
# 1a: entry == close da barra do candidato?
d_entry = [abs(R3[u["cj_t"]]["g_entry"] - CL[u["_ci"]]) for u in P0]
# barra do candidato: cj_t == TS[ci]?
mism = sum(1 for u in P0 if TS[u["_ci"]] != u["cj_t"])
print(f"  entry vs close[ci]: max|Δ|={max(d_entry):.4f} med={sorted(d_entry)[len(d_entry)//2]:.4f} | ci-timestamp mismatch={mism}/{len(P0)}")
# 1b: SL < entry sempre (long) e risco>0
bad_sl = sum(1 for u in P0 if not (R3[u["cj_t"]]["g_sl"] < R3[u["cj_t"]]["g_entry"]))
print(f"  g_sl<g_entry violado={bad_sl}/{len(P0)} (long coerente)")
# 1c: post_low causal — recomputar com min dos ANTERIORES apenas
leak_pl = 0
for ev in EV:
    mn = 1e18
    for pos, u in enumerate(ev, 1):
        prevmn = mn; want = int(pos > 1 and u["_flo"] > prevmn + 0.05 * u["_a"]); mn = min(mn, u["_flo"])
        if want != u["_post_low"]: leak_pl += 1
print(f"  post_low re-derivado causal: divergências={leak_pl} (0=causal)")
# 1d: reclaim leaky (peek barra ci+1) muda a seleção? se o edge some com causal->leaky seria sinal de circularidade
def first_leaky(ev):
    mn = 1e18
    for pos, u in enumerate(ev, 1):
        ci = u["_ci"]; prevmn = mn; pl = int(pos > 1 and u["_flo"] > prevmn + 0.05*u["_a"]); mn = min(mn, u["_flo"])
        rec_next = int(ci+1 < N and CL[ci+1] > HI[ci])  # peek futuro
        if pl and rec_next and u["_body_up"] == 1 and u["_cir"] >= 0.5: return u
    return None
LK = [u for ev in EV if (u := first_leaky(ev))]
print(f"  reclaim LEAKY(peek ci+1): N{len(LK)} hit={sum(map(hitv,LK))/len(LK):.4f} (causal P0={sum(map(hitv,P0))/len(P0):.4f}; se leaky>>causal => geometria circular)")

# ================= VETOR 2 — MULTIPLICIDADE (binomial exato) =================
print("\n=== V2 MULTIPLICIDADE ===")
def binom_ge(k, n, p):
    return sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(k, n+1))
for tag, rows in [("P0", P0), ("R-twoup", TWOUP)]:
    k = sum(map(hitv, rows)); n = len(rows)
    pex = binom_ge(k, n, p_univ)
    print(f"  {tag}: {k}/{n} vs p={p_univ:.4f} → binom P(≥{k})={pex:.5f} · Bonferroni×10={min(1,pex*10):.4f} {'PASS' if pex*10<0.05 else 'FAIL'}")

# ================= VETOR 3 — NULL POR EPISÓDIO =================
print("\n=== V3 NULL POR EPISÓDIO (candidatos do mesmo evento correlacionados) ===")
# eventos que PRODUZEM entrada P0
def per_episode_null(rows, picker_pool, seed, tag):
    # rows = entradas observadas (1/evento). null: para cada evento contribuinte, sortear 1 candidato do MESMO evento
    ev_of = {}
    for ev in EV:
        u = picker_pool(ev)
        if u is not None: ev_of[id(ev)] = ev
    obs = sum(map(hitv, rows)) / len(rows)
    random.seed(seed); ge = 0; NS = 4000
    evs = [ev for ev in EV if picker_pool(ev) is not None]
    for _ in range(NS):
        h = sum(hitv(random.choice(ev)) for ev in evs) / len(evs)   # candidato aleatório do MESMO evento
        if h >= obs: ge += 1
    # null 2: candidato aleatório do POOL de reclaims do evento
    random.seed(seed+1); ge2 = 0
    evr = [(ev, [u for u in ev if base_reclaim(u)]) for ev in evs]
    for _ in range(NS):
        h = sum(hitv(random.choice(rl)) for ev, rl in evr if rl) / len([1 for ev,rl in evr if rl])
        if h >= obs: ge2 += 1
    print(f"  {tag}: obs hit={obs:.4f} N-ev={len(evs)} | P(rand-cand-do-evento≥obs)={ge/NS:.4f} | P(rand-reclaim-do-evento≥obs)={ge2/NS:.4f}")
per_episode_null(P0, lambda ev: first(ev), 3001, "P0")
per_episode_null(TWOUP, lambda ev: first(ev, lambda x: x["_two_up"]==1), 3003, "R-twoup")

# ================= VETOR 4 — RECLAIM vs FAMÍLIA/SELEÇÃO =================
print("\n=== V4 É O RECLAIM OU A SELEÇÃO-DE-EVENTO? ===")
# reclaim aplicado ao universo TODO (não 1/evento)
print(f"  reclaim-pool(todos, não 1/ev): N{len(RECL_ALL)} hit={sum(map(hitv,RECL_ALL))/len(RECL_ALL):.4f} NET={sum(map(net,RECL_ALL)):+.1f} (univ 27.6%)")
# two_up isolado no universo TODO
TU_ALL = [u for ev in EV for u in ev if u["_two_up"] == 1]
print(f"  two_up isolado(todos): N{len(TU_ALL)} hit={sum(map(hitv,TU_ALL))/len(TU_ALL):.4f} NET={sum(map(net,TU_ALL)):+.1f}")
# reclaim SEM post_low (só a barra reclaim, 1º do evento incluído) — separa 'reclaim' de 'post-low selection'
NOPL = [u for ev in EV for u in ev if u["_reclaim"]==1 and u["_body_up"]==1 and u["_cir"]>=0.5]
print(f"  reclaim s/ post_low(todos): N{len(NOPL)} hit={sum(map(hitv,NOPL))/len(NOPL):.4f}")
# post_low SEM reclaim
PLONLY = [u for ev in EV for u in ev if u["_post_low"]==1 and u["_reclaim"]==0]
print(f"  post_low s/ reclaim(todos): N{len(PLONLY)} hit={sum(map(hitv,PLONLY))/len(PLONLY):.4f}")
# 1º candidato-qualquer por evento (só seleção 'primeiro pós-low', sem reclaim)
def first_pl(ev):
    for u in ev:
        if u["_post_low"]==1: return u
    return None
FPL = [u for ev in EV if (u := first_pl(ev))]
print(f"  1º-post_low/evento(sem exigir reclaim): N{len(FPL)} hit={sum(map(hitv,FPL))/len(FPL):.4f} NET={sum(map(net,FPL)):+.1f}")

# ================= VETOR 5 — ROBUSTEZ TEMPORAL (trimestre) =================
print("\n=== V5 ROBUSTEZ TEMPORAL (trimestre) ===")
def quarter(t):
    d = dt.datetime.utcfromtimestamp(t); return f"{d.year}Q{(d.month-1)//3+1}"
for tag, rows in [("P0", P0), ("R-twoup", TWOUP)]:
    q = {}
    for u in rows: q.setdefault(quarter(u["cj_t"]), []).append(u)
    print(f"  {tag}:")
    for k in sorted(q):
        rs = q[k]; h = sum(map(hitv,rs))/len(rs); nn = sum(map(net,rs))
        print(f"    {k}: N{len(rs):>3} hit {100*h:>5.1f}% NET {nn:>+7.1f}")
    nets = sorted(((sum(map(net,v)), k) for k,v in q.items()))
    posq = sum(1 for v in q.values() if sum(map(net,v))>0)
    print(f"    → trimestres+ {posq}/{len(q)} | pior {nets[0][1]} NET {nets[0][0]:+.1f} | maior trimestre NET={max(sum(map(net,v)) for v in q.values()):+.1f} de {sum(map(net,rows)):+.1f}")

# ================= VETOR 6 — WINNER'S CURSE (best-of-6) =================
print("\n=== V6 WINNER'S CURSE (R-twoup = melhor de 6 afinações) ===")
# reproduz os 6 looks, aplica max-statistic: sob H0 (rótulos permutados no UNIV), qual o melhor P dos 6?
def rec_str(u):
    ci=u["_ci"]; return (CL[ci]-HI[ci-1])/u["_a"] if ci>=1 else 0
def prev_wick(u):
    ci=u["_ci"]; return (min(OP[ci-1],CL[ci-1])-LO[ci-1])/u["_a"] if ci>=1 else 0
# choch_at_rec
def choch(u):
    ci=u["_ci"]; hi_e=bisect.bisect_right(ET,u["cj_t"])
    for m in range(hi_e-1,-1,-1):
        if u["cj_t"]-events[m]["t"]>4*900: break
        if events[m]["tok"]=="CHoCH+": return 1
    return 0
LOOKS6 = {
 "R-strength": lambda u: rec_str(u)>=0.1,
 "R-prevwick": lambda u: prev_wick(u)>=0.3,
 "R-choch": lambda u: choch(u)==1,
 "R-twoup": lambda u: u["_two_up"]==1,
 "R-str&wick": lambda u: rec_str(u)>=0.1 and prev_wick(u)>=0.3,
 "R-str&choch": lambda u: rec_str(u)>=0.1 and choch(u)==1,
}
look_rows = {nm: [u for ev in EV if (u := first(ev, ex))] for nm, ex in LOOKS6.items()}
look_hit = {nm: (sum(map(hitv,r))/len(r) if r else 0, len(r)) for nm,r in look_rows.items()}
for nm,(h,n) in look_hit.items(): print(f"  {nm}: N{n} hit={h:.4f}")
# max-statistic null: permuta rótulos de hit no UNIV, recomputa hit de cada look (mesma seleção de linhas), pega o MAIOR desvio
labels = {u["cj_t"]: hitv(u) for u in UNIV}
allcj = list(labels); base_lab = list(labels.values())
random.seed(6001); NS=2000; beat=0
obs_best_excess = max(look_hit[nm][0]-p_univ for nm in LOOKS6)
for _ in range(NS):
    perm = base_lab[:]; random.shuffle(perm)
    pm = dict(zip(allcj, perm))
    best = max((sum(pm[u["cj_t"]] for u in look_rows[nm])/len(look_rows[nm]) - sum(perm)/len(perm)) for nm in LOOKS6 if look_rows[nm])
    if best >= obs_best_excess: beat += 1
print(f"  obs best-excess(hit-p_univ)={obs_best_excess:.4f} | P(max de 6 ≥ obs sob H0 permutado)={beat/NS:.4f}")
print("\nDONE _da7_")
