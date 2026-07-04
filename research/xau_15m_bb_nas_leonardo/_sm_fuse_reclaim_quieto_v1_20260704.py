#!/usr/bin/env python3
"""RECLAIM-QUIETO v1.0 — fusao congelada D1 (RECLAIM-HL) + D2 (FLUXO-QUIETO) por DA-pre.
CONFIG UNICA, ZERO GRID. Uma rodada de caracterizacao freq/cobertura = 1 look declarado.
Outcome-blind: do arquivo dos 35 trades le-se APENAS r['t'].

Config congelada ANTES desta execucao (DA-pre §7):
  E1  borda reclaim: c >= ema21+0.15*atr E c[i-1] < ema21[i-1]+0.15*atr[i-1]
  E1b no-chase: (c-ema21)/atr <= 1.2
  E2  fresco: existe k em [i-24, i-1] com c[k] < ema21[k]
  M   paciencia: age do high da janela 96 >= 24
  C1  higher-low fractal +-2 confirmado, >=2 swings ascendentes
  C2  CHoCH: idade anchor <= 24 barras E known_at reconstruido <= t_i
      (known_at = 1a barra k > t_anchor com close cruzando e.price;
       sem cruzamento em 40 barras -> fallback known_at = t_anchor + 6 barras)
  C3  retrace96 em [0.25, 0.75]
  C4  quiet30 <= 1.0 (resample causal 15M->30M, so buckets completos)
  SL  anchor = min(ultimo fractal-low confirmado em 52 barras, min low 8 barras) - 0.25*atr
      d>4.0 ATR -> rejeita; d<1.2 ATR -> re-ancora dip_low96-0.25*atr, fora de [1.2,4.0] -> rejeita
      sanity dolar: d > $40 -> rejeita
  DEDUP cooldown 48 barras E episodio (jh do high-96 diferente do jh do ultimo sinal)
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

# --- CHoCH known_at reconstruido (correcao do leak DA-pre 1.1) ---
CLOSE_BY_T = {b["t"]: b["c"] for b in S}
def sign(x): return 1 if x > 0 else (-1 if x < 0 else 0)
CH = []  # (t_anchor, known_at)
for e in smc.values():
    ta, pr = e["t"], e.get("price")
    j0 = bisect.bisect_right(TS, ta) - 1
    if j0 < 0 or pr is None:
        continue
    s0 = sign(S[j0]["c"] - pr)
    known = None
    if s0 != 0:
        for k in range(j0 + 1, min(j0 + 41, len(S))):
            if sign(S[k]["c"] - pr) == -s0:
                known = S[k]["t"]; break
    if known is None:
        known = ta + 6 * 900          # fallback: idade do anchor >= 6 barras
    CH.append((ta, known))
CH.sort()
CH_TA = [c[0] for c in CH]

def choch_ok(t_i):
    # anchor com idade <= 24 barras E known_at <= t_i (barra de impressao fechada no close de i)
    j = bisect.bisect_right(CH_TA, t_i) - 1
    while j >= 0 and (t_i - CH_TA[j]) // 900 <= 24:
        if CH[j][1] <= t_i:
            return True
        j -= 1
    return False

# --- quiet30 causal (metodo D1 verificado; threshold 1.0 = feature sobrevivente) ---
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
T35 = sorted(r["t"] for r in AN)   # outcome-blind: apenas timestamps
T35_SPAN = (T35[0] - 86400, T35[-1] + 86400)
W = 96; BUF = 0.15

sigs = []; last_i = -10**9; last_jh_t = None
rej = collections.Counter()
for i in range(W + 2, len(S)):
    b, pb = S[i], S[i - 1]
    if b.get("ema21") is None or pb.get("ema21") is None: continue
    atr = b["atr"] or 1.0
    # E1 borda
    if not (b["c"] >= b["ema21"] + BUF * atr): continue
    if not (pb["c"] < pb["ema21"] + BUF * (pb["atr"] or atr)): continue
    # E1b no-chase
    if (b["c"] - b["ema21"]) / atr > 1.2: rej["chase"] += 1; continue
    # E2 fresco
    if not any(S[k]["c"] < S[k]["ema21"] for k in range(i - 24, i) if S[k].get("ema21")): continue
    win = S[i - W:i + 1]; lows = [x["l"] for x in win]; highs = [x["h"] for x in win]
    jh = max(range(len(win)), key=lambda k: win[k]["h"])
    if len(win) - 1 - jh < 24: rej["age"] += 1; continue           # M paciencia 24
    swl = [k for k in range(2, len(lows) - 2) if lows[k] == min(lows[k - 2:k + 3])]
    if not (len(swl) >= 2 and lows[swl[-1]] > lows[swl[-2]]): rej["hl"] += 1; continue
    if not choch_ok(b["t"]): rej["choch"] += 1; continue           # C2 known_at
    hi96, lo96 = max(highs), min(lows)
    ret = (hi96 - b["c"]) / ((hi96 - lo96) or atr)
    if not (0.25 <= ret <= 0.75): rej["ret"] += 1; continue        # C3
    q = quiet30_at(b["t"])
    if q is None or q > 1.0: rej["quiet"] += 1; continue           # C4
    # SL fusao (D2 anchor + rejeicoes)
    lows52 = [S[k]["l"] for k in range(i - 52, i + 1)]
    swl52 = [k for k in range(2, len(lows52) - 2) if lows52[k] == min(lows52[k - 2:k + 3])]
    dip_low96 = min(lows[jh:])
    anch = min(lows52[swl52[-1]] if swl52 else dip_low96, min(lows52[-8:]))
    sl = anch - 0.25 * atr
    d_atr = (b["c"] - sl) / atr
    if d_atr > 4.0: rej["sl_cap"] += 1; continue
    if d_atr < 1.2:
        sl = dip_low96 - 0.25 * atr
        d_atr = (b["c"] - sl) / atr
        if not (1.2 <= d_atr <= 4.0): rej["sl_floor"] += 1; continue
    if b["c"] - sl > 40.0: rej["sl_usd"] += 1; continue
    # DEDUP: cooldown 48 + episodio (mesmo high-96 nao dispara 2x)
    if i - last_i <= 48: rej["cooldown"] += 1; continue
    if last_jh_t is not None and win[jh]["t"] == last_jh_t: rej["episode"] += 1; continue
    sigs.append(dict(i=i, t=b["t"], t_sig=b["t"] + 900, c=b["c"], sl=round(sl, 2),
                     d_atr=round(d_atr, 2), d_usd=round(b["c"] - sl, 2),
                     age=len(win) - 1 - jh, ret=round(ret, 2),
                     e21d=round((b["c"] - b["ema21"]) / atr, 2)))
    last_i = i; last_jh_t = win[jh]["t"]

# --- caracterizacao (1 LOOK) ---
weeks_all = sorted({dt.datetime.utcfromtimestamp(b["t"]).strftime("%G-%V") for b in S})
wk = collections.Counter(dt.datetime.utcfromtimestamp(s["t"]).strftime("%G-%V") for s in sigs)
sig_ts = [s["t"] for s in sigs]
cov35 = [t0 for t0 in T35 if any(abs(st - t0) <= 6 * 900 for st in sig_ts)]
in_span = sum(1 for st in sig_ts if T35_SPAN[0] <= st <= T35_SPAN[1])
med = lambda a: sorted(a)[len(a) // 2]; q1 = lambda a: sorted(a)[len(a) // 4]; q3 = lambda a: sorted(a)[3 * len(a) // 4]
d_atr = [s["d_atr"] for s in sigs]; d_usd = [s["d_usd"] for s in sigs]
byyear = collections.Counter(dt.datetime.utcfromtimestamp(s["t"]).year for s in sigs)
burst = collections.Counter(wk.values())
idx = {t0: n for n, t0 in enumerate(T35, 1)}
fpw = len(sigs) / len(weeks_all)
print(f"RECLAIM-QUIETO v1.0 (config unica congelada): N={len(sigs)}  {fpw:.2f}/sem em {len(weeks_all)} semanas")
print(f"  span dos 35 (29 sem): {in_span} sinais = {in_span/29:.2f}/sem")
print(f"  semanas 0-sinal {len(weeks_all)-len(wk)}; dist " + "; ".join(f"{k}x{v}" for k, v in sorted(burst.items())))
print(f"  cobertura35 +-6 barras = {len(cov35)}/35 -> #{sorted(idx[t] for t in cov35)}")
print(f"  SL: med {med(d_atr):.2f} ATR [{q1(d_atr):.2f}-{q3(d_atr):.2f}]  ${med(d_usd):.1f} [{q1(d_usd):.1f}-{q3(d_usd):.1f}]  max ${max(d_usd):.1f}")
print(f"  perfil: age med {med([s['age'] for s in sigs])} | e21d med {med([s['e21d'] for s in sigs]):.2f} | ret med {med([s['ret'] for s in sigs]):.2f}")
print(f"  por-ano {dict(sorted(byyear.items()))}")
print(f"  rejeicoes: {dict(rej)}")
print(f"  VEREDITO banda [1.0, 3.5]/sem: {'DENTRO' if 1.0 <= fpw <= 3.5 else 'FORA -> DESENHO FALHOU (sem regrid; volta ao Cris)'}")
json.dump(sigs, open(HERE / "results" / "reclaim_quieto_v1_signals_20260704.json", "w"), indent=1)
print(f"  sinais salvos: results/reclaim_quieto_v1_signals_20260704.json")
