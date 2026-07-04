#!/usr/bin/env python3
"""BEAR-PULLBACK · PROBE 3 — CONFIG V2 (iteração OUTCOME-BLIND sobre V1; ledger look #2).
Motivação da iteração (só frequência V1=3,6/sem + contexto medido dos 4 do Cris; ZERO outcomes):
  · os 4 entram com recuperação MADURA: depth_from_low96 = 2,91/3,72/6,15/7,99 ATR
  · o SL deles fica sob o HIGHER-LOW local (risk 1,40-2,31 ATR), não sob o fundo do flush
  · o loser (#19) é o único com dist_ema21=1,29 ATR e RSI 68,5 (perseguição)
CONFIG V2 (congelada antes desta rodada; zero grid):
  R  : v5h==BEAR na barra (hour-causal)
  A  : âncora do universo selado (swept_prior_low=1, rsi_low<=40, in_demand=1),
       idade ∈ [2,32], flush-low intacto (nenhum low < g_sl da âncora desde cj)
  M  : maturidade — C[i] - min(L[i-95..i]) >= 2.5*ATR[i]
  P  : C[i] > EMA21[i] AND (C[i]-EMA21[i]) <= 0.6*ATR[i] AND micro-HL
       (min L[i-2..i] > min L[i-10..i-3])
  Fw : 40 <= RSI[i] <= 60 AND pos20 <= 0.85
  HL : swing-low = min(L[i-11..i]); exigir swing-low > flush_low da âncora (higher-low genuíno)
  SL : swing-low - 0.1*ATR[i]; BANDA 1.2 <= risk/ATR <= 4.0, fora = rejeita (nunca ajusta)
  DEDUP: 1 sinal por âncora (consome ao disparar conjunção); cooldown 96 barras pós-aceito
Medição outcome-blind: nº sinais, sinais/semana-BEAR, máx/semana, cobertura 4 Cris ±6 barras.
"""
import json, glob, bisect, io, contextlib, collections, datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
ns = {"__name__": "engine", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "engine", "exec"), ns)
regime_h = ns["regime_hourcausal"]

series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; N = len(S)
L = [b["l"] for b in S]; H = [b["h"] for b in S]; C = [b["c"] for b in S]

U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
U.sort(key=lambda r: r["cj_t"])
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def asof(t): return bisect.bisect_right(TS, t) - 1

ANCH = [{"cj_i": asof(r["cj_t"]), "cj_t": r["cj_t"], "g_sl": r["g_sl"],
         "flush_low": r["g_sl"]}   # g_sl = flush_low - 0.1*ATR(âncora); usamos g_sl como piso
        for r in U if fv(r, "swept_prior_low") == 1 and fv(r, "rsi_low", 99) <= 40 and fv(r, "in_demand") == 1]
ANCH.sort(key=lambda a: a["cj_i"]); AI = [a["cj_i"] for a in ANCH]

REG = {}
def reg(i):
    if i not in REG: REG[i] = regime_h(TS[i])
    return REG[i]

signals, rej_band, rej_hl = [], 0, 0
consumed = set(); cooldown_until = -1
for i in range(100, N):
    b = S[i]; ema = b.get("ema21"); atr = b.get("atr"); rsi = b.get("rsi")
    if not ema or not atr or rsi is None: continue
    k = bisect.bisect_right(AI, i - 2) - 1
    if k < 0: continue
    a = ANCH[k]; age = i - a["cj_i"]
    if age > 32 or k in consumed: continue
    if min(L[a["cj_i"] + 1:i + 1]) <= a["g_sl"]: continue
    # M — maturidade
    low96 = min(L[i - 95:i + 1])
    if (C[i] - low96) < 2.5 * atr: continue
    # P — prova a close
    if not (C[i] > ema and (C[i] - ema) <= 0.6 * atr): continue
    if not (min(L[i - 2:i + 1]) > min(L[i - 10:i - 2])): continue
    # Fw
    lo20 = min(L[i - 19:i + 1]); hi20 = max(H[i - 19:i + 1])
    pos20 = (C[i] - lo20) / ((hi20 - lo20) or atr)
    if not (40 <= rsi <= 60 and pos20 <= 0.85): continue
    # R — regime
    if reg(i) != "BEAR": continue
    consumed.add(k)
    if i <= cooldown_until: continue
    swing = min(L[i - 11:i + 1])
    if swing <= a["g_sl"]: rej_hl += 1; continue           # higher-low genuíno exigido
    sl = swing - 0.1 * atr; risk = C[i] - sl
    if not (1.2 * atr <= risk <= 4.0 * atr): rej_band += 1; continue
    cooldown_until = i + 96
    signals.append({"i": i, "t": TS[i], "utc": dt.datetime.utcfromtimestamp(TS[i]).strftime("%Y-%m-%d %H:%M"),
                    "entry": C[i], "sl": round(sl, 2), "risk_atr": round(risk / atr, 2), "anchor_age": age})

print(f"CONFIG V2 — SINAIS ACEITOS: {len(signals)} · rejeitados banda: {rej_band} · rejeitados higher-low: {rej_hl}")

wk_bars = collections.Counter(); wk_bear = collections.Counter()
for i in range(0, N, 4):
    d = dt.datetime.utcfromtimestamp(TS[i]); wk = f"{d.isocalendar()[0]}-{d.isocalendar()[1]:02d}"
    wk_bars[wk] += 1
    if reg(i) == "BEAR": wk_bear[wk] += 1
w_25 = [w for w in wk_bars if wk_bear[w] / wk_bars[w] >= 0.25]
w_50 = [w for w in wk_bars if wk_bear[w] / wk_bars[w] >= 0.50]
sig_wk = collections.Counter()
for s in signals:
    d = dt.datetime.utcfromtimestamp(s["t"]); sig_wk[f"{d.isocalendar()[0]}-{d.isocalendar()[1]:02d}"] += 1
for tag, ws in (("BEAR>=25%", w_25), ("BEAR>=50%", w_50)):
    tot = sum(sig_wk.get(w, 0) for w in ws)
    print(f"freq ({tag}): {tot} sinais / {len(ws)} semanas = {tot/max(1,len(ws)):.2f}/sem · máx/sem = "
          f"{max([sig_wk.get(w,0) for w in ws] or [0])} · fora dessas semanas: {sum(v for w,v in sig_wk.items() if w not in ws)}")

TR = json.load(open(HERE / "results" / "cris_trades_analysis_20260704.json"))
print("\nCOBERTURA 4 trades BEAR do Cris (±6 barras):")
for tr in TR:
    if tr["n"] not in (19, 20, 33, 34): continue
    i = asof(tr["t"])
    near = [s for s in signals if abs(s["i"] - i) <= 6]
    if near:
        print(f"  #{tr['n']} {tr['utc']}: COBERTO {near[0]['utc']} (dt={near[0]['i']-i:+d}, risk_atr={near[0]['risk_atr']})")
    else:
        c = min(signals, key=lambda s: abs(s["i"] - i)) if signals else None
        print(f"  #{tr['n']} {tr['utc']}: NÃO coberto (mais próximo: {c['utc'] if c else '-'} dt={c['i']-i:+d})" if c else "  sem sinais")

yr = collections.Counter(dt.datetime.utcfromtimestamp(s["t"]).year for s in signals)
print(f"\npor ano: {dict(sorted(yr.items()))}")
print("\nlista (outcome-blind):")
for s in signals: print(f"  {s['utc']}  entry {s['entry']:.2f} sl {s['sl']:.2f} risk/ATR {s['risk_atr']:.2f} idade {s['anchor_age']}")
