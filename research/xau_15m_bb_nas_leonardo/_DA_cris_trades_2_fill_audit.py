#!/usr/bin/env python3
"""DA — auditoria de FILL dos 35 trades do Cris.
Achado do script 1: 29/35 entries desenhados estão FORA do range da barra-âncora (j0) e 15/35
nunca são tocados depois. Aqui: (a) direção/magnitude do desvio (entry vs barra j0, em $ e em R);
(b) o entry corresponde a um LOW recente (dip pré-âncora)? — hindsight-fill;
(c) SIM-1 limit-forward (fill só se tocar depois; senão NO-FILL) e SIM-2 market@close(j0):
paineis corrigidos letrun + plano, comparados aos reportados (+62.4R WR100% / +183.6R WR97%)."""
import json, bisect
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
TICK = 0.01
ns = {"__name__": "e", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "e", "exec"), ns)
PRIMK, HMAX, RCAP = ns["PRIMK"], ns["HMAX"], ns["RCAP"]

raw = json.load(open(HERE / "results" / "cris_manual_trades_20260704.json"))
trades = []
for sh in raw["shapes"]:
    if sh.get("name") != "long_position": continue
    p = sh["props"]; pts = p["points"]; props = p["properties"]
    entry = pts[0]["price"]; t0 = pts[0]["time"]
    trades.append({"t": t0, "entry": entry, "sl": round(entry - props["stopLevel"] * TICK, 2),
                   "tgt": round(entry + props["profitLevel"] * TICK, 2)})
trades.sort(key=lambda x: x["t"])

def find_block(t):
    for k, pr in PRIMK.items():
        s = pr["series"]
        if s[0]["t"] <= t <= s[-1]["t"]: return k, s
    return None, None

def fractal_prev(L, i, lookback=120):
    best = None
    for q in range(max(2, i - lookback), i - 1):
        if L[q] == min(L[q - 2:q + 3]): best = q
    return best

def letrun_indep(s, j0, entry, sl, atr):
    risk = entry - sl
    if risk <= 0: return None, None
    stop = sl; armed = False
    end = min(j0 + HMAX, len(s) - 1)
    L = [b["l"] for b in s]
    for k in range(j0 + 1, end + 1):
        if s[k]["l"] <= stop:
            return max(-1.0, min(RCAP, (stop - entry) / risk)), ("TRAIL" if stop > sl else "SL")
        if not armed and (s[k]["h"] - entry) / risk >= 1: armed = True
        if armed:
            q = fractal_prev(L, k)
            if q is not None and L[q] - 0.1 * atr > stop: stop = L[q] - 0.1 * atr
    return max(-1.0, min(RCAP, (s[end]["c"] - entry) / risk)), "END"

def plan_from(s, k0, sl, tgt):
    for k in range(k0, len(s)):
        hs = s[k]["l"] <= sl; ht = s[k]["h"] >= tgt
        if hs and ht: return "AMBIGUO", k
        if hs: return "SL", k
        if ht: return "TARGET", k
    return "OPEN", len(s) - 1

print("A. DESVIO DO ENTRY vs BARRA-ÂNCORA j0 (e vs mínima das 12 barras anteriores)")
print(f"  {'#':>3} {'utc':<17} {'entry':>8} {'vs j0':<12} {'desvio$':>8} {'desvio_R':>8} {'dip12_low':>9} {'entry≥dip12?':<12} {'1º toque':>9}")
rows = []
for i, tr in enumerate(trades, 1):
    bk, s = find_block(tr["t"]); ts = [b["t"] for b in s]
    j0 = bisect.bisect_right(ts, tr["t"]) - 1
    bar = s[j0]; risk = tr["entry"] - tr["sl"]
    if bar["l"] <= tr["entry"] <= bar["h"]: pos, dev = "DENTRO", 0.0
    elif tr["entry"] < bar["l"]: pos, dev = "ABAIXO", round(bar["l"] - tr["entry"], 2)
    else: pos, dev = "ACIMA", round(tr["entry"] - bar["h"], 2)
    lo12 = min(b["l"] for b in s[max(0, j0 - 12):j0 + 1])
    touch = None
    for k in range(j0 + 1, len(s)):
        if s[k]["l"] <= tr["entry"] <= s[k]["h"]: touch = k; break
    rows.append((i, tr, j0, s, pos, dev, touch))
    print(f"  {i:>3} {dt.datetime.utcfromtimestamp(tr['t']).strftime('%Y-%m-%d %H:%M'):<17} {tr['entry']:>8} {pos:<12} {dev:>8} {round(dev/risk,2):>8} {lo12:>9} {str(tr['entry'] >= lo12 - 0.5):<12} {(str(touch - j0) + 'b') if touch else 'NUNCA':>9}")

n_ab = sum(1 for r in rows if r[4] == "ABAIXO"); n_ac = sum(1 for r in rows if r[4] == "ACIMA"); n_in = sum(1 for r in rows if r[4] == "DENTRO")
devR = sorted(r[5] / (r[1]["entry"] - r[1]["sl"]) for r in rows)
print(f"\n  DENTRO {n_in} · ABAIXO {n_ab} · ACIMA {n_ac} · desvio mediano {devR[len(devR)//2]:.2f}R · max {devR[-1]:.2f}R")
print(f"  entry dentro do range das últimas 12 barras (dip recente): {sum(1 for r in rows if r[1]['entry'] >= min(b['l'] for b in r[3][max(0, r[2]-12):r[2]+1]) - 0.5)}/35")

print("\nB. SIM-1 LIMIT-FORWARD (fill só quando preço toca o entry DEPOIS de t0; senão NO-FILL)")
lr1 = []; pl1 = []
nofill = []
for i, tr, j0, s, pos, dev, touch in rows:
    if pos == "DENTRO": kf = j0
    elif touch is not None: kf = touch
    else: nofill.append(i); continue
    atr = s[kf].get("atr") or 1.0
    # same-bar SL no fill?
    sb = "SL_SAME_BAR" if s[kf]["l"] <= tr["sl"] else ""
    R, kind = letrun_indep(s, kf, tr["entry"], tr["sl"], atr)
    lr1.append((i, R, kind, sb))
    oc, _ = plan_from(s, kf if sb else kf + 1, tr["sl"], tr["tgt"])
    if sb: oc = "SL(same-bar-fill)"
    pl1.append((i, oc, tr))
print(f"  NO-FILL (preço nunca voltou ao entry no bloco): {len(nofill)}/35 → {nofill}")
Rv = [r for _, r, _, _ in lr1 if r is not None]
print(f"  letrun (filled {len(Rv)}): sumR {sum(Rv):+.1f} · WR {100*sum(1 for x in Rv if x>0)/len(Rv):.0f}% ({sum(1 for x in Rv if x>0)}/{len(Rv)}) · runners>=3: {sum(1 for x in Rv if x>=3)}")
neg = [(i, round(r, 2), k, sb) for i, r, k, sb in lr1 if r is not None and r <= 0]
print(f"  letrun não-positivos: {neg}")
from collections import Counter
ocs = Counter(o for _, o, _ in pl1)
planR = []
for _, o, tr in pl1:
    rr = (tr["tgt"] - tr["entry"]) / (tr["entry"] - tr["sl"])
    if o == "TARGET": planR.append(rr)
    elif o.startswith("SL"): planR.append(-1.0)
print(f"  plano (filled {len(pl1)}): {dict(ocs)} · sumR {sum(planR):+.1f} · WR {100*sum(1 for x in planR if x>0)/max(1,len(planR)):.0f}%")

print("\nC. SIM-2 MARKET @ close(j0) (entra a mercado na barra-âncora, SL/target DELE mantidos)")
lr2 = []; pl2 = []
inval = []
for i, tr, j0, s, pos, dev, touch in rows:
    entry2 = s[j0]["c"]; risk2 = entry2 - tr["sl"]
    if risk2 <= 0: inval.append(i); continue
    atr = s[j0].get("atr") or 1.0
    R, kind = letrun_indep(s, j0, entry2, tr["sl"], atr)
    lr2.append((i, R, risk2))
    oc, _ = plan_from(s, j0 + 1, tr["sl"], tr["tgt"])
    rr2 = (tr["tgt"] - entry2) / risk2
    pl2.append((i, oc, rr2))
Rv2 = [r for _, r, _ in lr2 if r is not None]
print(f"  válidos {len(Rv2)}/35 (entry>SL) · letrun: sumR {sum(Rv2):+.1f} · WR {100*sum(1 for x in Rv2 if x>0)/len(Rv2):.0f}% ({sum(1 for x in Rv2 if x>0)}/{len(Rv2)}) · runners>=3: {sum(1 for x in Rv2 if x>=3)}")
neg2 = [(i, round(r, 2)) for i, r, _ in lr2 if r is not None and r <= 0]
print(f"  letrun não-positivos: {neg2}")
ocs2 = Counter(o for _, o, _ in pl2)
planR2 = [(rr if o == "TARGET" else (-1.0 if o == "SL" else None)) for _, o, rr in pl2]
planR2 = [x for x in planR2 if x is not None]
print(f"  plano: {dict(ocs2)} · sumR {sum(planR2):+.1f} · WR {100*sum(1 for x in planR2 if x>0)/max(1,len(planR2)):.0f}%")
print("\nDONE")
