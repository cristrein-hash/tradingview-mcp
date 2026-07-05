#!/usr/bin/env python3
"""FASE 1 — ENGENHARIA DE FEATURES DE PERNA HTF (4H + 1D), alvo MON+FORTE (2026-07-05, GO Cris).
Método (diretriz Cris): PERNA ESTRUTURAL primeiro; indicadores pós-estrutura na Fase 2.
Fonte: htf_primitives/htf_4H|1D.primitives.json (sancionadas, causais). Para cada candidato 15M (cj_t),
asof a última barra HTF FECHADA, computa geometria da perna:
  trend (ema21 subindo + close>ema21) · perna atual (swing-low fractal mais recente → leg_low/leg_high/idade)
  · posição-na-perna (entry−legLow)/(legHi−legLow) · retração (legHi−entry)/(legHi−legLow)
  · higher-high recente (perna intacta) · extensão-perna ATR · dist EMA21/EMA50 ATR · RSI.
Escreve results/htf_leg_features_20260705.jsonl (cj_t + features) e testa LIFT/convergência vs MON+FORTE.
Alvo forward N=58 = CALIBRAÇÃO estrita. Universo selado."""
import json, bisect, hashlib, collections, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
WEEKS = len({r["g_week"] for r in U})
MF = set(r["cj_t"] for r in U if fv(r, "is_monforte") == 1)

def load_htf(path):
    s = json.load(open(path))["series"]
    s = sorted(s, key=lambda b: b["t"])
    ts = [b["t"] for b in s]
    tf = int(st.median([ts[i] - ts[i - 1] for i in range(1, min(400, len(ts)))]))
    C = [b["c"] for b in s]
    def ema(n):
        k = 2 / (n + 1); e = [C[0]]
        for v in C[1:]: e.append(v * k + e[-1] * (1 - k))
        return e
    e21 = [b.get("ema21") for b in s]; e50 = ema(50)
    # swing lows/highs fractal ±2
    lows = [b["l"] for b in s]; highs = [b["h"] for b in s]
    swl = [i for i in range(2, len(s) - 2) if lows[i] == min(lows[i - 2:i + 3])]
    swh = [i for i in range(2, len(s) - 2) if highs[i] == max(highs[i - 2:i + 3])]
    return {"s": s, "ts": ts, "tf": tf, "e21": e21, "e50": e50, "swl": swl, "swh": swh,
            "lows": lows, "highs": highs, "C": C}

H4 = load_htf(HERE / "htf_primitives" / "htf_4H.primitives.json")
H1 = load_htf(HERE / "htf_primitives" / "htf_1D.primitives.json")

def leg_feats(M, cj_t, entry, pfx):
    # última barra HTF FECHADA: t + tf <= cj_t
    i = bisect.bisect_right(M["ts"], cj_t - M["tf"]) - 1
    if i < 60: return {}
    s = M["s"]; b = s[i]; atr = b.get("atr") or 1.0
    o = {}
    e21 = M["e21"][i] or b["c"]; e50 = M["e50"][i]
    o[pfx + "_trend_up"] = int(b["c"] > e21 and (M["e21"][i] or 0) > (M["e21"][max(0, i - 3)] or 0))
    o[pfx + "_ema21_dist"] = round((entry - e21) / atr, 2)
    o[pfx + "_ema50_dist"] = round((entry - e50) / atr, 2)
    o[pfx + "_rsi"] = b.get("rsi")
    # perna atual: swing-low mais recente <= i
    swl = [j for j in M["swl"] if j <= i]
    if not swl: return o
    lj = swl[-1]
    leg_low = M["lows"][lj]
    leg_hi = max(M["highs"][lj:i + 1])
    rng = leg_hi - leg_low
    o[pfx + "_leg_age"] = i - lj
    o[pfx + "_leg_ext_atr"] = round(rng / atr, 2)
    o[pfx + "_pos_in_leg"] = round((entry - leg_low) / rng, 3) if rng > 0 else 0.5
    o[pfx + "_retrace"] = round((leg_hi - entry) / rng, 3) if rng > 0 else 0.5
    # higher-high recente: último swing-high > swing-high anterior (perna intacta)
    swh = [j for j in M["swh"] if j <= i]
    o[pfx + "_hh_intact"] = int(len(swh) >= 2 and M["highs"][swh[-1]] > M["highs"][swh[-2]])
    # dist abaixo do topo da perna em ATR (dip real)
    o[pfx + "_below_hi_atr"] = round((leg_hi - entry) / atr, 2)
    return o

OUT = []
for r in U:
    f = {"cj_t": r["cj_t"], "is_mf": int(r["cj_t"] in MF)}
    f.update(leg_feats(H4, r["cj_t"], r["g_entry"], "h4"))
    f.update(leg_feats(H1, r["cj_t"], r["g_entry"], "d1"))
    OUT.append(f)
(HERE / "results" / "htf_leg_features_20260705.jsonl").write_text("\n".join(json.dumps(x) for x in OUT))
FT = {x["cj_t"]: x for x in OUT}
print(f"features de perna HTF escritas p/ {len(OUT)} candidatos · alvo MON+FORTE {len(MF)}")

mf = [x for x in OUT if x["is_mf"]]; rest = [x for x in OUT if not x["is_mf"]]
def med(rows, k):
    v = sorted(x[k] for x in rows if k in x and isinstance(x[k], (int, float)))
    return v[len(v) // 2] if v else None
print("\nMEDIANAS perna HTF (MON+FORTE vs resto):")
for k in ("h4_trend_up", "h4_pos_in_leg", "h4_retrace", "h4_leg_age", "h4_leg_ext_atr", "h4_hh_intact",
          "h4_below_hi_atr", "h4_ema21_dist", "h4_ema50_dist", "h4_rsi",
          "d1_trend_up", "d1_pos_in_leg", "d1_retrace", "d1_hh_intact", "d1_rsi"):
    print(f"  {k:<16} MF={med(mf,k)}  resto={med(rest,k)}")

base = len(MF) / len(U)
LENS = {
 "h4_trend_up": lambda x: x.get("h4_trend_up") == 1,
 "h4_pos_leg<=0.4": lambda x: x.get("h4_pos_in_leg", 1) <= 0.4,
 "h4_retrace 0.3-0.75": lambda x: 0.3 <= x.get("h4_retrace", 0) <= 0.75,
 "h4_hh_intact": lambda x: x.get("h4_hh_intact") == 1,
 "h4_below_hi>=1atr": lambda x: x.get("h4_below_hi_atr", 0) >= 1.0,
 "d1_trend_up": lambda x: x.get("d1_trend_up") == 1,
 "d1_hh_intact": lambda x: x.get("d1_hh_intact") == 1,
 "d1_pos_leg<=0.5": lambda x: x.get("d1_pos_in_leg", 1) <= 0.5,
 "h4_leg_ext>=3atr": lambda x: x.get("h4_leg_ext_atr", 0) >= 3.0,
 "h4_rsi 40-60": lambda x: x.get("h4_rsi") is not None and 40 <= x["h4_rsi"] <= 60,
}
rows = []
for nm, fn in LENS.items():
    sub = [x for x in OUT if fn(x)]
    mfin = sum(1 for x in sub if x["is_mf"]); prec = mfin / len(sub) if sub else 0
    rows.append((nm, prec / base if base else 0, prec, mfin, len(sub)))
rows.sort(key=lambda x: -x[1])
print("\nLENTES PERNA HTF por LIFT sobre MON+FORTE:")
for nm, lift, prec, mfin, nn in rows:
    print(f"  lift {lift:>4.1f}x  prec {100*prec:>4.1f}%  recall {mfin}/{len(MF)}  N{nn:>5}  {nm}")
HL = [nm for nm, lift, prec, mfin, nn in rows if lift >= 1.3]
print(f"\nCONVERGÊNCIA lentes-perna de alto lift {HL}:")
def votes(x): return sum(1 for nm in HL if LENS[nm](x))
for k in range(2, len(HL) + 1):
    keep = [x for x in OUT if votes(x) >= k]
    mfin = sum(1 for x in keep if x["is_mf"])
    prec = mfin / len(keep) if keep else 0
    h3 = sum(1 for x in keep if R3[x["cj_t"]]["R3"] >= 3) / len(keep) if keep else 0
    print(f"  >={k}/{len(HL)}: N{len(keep):>4} ({len(keep)/WEEKS:.2f}/sem) · MF {mfin}/{len(MF)} · prec {100*prec:.1f}% (lift {prec/base:.1f}x) · hit3R {100*h3:.1f}%")
print("OK → results/htf_leg_features_20260705.jsonl")
