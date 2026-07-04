#!/usr/bin/env python3
"""LAB B r2 — STRUCTURAL CONTEXT · medição oficial (2026-07-04).
Prereg: docs/architecture/XAU_15M_LONG_LAB_B_R2_STRUCTURAL_CONTEXT_PREREG_20260704.md (famílias
congeladas do discovery wf_6e643ea3-184). STATUS DA RODADA: CALIBRAÇÃO (canon 45-grupos; ~100 looks
declarados no ledger; árbitro = extensão RAW futura não-BEAR). Runner preservation = gate duro.
Preâmbulo = integridade do universo SELADO (sha256 + counts fail-loud — exigência #1 pós-incidente).
Seed 42. Zero varredura além do congelado."""
import json, csv, random, hashlib, datetime as dt
from pathlib import Path

HERE = Path(__file__).parent
SB = 0.80
random.seed(42)

# ---------- integridade do canônico (exigência #1) ----------
CANON = HERE / "results" / "lab_g_candidates.jsonl"
sha = hashlib.sha256(CANON.read_bytes()).hexdigest()
expected = (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
assert sha == expected, f"CANÔNICO VIOLADO: {sha[:12]} != {expected[:12]}"
U = [json.loads(l) for l in open(CANON)]
BASE = sorted([r for r in U if r["g_in_base435"] == 1 and r["g_v5h"] != "BEAR"], key=lambda r: r["cj_t"])
assert len(U) == 4739 and len(BASE) == 435
MAT = {m["t"]: m for m in json.load(open(HERE / "base4_maturation_features.json"))}
assert all(b["cj_t"] in MAT for b in BASE), "join maturation falhou"
FEATS = {f["cj_t"]: f for f in json.load(open(HERE / "results" / "_labB_r2_regime_box_feats.json"))}
assert all(b["cj_t"] in FEATS for b in BASE), "join rbox feats falhou"

def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def net(r, w=1.0): return w * (r["g_R"] - SB / r["g_risk"])

def panel(idxs, wts=None):
    seq = sorted(idxs, key=lambda i: BASE[i]["cj_t"]); n = len(seq)
    if not n: return None
    W = wts or {}
    Rg = [W.get(i, 1.0) * BASE[i]["g_R"] for i in seq]
    Rn = [net(BASE[i], W.get(i, 1.0)) for i in seq]
    out = {"N": n}
    for tag, R in (("g", Rg), ("q", Rn)):
        eq = pk = dd = 0.0; mL = cl = 0
        for x in R:
            eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
            if x <= 0: cl += 1; mL = max(mL, cl)
            else: cl = 0
        w = sum(1 for x in R if x > 0)
        out[tag] = dict(sum=round(sum(R), 1), wr=round(100 * w / n, 1), avg=round(sum(R) / n, 3),
                        dd=round(dd, 1), rdd=round(abs(sum(R) / dd), 2) if dd < 0 else 99, stkL=mL)
    out["yrs"] = {y: round(sum(net(BASE[i], W.get(i, 1.0)) for i in seq if BASE[i]["yr"] == y), 1) for y in (2024, 2025, 2026)}
    out["runners_kept"] = sum(1 for i in seq if BASE[i]["g_R"] >= 3 and W.get(i, 1.0) > 0)
    return out
def show(tag, st, extra=""):
    q = st["q"]
    print(f"  {tag:<26} N{st['N']:>3} WR{q['wr']:>5.1f} NET{q['sum']:>7.1f} DD{q['dd']:>6.1f} r/DD{q['rdd']:>5.2f} "
          f"stk-{q['stkL']} run{st['runners_kept']} | anos {st['yrs'][2024]}/{st['yrs'][2025]}/{st['yrs'][2026]} {extra}")

bs = panel(range(435))
assert abs(bs["q"]["sum"] - 233.6) < 0.1 and bs["runners_kept"] == 53 and bs["q"]["stkL"] == 8
print("=" * 112)
print("LAB B r2 — STRUCTURAL CONTEXT (medição oficial; CALIBRAÇÃO; runner-gate duro)")
print("=" * 112)
show("BASELINE", bs)
RES = {"canon_sha": sha}

# ---------- FB3 assert de causalidade do rbox (amostra; divergência => BLOCKED) ----------
ns = {"__name__": "e", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "e", "exec"), ns)
regime_h = ns["regime_hourcausal"]; PRIMK = ns["PRIMK"]
BARS_ALL = sorted({x["t"]: x for pr in PRIMK.values() for x in pr["series"]}.items())
def rbox_recompute(b):
    """reconstrói segmento do regime truncado em cj_t (convenções ADJUDICADAS pelo DA — o assert v1
    tinha sign-flip em prev_hi_dist e usava close da hora corrente [não-causal] + timeline por bloco):
    timeline GLOBAL; estado por hora = regime_hourcausal(h*3600); prev_hi_dist = (phi−entry)/atr (>0 = teto acima)."""
    t = b["cj_t"]
    hrs = sorted({tt // 3600 for tt, x in BARS_ALL if tt <= t})
    if len(hrs) < 8: return None
    st_of = lambda h: regime_h(h * 3600)
    cur = st_of(hrs[-1]); i = len(hrs) - 1
    while i > 0 and st_of(hrs[i - 1]) == cur: i -= 1
    seg_h = hrs[i:]
    age = len(seg_h)
    j = i - 1
    if j < 0: return None
    pstate = st_of(hrs[j]); k = j
    while k > 0 and st_of(hrs[k - 1]) == pstate: k -= 1
    prev_h = hrs[k:j + 1]
    bars = [x for tt, x in BARS_ALL if tt <= t]
    inseg = [x for x in bars if x["t"] // 3600 in set(seg_h)]
    inprev = [x for x in bars if x["t"] // 3600 in set(prev_h)]
    if not inseg or not inprev: return None
    hi, lo = max(x["h"] for x in inseg), min(x["l"] for x in inseg)
    phi = max(x["h"] for x in inprev)
    atr = b["g_atr"]; entry = b["g_entry"]
    return {"rbox_age_h": age, "prev_state": pstate,
            "rbox_pos": (entry - lo) / ((hi - lo) or atr),
            "prev_hi_dist_atr": (phi - entry) / atr}
smp = random.sample(range(435), 40)
mism = 0; checked = 0
for i in smp:
    b = BASE[i]; rc = rbox_recompute(b); fj = FEATS[b["cj_t"]]
    if rc is None: continue
    checked += 1
    ok = (rc["prev_state"] == fj["prev_state"] and abs(rc["rbox_age_h"] - fj["rbox_age_h"]) <= 2
          and abs(rc["rbox_pos"] - fj["rbox_pos"]) <= 0.05 and abs(rc["prev_hi_dist_atr"] - fj["prev_hi_dist_atr"]) <= 0.25)
    if not ok: mism += 1
fb3_blocked = mism > max(2, 0.1 * checked)
print(f"\nFB3 assert causalidade rbox (recompute truncado em cj_t, amostra {checked}): mismatches {mism} → "
      f"{'BLOCKED_BY_MAPPING' if fb3_blocked else 'PASS'}")
RES["fb3_causality"] = {"checked": checked, "mismatches": mism, "blocked": fb3_blocked}

# ---------- FB1 — anti-veto teto: componentes, dedup, painel protegido ----------
print("\nFB1 — ANTI-VETO TETO (proteção; nada removido)")
def comp_sets():
    c = {}
    c["conv4"] = {i for i, b in enumerate(BASE) if fv(b, "h1n_clean_sky_atr", 99) <= 0.29 and fv(b, "h4n_clean_sky_atr", 99) <= 0.12}
    c["box96top"] = {i for i, b in enumerate(BASE) if 0.906 <= b["g_box96"] < 0.947}
    c["legtop"] = {i for i, b in enumerate(BASE) if fv(b, "legpos90") >= 0.804}
    c["htfceil"] = {i for i, b in enumerate(BASE) if fv(b, "h1n_clean_sky_atr", 99) <= 0.39 and fv(b, "h4n_clean_sky_atr", 99) <= 0.17}
    c["rb_p1"] = {i for i, b in enumerate(BASE) if b["g_v5h"] == "BULL" and FEATS[b["cj_t"]]["prev_hi_dist_atr"] >= -2 and FEATS[b["cj_t"]]["rbox_age_h"] <= 178}
    c["rb_p2"] = {i for i, b in enumerate(BASE) if b["g_v5h"] == "RANGE" and FEATS[b["cj_t"]]["rbox_pos"] >= 0.9 and FEATS[b["cj_t"]]["prev_state"] == "BULL" and FEATS[b["cj_t"]]["prev_hi_dist_atr"] > 0}
    c["rb_p3"] = {i for i, b in enumerate(BASE) if b["g_v5h"] == "BULL" and 3 < FEATS[b["cj_t"]]["rbox_hi_dist_atr"] <= 8}
    return c
C = comp_sets()
seen = set(); dedup = {}
for k, s in C.items():
    newm = s - seen
    dedup[k] = {"n": len(s), "new": len(newm), "new_pct": round(100 * len(newm) / len(s), 0) if s else 0,
                "runners": sum(1 for i in s if BASE[i]["g_R"] >= 3)}
    seen |= s
prot = set().union(*C.values())
stp = panel(sorted(prot))
for k, d in dedup.items():
    flag = " ⚠ re-rotulação(<30% novos)" if d["new_pct"] < 30 else ""
    print(f"    {k:<9} n{d['n']:>3} novos {d['new_pct']:>3.0f}% runners {d['runners']}{flag}")
show("FB1 protegidos (união)", stp, f"= {len(prot)}/435 ({100*len(prot)/435:.0f}%)")
RES["fb1"] = {"union": len(prot), "union_runners": stp["runners_kept"], "union_net": stp["q"]["sum"], "dedup": dedup}

# ---------- helpers null ----------
def wk_null_skip(flag, reps=500):
    """random-skip week-aware: mesmo nº de cortes POR SEMANA ISO."""
    bywk = {}
    for i in flag: bywk.setdefault(BASE[i]["g_week"], []).append(i)
    pool = {}
    for i in range(435): pool.setdefault(BASE[i]["g_week"], []).append(i)
    out = []
    for _ in range(reps):
        drop = set()
        for wk, mem in bywk.items():
            drop |= set(random.sample(pool[wk], min(len(mem), len(pool[wk]))))
        out.append(sum(net(BASE[i]) for i in range(435) if i not in drop))
    return out
def pct(obs, dist): return round(100 * sum(1 for d in dist if d < obs) / len(dist), 1)

# ---------- FB2 — fundo/early-leg ----------
print("\nFB2 — FUNDO_EARLYLEG (legpos60<=0,25 AND h1_pos<=0,61)")
fb2 = [i for i, b in enumerate(BASE) if fv(b, "legpos60", 1) <= 0.25 and fv(b, "h1_pos", 1) <= 0.61]
stf = panel(fb2)
show("FB2 flagged", stf, f"({len(fb2)}/435)")
kept2 = [i for i in range(435) if i not in set(fb2)]
sts = panel(kept2)
show("FB2 SKIP (BLOQUEADO)", sts, "← counterfactual, NÃO acionável nesta rodada")
w2 = {i: (0.5 if i in set(fb2) else 1.0) for i in range(435)}
sth = panel(range(435), wts=w2)
show("FB2 SIZE_50 (acionável)", sth)
nd = wk_null_skip(fb2)
p_skip = pct(sts["q"]["sum"], nd)
nd_size = []
for _ in range(500):
    pick = set(random.sample(range(435), len(fb2)))
    nd_size.append(sum(net(BASE[i], 0.5 if i in pick else 1.0) for i in range(435)))
p_size = pct(sth["q"]["sum"], nd_size)
rk2 = [i for i in fb2 if BASE[i]["g_R"] >= 3]
print(f"    nulls: SKIP week-aware pct {p_skip}% · SIZE_50 random pct {p_size}% | runner-kill sob SKIP: "
      f"{len(rk2)} ({[BASE[i]['yr'] for i in rk2]}) — 2026 = veto | retenção SIZE_50 {100*sth['q']['sum']/bs['q']['sum']:.1f}%")
# overlap com F4 chain_pos (dupla-taxação): chain estrita com exits reais
letrun_exit = {}
cf_low, HMAX, RCAP = ns["cf_low"], ns["HMAX"], ns["RCAP"]
def letrun_ext(s, j0, entry, sl, atr):
    risk = entry - sl; trail = sl; r1 = False; end = min(j0 + HMAX, len(s) - 1)
    for k in range(j0 + 1, end + 1):
        if s[k]["l"] <= trail: return k
        if (s[k]["h"] - entry) / risk >= 1: r1 = True
        if r1:
            sw = cf_low(s, k)
            if sw: trail = max(trail, sw - 0.1 * atr)
    return end
exit_t = {}
for b in BASE:
    s = PRIMK[b["block"]]["series"]; tmap = {x["t"]: i for i, x in enumerate(s)}
    ek = letrun_ext(s, tmap[b["cj_t"]], b["g_entry"], b["g_sl"], b["g_atr"])
    exit_t[b["cj_t"]] = s[ek]["t"]
chain = [0] * 435
for i in range(1, 435):
    a, b = BASE[i - 1], BASE[i]
    if (b["cj_t"] - a["cj_t"]) <= 96 * 900 and exit_t[a["cj_t"]] <= b["cj_t"] and net(a) <= 0 \
       and abs((b["g_sl"] + 0.1 * b["g_atr"]) - (a["g_sl"] + 0.1 * a["g_atr"])) <= a["g_atr"]:
        chain[i] = chain[i - 1] + 1
dbl = sum(1 for i in fb2 if chain[i] >= 1)
print(f"    overlap F4 (dupla-taxação): {dbl}/{len(fb2)} flagged com chain_pos>=1 = {100*dbl/len(fb2):.0f}% (kill iii se >50%)")
RES["fb2"] = {"flagged": len(fb2), "flagged_net": stf["q"]["sum"], "skip_net": sts["q"]["sum"], "size50_net": sth["q"]["sum"],
              "size50_dd": sth["q"]["dd"], "size50_stk": sth["q"]["stkL"], "size50_runners": sth["runners_kept"],
              "p_skip_wk": p_skip, "p_size": p_size, "runner_kill_skip": len(rk2), "rk_years": [BASE[i]["yr"] for i in rk2],
              "f4_overlap_pct": round(100 * dbl / len(fb2), 0), "retention_size50": round(100 * sth["q"]["sum"] / bs["q"]["sum"], 1)}

# ---------- FB3 — limbo pós-breakout ----------
print("\nFB3 — RB_LIMBO (BULL, teto herdado do regime anterior 2-10 ATR ABAIXO do entry = pós-breakout; + supply>=16 OU idade Q2)")
if fb3_blocked:
    print("    BLOCKED_BY_MAPPING (assert falhou) — painéis não computados")
    RES["fb3"] = {"status": "BLOCKED_BY_MAPPING"}
else:
    fb3 = [i for i, b in enumerate(BASE) if b["g_v5h"] == "BULL" and -10 < FEATS[b["cj_t"]]["prev_hi_dist_atr"] <= -2
           and (fv(b, "n_supply_overhead") >= 16 or 178 < FEATS[b["cj_t"]]["rbox_age_h"] <= 415)]
    st3f = panel(fb3); show("FB3 flagged", st3f, f"({len(fb3)}/435)")
    st3 = panel([i for i in range(435) if i not in set(fb3)])
    show("FB3 SKIP (prateleira)", st3)
    p3 = pct(st3["q"]["sum"], wk_null_skip(fb3))
    rk3 = [i for i in fb3 if BASE[i]["g_R"] >= 3]
    ov1 = len(set(fb3) & prot)
    print(f"    null week-aware pct {p3}% | runner-kill {len(rk3)} | overlap com FB1 protegidos: {ov1} (deve ser 0)")
    RES["fb3"] = {"status": "CANDIDATE_SHELF", "flagged": len(fb3), "flagged_net": st3f["q"]["sum"],
                  "skip_net": st3["q"]["sum"], "skip_dd": st3["q"]["dd"], "skip_stk": st3["q"]["stkL"],
                  "p_wk": p3, "runner_kill": len(rk3), "overlap_fb1": ov1}

# ---------- FB4 — classes p/ F4 ----------
print("\nFB4 — CLASSES DE CONTEXTO (anotação p/ F4; zero eliminação)")
qp = [i for i, b in enumerate(BASE) if MAT[b["cj_t"]].get("room_above", 9) <= 1.11]
kn = [i for i, b in enumerate(BASE) if b["g_ema21_dist"] <= 0.16 and i not in set(qp)]
for tag, s_ in (("QUICKPOP", qp), ("KNIFE_RUNNER", kn)):
    st_ = panel(s_); show(f"FB4 {tag}", st_, f"({len(s_)}/435; overlap FB1 {len(set(s_) & prot)})")
RES["fb4"] = {"quickpop": len(qp), "knife": len(kn),
              "quickpop_runners": sum(1 for i in qp if BASE[i]["g_R"] >= 3),
              "knife_runners": sum(1 for i in kn if BASE[i]["g_R"] >= 3)}

# ---------- FB5 — forward-ledger (listas congeladas) ----------
LEDGER = {
    "CONV1": lambda b: fv(b, "clean_sky_atr", 99) <= 0.05 and fv(b, "n_supply_overhead") >= 48,
    "EXT": lambda b: b["g_ema21_dist"] >= 2.18 or b["g_ema50_dist"] >= 3.46,
    "CAL3_DVOID": lambda b: fv(b, "dist_demand_atr", 0) >= 1.37,
    "CAL4_B480": lambda b: 0.943 <= b["g_box480"] < 0.968,
    "H4_MIDLID": lambda b: fv(b, "h4n_clean_sky_atr", 99) != 99 and 0.38 <= fv(b, "h4n_clean_sky_atr", 99) < 0.92,
}
fw = {}
print("\nFB5 — FORWARD-LEDGER (listas de membros congeladas; avaliação só na extensão RAW futura)")
for k, fn in LEDGER.items():
    mem = [BASE[i]["cj_t"] for i in range(435) if fn(BASE[i])]
    rk = sum(1 for i in range(435) if fn(BASE[i]) and BASE[i]["g_R"] >= 3)
    fw[k] = {"n": len(mem), "runners_ref": rk, "members_cjt": mem}
    print(f"    {k:<10} n{len(mem):>3} runners-ref {rk}")
RES["fb5_ledger"] = {k: {kk: v[kk] for kk in ("n", "runners_ref")} for k, v in fw.items()}

# ---------- outputs ----------
rows = []
def addrow(name, st, note=""):
    if st is None: return
    q = st["q"]
    rows.append(dict(variant=name, N=st["N"], WR_liq=q["wr"], sumNET=q["sum"], DD=q["dd"], rDD=q["rdd"],
                     streak=q["stkL"], runners=st["runners_kept"], yr2024=st["yrs"][2024], yr2025=st["yrs"][2025],
                     yr2026=st["yrs"][2026], retention=round(100 * q["sum"] / bs["q"]["sum"], 1), note=note))
addrow("BASELINE", bs); addrow("FB1_protected_set", stp, "proteção, não filtro")
addrow("FB2_flagged", stf); addrow("FB2_SKIP_blocked", sts, "counterfactual bloqueado")
addrow("FB2_SIZE50", sth, "acionável via F4 floor 0,5")
if not fb3_blocked:
    addrow("FB3_flagged", st3f); addrow("FB3_SKIP_shelf", st3, "prateleira")
with open(HERE / "results" / "lab_b_r2_structural_context_results.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader()
    for r in rows: w.writerow(r)
RES["ledger_note"] = "CALIBRACAO (canon 45-grupos): ~100 looks no discovery; nulls pos-selecao; arbitro = extensao RAW nao-BEAR"
RES["forward_ledger_members"] = {k: v["members_cjt"] for k, v in fw.items()}
RES["fb2_members_cjt"] = [BASE[i]["cj_t"] for i in fb2]
json.dump(RES, open(HERE / "results" / "lab_b_r2_structural_context_summary.json", "w"), indent=1)
print("\nOK → results/lab_b_r2_structural_context_{results.csv,summary.json}")
