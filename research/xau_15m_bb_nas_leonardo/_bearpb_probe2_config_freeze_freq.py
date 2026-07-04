#!/usr/bin/env python3
"""BEAR-PULLBACK · PROBE 2 — CONFIG CONGELADA V1 + medição OUTCOME-BLIND.
=====================================================================================
CONFIG DECLARADA ANTES DE RODAR (2026-07-04, designer). ZERO leitura de R3/outcome de
sinais novos neste script — mede apenas: prevalência de âncoras, nº de sinais,
sinais/semana-BEAR, máx/semana, cobertura dos 4 trades BEAR do Cris (±6 barras).

CONFIG "BEAR-PULLBACK V1" (uma config, zero grid):
  R  REGIME     : v5h == BEAR na barra do gatilho (regime_hourcausal, causal)
  A  ÂNCORA     : candidato mais recente do universo selado lab_g com
                  swept_prior_low==1 AND rsi_low<=40 AND in_demand==1;
                  idade = i - cj_i ∈ [2, 32] barras; low do flush INTACTO
                  (min L[cj_i+1..i] > g_sl da âncora)  [veto de faca/continuação]
  P  PROVA      : C[i] > EMA21[i] AND (C[i]-EMA21[i]) <= 0.6*ATR[i]  (reclaim na borda)
                  AND micro higher-low: min(L[i-2..i]) > min(L[i-10..i-3])
  Fw FLUXO      : 40 <= RSI[i] <= 60 AND pos20(close) <= 0.85  (não-perseguição)
  GATILHO       : primeira barra com R∧P∧Fw enquanto âncora viva → consome a âncora
  SL ESTRUTURAL : min(g_sl_âncora, min(L[cj_i+1..i]) - 0.1*ATR[i])
  BANDA         : 1.2 <= (C[i]-SL)/ATR[i] <= 4.0, fora da banda = REJEITA (nunca ajusta)
  DEDUP         : 1 sinal máx por âncora; cooldown 32 barras pós-sinal aceito;
                  avaliar apenas a âncora mais recente viva por barra
Fatores ortogonais: R (regime) · A (estrutura/capitulação+zona demand) · P (price-action
a close real) · Fw (momentum/fluxo) · veto de faca embutido em A (low intacto).
=====================================================================================
"""
import json, glob, bisect, io, contextlib, datetime as dt
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

# ---- âncoras qualificadas (features do candidato, outcome-blind) ----
ANCH = []
for r in U:
    if fv(r, "swept_prior_low") == 1 and fv(r, "rsi_low", 99) <= 40 and fv(r, "in_demand") == 1:
        i = asof(r["cj_t"])
        if TS[i] == r["cj_t"] or True:
            ANCH.append({"cj_i": i, "cj_t": r["cj_t"], "g_sl": r["g_sl"], "g_v5h": r.get("g_v5h")})
ANCH.sort(key=lambda a: a["cj_i"]); AI = [a["cj_i"] for a in ANCH]
print(f"universo selado: {len(U)} candidatos · âncoras qualificadas (swept+rsi_low<=40+in_demand): {len(ANCH)}")
print(f"  âncoras em regime BEAR (do candidato): {sum(1 for a in ANCH if a['g_v5h']=='BEAR')}")

# ---- regime por barra (só computa quando precisa; cache por barra) ----
REG = {}
def reg(i):
    if i not in REG: REG[i] = regime_h(TS[i])
    return REG[i]

# ---- gerador ----
signals, rejected_band = [], []
consumed = set()          # âncoras consumidas (índice em ANCH)
cooldown_until = -1
for i in range(40, N):
    b = S[i]; ema = b.get("ema21"); atr = b.get("atr"); rsi = b.get("rsi")
    if not ema or not atr or rsi is None: continue
    # âncora mais recente viva
    k = bisect.bisect_right(AI, i - 2) - 1   # idade >= 2
    if k < 0: continue
    a = ANCH[k]; age = i - a["cj_i"]
    if age > 32 or k in consumed: continue
    if min(L[a["cj_i"] + 1:i + 1]) <= a["g_sl"]: continue      # flush low quebrado → âncora morta
    # P — prova a close real
    if not (C[i] > ema and (C[i] - ema) <= 0.6 * atr): continue
    if not (min(L[i - 2:i + 1]) > min(L[i - 10:i - 2])): continue
    # Fw — fluxo
    lo20 = min(L[i - 19:i + 1]); hi20 = max(H[i - 19:i + 1])
    pos20 = (C[i] - lo20) / ((hi20 - lo20) or atr)
    if not (40 <= rsi <= 60 and pos20 <= 0.85): continue
    # R — regime (avaliado por último: é o mais caro)
    if reg(i) != "BEAR": continue
    # gatilho: consome âncora
    consumed.add(k)
    if i <= cooldown_until: continue
    sl = min(a["g_sl"], min(L[a["cj_i"] + 1:i + 1]) - 0.1 * atr)
    risk = C[i] - sl
    if not (1.2 * atr <= risk <= 4.0 * atr):
        rejected_band.append({"t": TS[i], "risk_atr": round(risk / atr, 2)}); continue
    cooldown_until = i + 32
    signals.append({"i": i, "t": TS[i], "utc": dt.datetime.utcfromtimestamp(TS[i]).strftime("%Y-%m-%d %H:%M"),
                    "entry": C[i], "sl": round(sl, 2), "risk": round(risk, 2),
                    "risk_atr": round(risk / atr, 2), "anchor_age": age,
                    "anchor_t": a["cj_t"]})

print(f"\nSINAIS ACEITOS: {len(signals)} · rejeitados pela banda [1.2,4.0]ATR: {len(rejected_band)}")

# ---- semanas BEAR (por barra, 3 definições) e freq ----
import collections
wk_bars = collections.Counter(); wk_bear = collections.Counter()
for i in range(0, N, 4):     # amostra 1h p/ custo do regime
    d = dt.datetime.utcfromtimestamp(TS[i]); wk = f"{d.isocalendar()[0]}-{d.isocalendar()[1]:02d}"
    wk_bars[wk] += 1
    if reg(i) == "BEAR": wk_bear[wk] += 1
w_any = [w for w in wk_bars if wk_bear[w] > 0]
w_25 = [w for w in wk_bars if wk_bear[w] / wk_bars[w] >= 0.25]
w_50 = [w for w in wk_bars if wk_bear[w] / wk_bars[w] >= 0.50]
print(f"semanas no dataset: {len(wk_bars)} · BEAR>0%: {len(w_any)} · BEAR>=25%: {len(w_25)} · BEAR>=50%: {len(w_50)}")

sig_wk = collections.Counter()
for s in signals:
    d = dt.datetime.utcfromtimestamp(s["t"]); sig_wk[f"{d.isocalendar()[0]}-{d.isocalendar()[1]:02d}"] += 1
for tag, ws in (("BEAR>=25%", w_25), ("BEAR>=50%", w_50)):
    tot = sum(sig_wk.get(w, 0) for w in ws)
    print(f"freq ({tag}): {tot} sinais em {len(ws)} semanas = {tot/max(1,len(ws)):.2f}/semana · máx/semana = "
          f"{max([sig_wk.get(w,0) for w in ws] or [0])}")
out = [w for w in sig_wk if w not in w_25]
print(f"sinais FORA de semanas BEAR>=25%: {sum(sig_wk[w] for w in out)}")

# ---- cobertura dos 4 trades BEAR do Cris (±6 barras) ----
TR = json.load(open(HERE / "results" / "cris_trades_analysis_20260704.json"))
print("\nCOBERTURA dos 4 trades BEAR do Cris (±6 barras):")
for tr in TR:
    if tr["n"] not in (19, 20, 33, 34): continue
    i = asof(tr["t"])
    near = [s for s in signals if abs(s["i"] - i) <= 6]
    print(f"  #{tr['n']} {tr['utc']}: {'COBERTO ' + near[0]['utc'] if near else 'NÃO coberto'}"
          + (f" (dt={near[0]['i']-i:+d} barras, risk_atr={near[0]['risk_atr']})" if near else ""))
    # diagnóstico: sinal mais próximo em qualquer janela
    if not near and signals:
        c = min(signals, key=lambda s: abs(s["i"] - i))
        print(f"      sinal mais próximo: {c['utc']} (dt={c['i']-i:+d} barras)")

# ---- distribuição anual + lista de sinais ----
yr = collections.Counter(dt.datetime.utcfromtimestamp(s["t"]).year for s in signals)
print(f"\npor ano: {dict(sorted(yr.items()))}")
print("\nlista de sinais (outcome-blind):")
for s in signals: print(f"  {s['utc']}  entry {s['entry']:.2f} sl {s['sl']:.2f} risk/ATR {s['risk_atr']:.2f} idade_âncora {s['anchor_age']}")
