#!/usr/bin/env python3
"""DEVIL'S ADVOCATE / DA6 (2026-07-06) — decompor FASE A por causalidade e testar a hipótese:
'o sinal de evento da FASE A e majoritariamente RETROSPECTIVO; no ponto de entrada causal a
distincao colapsa; a FASE B negativa esta correta.'
NAO commita. NAO modifica ficheiros existentes. Sufixo _da6_. Reusa exatamente o loading/matcher/
colapso dos scripts event_level_map / event_causal_layer.

TAREFAS:
 1. classificar as ~14 features do mapa em RETROSPECTIVA vs CAUSAL-PROGRESSIVA.
 2. teste causal limpo: em pontos de decisao causais fixos (K=1,2,3 e 'ultimo'=FASE A), recomputar
    features SO com candidatos ate ali; MWU evento-fundo vs nao. Quais p<0,05 SOBREVIVEM?
 3. FASE B falha por FEATURE ou por POLITICA? oracle-dentro-do-aceito vs 1o-que-qualifica.
 4. confirmar FASE B (reproduzir S1,S3)."""
import json, bisect, hashlib, math, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])  # U,R3,S,TS
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]; OP = [b.get("o", b["c"]) for b in S]
CACHE = {r["cj_t"]: r for r in (json.loads(l) for l in open(HERE / "results" / "raw_feature_cache_20260706.jsonl"))}
UNIV = sorted([u for u in U if u["cj_t"] in R3 and u["cj_t"] in CACHE], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]
for u in UNIV:
    u["_flo"] = u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0); u["_a"] = u.get("g_atr") or 5.0
    u["_circ"] = set(); u["_F"] = CACHE[u["cj_t"]]
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"] + 8 * 3600:
        u = UNIV[j]; d = u["_flo"] - g["flush_low"]
        if -3 * u["_a"] <= d <= 1 * u["_a"]: u["_circ"].add(gi)
        j += 1
# colapso identico
EV = []; cur = []
for u in UNIV:
    if cur and u["cj_t"] - cur[-1]["cj_t"] <= 48 * 3600 and abs(u["_flo"] - cur[-1]["_flo"]) <= 3 * u["_a"]:
        cur.append(u)
    else:
        if cur: EV.append(cur)
        cur = [u]
if cur: EV.append(cur)
for ei, ev in enumerate(EV):
    for u in ev: u["_ev"] = ei
FUND = [ev for ev in EV if any(u["_circ"] for u in ev)]
NON = [ev for ev in EV if not any(u["_circ"] for u in ev)]
print(f"eventos {len(EV)} · fundo {len(FUND)} · nao {len(NON)} · densidade {len(NON)/len(FUND):.1f}:1")

def mwu_p(a, b):
    na, nb = len(a), len(b)
    if na < 5 or nb < 5: return 1.0
    allv = sorted([(v, 0) for v in a] + [(v, 1) for v in b]); ranks = [0.0]*len(allv); i = 0
    while i < len(allv):
        j = i
        while j+1 < len(allv) and allv[j+1][0] == allv[i][0]: j += 1
        for k in range(i, j+1): ranks[k] = (i+j)/2 + 1
        i = j+1
    Ra = sum(ranks[k] for k in range(len(allv)) if allv[k][1] == 0)
    Ua = Ra - na*(na+1)/2; Uu = min(Ua, na*nb - Ua)
    mu = na*nb/2; sd = math.sqrt(na*nb*(na+nb+1)/12)
    if sd == 0: return 1.0
    return math.erfc(abs((Uu-mu)/sd)/math.sqrt(2))

# ---------- features causais-no-ponto: aggregate over candidates 1..k of an event ----------
def feats_upto(ev, k):
    """features conhecidas no ponto de decisao = k-esimo candidato (1-based). SO cands 1..k e
    SO barras <= barra do k-esimo candidato. Retorna dict."""
    sub = ev[:k]
    F = [u["_F"] for u in sub]
    o = {}
    # aggregaveis progressivas (min/max sobre cands 1..k)
    o["rsi_min8_min"] = min(f["rsi_min8"] for f in F)
    o["rsi_cj_min"]   = min(f["rsi_cj"] for f in F)
    o["nas_dist_min"] = min(f["nas_dist"] for f in F)
    o["poc_dist_min"] = min(f["poc_dist"] for f in F)
    o["below_poc_any"] = max(f["below_poc"] for f in F)
    o["sell_climax_max"] = max(f["sell_climax4"] for f in F)
    o["nas_long_any"]  = max(f["nas_long_rec"] for f in F)
    o["flow_div_any"]  = max(f["flow_divergence"] for f in F)
    o["rsi_bull_div_any"] = max(f["rsi_bull_div"] for f in F)
    # familia-evento (as suspeitas retrospectivas), agora SO com cands 1..k
    o["n_cand"]  = k
    o["dur_h"]   = (sub[-1]["cj_t"] - sub[0]["cj_t"]) / 3600
    si = bisect.bisect_right(TS, ev[0]["cj_t"]) - 1
    ck = bisect.bisect_right(TS, sub[-1]["cj_t"]) - 1
    a = ATR[ck] or 5.0
    pre_hi = max(HI[max(0, si-96):si+1])          # perna ANTES do evento — causal
    lo_i = min(range(max(0, si-8), ck+1), key=lambda z: LO[z])  # low ate barra do cand-k
    o["pre_drop_atr"] = (pre_hi - LO[lo_i]) / a
    o["rev_speed"] = (ck - lo_i)                   # barras do running-low ate cand-k
    wick = 0.0
    for u in sub:
        ci = bisect.bisect_right(TS, u["cj_t"]) - 1
        for z in range(max(0, ci-3), ci+1):
            wick = max(wick, (min(OP[z], CL[z]) - LO[z]) / a)
    o["low_wick_max"] = wick
    return o

MAP_KEYS = ["rsi_min8_min","nas_dist_min","rsi_cj_min","nas_long_any","sell_climax_max","rev_speed",
            "dur_h","pre_drop_atr","n_cand","poc_dist_min","flow_div_any","low_wick_max",
            "below_poc_any","rsi_bull_div_any"]

# ============ TASK 1 — classificacao de causalidade ============
CLASS = {
 "n_cand":        ("RETROSPECTIVA", "contagem de TODOS os candidatos; so conhecida no fim do evento"),
 "dur_h":         ("RETROSPECTIVA", "precisa do ULTIMO candidato do evento"),
 "rev_speed":     ("RETROSPECTIVA", "barras low->ultimo-close; precisa do low + fim do evento"),
 "low_wick_max":  ("RETROSPECTIVA", "max wick sobre TODOS candidatos (inclui futuros)"),
 "pre_drop_atr":  ("MISTA→causal-progressiva", "perna pre-evento e causal; LO usa low corrente (progressivo)"),
 "rsi_min8_min":  ("CAUSAL-PROGRESSIVA", "min acumulavel; valor FASE-A usa min sobre todos = peek"),
 "rsi_cj_min":    ("CAUSAL-PROGRESSIVA", "idem min acumulavel"),
 "nas_dist_min":  ("CAUSAL-PROGRESSIVA", "idem min acumulavel"),
 "poc_dist_min":  ("CAUSAL-PROGRESSIVA", "idem min acumulavel"),
 "below_poc_any": ("CAUSAL-PROGRESSIVA", "max acumulavel"),
 "sell_climax_max":("CAUSAL-PROGRESSIVA","max acumulavel"),
 "nas_long_any":  ("CAUSAL-PROGRESSIVA", "max acumulavel"),
 "flow_div_any":  ("CAUSAL-PROGRESSIVA", "max acumulavel"),
 "rsi_bull_div_any":("CAUSAL-PROGRESSIVA","max acumulavel"),
}
print("\n===== TASK 1 — classificacao de causalidade das features do mapa =====")
for k in MAP_KEYS:
    c, why = CLASS[k]
    print(f"  {k:<18} {c:<24} {why}")
retro = [k for k in MAP_KEYS if CLASS[k][0].startswith("RETRO")]
print(f"  -> RETROSPECTIVAS puras: {retro}")

# ============ TASK 2 — teste causal limpo em pontos de decisao fixos ============
print("\n===== TASK 2 — MWU evento-fundo vs nao, com features CAUSAIS-NO-PONTO =====")
print("  (K = k-esimo candidato do evento; cap no ultimo se o evento tiver menos)")
for K in (1, 2, 3, "ALL"):
    rows = []
    for k in MAP_KEYS:
        A = []; B = []
        for ev in EV:
            kk = len(ev) if K == "ALL" else min(K, len(ev))
            fv = feats_upto(ev, kk)[k]
            (A if any(u["_circ"] for u in ev) else B).append(fv)
        rows.append((mwu_p(A, B), k, sum(A)/len(A), sum(B)/len(B)))
    rows.sort()
    surv = [r for r in rows if r[0] < 0.05]
    tag = "ULTIMO=FASE A (retrospectivo)" if K == "ALL" else f"K={K}"
    print(f"\n  --- decisao no {tag} · sobrevivem p<0,05: {len(surv)}/14 ---")
    for p, k, ma, mb in rows:
        mark = "***" if p < 0.05 else ("*" if p < 0.10 else "   ")
        print(f"    {mark} {k:<18} p={p:.4f} · fundo {ma:>8.2f} · nao {mb:>8.2f}  [{CLASS[k][0][:5]}]")

# ============ TASK 3 & 4 — FASE B: feature vs politica ============
# reconstruir _acc progressivo (identico a FASE B)
for ev in EV:
    st_i = bisect.bisect_right(TS, ev[0]["cj_t"]) - 1
    pre_hi = max(HI[max(0, st_i-96):st_i+1])
    acc = {"rsi_min8":99,"nas_dist":99,"sell_climax":0,"nas_long":0,"below_poc":0,"n":0,
           "poc_dist":99,"low_wick":0,"buy_accum":0}
    for u in ev:
        f = u["_F"]
        acc["rsi_min8"] = min(acc["rsi_min8"], f["rsi_min8"])
        acc["nas_dist"] = min(acc["nas_dist"], f["nas_dist"])
        acc["sell_climax"] = max(acc["sell_climax"], f["sell_climax4"])
        acc["nas_long"] = max(acc["nas_long"], f["nas_long_rec"])
        acc["below_poc"] = max(acc["below_poc"], f["below_poc"])
        acc["poc_dist"] = min(acc["poc_dist"], f["poc_dist"])
        acc["buy_accum"] = max(acc["buy_accum"], f["buy_accum12"])
        acc["n"] += 1
        ci = bisect.bisect_right(TS, u["cj_t"]) - 1
        u["_acc"] = dict(acc)
        u["_acc"]["dur_h"] = (u["cj_t"] - ev[0]["cj_t"]) / 3600
        u["_acc"]["pre_drop"] = (pre_hi - min(LO[max(0, st_i-8):ci+1])) / (u["_a"])

def selector(name):
    if name == "S1":
        return lambda u: u["_acc"]["rsi_min8"]<=32 and u["_acc"]["n"]>=2 and (u["_acc"]["sell_climax"]>=1 or u["_acc"]["nas_long"]==1) and u["_acc"]["below_poc"]==1
    if name == "S2":
        return lambda u: u["_acc"]["rsi_min8"]<=30 and u["_acc"]["n"]>=3 and u["_acc"]["sell_climax"]>=1 and u["_acc"]["below_poc"]==1 and u["_acc"]["pre_drop"]>=8
    if name == "S3":
        return lambda u: u["_acc"]["rsi_min8"]<=40 and u["_acc"]["nas_long"]==1 and u["_acc"]["n"]>=2 and u["_acc"]["below_poc"]==1
    if name == "S4":
        return lambda u: u["_acc"]["rsi_min8"]<=34 and u["_acc"]["n"]>=2 and (u["_acc"]["sell_climax"]>=1 or u["_acc"]["nas_long"]==1)

def hit(u): return 1 if R3[u["cj_t"]]["R3"] >= 3 else 0

# base rates
base_ev_bottom = len(FUND)/len(EV)
allc_hit = sum(hit(u) for u in UNIV)/len(UNIV)
print("\n===== TASK 3 — FASE B falha por FEATURE (seletor-de-evento) ou POLITICA (entrada)? =====")
print(f"  base: P(evento e fundo)={base_ev_bottom:.3f} ({len(FUND)}/{len(EV)}) · hit3R medio de todos candidatos={allc_hit:.3f}")
print(f"  {'sel':<4} {'#ev_acc':>7} {'1o-qualif':>10} {'best-in-acc':>12} {'any-in-ev(oracle)':>17} {'circ_acc':>9}")
task3 = {}
for nm in ("S1","S2","S3","S4"):
    sel = selector(nm)
    ev_acc = []      # eventos com >=1 candidato aceito
    first_hit = []   # politica: 1o que qualifica
    best_hit = []    # oracle DENTRO do aceito: melhor R3 entre os aceitos
    orc_ev_hit = []  # oracle sobre TODOS candidatos do evento aceito (teto se selecao-evento fosse o unico filtro)
    circ = set()
    for ev in EV:
        acc = [u for u in ev if sel(u)]
        if not acc: continue
        ev_acc.append(ev)
        acc_sorted = sorted(acc, key=lambda u: u["cj_t"])
        first_hit.append(hit(acc_sorted[0]))
        best_hit.append(max(hit(u) for u in acc))
        orc_ev_hit.append(max(hit(u) for u in ev))
        for u in ev: circ |= u["_circ"]
    n = len(ev_acc)
    if n == 0:
        print(f"  {nm:<4} vazio"); continue
    fr = sum(first_hit)/n; br = sum(best_hit)/n; orc = sum(orc_ev_hit)/n
    print(f"  {nm:<4} {n:>7} {100*fr:>9.1f}% {100*br:>11.1f}% {100*orc:>16.1f}% {len(circ):>8}/60")
    task3[nm] = {"n_ev": n, "first_hit": round(fr,3), "best_in_acc": round(br,3), "oracle_any_in_ev": round(orc,3), "circ": len(circ)}
print("  leitura: first≈best≈base -> a FEATURE (seletor de evento) e o gargalo (aceita eventos que NAO sao fundo).")
print("           best>>first -> a POLITICA de entrada e o gargalo (o evento tem fundo mas o 1o candidato erra).")

# ============ TASK 4 — confirmar FASE B (reproduzir null de S1,S3) ============
print("\n===== TASK 4 — confirmacao FASE B (null vs base 1/evento) =====")
BASE_first = []; seen = set()
for u in UNIV:
    if u["_ev"] not in seen: BASE_first.append(u); seen.add(u["_ev"])
def first_per_event(sel):
    out = {}
    for u in UNIV:
        if u["_ev"] in out: continue
        if sel(u): out[u["_ev"]] = u
    return list(out.values())
def null_p(rows, ref, seed):
    H0 = [hit(r) for r in ref]; obs = sum(hit(r) for r in rows)/len(rows)
    random.seed(seed)
    return sum(1 for _ in range(4000) if sum(random.sample(H0, len(rows)))/len(rows) >= obs)/4000
bhit = sum(hit(r) for r in BASE_first)/len(BASE_first)
print(f"  BASE 1/evento N{len(BASE_first)} hit3R {100*bhit:.1f}%")
for nm in ("S1","S3"):
    rows = first_per_event(selector(nm))
    h = sum(hit(r) for r in rows)/len(rows)
    print(f"  {nm} N{len(rows)} hit3R {100*h:.1f}% · P(null vs base)={null_p(rows, BASE_first, 601):.4f}")

json.dump({"task3": task3, "base_ev_bottom": round(base_ev_bottom,3), "allc_hit": round(allc_hit,3)},
          open(HERE / "results" / "event_causal_decompose_da6_20260706.json", "w"), indent=1)
print("\nOK → results/event_causal_decompose_da6_20260706.json")
