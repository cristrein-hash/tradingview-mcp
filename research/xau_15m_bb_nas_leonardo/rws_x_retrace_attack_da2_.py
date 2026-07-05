#!/usr/bin/env python3
"""DA2 — ataque adversarial ao cruzamento loader×retrace v2 (X2'/X4').
Vetores: (1) X4' fora de NB · (2) binomial exato + multiplicidade · (3) overlap X2'/X3'/X4'
vs RWS54∩banda (slice?) · (5) jackknife + concentração temporal. Read-only sobre os dados;
não modifica ficheiros existentes."""
import json, bisect, random, math, collections
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
# mesmo bootstrap da v2: exec v1 até o marcador (define U,R3,S,TS,FT,rws15m,UNIV,IN,panel2,fv,...)
exec((HERE / "rws_loader_x_macro_retrace_20260705.py").read_text().split("# D0: onde os 54")[0])

NB = [r for r in UNIV if r["g_v5h"] != "BEAR" and r["g_knife"] == 0]
NBset = {r["cj_t"] for r in NB}
RWS54 = [r for r in NB if rws15m(r)]
BANDA = [r for r in RWS54 if IN(r)]

def deep_ok(r):
    f = FT.get(r["cj_t"], {})
    if not f or f.get("buy_recent", 0) < 2 or not IN(r):
        return False
    if f.get("burst_recent_vs_older", 0) >= 3 and f.get("large_buy_win8") == 0 and f.get("nas_last_short_recent") == 0:
        return False
    if f.get("rsi_bear_div_20", 0) >= 2:
        return False
    return True

X2p = [r for r in NB if FT.get(r["cj_t"], {}).get("buy_recent", 0) >= 2 and IN(r)]
X3p = [r for r in NB if deep_ok(r)]
X4p = [r for r in X3p if fv(r, "reclaim_atr") >= 1.5]

# cruzamento com sinais selados do hardening
sealed = json.load(open(HERE / "results" / "rws15m_signals_20260705.json"))
sealed_ts = set(s["cj_t"] if isinstance(s, dict) else s for s in (sealed if isinstance(sealed, list) else sealed.get("signals", sealed)))
r54 = {r["cj_t"] for r in RWS54}
print(f"[SEAL] RWS54 recomputado N{len(RWS54)} · sinais selados N{len(sealed_ts)} · iguais: {r54 == sealed_ts}")

# ---------- VETOR 3: overlap / slice ----------
s2, s3, s4, sb = ({r["cj_t"] for r in X} for X in (X2p, X3p, X4p, BANDA))
print(f"\n[V3] X3' == RWS54∩banda? {s3 == sb} · X2'∩(RWS54∩banda)={len(s2 & sb)}/{len(s2)} · "
      f"X2'\\RWS54={len(s2 - r54)} · X4'⊆RWS54? {s4 <= r54} · X4'⊆banda? {s4 <= sb}")
extra = s2 - sb
for t in sorted(extra):
    r = next(x for x in X2p if x["cj_t"] == t)
    f = FT[t]
    print(f"   membro X2' fora do slice: {dt.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d %H:%M')} "
          f"net {R3[t]['net3']:+.1f} rsi_above_ma={f.get('rsi_above_ma')} supply={fv(r,'n_supply_overhead',99)} "
          f"burst={f.get('burst_recent_vs_older')} bd20={f.get('rsi_bear_div_20')}")

# ---------- VETOR 1: X4' fora de NB ----------
OUT_NB = [r for r in UNIV if r["cj_t"] not in NBset]
X4_out = [r for r in OUT_NB if deep_ok(r) and fv(r, "reclaim_atr") >= 1.5]
panel2(X4_out, "[V1] X4-regra FORA de NB")
by = collections.Counter((r["g_v5h"], r["g_knife"]) for r in X4_out)
print(f"   composição fora-NB: {dict(by)}")
X4_all = [r for r in UNIV if deep_ok(r) and fv(r, "reclaim_atr") >= 1.5]
panel2(X4_all, "[V1] X4-regra universo (=v1 X4)")

# ---------- VETOR 2: binomial exato + nulls condicionais ----------
def binom_ge(k, n, p):
    return sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(k, n+1))
hit = lambda rows: sum(1 for r in rows if R3[r["cj_t"]]["R3"] >= 3)
pNB = hit(NB) / len(NB)
p54 = hit(RWS54) / len(RWS54)
h4, n4 = hit(X4p), len(X4p)
h2, n2 = hit(X2p), len(X2p)
print(f"\n[V2] base NB={pNB:.3f} · base RWS54={p54:.3f}")
print(f"   X2' {h2}/{n2}: binom vs NB p={binom_ge(h2,n2,pNB):.4f} · vs RWS54 p={binom_ge(h2,n2,p54):.4f}")
print(f"   X4' {h4}/{n4}: binom vs NB p={binom_ge(h4,n4,pNB):.4f} · vs RWS54 p={binom_ge(h4,n4,p54):.4f}")
# null condicional por resample DENTRO do RWS54 (o teste certo se for slice)
H54 = [1 if R3[r["cj_t"]]["R3"] >= 3 else 0 for r in RWS54]
random.seed(99)
pc = sum(1 for _ in range(20000) if sum(random.sample(H54, n4)) / n4 >= h4 / n4) / 20000
print(f"   X4' vs resample-em-RWS54 (null slice): P={pc:.4f}")
# Fisher exato one-sided dentro do RWS54: banda vs fora-banda
a, b = hit(BANDA), len(BANDA) - hit(BANDA)
c, d = hit(RWS54) - a, (len(RWS54) - len(BANDA)) - (hit(RWS54) - hit(BANDA))
def fisher_ge(a, b, c, d):
    n = a + b + c + d; r1 = a + b; c1 = a + c
    return sum(math.comb(c1, x) * math.comb(n - c1, r1 - x) for x in range(a, min(r1, c1) + 1)) / math.comb(n, r1)
print(f"   dentro RWS54: banda {a}/{a+b} vs fora {c}/{c+d} · Fisher one-sided p={fisher_ge(a,b,c,d):.4f}")
for k in (10, 36):
    print(f"   multiplicidade k={k}: Sidak(0.0255)={1-(1-0.0255)**k:.3f} · Bonf={min(1,0.0255*k):.3f}")

# ---------- VETOR 5: jackknife + concentração ----------
rows = sorted(X4p, key=lambda r: r["cj_t"])
nets = [R3[r["cj_t"]]["net3"] for r in rows]
print(f"\n[V5] membros X4' (N{len(rows)}):")
for r, x in zip(rows, nets):
    print(f"   {dt.datetime.utcfromtimestamp(r['cj_t']).strftime('%Y-%m-%d %H:%M')} "
          f"{'HIT ' if R3[r['cj_t']]['R3']>=3 else '----'} net {x:+.1f} retr {r['_retr']:.2f} GT={r['_gt']}")
jk = []
for i in range(len(rows)):
    rest = [x for j, x in enumerate(nets) if j != i]
    hh = sum(1 for j, r in enumerate(rows) if j != i and R3[r["cj_t"]]["R3"] >= 3)
    jk.append((hh / (len(rows) - 1), sum(rest)))
worst = min(jk); best = max(jk)
print(f"   jackknife hit: worst {100*worst[0]:.1f}% NET {worst[1]:+.1f} · best {100*best[0]:.1f}% NET {best[1]:+.1f}")
mon = collections.Counter(dt.datetime.utcfromtimestamp(r["cj_t"]).strftime("%Y-%m") for r in rows)
monH = collections.Counter(dt.datetime.utcfromtimestamp(r["cj_t"]).strftime("%Y-%m") for r in rows if R3[r["cj_t"]]["R3"] >= 3)
print(f"   por mês (N): {dict(sorted(mon.items()))}")
print(f"   por mês (HITs): {dict(sorted(monH.items()))}")
span_d = (rows[-1]["cj_t"] - rows[0]["cj_t"]) / 86400
print(f"   span {span_d:.0f} dias · freq {len(rows)/(span_d/7):.3f}/sem")
