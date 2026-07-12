#!/usr/bin/env python3
"""SANITY_PROBE (ordem Cris 2026-07-12): separação EMA10-EMA30 do 1D, normalizada por ATR14_1D,
em duas populações: (a) barras 1D da janela nov/2024 BEAR do GT; (b) barras 1D das 4 janelas
RANGE do GT. Reporta distribuições (assinada e absoluta). Decide se um limiar de override é
fisicamente possível ANTES de qualquer corrida. Sem treino, sem seleção, sem P&L."""
import json, statistics
from pathlib import Path
HERE = Path(__file__).resolve().parent
GT = json.load(open(HERE/"results/REGIME_GT_CRIS_4H_20260712.json"))
D1 = [json.loads(l) for l in open(HERE/"raw_1d_ohlc.jsonl")]
T = [b["t"] for b in D1]; C = [b["c"] for b in D1]; H = [b["h"] for b in D1]; L = [b["l"] for b in D1]

def ema(vals, n):
    k = 2/(n+1); e = vals[0]; out = []
    for v in vals: e = v*k + e*(1-k); out.append(e)
    return out

E10, E30 = ema(C, 10), ema(C, 30)
TR = [0.0]
for i in range(1, len(T)):
    TR.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
def atr(i, n=14):
    a = TR[max(1, i-n+1):i+1]; return sum(a)/len(a) if a else 1.0

SEP = [(E10[i]-E30[i])/(atr(i) or 1.0) for i in range(len(T))]

def pop(windows):
    idx = [i for i in range(len(T)) if any(w["t0"] <= T[i] <= w["t1"] for w in windows)]
    return [SEP[i] for i in idx]

def dist(tag, xs):
    xs_s = sorted(xs); n = len(xs_s)
    q = lambda p: xs_s[min(n-1, int(p*n))]
    print(f"{tag:<28} n={n:<4} min={xs_s[0]:+.2f} p10={q(.10):+.2f} p25={q(.25):+.2f} "
          f"med={q(.50):+.2f} p75={q(.75):+.2f} p90={q(.90):+.2f} max={xs_s[-1]:+.2f} "
          f"média={statistics.mean(xs):+.2f}")
    ab = sorted(abs(x) for x in xs)
    qa = lambda p: ab[min(n-1, int(p*n))]
    print(f"{'':<28} |sep|: p25={qa(.25):.2f} med={qa(.50):.2f} p75={qa(.75):.2f} p90={qa(.90):.2f}")

def main():
    nov = [w for w in GT["windows"] if w["d0"] == "2024-11-10"]
    rng = [w for w in GT["windows"] if w["regime"] == "RANGE"]
    a, b = pop(nov), pop(rng)
    print("separação = (EMA10−EMA30)/ATR14, diário 1D nativo")
    dist("(a) nov/2024 BEAR", a)
    dist("(b) 4 janelas RANGE", b)
    # sobreposição bruta: fração de (b) com sep <= p90 de (a) etc.
    a_s = sorted(a); b_s = sorted(b)
    med_a = a_s[len(a_s)//2]
    frac_b_below = sum(1 for x in b_s if x <= med_a)/len(b_s)
    print(f"\nfração de RANGE com sep <= mediana de nov/2024 ({med_a:+.2f}): {100*frac_b_below:.1f}%")

if __name__ == "__main__":
    main()
