#!/usr/bin/env python3
"""LINHA B Camada A Passo 1 — gerador de candidatos de BOTTOM NOVOS (fora dos 276) a partir do raw_features (9880 bars).
Deriva sinais por-bar (D1 capitulação, D2 oversold, D3 absorção bubbles, D4 NAS/SMC, D6 regime), RECALIBRA thresholds
por PERCENTIL no RAW (não slim), e reporta LARGURA (quantos candidatos cada sinal/dimensão gera). SEM outcome (Passo 2).
Bubble SELL=plot_6/8/10 (plot_10=LARGE). Causal. Verified 2026-06-25."""
import json, csv, datetime as dt, bisect, statistics
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
N = len(F); H = [r["high"] for r in F]; L = [r["low"] for r in F]; C = [r["close"] for r in F]; RSI = [r.get("rsi") for r in F]
ATR14 = [None] * N; ATR30 = [None] * N; trs = []
for i in range(1, N):
    trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
    if i >= 14: ATR14[i] = sum(trs[i - 14:i]) / 14
    if i >= 30: ATR30[i] = sum(trs[i - 30:i]) / 30
# regime v3 + cascade as-of
REG = V1 / "../../../../strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl"
def toep(s):
    try: return int(dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp())
    except Exception: return int(dt.datetime.strptime(str(s)[:10], "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
rb = [json.loads(l) for l in open(REG) if json.loads(l).get("ts")]
for r in rb: r["_e"] = toep(r["ts"])
rb.sort(key=lambda r: r["_e"]); rbt = [r["_e"] for r in rb]
def reg_asof(et):
    k = bisect.bisect_right(rbt, et) - 1
    return rb[k] if k >= 0 else {}
OUT276 = set(int(r["bar_idx"]) for r in csv.DictReader(open(V1 / "results/l2_bpt_uncapped_or_proxy_outcomes_276.csv")))

def feats(i):
    # SÓ OHLC+RSI+regime (RAW-fiéis). D3 bubbles / D4 NAS-SMC entram do RAW SVP gz no Passo 2 (NÃO usar listas derivadas).
    if i < 30 or not ATR14[i] or not ATR30[i]: return None
    drop20 = (C[i - 20] - C[i]) / ATR14[i]
    rsi = RSI[i]; rsi_min8 = min([x for x in RSI[i - 7:i + 1] if x is not None], default=None)
    atr_ratio = ATR14[i] / ATR30[i]
    cd = 0
    j = i
    while j > 0 and C[j] < C[j - 1]: cd += 1; j -= 1
    rg = reg_asof(int(F[i]["ts_epoch"])); v3 = rg.get("raw_state"); casc = rg.get("cascade_score")
    return dict(i=i, drop20=drop20, rsi=rsi, rsi_min8=rsi_min8, atr_ratio=atr_ratio, consec_down=cd, v3=v3, casc=casc)

A = [f for i in range(30, N) if (f := feats(i))]
print(f"bars com features = {len(A)}\n")
# RECALIBRAÇÃO POR PERCENTIL (RAW)
def pctl(key, p):
    xs = sorted(x[key] for x in A if x[key] is not None)
    return xs[int(p * len(xs))]
print("=== thresholds RECALIBRADOS por percentil (RAW) ===")
drop_p75 = pctl("drop20", 0.75); drop_p90 = pctl("drop20", 0.90)
rsi_p10 = pctl("rsi", 0.10); rsi_p20 = pctl("rsi", 0.20); atr_p75 = pctl("atr_ratio", 0.75)
print(f"  drop20: p75={drop_p75:.2f} p90={drop_p90:.2f} (slim usava ≥4)")
print(f"  rsi: p10={rsi_p10:.1f} p20={rsi_p20:.1f} (slim usava ≤30) | atr_ratio p75={atr_p75:.2f} (cap usava ≥1.3)")

# sinais por dimensão DERIVÁVEIS de OHLC/RSI/regime (RAW-fiéis). D3 absorção / D4 NAS-SMC = RAW SVP gz no Passo 2.
def sig(f):
    return dict(
        D1_capit=(f["drop20"] >= drop_p90 or (f["atr_ratio"] >= 1.3 and f["drop20"] >= drop_p75)),
        D2_oversold=(f["rsi"] is not None and f["rsi"] <= rsi_p20) or (f["rsi_min8"] is not None and f["rsi_min8"] <= 30),
        D6_regbear=(f["v3"] in ("BEAR", "TRANSITION")),
        deep_casc=(f["casc"] is not None and f["casc"] <= -3),
    )
for f in A: f.update(sig(f))
def yr(f): return dt.datetime.utcfromtimestamp(int(F[f["i"]]["ts_epoch"])).year

print("\n=== LARGURA por dimensão OHLC/regime (todos os bars) — D3/D4 vêm do RAW gz no Passo 2 ===")
for d in ("D1_capit", "D2_oversold", "D6_regbear", "deep_casc"):
    print(f"  {d:>12}: {sum(1 for f in A if f[d])} bars")

# POOL = contexto de fundo (capitulação OU oversold) & regime BEAR/TRANSITION, FORA dos 276 (dedup ±6)
def near276(i): return any(abs(i - b) <= 6 for b in OUT276)
pool = [f for f in A if (f["D1_capit"] or f["D2_oversold"]) and f["D6_regbear"] and not near276(f["i"])]
from collections import Counter
print(f"\n=== POOL candidatos NOVOS (capit OU oversold) & BEAR/TRANS & fora dos 276 = {len(pool)} ===")
print("  por ano:", dict(sorted(Counter(yr(f) for f in pool).items())))
print("  D1_capit:", sum(1 for f in pool if f["D1_capit"]), "| D2_oversold:", sum(1 for f in pool if f["D2_oversold"]),
      "| ambos:", sum(1 for f in pool if f["D1_capit"] and f["D2_oversold"]), "| deep_casc:", sum(1 for f in pool if f["deep_casc"]))
json.dump([{k: f[k] for k in ("i", "drop20", "rsi", "rsi_min8", "atr_ratio", "consec_down", "v3", "casc",
            "D1_capit", "D2_oversold", "D6_regbear", "deep_casc")} for f in pool],
          open(V1 / "results/l2_bpt_lineB_candidate_pool.json", "w"))
print(f"\npool salvo -> results/l2_bpt_lineB_candidate_pool.json ({len(pool)}). Passo 2 = RAW gz (bubbles/NAS/SMC/demanda) + outcome SL_CONTEXT+let-run.")
