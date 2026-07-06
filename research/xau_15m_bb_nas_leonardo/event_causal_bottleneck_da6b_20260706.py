#!/usr/bin/env python3
"""DA6b (2026-07-06) — desambiguar TASK 3: 'best-in-accepted >> first' e sinal-de-timing REAL
ou apenas inflacao de max-sobre-K candidatos? E o seletor de evento ENRIQUECE fundos (precisao)?
NAO commita, NAO modifica ficheiros, sufixo _da6_.
SANITY_PROBE: desambiguacao de artefato (order-statistic null + precisao de selecao), nao busca de eixo novo;
reusa seletores S1/S3/S4 ja congelados da FASE B; arbitro = null mecanico de max-de-K, nao in-sample."""
import json, bisect, hashlib, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF)); ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]
CACHE = {r["cj_t"]: r for r in (json.loads(l) for l in open(HERE / "results" / "raw_feature_cache_20260706.jsonl"))}
UNIV = sorted([u for u in U if u["cj_t"] in R3 and u["cj_t"] in CACHE], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]
for u in UNIV:
    u["_flo"] = u["g_sl"] + 0.1*(u.get("g_atr") or 5.0); u["_a"] = u.get("g_atr") or 5.0
    u["_circ"] = set(); u["_F"] = CACHE[u["cj_t"]]
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"] - 8*3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"] + 8*3600:
        u = UNIV[j]; d = u["_flo"] - g["flush_low"]
        if -3*u["_a"] <= d <= 1*u["_a"]: u["_circ"].add(gi)
        j += 1
EV = []; cur = []
for u in UNIV:
    if cur and u["cj_t"]-cur[-1]["cj_t"] <= 48*3600 and abs(u["_flo"]-cur[-1]["_flo"]) <= 3*u["_a"]:
        cur.append(u)
    else:
        if cur: EV.append(cur)
        cur = [u]
if cur: EV.append(cur)
for u in UNIV: pass
for ei, ev in enumerate(EV):
    for u in ev: u["_ev"] = ei
for ev in EV:
    st_i = bisect.bisect_right(TS, ev[0]["cj_t"]) - 1
    pre_hi = max(HI[max(0, st_i-96):st_i+1])
    acc = {"rsi_min8":99,"nas_dist":99,"sell_climax":0,"nas_long":0,"below_poc":0,"n":0,"poc_dist":99}
    for u in ev:
        f = u["_F"]
        acc["rsi_min8"]=min(acc["rsi_min8"],f["rsi_min8"]); acc["nas_dist"]=min(acc["nas_dist"],f["nas_dist"])
        acc["sell_climax"]=max(acc["sell_climax"],f["sell_climax4"]); acc["nas_long"]=max(acc["nas_long"],f["nas_long_rec"])
        acc["below_poc"]=max(acc["below_poc"],f["below_poc"]); acc["poc_dist"]=min(acc["poc_dist"],f["poc_dist"]); acc["n"]+=1
        ci = bisect.bisect_right(TS, u["cj_t"]) - 1
        u["_acc"]=dict(acc); u["_acc"]["pre_drop"]=(pre_hi-min(LO[max(0,st_i-8):ci+1]))/u["_a"]
def selector(name):
    if name=="S1": return lambda u: u["_acc"]["rsi_min8"]<=32 and u["_acc"]["n"]>=2 and (u["_acc"]["sell_climax"]>=1 or u["_acc"]["nas_long"]==1) and u["_acc"]["below_poc"]==1
    if name=="S3": return lambda u: u["_acc"]["rsi_min8"]<=40 and u["_acc"]["nas_long"]==1 and u["_acc"]["n"]>=2 and u["_acc"]["below_poc"]==1
    if name=="S4": return lambda u: u["_acc"]["rsi_min8"]<=34 and u["_acc"]["n"]>=2 and (u["_acc"]["sell_climax"]>=1 or u["_acc"]["nas_long"]==1)
def hit(u): return 1 if R3[u["cj_t"]]["R3"]>=3 else 0

FUND = set(ei for ei,ev in enumerate(EV) if any(u["_circ"] for u in ev))
base_prec = len(FUND)/len(EV)
allc_hit = sum(hit(u) for u in UNIV)/len(UNIV)
print(f"base: P(evento-fundo)={base_prec:.3f} · hit3R medio candidato={allc_hit:.3f} · eventos={len(EV)}")
print(f"\n{'sel':<4}{'#ev':>5}{'prec_fund':>10}{'lift':>6} | {'first':>6}{'rand-in-acc':>12}{'best-in-acc':>12}{'exp_max_null':>13}{'evt3R_pool':>11}")
random.seed(707)
out = {}
for nm in ("S1","S3","S4"):
    sel = selector(nm)
    acc_events = []
    for ev in EV:
        a = [u for u in ev if sel(u)]
        if a: acc_events.append((ev, a))
    n = len(acc_events)
    prec_fund = sum(1 for ev,a in acc_events if any(u["_circ"] for u in ev))/n   # P(fund|accepted)
    first = sum(hit(sorted(a,key=lambda u:u["cj_t"])[0]) for ev,a in acc_events)/n
    best  = sum(max(hit(u) for u in a) for ev,a in acc_events)/n
    # random accepted candidate hit (expected)
    rand_acc = sum(sum(hit(u) for u in a)/len(a) for ev,a in acc_events)/n
    # expected best-of-k under null (accepted candidates each drawn at rand_acc prob, k=len(a)):
    exp_max = sum(1-(1-(sum(hit(u) for u in a)/len(a)))**len(a) for ev,a in acc_events)/n
    # pool of accepted events: does event CONTAIN a 3R hitter among ALL its candidates?
    evt3R = sum(1 for ev,a in acc_events if any(hit(u) for u in ev))/n
    lift = prec_fund/base_prec
    print(f"{nm:<4}{n:>5}{prec_fund:>10.3f}{lift:>6.1f}x | {100*first:>5.1f}%{100*rand_acc:>11.1f}%{100*best:>11.1f}%{100*exp_max:>12.1f}%{100*evt3R:>10.1f}%")
    out[nm] = {"n":n,"prec_fund":round(prec_fund,3),"lift":round(lift,1),"first":round(first,3),
               "rand_in_acc":round(rand_acc,3),"best_in_acc":round(best,3),"exp_max_null":round(exp_max,3),"evt_has_3R":round(evt3R,3)}
print("\nLEITURA:")
print(" - prec_fund vs base -> o seletor CLASSIFICA fundos melhor que acaso? (lift)")
print(" - first vs rand-in-acc -> entrar no 1o e PIOR que entrar num aceito aleatorio? (perda de timing)")
print(" - best-in-acc vs exp_max_null -> o 'best' excede a inflacao mecanica de max-de-K? (timing REAL)")
json.dump(out, open(HERE/"results"/"event_causal_bottleneck_da6b_20260706.json","w"), indent=1)
print("\nOK → results/event_causal_bottleneck_da6b_20260706.json")
