#!/usr/bin/env python3
"""SANITY_PROBE — null do engine sequencial RWS-15M (N54, hit3R 44,4%). O 44% e o streak-4 são
distinguíveis de 54 sorteios aleatórios do pool não-BEAR? + robustez: hit3R por ano + ablação de
cada camada RWS (qual read carrega). Reusa o gerador do rws_sequence_engine."""
import json, glob, bisect, random, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
random.seed(42)
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
# recomputa FT via import do engine (mesma lógica)
import importlib.util
spec = importlib.util.spec_from_file_location("rws", HERE / "rws_sequence_engine_20260705.py")
# em vez de reexecutar (custa), replicamos a seleção lendo o json + re-rodando seria caro; reconstruímos FT rápido:
import glob as _g
series = {}; nas = []
for p in sorted(_g.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"], b)
    nas += [e for e in d["nas_events"] if e.get("t")]
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; N = len(S)
RSI = [b.get("rsi") for b in S]
RSIMA = [None] * N
for i in range(N):
    w = [RSI[j] for j in range(max(0, i - 13), i + 1) if RSI[j] is not None]
    RSIMA[i] = sum(w) / len(w) if w else None
BUB = sorted([json.loads(l) for p in _g.glob(str(HERE / "bubbles" / "*.bubbles.jsonl")) for l in open(p)],
             key=lambda x: (x.get("known_at") or x["t"]))
BUBK = [(x.get("known_at") or x["t"]) for x in BUB]
nas.sort(key=lambda e: e["t"]); NAST = [e["t"] for e in nas]
wgt = {"S": 1, "M": 2, "L": 3}
def bub(t0, wlo, whi):
    hi = bisect.bisect_right(BUBK, t0)
    return [BUB[i] for i in range(hi) if t0 - whi * 900 <= BUB[i]["t"] <= t0 - wlo * 900]
def rws_layers(cj_t):
    i = bisect.bisect_right(TS, cj_t) - 1
    if i < 40: return None
    recent = bub(cj_t, 0, 4); older = bub(cj_t, 5, 10); win8 = bub(cj_t, 0, 8)
    buy_recent = sum(wgt[x["size"]] for x in recent if x["side"] == "BUY")
    burst = buy_recent - sum(wgt[x["size"]] for x in older if x["side"] == "BUY")
    large8 = int(any(x["side"] == "BUY" and x["size"] == "L" for x in win8))
    rsi_above = int(RSI[i] is not None and RSIMA[i] is not None and RSI[i] > RSIMA[i])
    bd = 0
    for k in range(i - 20, i - 2):
        if k < 3: continue
        if S[k]["h"] == max(x["h"] for x in S[k - 2:k + 3]):
            prev = [j for j in range(k - 12, k - 2) if S[j]["h"] == max(x["h"] for x in S[max(0, j - 2):j + 3])]
            if prev and RSI[k] is not None and RSI[prev[-1]] is not None and S[k]["h"] > S[prev[-1]]["h"] and RSI[k] < RSI[prev[-1]]:
                bd += 1
    j = bisect.bisect_right(NAST, cj_t) - 1
    nas_short = int(j >= 0 and nas[j]["dir"] == "SHORT" and (cj_t - nas[j]["t"]) // 900 <= 4)
    return {"buy_recent": buy_recent, "burst": burst, "large8": large8, "rsi_above": rsi_above, "bd": bd, "nas_short": nas_short}
NB = [r for r in U if r["g_v5h"] != "BEAR" and r["g_knife"] == 0]
def passes(r, drop=None):
    f = rws_layers(r["cj_t"])
    if f is None: return False
    supply = fv(r, "n_supply_overhead", 99)
    if drop != "buy" and f["buy_recent"] < 2: return False
    if drop != "rws" and f["rsi_above"] == 0 and supply <= 20: return False
    if drop != "a6" and f["burst"] >= 3 and f["large8"] == 0 and f["nas_short"] == 0: return False
    if drop != "a7" and f["bd"] >= 2: return False
    return True
sel = [r for r in NB if passes(r)]
k = len(sel)
obs_hit = sum(1 for r in sel if R3[r["cj_t"]]["R3"] >= 3) / k
obs_net = sum(R3[r["cj_t"]]["net3"] for r in sel)
def streak(rows):
    mL = cl = 0
    for r in sorted(rows, key=lambda r: r["cj_t"]):
        if R3[r["cj_t"]]["net3"] <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    return mL
print(f"RWS-15M: N{k} hit3R {100*obs_hit:.1f}% NET {obs_net:.1f} streak {streak(sel)}")
# null: 54 sorteios aleatórios do pool não-BEAR
hn = []; nn = []; stk = []
for _ in range(1000):
    s = random.sample(NB, k)
    hn.append(sum(1 for r in s if R3[r["cj_t"]]["R3"] >= 3) / k)
    nn.append(sum(R3[r["cj_t"]]["net3"] for r in s))
    stk.append(streak(s))
p_hit = sum(1 for x in hn if x >= obs_hit) / 1000
p_net = sum(1 for x in nn if x >= obs_net) / 1000
import statistics as st
print(f"null (1000): hit méd {100*st.mean(hn):.1f}% q95 {100*sorted(hn)[950]:.1f}% → P(null>=obs) {100*p_hit:.1f}%")
print(f"            NET méd {st.mean(nn):.1f} q95 {sorted(nn)[950]:.1f} → P(null>=obs) {100*p_net:.1f}%")
print(f"            streak méd {st.mean(stk):.1f} (obs {streak(sel)} = {'melhor' if streak(sel)<st.mean(stk) else 'pior'})")
print("\nABLAÇÃO (remove 1 camada; queda no hit = camada carrega):")
for dl, nm in [("buy", "buy_recent"), ("rws", "rsi/supply"), ("a6", "anti-burst"), ("a7", "anti-beardiv")]:
    s2 = [r for r in NB if passes(r, drop=dl)]
    h2 = sum(1 for r in s2 if R3[r["cj_t"]]["R3"] >= 3) / len(s2) if s2 else 0
    print(f"  sem {nm:<12}: N{len(s2):>4} hit3R {100*h2:.1f}%")
