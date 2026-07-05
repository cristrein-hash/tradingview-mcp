#!/usr/bin/env python3
"""SM probe 8 — MEDIDA FINAL do sistema 'RECLAIM-HL' (outcome-blind).

CONFIG FINAL (candidata a spec):
  E1 borda reclaim: c[i] >= ema21[i]+0.15*atr  E  c[i-1] < ema21[i-1]+0.15*atr[i-1]
  E2 fresco:        algum close < ema21 nas ultimas 24 barras
  M  paciencia:     pullback_age >= 8 (janela 96)
  C1 HIGHER-LOW:    obrigatorio (par campeao 1/2)
  C2 CHOCH<=32b:    obrigatorio (par campeao 2/2)
  C3 >=1 de {retrace box96 close em [0.25,0.75], quiet30<=1.15}
  DEDUP: cooldown {24,48} barras (grade final)
  SL: fundo da perna de queda (min low desde high96) - 0.1*ATR
Report: N, freq/sem total e no span dos 35, distribuicao semanal (max burst),
cobertura35 ±6 barras (lista), SL geometria ATR/$, por-ano. NADA de outcome.
LOOK LEDGER probe 8: 2 linhas — total acumulado 26 looks de frequencia/cobertura.
"""
import json, bisect, glob, datetime as dt, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
series, smc = {}, {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"], b)
    for e in d["smc_events"]:
        if "CHOCH" in str(e.get("text", "")).upper(): smc.setdefault((e["t"], e.get("id")), e)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]
CH_TS = sorted(e["t"] for e in smc.values())
b30 = {}
for b in S:
    key = b["t"] // 1800
    r = b30.setdefault(key, {"h": b["h"], "l": b["l"], "t_close": b["t"]})
    r["h"] = max(r["h"], b["h"]); r["l"] = min(r["l"], b["l"]); r["t_close"] = max(r["t_close"], b["t"])
B30 = sorted(b30.values(), key=lambda r: r["t_close"])
B30_CLOSE = [r["t_close"] for r in B30]; TR30 = [r["h"] - r["l"] for r in B30]
ATR30 = []; a = None
for tr in TR30:
    a = tr if a is None else (a * 13 + tr) / 14.0; ATR30.append(a)
def quiet30_at(t0):
    j = bisect.bisect_right(B30_CLOSE, t0) - 1
    return None if j < 20 else sum(TR30[j - 3:j + 1]) / 4.0 / max(1e-9, ATR30[j])

AN = json.load(open(HERE / "results" / "cris_trades_analysis_20260704.json"))
T35 = sorted(r["t"] for r in AN)
T35_SPAN = (T35[0] - 86400, T35[-1] + 86400)
W = 96
BUF = 0.15

def scan(COOLDOWN):
    sigs = []; last = -10**9
    for i in range(W + 2, len(S)):
        b, pb = S[i], S[i - 1]
        if b.get("ema21") is None or pb.get("ema21") is None: continue
        atr = b["atr"] or 1.0
        if not (b["c"] >= b["ema21"] + BUF * atr): continue
        if not (pb["c"] < pb["ema21"] + BUF * (pb["atr"] or atr)): continue
        if not any(S[k]["c"] < S[k]["ema21"] for k in range(i - 24, i) if S[k].get("ema21")): continue
        if i - last <= COOLDOWN: continue
        win = S[i - W:i + 1]; lows = [x["l"] for x in win]; highs = [x["h"] for x in win]
        jh = max(range(len(win)), key=lambda k: win[k]["h"])
        if len(win) - 1 - jh < 8: continue
        swl = [k for k in range(2, len(lows) - 2) if lows[k] == min(lows[k - 2:k + 3])]
        if not (len(swl) >= 2 and lows[swl[-1]] > lows[swl[-2]]): continue      # C1
        jc = bisect.bisect_right(CH_TS, b["t"]) - 1
        if not (jc >= 0 and (b["t"] - CH_TS[jc]) // 900 <= 32): continue        # C2
        hi96, lo96 = max(highs), min(lows)
        ret = (hi96 - b["c"]) / ((hi96 - lo96) or atr)
        q = quiet30_at(b["t"])
        if not ((0.25 <= ret <= 0.75) or (q is not None and q <= 1.15)): continue  # C3
        dip_low = min(lows[jh:])
        sl = dip_low - 0.1 * atr
        sigs.append(dict(i=i, t=b["t"], c=b["c"], sl=sl,
                         d_atr=(b["c"] - sl) / atr, d_usd=b["c"] - sl))
        last = i
    return sigs

def report(name, sigs):
    weeks_all = sorted({dt.datetime.utcfromtimestamp(b["t"]).strftime("%G-%V") for b in S})
    wk_count = collections.Counter(dt.datetime.utcfromtimestamp(s["t"]).strftime("%G-%V") for s in sigs)
    sig_ts = [s["t"] for s in sigs]
    cov35 = [t0 for t0 in T35 if any(abs(st - t0) <= 6 * 900 for st in sig_ts)]
    in_span = sum(1 for st in sig_ts if T35_SPAN[0] <= st <= T35_SPAN[1])
    d_atr = sorted(s["d_atr"] for s in sigs); d_usd = sorted(s["d_usd"] for s in sigs)
    med = lambda a: a[len(a) // 2]; q1 = lambda a: a[len(a) // 4]; q3 = lambda a: a[3 * len(a) // 4]
    byyear = collections.Counter(dt.datetime.utcfromtimestamp(s["t"]).year for s in sigs)
    burst = collections.Counter(wk_count.values())
    zero_wk = len(weeks_all) - len(wk_count)
    idx = {t0: n for n, t0 in enumerate(T35, 1)}
    print(f"\n{name}: N={len(sigs)}  {len(sigs)/len(weeks_all):.2f}/sem (todas {len(weeks_all)} sem)"
          f"  span35: {in_span} ({in_span/29:.2f}/sem)")
    print(f"  dist semanal: 0-sinal {zero_wk} sem; " + "; ".join(f"{k}/sem x{v}" for k, v in sorted(burst.items())))
    print(f"  cobertura35 = {len(cov35)}/35  -> #{sorted(idx[t] for t in cov35)}")
    print(f"  SL: {med(d_atr):.2f} ATR [{q1(d_atr):.2f}-{q3(d_atr):.2f}]  ${med(d_usd):.1f} [{q1(d_usd):.1f}-{q3(d_usd):.1f}]")
    print(f"  por-ano: {dict(sorted(byyear.items()))}")

for cd in (24, 48):
    report(f"FINAL cooldown={cd}", scan(cd))
