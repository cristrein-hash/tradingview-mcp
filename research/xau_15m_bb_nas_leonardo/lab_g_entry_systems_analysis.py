#!/usr/bin/env python3
"""LAB G · G4 — EXECUÇÃO dos 2 sistemas congelados (2026-07-03).
Specs congeladas: síntese do workflow wf_15184946-f29 (Sistema A "EMA-SHAKEOUT" BULL-only ·
Sistema B "PoT-Map v2.1" 3-lentes/k-misto/day-cap2 — 1ª medição do painel de B acontece AQUI).
Protocolo (10 passos do DA-pré): Passo 0 auditoria do builder embutida · reprodução fail-loud ·
ledger = EXATAMENTE 2 tentativas (multiplicidade familiar ~18 olhadas DECLARADA — percentis
individuais não sobrevivem ao desconto max-of-family) · nulls (a) freq-matched por regime
(b) endurecido context-matched (c) permutação de lentes (B) (d) time-matched · sub-janelas
ano/semestre · jackknife semana+cluster · streak bootstrap intra-regime 1000x · painel completo
bruto+SB $0,80 · perfil de convexidade · bandas de frequência · overlap A∩B e vs base435.
STATUS DA RODADA: EXPLORATORY_CALIBRATION. Seed 42. Zero re-tuning."""
import json, random, datetime as dt
from pathlib import Path

HERE = Path(__file__).parent
SB = 0.80
random.seed(42)

# ---------- PASSO 0 — auditoria do builder (fail-loud) ----------
ns = {"__name__": "engine", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "engine", "exec"), ns)
PRIMK = ns["PRIMK"]
U = sorted([json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")], key=lambda r: r["cj_t"])
assert len(U) == 4499, "universo não reproduz"
bad = 0
for r in U:
    s = PRIMK[r["block"]]["series"]; tmap = {b["t"]: i for i, b in enumerate(s)}
    if tmap[r["cj_t"]] - tmap[r["t"]] != 3: bad += 1
assert bad == 0, f"cj não é regra fixa p+3: {bad} violações"
import collections
regcnt = collections.Counter(r["g_v5h"] for r in U)
assert dict(regcnt) == {"RANGE": 1461, "BULL": 2132, "BEAR": 906}, regcnt
print(f"PASSO 0: cj==p+3 (índice) 4499/4499 · universo/regimes reproduzem · features g_* construídas <=cj por construção (lab_g_context_inventory.py) → PASS")

def fv(r, k, d=0):
    v = r.get(k)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d

# ---------- sistemas congelados (re-implementados DO TEXTO da spec) ----------
def sysA(r):
    return (r["g_v5h"] == "BULL"
            and fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.33
            and (fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 3)
            and (fv(r, "g_atr_spike") >= 1.27 or fv(r, "g_downrun") >= 3)
            and (fv(r, "in_demand") == 1 or fv(r, "htf_demand_any") == 1)
            and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0)
            and r["g_knife"] == 0)

def knife_ok(r): return r["g_knife"] == 0 or r["g_rsi_div"] == 1 or fv(r, "sell_bub_w") >= 4
def pot(r): return fv(r, "reclaim_atr") >= 1.35 and (fv(r, "g_cj_body") >= 0.40 or fv(r, "up_closes_pc") >= 3)
def lenses3(r):
    return [fv(r, "sell_bub_w") >= 4 or r["g_rsi_div"] == 1,
            fv(r, "h1n_choch_up_rec") == 1 or fv(r, "nas_long_16") >= 1,
            fv(r, "h1n_in_demand") == 1 or fv(r, "htf_demand_confluence") == 1]
def sysB_raw(r):
    if r["g_v5h"] == "BEAR": return False
    k = 2 if r["g_v5h"] == "RANGE" else 1
    need = k + (1 if r["g_regime_flip5d"] else 0)
    if r["g_v5h"] == "RANGE":
        return (pot(r) and knife_ok(r) and r["g_box96"] <= 0.60
                and fv(r, "downleg_eff") <= 0.33 and sum(lenses3(r)) >= need)
    return (pot(r) and knife_ok(r) and fv(r, "h1n_trend") == 1 and fv(r, "h4n_trend") == 1
            and (r["g_ema21_dist"] <= 0.20 or fv(r, "in_demand") == 1)
            and sum(lenses3(r)) >= need)
def day_cap(idxs, cap=2):
    out = []; cnt = {}
    for i in idxs:
        d = U[i]["cj_t"] // 86400
        if cnt.get(d, 0) < cap: out.append(i); cnt[d] = cnt.get(d, 0) + 1
    return out

A_idx = [i for i, r in enumerate(U) if sysA(r)]
B_idx = day_cap([i for i, r in enumerate(U) if sysB_raw(r)], 2)

# ---------- painel ----------
def net_of(r): return r["g_R"] - SB / r["g_risk"]
def panel(idxs):
    seq = sorted(idxs, key=lambda i: U[i]["cj_t"]); n = len(seq)
    if not n: return None
    out = {"N": n}
    for tag, R in (("g", [U[i]["g_R"] for i in seq]), ("q", [net_of(U[i]) for i in seq])):
        eq = pk = dd = 0.0; mL = mW = cl = cw = 0
        for x in R:
            eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
            if x > 0: cw += 1; cl = 0
            else: cl += 1; cw = 0
            mW = max(mW, cw); mL = max(mL, cl)
        w = sum(1 for x in R if x > 0)
        out[tag] = dict(sum=round(sum(R), 1), wr=round(100 * w / n, 1), avg=round(sum(R) / n, 3),
                        dd=round(dd, 1), rdd=round(abs(sum(R) / dd), 2) if dd < 0 else 99,
                        stkL=mL, run=sum(1 for x in R if x >= 3))
    out["yrs"] = {y: round(sum(net_of(U[i]) for i in seq if U[i]["yr"] == y), 1) for y in (2024, 2025, 2026)}
    out["cells"] = {}
    for rg in ("RANGE", "BULL", "BEAR"):
        c = [i for i in seq if U[i]["g_v5h"] == rg]
        out["cells"][rg] = {"N": len(c), "net": round(sum(net_of(U[i]) for i in c), 1),
                            "power": "SEM PODER" if 0 < len(c) < 25 else ""}
    risks = sorted(U[i]["g_risk"] for i in seq)
    wins = [U[i]["g_R"] for i in seq if U[i]["g_R"] > 0]
    out["convex"] = {"risk_med": risks[n // 2], "win_avgR": round(sum(wins) / len(wins), 2) if wins else 0,
                     "share_R3": round(100 * out["g"]["run"] / n, 1)}
    return out

def show(nm, st):
    q = st["q"]
    print(f"{nm:<14} N{st['N']:>3} | WR_liq {q['wr']:>5.1f} NET {q['sum']:>6.1f} avg {q['avg']:>6.3f} DD {q['dd']:>6.1f} "
          f"r/DD {q['rdd']:>5.2f} stk-{q['stkL']} run{q['run']} | anos {st['yrs'][2024]}/{st['yrs'][2025]}/{st['yrs'][2026]} | "
          f"células { {k: (v['N'], v['net'], v['power']) for k, v in st['cells'].items()} } | "
          f"convex risk_med {st['convex']['risk_med']} win_avg {st['convex']['win_avgR']} R>=3 {st['convex']['share_R3']}% "
          f"(pool: 7,16 / 2,04 / 6,98%)")

print("\n" + "=" * 116)
print("LAB G · G4 — EXECUÇÃO (ledger = 2 tentativas; família ~18 olhadas DECLARADA; EXPLORATORY_CALIBRATION)")
print("=" * 116)
stA, stB = panel(A_idx), panel(B_idx)
# kill (b) de A: reprodução byte-exata do painel registrado
assert stA["N"] == 53 and abs(stA["g"]["sum"] - 29.8) < 0.1 and abs(stA["q"]["sum"] - 25.9) < 0.1, \
    f"Sistema A não reproduz spec: N{stA['N']} {stA['g']['sum']}/{stA['q']['sum']}"
show("A EMA-SHAKEOUT", stA)
show("B PoT-Map v2.1", stB)
ovl = len(set(U[i]["cj_t"] for i in A_idx) & set(U[i]["cj_t"] for i in B_idx))
b435_A = sum(1 for i in A_idx if U[i]["g_in_base435"]); b435_B = sum(1 for i in B_idx if U[i]["g_in_base435"])
print(f"overlap A∩B: {ovl} · A∩base435: {b435_A}/{stA['N']} · B∩base435: {b435_B}/{stB['N']}")

# ---------- frequência por regime-week ----------
def freq(idxs, nm):
    wk = collections.Counter(U[i]["g_week"] for i in idxs)
    regwk = {}
    for rg in ("RANGE", "BULL", "BEAR"):
        # semana atribuída ao regime pela maioria dos candidatos da semana
        pass
    # semanas ativas por regime do PICK
    per = collections.defaultdict(lambda: collections.Counter())
    for i in idxs: per[U[i]["g_v5h"]][U[i]["g_week"]] += 1
    tot_wk = len(set(r["g_week"] for r in U))
    line = []
    for rg in ("RANGE", "BULL", "BEAR"):
        c = per[rg]; n = sum(c.values())
        wks_reg = len(set(r["g_week"] for r in U if r["g_v5h"] == rg))
        over = sum(1 for w, k in c.items() if k > 3)
        line.append(f"{rg} {n} picks/{wks_reg}wk={n/max(1,wks_reg):.2f}/sem máx{max(c.values()) if c else 0} >teto{over}")
    print(f"  freq {nm}: " + " · ".join(line) + f" | total {len(idxs)}/{tot_wk}wk = {len(idxs)/tot_wk:.2f}/sem")
freq(A_idx, "A"); freq(B_idx, "B")

# ---------- nulls ----------
def pctile(obs, dist): return round(100 * sum(1 for d in dist if d < obs) / len(dist), 1)
by_reg = {rg: [i for i, r in enumerate(U) if r["g_v5h"] == rg] for rg in ("RANGE", "BULL", "BEAR")}

def null_freq_matched(idxs, cap, reps=500):
    mix = collections.Counter(U[i]["g_v5h"] for i in idxs)
    out = []
    for _ in range(reps):
        pick = []
        for rg, k in mix.items(): pick += random.sample(by_reg[rg], k)
        pick.sort(key=lambda i: U[i]["cj_t"])
        if cap: pick = day_cap(pick, cap)
        out.append(sum(net_of(U[i]) for i in pick))
    return out

def null_pool(idxs, pool, reps=500):
    n = len(idxs); out = []
    for _ in range(reps): out.append(sum(net_of(U[i]) for i in random.sample(pool, n)))
    return out

poolA = [i for i, r in enumerate(U) if r["g_v5h"] == "BULL" and r["g_knife"] == 0
         and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0)]
poolB = [i for i, r in enumerate(U) if r["g_v5h"] != "BEAR" and pot(r) and knife_ok(r)]

def null_lens_perm(reps=500):
    """(c) permutação de lentes de B: embaralha contagem de lentes entre candidatos do mesmo regime."""
    out = []
    cnts = {rg: [sum(lenses3(U[i])) for i in by_reg[rg]] for rg in ("RANGE", "BULL")}
    for _ in range(reps):
        pick = []
        for rg in ("RANGE", "BULL"):
            perm = cnts[rg][:]; random.shuffle(perm)
            for j, i in enumerate(by_reg[rg]):
                r = U[i]
                k = 2 if rg == "RANGE" else 1
                need = k + (1 if r["g_regime_flip5d"] else 0)
                if rg == "RANGE":
                    ok = (pot(r) and knife_ok(r) and r["g_box96"] <= 0.60
                          and fv(r, "downleg_eff") <= 0.33 and perm[j] >= need)
                else:
                    ok = (pot(r) and knife_ok(r) and fv(r, "h1n_trend") == 1 and fv(r, "h4n_trend") == 1
                          and (r["g_ema21_dist"] <= 0.20 or fv(r, "in_demand") == 1) and perm[j] >= need)
                if ok: pick.append(i)
        pick.sort(key=lambda i: U[i]["cj_t"])
        pick = day_cap(pick, 2)
        out.append(sum(net_of(U[i]) for i in pick))
    return out

def null_time_matched(idxs, reps=500):
    """(d) mesmos dias UTC, candidato trocado por outro do mesmo dia."""
    byday = collections.defaultdict(list)
    for i, r in enumerate(U): byday[r["cj_t"] // 86400].append(i)
    out = []
    for _ in range(reps):
        tot = 0.0
        for i in idxs: tot += net_of(U[random.choice(byday[U[i]["cj_t"] // 86400])])
        out.append(tot)
    return out

print("\nNULLS (percentil do sistema na distribuição; família ~18 olhadas → percentis individuais NÃO são edge):")
NULLP = {}
for nm, idxs, cap, pool in (("A", A_idx, None, poolA), ("B", B_idx, 2, poolB)):
    st = stA if nm == "A" else stB
    obs = st["q"]["sum"]
    p1 = pctile(obs, null_freq_matched(idxs, cap))
    # kill de A ancora no context-pool → precisão maior (2000 reps, declarado)
    p2 = pctile(obs, null_pool(idxs, pool, reps=2000))
    p4 = pctile(obs, null_time_matched(idxs))
    extra = ""
    if nm == "B":
        p3 = pctile(obs, null_lens_perm())
        extra = f" · lens-perm {p3}%"
    NULLP[nm] = {"freq": p1, "context": p2, "time": p4}
    print(f"  {nm}: freq-matched {p1}% · context-pool({len(pool)}, 2000 reps) {p2}%{extra} · time-matched {p4}% "
          f"| kills: A exige context>=90 / B exige freq>=70")

# ---------- sub-janelas + jackknife + streak bootstrap ----------
def subwin(idxs, nm):
    seq = sorted(idxs, key=lambda i: U[i]["cj_t"])
    sem = collections.defaultdict(float)
    for i in seq:
        d = dt.datetime.utcfromtimestamp(U[i]["cj_t"])
        sem[f"{d.year}H{1 if d.month <= 6 else 2}"] = round(sem[f"{d.year}H{1 if d.month <= 6 else 2}"] + net_of(U[i]), 1)
    print(f"  {nm} semestres: {dict(sorted(sem.items()))}")
    # jackknife por semana e por cluster (<4h)
    wks = collections.defaultdict(float)
    for i in seq: wks[U[i]["g_week"]] += net_of(U[i])
    tot = sum(wks.values())
    wk_max = max(wks.items(), key=lambda kv: kv[1])
    print(f"    jackknife-semana: pior remoção deixa {round(tot - wk_max[1], 1)} (semana {wk_max[0]} = {round(wk_max[1], 1)} = {round(100 * wk_max[1] / tot, 0) if tot else 0}%)")
    cl = []; last = None
    for i in seq:
        if last is not None and U[i]["cj_t"] - last <= 4 * 3600: cl[-1].append(i)
        else: cl.append([i])
        last = U[i]["cj_t"]
    clsum = [sum(net_of(U[i]) for i in c) for c in cl]
    cmax = max(clsum)
    print(f"    jackknife-cluster(<4h): {len(cl)} clusters · maior = {round(cmax, 1)} = {round(100 * cmax / tot, 0) if tot else 0}% do NET")
    # streak bootstrap intra-regime
    slots = [U[i]["g_v5h"] for i in seq]
    vals = {rg: [net_of(U[i]) for i in seq if U[i]["g_v5h"] == rg] for rg in set(slots)}
    worst = []
    for _ in range(1000):
        pools = {rg: random.sample(v, len(v)) for rg, v in vals.items()}
        ptr = {rg: 0 for rg in pools}
        mL = cl_ = 0
        for rg in slots:
            x = pools[rg][ptr[rg]]; ptr[rg] += 1
            if x <= 0: cl_ += 1; mL = max(mL, cl_)
            else: cl_ = 0
        worst.append(mL)
    p7 = sum(1 for w in worst if w >= 7) / len(worst)
    print(f"    streak bootstrap intra-regime: P(streak<=-7)={100*p7:.0f}% (gate FN <20%) · obs -{(stA if nm=='A' else stB)['q']['stkL']}")
    return p7
print("\nROBUSTEZ:")
pA7 = subwin(A_idx, "A"); pB7 = subwin(B_idx, "B")

fnA = stA["q"]["wr"] >= 50 and pA7 < 0.20
fnB = stB["q"]["wr"] >= 50 and pB7 < 0.20
print(f"\nGATE FN: A WR{stA['q']['wr']} P7 {100*pA7:.0f}% → {'PASS' if fnA else 'FAIL'} · B WR{stB['q']['wr']} P7 {100*pB7:.0f}% → {'PASS' if fnB else 'FAIL'}")

# ---------- amputação PRÉ-AUTORIZADA de B (kill-criteria: célula RANGE avgR_liq<0 em N>=40 → amputar; conta como look) ----------
rangeN = stB["cells"]["RANGE"]["N"]; rangeNet = stB["cells"]["RANGE"]["net"]
stB2 = None
if rangeN >= 40 and rangeNet < 0:
    print(f"\nAMPUTAÇÃO B (pré-autorizada; look extra no ledger): célula RANGE N{rangeN} net {rangeNet} < 0")
    B2_idx = day_cap([i for i, r in enumerate(U) if r["g_v5h"] == "BULL" and sysB_raw(r)], 2)
    stB2 = panel(B2_idx)
    show("B' BULL-only", stB2)
    obs2 = stB2["q"]["sum"]
    p1 = pctile(obs2, null_freq_matched(B2_idx, 2))
    p2 = pctile(obs2, null_pool(B2_idx, poolB, reps=2000))
    seq2 = sorted(B2_idx, key=lambda i: U[i]["cj_t"])
    vals2 = [net_of(U[i]) for i in seq2]
    worst2 = []
    for _ in range(1000):
        vv = random.sample(vals2, len(vals2)); mL = cl_ = 0
        for x in vv:
            if x <= 0: cl_ += 1; mL = max(mL, cl_)
            else: cl_ = 0
        worst2.append(mL)
    p7b2 = sum(1 for w in worst2 if w >= 7) / 1000
    fnB2 = stB2["q"]["wr"] >= 50 and p7b2 < 0.20
    print(f"  B' nulls: freq-matched {p1}% · context-pool {p2}% | P(streak<=-7)={100*p7b2:.0f}% | GATE FN → {'PASS' if fnB2 else 'FAIL'}")

json.dump({"A": stA, "B": stB, "B_amputated_BULL": stB2, "nulls": NULLP,
           "overlap_AB": ovl, "A_base435": b435_A, "B_base435": b435_B,
           "status": "EXPLORATORY_CALIBRATION",
           "ledger": "2 tentativas congeladas + 1 amputação pré-autorizada; família ~18 olhadas"},
          open(HERE / "results" / "lab_g_systems_results.json", "w"), indent=1)
print("\nOK → results/lab_g_systems_results.json")
