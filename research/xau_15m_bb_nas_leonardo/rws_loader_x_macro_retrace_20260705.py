#!/usr/bin/env python3
"""CRUZAMENTO DECLARADO: carregador sequencial (RWS buy_recent) × retração macro profunda
(2026-07-05, ordem Cris "VAMOS PARA ESSA LEITURA"). QUEM compra (acumulação de bubbles) ×
ONDE compra (perna macro devolvida 0,5-1,3 — assinatura GT sobrevivente do DA). Nunca testados
juntos: RWS validado vive em pullback raso de uptrend; os fundos do Cris em retração profunda.

LEDGER PRÉ-DECLARADO (5 looks de outcome, nada além):
  D0 (descritivo, sem look): distribuição de retr dos 54 RWS — onde o engine validado já senta
  X1 split RWS-54: dentro vs fora da banda retr[0,5,1,3]
  X2 LOADER×ONDE: buy_recent>=2 & banda (o cruzamento nu)
  X3 RWS-DEEP: X2 + anti-filtros A6 (burst-fake sem institucional) + A7 (bear-div cluster)
     [sem o gate rsi_above_ma/supply do RWS raso — ele seleciona pullback raso, conflita com ONDE]
  X4 X3 & reclaim_atr>=1,5 (gatilho de força)
Painel completo (N·hit3R·WR·NET·DD·stk·freq·por-ano) + GT-precisão/recall estrito + null 4000×
vs universo + streak distribucional nos aprovados.
SANITY_PROBE: P1 zigzag causal (known_i<=fi assert) · P2 banda vem do DA de ontem (candidatos
não-GT como null), não recalibrada aqui · P3 GT nunca é feature · P4 loader byte-igual ao engine
selado (exec do fonte, zero cópia)."""
import json, bisect, random, hashlib
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "rws_sequence_engine_20260705.py").read_text()
exec(src.split("def panel(")[0])          # U, R3, S, TS, FT (seq feats), rws15m, MF, WEEKS, fv
GT_60 = json.load(open(HERE / "results" / "ground_truth_bottoms_20260705.json"))
assert hashlib.sha256((HERE / "results" / "ground_truth_bottoms_20260705.json").read_bytes()).hexdigest() == \
    (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
N = len(S)
ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]

def zigzag_low_pivots(r=6):
    lows = []; d = 0; ehi = elo = 0
    for i in range(1, N):
        atr = ATR[i]
        if HI[i] > HI[ehi]: ehi = i
        if LO[i] < LO[elo]: elo = i
        if d >= 0 and HI[ehi] - LO[i] >= r * atr and ehi < i:
            d = -1; elo = min(range(ehi, i + 1), key=lambda k: LO[k])
        elif d <= 0 and HI[i] - LO[elo] >= r * atr and elo < i:
            lows.append((i, elo)); d = 1
            ehi = max(range(elo, i + 1), key=lambda k: HI[k])
    return lows
LOWS = zigzag_low_pivots(6); KLOW = [x[0] for x in LOWS]

UNIV = [r for r in U if r["cj_t"] in R3]
US = sorted(UNIV, key=lambda r: r["cj_t"]); UT = [r["cj_t"] for r in US]
for r in UNIV: r["_gt"] = 0
for g in GT_60:
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UT) and UT[j] <= g["flush_t"] + 8 * 3600:
        v = US[j]
        if abs((v["g_sl"] + 0.1 * (v.get("g_atr") or 5.0)) - g["flush_low"]) <= (v.get("g_atr") or 5.0):
            v["_gt"] = 1
        j += 1
for r in UNIV:
    fi = bisect.bisect_right(TS, r["cj_t"]) - 1
    a = r.get("g_atr") or 5.0
    flo = r["g_sl"] + 0.1 * a
    j = bisect.bisect_right(KLOW, fi) - 1
    r["_retr"] = None
    if j >= 0:
        ki, l0i = LOWS[j]
        assert ki <= fi  # P1
        L0 = LO[l0i]; H1 = max(HI[k] for k in range(l0i, fi + 1))
        if H1 - L0 > 1e-9:
            r["_retr"] = (H1 - flo) / (H1 - L0)
IN = lambda r: r["_retr"] is not None and 0.5 <= r["_retr"] <= 1.3

GT_ALL = [(g["flush_t"], g["flush_low"]) for g in GT_60]
def strict_recall(rows):
    got = 0
    ts = sorted((r["cj_t"], r["g_sl"] + 0.1 * (r.get("g_atr") or 5.0), r.get("g_atr") or 5.0) for r in rows)
    T = [x[0] for x in ts]
    for ft, flo in GT_ALL:
        j = bisect.bisect_left(T, ft - 8 * 3600); ok = False
        while j < len(T) and T[j] <= ft + 8 * 3600:
            if abs(ts[j][1] - flo) <= ts[j][2]:
                ok = True; break
            j += 1
        got += ok
    return got

def panel2(rows, tag):
    n = len(rows)
    if not n:
        print(f"  {tag:<28} vazio"); return None
    rs = sorted(rows, key=lambda r: r["cj_t"]); nets = [R3[r["cj_t"]]["net3"] for r in rs]
    h = sum(1 for r in rs if R3[r["cj_t"]]["R3"] >= 3); w = sum(1 for x in nets if x > 0)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {}
    for r, x in zip(rs, nets): yr[r["yr"]] = round(yr.get(r["yr"], 0) + x, 1)
    gtp = sum(r["_gt"] for r in rs)
    print(f"  {tag:<28} N{n:>4} hit3R {100*h/n:>5.1f}% WR {100*w/n:>5.1f}% NET {sum(nets):>+7.1f} DD {dd:>6.1f} "
          f"stk-{mL} | {n/WEEKS:.2f}/sem | GTprec {gtp}/{n}={100*gtp/n:.0f}% recall {strict_recall(rs)}/60 | {yr}")
    return {"n": n, "hit": round(h/n, 3), "wr": round(w/n, 3), "net": round(sum(nets), 1),
            "dd": round(dd, 1), "stk": mL, "gt_prec": gtp, "recall": strict_recall(rs)}

def null_p(rows, seed):
    H0 = [1 if R3[r["cj_t"]]["R3"] >= 3 else 0 for r in UNIV]
    obs = sum(1 for r in rows if R3[r["cj_t"]]["R3"] >= 3) / len(rows)
    random.seed(seed)
    return sum(1 for _ in range(4000) if sum(random.sample(H0, len(rows))) / len(rows) >= obs) / 4000

def streak_dist(rows, seed):
    nets = [R3[r["cj_t"]]["net3"] for r in sorted(rows, key=lambda x: x["cj_t"])]
    random.seed(seed); q = []
    for _ in range(2000):
        sq = random.choices(nets, k=len(nets)); c2 = m2 = 0
        for x in sq:
            c2 = c2 + 1 if x <= 0 else 0; m2 = max(m2, c2)
        q.append(m2)
    q.sort()
    return q[1000], q[int(0.95 * 2000)], sum(1 for x in q if x > 5) / 2000

# D0: onde os 54 RWS sentam
RWS = [r for r in UNIV if rws15m(r)]
rv = sorted(r["_retr"] for r in RWS if r["_retr"] is not None)
print(f"D0: RWS-54 retr q25/med/q75 = {rv[len(rv)//4]:.2f}/{rv[len(rv)//2]:.2f}/{rv[3*len(rv)//4]:.2f} "
      f"· na banda [0,5-1,3]: {sum(1 for r in RWS if IN(r))}/{len(RWS)}")
panel2(UNIV, "UNIVERSO")
# X1 split
X1a = [r for r in RWS if IN(r)]; X1b = [r for r in RWS if not IN(r)]
panel2(X1a, "X1 RWS ∩ banda")
panel2(X1b, "X1 RWS fora banda")
# X2 loader nu × onde
X2 = [r for r in UNIV if FT.get(r["cj_t"], {}).get("buy_recent", 0) >= 2 and IN(r)]
p2 = panel2(X2, "X2 loader>=2 & banda")
print(f"      P(null)={null_p(X2, 61):.4f}")
# X3 RWS-DEEP
def deep_ok(r):
    f = FT.get(r["cj_t"], {})
    if not f or f.get("buy_recent", 0) < 2 or not IN(r):
        return False
    if f.get("burst_recent_vs_older", 0) >= 3 and f.get("large_buy_win8") == 0 and f.get("nas_last_short_recent") == 0:
        return False
    if f.get("rsi_bear_div_20", 0) >= 2:
        return False
    return True
X3 = [r for r in UNIV if deep_ok(r)]
p3 = panel2(X3, "X3 RWS-DEEP (X2+A6+A7)")
if X3:
    q50, q95, pgt5 = streak_dist(X3, 63)
    print(f"      P(null)={null_p(X3, 62):.4f} · streak dist q50 {q50} q95 {q95} P(>5) {pgt5:.2f}")
# X4 + reclaim
X4 = [r for r in X3 if fv(r, "reclaim_atr") >= 1.5]
p4 = panel2(X4, "X4 X3 & reclaim>=1,5")
if X4:
    q50, q95, pgt5 = streak_dist(X4, 65)
    print(f"      P(null)={null_p(X4, 64):.4f} · streak dist q50 {q50} q95 {q95} P(>5) {pgt5:.2f}")
    print("\n  membros X4 (p/ visual):")
    for r in sorted(X4, key=lambda x: x["cj_t"]):
        r3 = R3[r["cj_t"]]
        print(f"   {dt.datetime.utcfromtimestamp(r['cj_t']).strftime('%Y-%m-%d %H:%M')} "
              f"{'WIN ' if r3['R3']>=3 else 'loss'} net {r3['net3']:+.1f} GT={r['_gt']} retr {r['_retr']:.2f} "
              f"buy_rec {FT[r['cj_t']].get('buy_recent')}")
json.dump({"X2": p2, "X3": p3, "X4": p4},
          open(HERE / "results" / "rws_loader_x_macro_retrace_20260705.json", "w"), indent=1)
print("OK → results/rws_loader_x_macro_retrace_20260705.json")
