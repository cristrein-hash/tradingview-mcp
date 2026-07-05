#!/usr/bin/env python3
"""FRENTE 1 — HARDENING FORMAL RWS-15M (2026-07-05, GO Cris; rigor do V1.4g-4H).
Config CONGELADA (porte V1.4g-RWS-A6, leitura sequencial):
  buy_recent(bubbles 0-4b)>=2 · (rsi_above_ma OU n_supply>20) · anti-burst-fake(A6) · anti-beardiv-cluster(A7)
  regime !=BEAR · sem faca · entry=close@cj · SL=flush-0,1ATR · EXIT: alvo fixo 3R first-touch (árbitro).
Sela lista de sinais (sha). Hardening: (1) painel completo bruto+SB; (2) WALK-FORWARD 3 janelas
(24/25/26 por ano — 2016-2023 não temos, então por ANO como janela); (3) NULLS por regime
(random mesma-freq BULL+RANGE 1000 · year-aware); (4) streak DISTRIBUCIONAL (block-bootstrap episódio);
(5) EXIT alternativo (let-run trail) reportado; (6) jackknife-episódio (concentração). One-shot já lido
antes (44%/stk4); este = validação formal. Universo selado."""
import json, glob, bisect, hashlib, random, collections
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
SB = 0.80; random.seed(42)
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
WEEKS = len({r["g_week"] for r in U})
# --- séries + sequencial ---
series = {}; nas = []
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"], b)
    nas += [e for e in d["nas_events"] if e.get("t")]
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; Np = len(S)
L = [b["l"] for b in S]; H = [b["h"] for b in S]; Cc = [b["c"] for b in S]
RSI = [b.get("rsi") for b in S]; RSIMA = [None] * Np
for i in range(Np):
    w = [RSI[j] for j in range(max(0, i - 13), i + 1) if RSI[j] is not None]; RSIMA[i] = sum(w) / len(w) if w else None
BUB = sorted([json.loads(l) for p in glob.glob(str(HERE / "bubbles" / "*.bubbles.jsonl")) for l in open(p)], key=lambda x: (x.get("known_at") or x["t"]))
BUBK = [(x.get("known_at") or x["t"]) for x in BUB]; nas.sort(key=lambda e: e["t"]); NAST = [e["t"] for e in nas]
wgt = {"S": 1, "M": 2, "L": 3}
def bub(t0, lo, hi):
    h = bisect.bisect_right(BUBK, t0); return [BUB[i] for i in range(h) if t0 - hi * 900 <= BUB[i]["t"] <= t0 - lo * 900]
def rws(r):
    cj = r["cj_t"]; i = bisect.bisect_right(TS, cj) - 1
    if i < 40: return False
    w4 = bub(cj, 0, 4); old = bub(cj, 5, 10); w8 = bub(cj, 0, 8)
    buy4 = sum(wgt[x["size"]] for x in w4 if x["side"] == "BUY"); burst = buy4 - sum(wgt[x["size"]] for x in old if x["side"] == "BUY")
    large8 = int(any(x["side"] == "BUY" and x["size"] == "L" for x in w8))
    rsi_above = int(RSI[i] is not None and RSIMA[i] is not None and RSI[i] > RSIMA[i])
    bd = 0
    for k in range(i - 20, i - 2):
        if k < 3: continue
        if H[k] == max(H[k - 2:k + 3]):
            pv = [j for j in range(k - 12, k - 2) if H[j] == max(H[max(0, j - 2):j + 3])]
            if pv and RSI[k] is not None and RSI[pv[-1]] is not None and H[k] > H[pv[-1]] and RSI[k] < RSI[pv[-1]]: bd += 1
    j = bisect.bisect_right(NAST, cj) - 1; nas_short = int(j >= 0 and nas[j]["dir"] == "SHORT" and (cj - nas[j]["t"]) // 900 <= 4)
    return buy4 >= 2 and not (rsi_above == 0 and fv(r, "n_supply_overhead", 99) <= 20) and not (burst >= 3 and large8 == 0 and nas_short == 0) and bd < 2
NB = [r for r in U if r["g_v5h"] != "BEAR" and r["g_knife"] == 0]
SEL = sorted([r for r in NB if rws(r)], key=lambda r: r["cj_t"])
sig = [{"cj_t": r["cj_t"], "yr": r["yr"], "regime": r["g_v5h"], "entry": r["g_entry"], "sl": r["g_sl"],
        "risk": round(r["g_risk"], 2), "atr": r["g_atr"]} for r in SEL]
(HERE / "results" / "rws15m_signals_20260705.json").write_text(json.dumps(sig, indent=1))
sha = hashlib.sha256((HERE / "results" / "rws15m_signals_20260705.json").read_bytes()).hexdigest()
(HERE / "results" / "rws15m_signals_20260705.sha256").write_text(sha + "  results/rws15m_signals_20260705.json\n")
print(f"SELADO: {len(sig)} sinais RWS-15M · sha {sha[:16]}")

def r3net(r): return R3[r["cj_t"]]["R3"], R3[r["cj_t"]]["R3"] - SB / r["g_risk"]
def letrun(r):
    i = bisect.bisect_right(TS, r["cj_t"]) - 1; entry = r["g_entry"]; sl = r["g_sl"]; atr = r["g_atr"]; risk = entry - sl
    trail = sl; r1 = False; end = min(i + 480, Np - 1)
    ISLOW = None
    for k in range(i + 1, end + 1):
        if L[k] <= trail: return max(-1.0, min(20.0, (trail - entry) / risk))
        if (H[k] - entry) / risk >= 1: r1 = True
        if r1:
            p = None
            for q in range(k - 2, max(1, k - 122), -1):
                if L[q] == min(L[q - 2:q + 3]): p = q; break
            if p is not None: trail = max(trail, L[p] - 0.1 * atr)
    return max(-1.0, min(20.0, (Cc[end] - entry) / risk))
def panel(rows, label="3R"):
    n = len(rows)
    if not n: return None
    rs = sorted(rows, key=lambda r: r["cj_t"])
    if label == "3R": g = [R3[r["cj_t"]]["R3"] for r in rs]; q = [R3[r["cj_t"]]["net3"] for r in rs]
    else:
        g = [letrun(r) for r in rs]; q = [x - SB / r["g_risk"] for x, r in zip(g, rs)]
    out = {"N": n, "hit3R": round(100 * sum(1 for r in rs if R3[r["cj_t"]]["R3"] >= 3) / n, 1)}
    for tag, Rr in (("g", g), ("q", q)):
        eq = pk = dd = 0.0; mL = cl = 0
        for x in Rr:
            eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
            if x <= 0: cl += 1; mL = max(mL, cl)
            else: cl = 0
        w = sum(1 for x in Rr if x > 0)
        out[tag] = dict(sum=round(sum(Rr), 1), wr=round(100 * w / n, 1), dd=round(dd, 1),
                        rdd=round(abs(sum(Rr) / dd), 2) if dd < 0 else 99, stk=mL)
    out["yrs"] = {y: round(sum(qq for qq, r in zip(q, rs) if r["yr"] == y), 1) for y in (2024, 2025, 2026)}
    return out
def show(t, p):
    if not p: print(f"  {t:<20} vazio"); return
    print(f"  {t:<20} N{p['N']:>3} hit3R {p['hit3R']:>5.1f}% | BRUTO {p['g']['sum']:>6.1f} WR{p['g']['wr']:>5.1f} | "
          f"NET {p['q']['sum']:>6.1f} WR{p['q']['wr']:>5.1f} DD{p['q']['dd']:>6.1f} r/DD{p['q']['rdd']:>5.2f} stk-{p['q']['stk']} | {p['yrs']}")
print("\n" + "=" * 106)
print("HARDENING RWS-15M — árbitro 3R-fixo (config congelada)")
print("=" * 106)
p3 = panel(SEL, "3R"); show("EXIT 3R-fixo", p3)
plr = panel(SEL, "letrun"); show("EXIT let-run (alt)", plr)
# WALK-FORWARD por ano
print("\nWALK-FORWARD (por ano, exit 3R):")
for y in (2024, 2025, 2026):
    show(f"  {y}", panel([r for r in SEL if r["yr"] == y], "3R"))
# NULLS por regime (mesma-freq BULL+RANGE)
k = len(SEL); nets = [R3[r["cj_t"]]["net3"] for r in SEL]; obs_net = sum(nets)
obs_hit = sum(1 for r in SEL if R3[r["cj_t"]]["R3"] >= 3) / k
by_reg = collections.Counter(r["g_v5h"] for r in SEL)
pool_reg = {rg: [r for r in NB if r["g_v5h"] == rg] for rg in by_reg}
by_yr = collections.defaultdict(list)
for r in NB: by_yr[r["yr"]].append(r)
kyr = collections.Counter(r["yr"] for r in SEL)
ndh = []; ndn = []; ndhy = []
for _ in range(1000):
    pk_ = [r for rg, c in by_reg.items() for r in random.sample(pool_reg[rg], c)]
    ndh.append(sum(1 for r in pk_ if R3[r["cj_t"]]["R3"] >= 3) / k); ndn.append(sum(R3[r["cj_t"]]["net3"] for r in pk_))
    py = [r for y, c in kyr.items() for r in random.sample(by_yr[y], min(c, len(by_yr[y])))]
    ndhy.append(sum(1 for r in py if R3[r["cj_t"]]["R3"] >= 3) / k)
pv = lambda o, d, ge=True: round(sum(1 for x in d if (x >= o) == ge) / len(d), 4)
print(f"\nNULLS (1000): hit3R obs {100*obs_hit:.1f}% vs regime-matched méd {100*sum(ndh)/1000:.1f}% P {pv(obs_hit,ndh)} · "
      f"year-matched P {pv(obs_hit,ndhy)} | NET obs {obs_net:.1f} vs méd {sum(ndn)/1000:.1f} P {pv(obs_net,ndn)}")
# streak distribucional (block bootstrap episódio)
eps = []; lastt = None
for j, r in enumerate(SEL):
    if lastt is not None and r["cj_t"] - lastt <= 96 * 900: eps[-1].append(j)
    else: eps.append([j])
    lastt = r["cj_t"]
worst = []
for _ in range(1000):
    seq = [nets[j] for _ in range(len(eps)) for j in eps[random.randrange(len(eps))]]
    mL = cl = 0
    for x in seq:
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    worst.append(mL)
print(f"streak: obs {p3['q']['stk']} · bootstrap-episódio q95 {sorted(worst)[950]} · P(streak>5) {round(sum(1 for x in worst if x>5)/1000,3)}")
# jackknife: concentração por mês
mo = collections.defaultdict(float)
for r in SEL: mo[dt.datetime.utcfromtimestamp(r["cj_t"]).strftime("%Y-%m")] += R3[r["cj_t"]]["net3"]
mx = max(mo.items(), key=lambda kv: kv[1])
print(f"jackknife: pior remoção-mês deixa {round(obs_net - mx[1],1)} (mês {mx[0]} = {round(mx[1],1)} = {round(100*mx[1]/obs_net,0)}%)")
print(f"FN-GATE: WR3R {p3['q']['wr']} · streak {p3['q']['stk']}(q95 {sorted(worst)[950]}) · anos+ {all(v>0 for v in p3['yrs'].values())} · freq {k/WEEKS:.2f}/sem={round(k/(WEEKS/52.14),0)}/ano")
json.dump({"n": k, "sha": sha, "panel_3R": p3, "panel_letrun": plr,
           "null_hit_P": pv(obs_hit, ndh), "null_net_P": pv(obs_net, ndn), "null_hit_year_P": pv(obs_hit, ndhy),
           "streak_q95": sorted(worst)[950], "p_streak_gt5": round(sum(1 for x in worst if x > 5) / 1000, 3),
           "month_conc_pct": round(100 * mx[1] / obs_net, 0)},
          open(HERE / "results" / "rws15m_hardening_20260705.json", "w"), indent=1)
print("OK → results/rws15m_hardening_20260705.json")
