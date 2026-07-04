#!/usr/bin/env python3
"""DA LAB B r2 — ATAQUE 1: adjudicação FB3 (assert 20/20 mismatch → BLOCKED provisório).
Perguntas: (a) feats json do regimebox agent é CAUSAL? (b) assert do lab está mal-especificado?
Método:
  A. Reproduzir o assert do lab byte-a-byte (seed 42, mesma amostra) → confirmar 20/20.
  B. Diagnóstico por componente do mismatch (sinal? estado-por-hora? timeline de bloco?).
  C. Recompute independente GLOBAL (spec do probe1, código próprio) vs feats — 435/435.
  D. PROVA DE CAUSALIDADE: recompute com pipeline INTEIRO truncado em bars t<=cj_t
     (agregados H/D, EMA, stable, ov_hour reconstruídos só do passado) vs feats — amostra 40.
  E. Assert CORRIGIDO (diff mínimo) na mesma amostra do lab → mismatches.
  F. Painéis FB3 como teriam saído (flagged/SKIP/null week-aware/runner-kill/overlap FB1).
Leitura-só: nada é escrito fora deste print. PROIBIDO commit.
"""
import json, random, bisect, hashlib
from pathlib import Path

HERE = Path(__file__).parent
SB = 0.80

# ---- selo do universo ----
CANON = HERE / "results" / "lab_g_candidates.jsonl"
sha = hashlib.sha256(CANON.read_bytes()).hexdigest()
assert sha == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = [json.loads(l) for l in open(CANON)]
BASE = sorted([r for r in U if r["g_in_base435"] == 1 and r["g_v5h"] != "BEAR"], key=lambda r: r["cj_t"])
assert len(BASE) == 435
FEATS = {f["cj_t"]: f for f in json.load(open(HERE / "results" / "_labB_r2_regime_box_feats.json"))}

# ---- engine ----
ns = {"__name__": "e", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "e", "exec"), ns)
regime_h = ns["regime_hourcausal"]; PRIMK = ns["PRIMK"]
HK, DK = ns["HK"], ns["DK"]
bars, T15 = ns["bars"], ns["T15"]

def net(r): return r["g_R"] - SB / r["g_risk"]

# ============ A. reprodução exata do assert do lab ============
def rbox_recompute_LAB(b):
    t = b["cj_t"]; s = PRIMK[b["block"]]["series"]
    hrs = sorted({x["t"] // 3600 for x in s if x["t"] <= t})
    if len(hrs) < 8: return None
    st_of = lambda h: regime_h((h + 1) * 3600)
    cur = st_of(hrs[-1]); i = len(hrs) - 1
    while i > 0 and st_of(hrs[i - 1]) == cur: i -= 1
    seg_h = hrs[i:]
    age = len(seg_h)
    j = i - 1
    if j < 0: return None
    pstate = st_of(hrs[j]); k = j
    while k > 0 and st_of(hrs[k - 1]) == pstate: k -= 1
    prev_h = hrs[k:j + 1]
    bb = [x for x in s if x["t"] <= t]
    inseg = [x for x in bb if x["t"] // 3600 in set(seg_h)]
    inprev = [x for x in bb if x["t"] // 3600 in set(prev_h)]
    if not inseg or not inprev: return None
    hi, lo = max(x["h"] for x in inseg), min(x["l"] for x in inseg)
    phi = max(x["h"] for x in inprev)
    atr = b["g_atr"]; entry = b["g_entry"]
    return {"rbox_age_h": age, "prev_state": pstate,
            "rbox_pos": (entry - lo) / ((hi - lo) or atr),
            "prev_hi_dist_atr": (entry - phi) / atr}

random.seed(42)
smp = random.sample(range(435), 40)
mism = 0; checked = 0; diag = []
for i in smp:
    b = BASE[i]; rc = rbox_recompute_LAB(b); fj = FEATS[b["cj_t"]]
    if rc is None: continue
    checked += 1
    ok = (rc["prev_state"] == fj["prev_state"] and abs(rc["rbox_age_h"] - fj["rbox_age_h"]) <= 2
          and abs(rc["rbox_pos"] - fj["rbox_pos"]) <= 0.05
          and abs(rc["prev_hi_dist_atr"] - (fj["prev_hi_dist_atr"] if fj["prev_hi_dist_atr"] is not None else 0)) <= 0.25)
    if not ok:
        mism += 1
        fp = fj["prev_hi_dist_atr"]
        diag.append({
            "i": i, "state_ok": rc["prev_state"] == fj["prev_state"],
            "age_ok": abs(rc["rbox_age_h"] - fj["rbox_age_h"]) <= 2,
            "pos_ok": abs(rc["rbox_pos"] - fj["rbox_pos"]) <= 0.05,
            "dist_ok": fp is not None and abs(rc["prev_hi_dist_atr"] - fp) <= 0.25,
            "dist_SIGNFLIP_ok": fp is not None and abs(rc["prev_hi_dist_atr"] + fp) <= 0.25,
        })
print("=" * 100)
print(f"A. assert do lab reproduzido: checked {checked} mismatches {mism} (lab reportou 20/20)")
n_sign = sum(1 for d in diag if d["dist_SIGNFLIP_ok"])
n_dist_bad = sum(1 for d in diag if not d["dist_ok"])
print(f"B. diagnóstico dos {len(diag)} mismatches:")
print(f"   dist FALHA em {n_dist_bad}/{len(diag)}; com SINAL INVERTIDO (entry-phi vs phi-entry) bate em {n_sign}/{len(diag)}")
print(f"   state_ok {sum(d['state_ok'] for d in diag)}/{len(diag)} · age_ok {sum(d['age_ok'] for d in diag)}/{len(diag)} · pos_ok {sum(d['pos_ok'] for d in diag)}/{len(diag)}")

# ============ C. recompute independente GLOBAL (spec probe1, timeline global do engine) ============
STATE = [regime_h(hk * 3600) for hk in HK]   # convenção do probe1 == estado do engine dentro da hora hk
def rbox_recompute_GLOBAL(b, hk_list=HK, state=STATE, t15=T15, bmap=bars):
    t = b["cj_t"]; entry = b["g_entry"]; atr = b["g_atr"]
    j = bisect.bisect_right(hk_list, t // 3600) - 1
    i = j
    while i > 0 and state[i - 1] == state[j]: i -= 1
    t0 = hk_list[i] * 3600
    i0 = bisect.bisect_left(t15, t0); i1 = bisect.bisect_right(t15, t)
    seg = [bmap[x] for x in t15[i0:i1]]
    hi, lo = max(x["h"] for x in seg), min(x["l"] for x in seg)
    out = {"rbox_pos": (entry - lo) / ((hi - lo) or atr), "rbox_age_h": j - i + 1,
           "rbox_hi_dist_atr": (hi - entry) / atr}
    if i == 0:
        out["prev_state"] = None; out["prev_hi_dist_atr"] = None
    else:
        pj = i - 1; pk = pj
        while pk > 0 and state[pk - 1] == state[pj]: pk -= 1
        pt0, pt1 = hk_list[pk] * 3600, (hk_list[pj] + 1) * 3600
        pi0, pi1 = bisect.bisect_left(t15, pt0), bisect.bisect_left(t15, pt1)
        pbb = [bmap[x] for x in t15[pi0:pi1]]
        out["prev_state"] = state[pj]
        out["prev_hi_dist_atr"] = (max(x["h"] for x in pbb) - entry) / atr
    return out

bad = 0
for b in BASE:
    rc = rbox_recompute_GLOBAL(b); fj = FEATS[b["cj_t"]]
    okp = (fj["prev_hi_dist_atr"] is None and rc["prev_hi_dist_atr"] is None) or \
          (fj["prev_hi_dist_atr"] is not None and rc["prev_hi_dist_atr"] is not None
           and abs(rc["prev_hi_dist_atr"] - fj["prev_hi_dist_atr"]) <= 0.002)
    ok = (rc["prev_state"] == fj["prev_state"] and rc["rbox_age_h"] == fj["rbox_age_h"]
          and abs(rc["rbox_pos"] - fj["rbox_pos"]) <= 0.001
          and abs(rc["rbox_hi_dist_atr"] - fj["rbox_hi_dist_atr"]) <= 0.002 and okp)
    if not ok: bad += 1
print(f"\nC. recompute independente GLOBAL (convenção probe1 = engine, timeline global): mismatches {bad}/435")

# ============ D. PROVA DE CAUSALIDADE — pipeline inteiro truncado em t<=cj_t ============
def full_truncated(b):
    """reconstrói TUDO (agregados H/D, TR, EMA, raw_stable, stable, ov_hour, estado, segmentos,
    boxes) usando SOMENTE bars com t <= cj_t. Zero acesso a dados futuros."""
    t_cut = b["cj_t"]
    tb = [t for t in T15 if t <= t_cut]
    Hh = {}
    for t in tb:
        x = bars[t]; hk = t // 3600
        g = Hh.setdefault(hk, {"c": x["c"], "h": x["h"]}); g["h"] = max(g["h"], x["h"]); g["c"] = x["c"]
    hks = sorted(Hh); hc = [Hh[k]["c"] for k in hks]; hh = [Hh[k]["h"] for k in hks]
    Dd = {}
    for t in tb:
        x = bars[t]; k = t // 86400
        g = Dd.setdefault(k, {"h": x["h"], "l": x["l"], "c": x["c"]})
        g["h"] = max(g["h"], x["h"]); g["l"] = min(g["l"], x["l"]); g["c"] = x["c"]
    dks = sorted(Dd); dc = [Dd[k]["c"] for k in dks]; dh = [Dd[k]["h"] for k in dks]; dl = [Dd[k]["l"] for k in dks]
    tr = [0.0]
    for i in range(1, len(dks)): tr.append(max(dh[i] - dl[i], abs(dh[i] - dc[i - 1]), abs(dl[i] - dc[i - 1])))
    def atrd(i, n=14):
        a = tr[max(1, i - n + 1):i + 1]; return sum(a) / len(a) if a else 1.0
    def ema_at(arr, i, n):
        c = arr[max(0, i - 3 * n):i + 1]; k = 2 / (n + 1); e = c[0]
        for v in c[1:]: e = v * k + e * (1 - k)
        return e
    e50 = [ema_at(dc, i, 50) for i in range(len(dks))]; e100 = [ema_at(dc, i, 100) for i in range(len(dks))]
    N, eff_thr, slope_thr, R_thr, K, Kbear = 15, 0.30, 0.20, 2.0, 5, 5
    def raw_stable(i):
        if i < max(2 * N, 40): return "RANGE"
        a = atrd(i) or 1.0; slope = (e50[i] - e50[i - 5]) / a
        seg = dc[i - N:i + 1]; nt = seg[-1] - seg[0]; path = sum(abs(seg[j] - seg[j - 1]) for j in range(1, len(seg))); eff = abs(nt) / path if path > 0 else 0
        hh_ = max(dh[i - N:i]); ll = min(dl[i - N:i]); pos = (dc[i] - ll) / (hh_ - ll) if hh_ > ll else .5; s100 = (e100[i] - e100[i - 10]) / a
        tu = eff >= eff_thr and slope > slope_thr; td = eff >= eff_thr and slope < -slope_thr
        sb = e50[i] > e100[i] and s100 > 0; se = e50[i] < e100[i] and s100 < 0
        cont = eff < eff_thr and 0.15 <= pos <= 0.85 and abs(slope) < slope_thr
        peak = max(dh[i - 30:i + 1]); retreat = (peak - dc[i]) / a; lh = max(dh[i - N:i]) < max(dh[i - 2 * N:i - N]); bef = dc[i] < e50[i] and (e50[i] - e50[i - 5]) < 0; bl = dc[i] < min(dl[i - N:i - 2])
        if (bl and bef) or (retreat >= R_thr and lh and bef) or td or (se and pos < 0.6 and not cont): return "BEAR"
        if tu or (sb and pos > 0.55 and not cont): return "BULL"
        return "RANGE"
    raws = [raw_stable(i) for i in range(len(dks))]
    stb = []; cur = "RANGE"; pend = None; pn = 0
    for v in raws:
        if v == cur: pend = None; pn = 0
        elif v == pend: pn += 1
        else: pend = v; pn = 1
        need = Kbear if pend == "BEAR" else K
        if pn >= need: cur = pend; pend = None; pn = 0
        stb.append(cur)
    P, mom, dd_intra, Krec_h = 48, 24, 0.06, 120
    ovh = []; ov = False; quiet = 0
    for j in range(len(hks)):
        if j < max(P, mom): ovh.append(False); continue
        peak = max(hh[j - P:j + 1]); ddp = (peak - hc[j]) / peak if peak > 0 else 0
        fired = ddp >= dd_intra and hc[j] < hc[j - mom]
        if fired: ov = True; quiet = 0
        elif ov:
            quiet += 1
            if quiet >= Krec_h: ov = False
        ovh.append(ov)
    def reg(cjt):
        dk_today = cjt // 86400
        di = bisect.bisect_left(dks, dk_today) - 1
        st = "RANGE" if di < 0 else stb[di]
        hi = bisect.bisect_right(hks, (cjt // 3600) - 1) - 1
        ovr = ovh[hi] if hi >= 0 else False
        return "BEAR" if (ovr or st == "BEAR") else st
    state = [reg(hk * 3600) for hk in hks]
    return rbox_recompute_GLOBAL(b, hk_list=hks, state=state, t15=tb, bmap=bars)

sub = [BASE[i] for i in smp]                       # mesma amostra do lab (40)
sub += BASE[:3] + BASE[-3:]                        # + extremos (bordas de dados)
badT = 0; det = []
for b in sub:
    rc = full_truncated(b); fj = FEATS[b["cj_t"]]
    okp = (fj["prev_hi_dist_atr"] is None and rc["prev_hi_dist_atr"] is None) or \
          (fj["prev_hi_dist_atr"] is not None and rc["prev_hi_dist_atr"] is not None
           and abs(rc["prev_hi_dist_atr"] - fj["prev_hi_dist_atr"]) <= 0.002)
    ok = (rc["prev_state"] == fj["prev_state"] and rc["rbox_age_h"] == fj["rbox_age_h"]
          and abs(rc["rbox_pos"] - fj["rbox_pos"]) <= 0.001 and okp)
    if not ok: badT += 1; det.append((b["cj_t"], rc, {k: fj[k] for k in ("prev_state", "rbox_age_h", "rbox_pos", "prev_hi_dist_atr")}))
print(f"\nD. CAUSALIDADE — pipeline inteiro reconstruído SÓ com bars t<=cj_t ({len(sub)} casos, "
      f"amostra do lab + bordas): mismatches vs feats = {badT}")
for d in det[:5]: print("   DIVERGE:", d)

# ============ E. assert CORRIGIDO (diff mínimo sobre o do lab) ============
def rbox_recompute_FIXED(b):
    t = b["cj_t"]
    hrs_all = HK                                   # FIX 3: timeline GLOBAL, não bloco
    jj = bisect.bisect_right(hrs_all, t // 3600) - 1
    hrs = hrs_all[:jj + 1]
    if len(hrs) < 8: return None
    st_of = lambda h: regime_h(h * 3600)           # FIX 2: estado NA hora h (engine), não (h+1)
    cur = st_of(hrs[-1]); i = len(hrs) - 1
    while i > 0 and st_of(hrs[i - 1]) == cur: i -= 1
    seg_h = hrs[i:]; age = len(seg_h)
    j = i - 1
    if j < 0: return None
    pstate = st_of(hrs[j]); k = j
    while k > 0 and st_of(hrs[k - 1]) == pstate: k -= 1
    prev_h = hrs[k:j + 1]
    i0 = bisect.bisect_left(T15, seg_h[0] * 3600); i1 = bisect.bisect_right(T15, t)
    inseg = [bars[x] for x in T15[i0:i1]]
    p0 = bisect.bisect_left(T15, prev_h[0] * 3600); p1 = bisect.bisect_left(T15, (prev_h[-1] + 1) * 3600)
    inprev = [bars[x] for x in T15[p0:p1]]
    if not inseg or not inprev: return None
    hi, lo = max(x["h"] for x in inseg), min(x["l"] for x in inseg)
    phi = max(x["h"] for x in inprev)
    atr = b["g_atr"]; entry = b["g_entry"]
    return {"rbox_age_h": age, "prev_state": pstate,
            "rbox_pos": (entry - lo) / ((hi - lo) or atr),
            "prev_hi_dist_atr": (phi - entry) / atr}   # FIX 1: sinal do probe (>0 = teto acima)

mismF = 0; checkedF = 0
for i in smp:
    b = BASE[i]; rc = rbox_recompute_FIXED(b); fj = FEATS[b["cj_t"]]
    if rc is None or fj["prev_hi_dist_atr"] is None: continue
    checkedF += 1
    ok = (rc["prev_state"] == fj["prev_state"] and abs(rc["rbox_age_h"] - fj["rbox_age_h"]) <= 2
          and abs(rc["rbox_pos"] - fj["rbox_pos"]) <= 0.05 and abs(rc["prev_hi_dist_atr"] - fj["prev_hi_dist_atr"]) <= 0.25)
    if not ok: mismF += 1
print(f"\nE. assert CORRIGIDO (sinal + estado-hora + timeline global), mesma amostra: checked {checkedF} mismatches {mismF}")

# variante: SÓ o fix do sinal, mantendo bloco + (h+1) — quanto resolve sozinho?
mismS = 0; checkedS = 0
for i in smp:
    b = BASE[i]; rc = rbox_recompute_LAB(b); fj = FEATS[b["cj_t"]]
    if rc is None or fj["prev_hi_dist_atr"] is None: continue
    checkedS += 1
    ok = (rc["prev_state"] == fj["prev_state"] and abs(rc["rbox_age_h"] - fj["rbox_age_h"]) <= 2
          and abs(rc["rbox_pos"] - fj["rbox_pos"]) <= 0.05 and abs(-rc["prev_hi_dist_atr"] - fj["prev_hi_dist_atr"]) <= 0.25)
    if not ok: mismS += 1
print(f"   variante SÓ-sinal (mantém bloco/(h+1)): checked {checkedS} mismatches {mismS}")

# ============ F. painéis FB3 como teriam saído ============
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def panel(idxs):
    seq = sorted(idxs, key=lambda i: BASE[i]["cj_t"]); n = len(seq)
    R = [net(BASE[i]) for i in seq]
    eq = pk = dd = 0.0; mL = cl = 0
    for x in R:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    w = sum(1 for x in R if x > 0)
    yrs = {y: round(sum(net(BASE[i]) for i in seq if BASE[i]["yr"] == y), 1) for y in (2024, 2025, 2026)}
    return dict(N=n, wr=round(100 * w / n, 1), sum=round(sum(R), 1), dd=round(dd, 1),
                rdd=round(abs(sum(R) / dd), 2) if dd < 0 else 99, stk=mL,
                run=sum(1 for i in seq if BASE[i]["g_R"] >= 3), yrs=yrs)

fb3 = [i for i, b in enumerate(BASE) if b["g_v5h"] == "BULL" and FEATS[b["cj_t"]]["prev_hi_dist_atr"] is not None
       and -10 < FEATS[b["cj_t"]]["prev_hi_dist_atr"] <= -2
       and (fv(b, "n_supply_overhead") >= 16 or 178 < FEATS[b["cj_t"]]["rbox_age_h"] <= 415)]
stf = panel(fb3); sts = panel([i for i in range(435) if i not in set(fb3)])
print(f"\nF. FB3 painéis (com feats ADJUDICADOS):")
print(f"   flagged  {stf}")
print(f"   SKIP     {sts}")
# null week-aware (código próprio)
random.seed(7)
bywk = {}
for i in fb3: bywk.setdefault(BASE[i]["g_week"], []).append(i)
pool = {}
for i in range(435): pool.setdefault(BASE[i]["g_week"], []).append(i)
dist = []
for _ in range(2000):
    drop = set()
    for wk, mem in bywk.items(): drop |= set(random.sample(pool[wk], min(len(mem), len(pool[wk]))))
    dist.append(sum(net(BASE[i]) for i in range(435) if i not in drop))
p3 = 100 * sum(1 for d in dist if d < sts["sum"]) / len(dist)
rk3 = [i for i in fb3 if BASE[i]["g_R"] >= 3]
# overlap com FB1 protegidos
C = {}
C["conv4"] = {i for i, b in enumerate(BASE) if fv(b, "h1n_clean_sky_atr", 99) <= 0.29 and fv(b, "h4n_clean_sky_atr", 99) <= 0.12}
C["box96top"] = {i for i, b in enumerate(BASE) if 0.906 <= b["g_box96"] < 0.947}
C["legtop"] = {i for i, b in enumerate(BASE) if fv(b, "legpos90") >= 0.804}
C["htfceil"] = {i for i, b in enumerate(BASE) if fv(b, "h1n_clean_sky_atr", 99) <= 0.39 and fv(b, "h4n_clean_sky_atr", 99) <= 0.17}
C["rb_p1"] = {i for i, b in enumerate(BASE) if b["g_v5h"] == "BULL" and FEATS[b["cj_t"]]["prev_hi_dist_atr"] is not None and FEATS[b["cj_t"]]["prev_hi_dist_atr"] >= -2 and FEATS[b["cj_t"]]["rbox_age_h"] <= 178}
C["rb_p2"] = {i for i, b in enumerate(BASE) if b["g_v5h"] == "RANGE" and FEATS[b["cj_t"]]["rbox_pos"] >= 0.9 and FEATS[b["cj_t"]]["prev_state"] == "BULL" and (FEATS[b["cj_t"]]["prev_hi_dist_atr"] or 0) > 0}
C["rb_p3"] = {i for i, b in enumerate(BASE) if b["g_v5h"] == "BULL" and 3 < FEATS[b["cj_t"]]["rbox_hi_dist_atr"] <= 8}
prot = set().union(*C.values())
ov1 = len(set(fb3) & prot)
ovc = {k: len(set(fb3) & v) for k, v in C.items() if set(fb3) & v}
print(f"   null week-aware (2000 reps, seed próprio) pct {p3:.1f}% | runner-kill {len(rk3)} "
      f"({[round(BASE[i]['g_R'],2) for i in rk3]}) | overlap FB1 {ov1} {ovc}")
print(f"   jackknife: flagged por ano {stf['yrs']} | membros: "
      f"{[__import__('datetime').datetime.utcfromtimestamp(BASE[i]['cj_t']).strftime('%y-%m-%d') for i in fb3]}")
