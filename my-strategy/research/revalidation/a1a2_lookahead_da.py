#!/usr/bin/env python3
"""DA LOOKAHEAD-ONLY do gatilho MB3 (ordem Cris 2026-07-15): "tens certeza sem lookahead?".
Testa o ÚNICO ponto suspeito — a âncora do low usa janela [j−16, j+8] (8 barras À FRENTE da marca).
Compara:
  RESEARCH: al = argmin L em [j−16, j+8]; entry = 1º MB3 após al; SL = L[al]−0.1ATR.
  ESTRITO-CAUSAL: entry = 1º MB3 a partir da marca j; SL = (min L em [j−16, ENTRY])−0.1ATR (âncora só
    até à entrada, ZERO barras à frente). É o que dá para fazer live (marca após o low, SL do min-até-agora).
Se os outcomes coincidirem => o +8 é benigno (marca ~no low). Se divergirem => quantifica o lookahead.
Trigger MB3 e outcome SL-first são idênticos nos dois; só muda a âncora. RAW 15M direto do HD."""
import gzip, json, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
BLOCKS = ["XAUUSD_15m_replay_2025-02-25_to_2025-05-25.jsonl.gz", "XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz",
          "XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz", "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz"]
LOWBACK, LOWFWD, TRIG_WIN, HORIZON = 16, 8, 48, 480
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
bars = {}
for blk in BLOCKS:
    with gzip.open(RAW/blk, "rt") as fh:
        for l in fh:
            i = l.find('"ohlcv":')
            if i < 0: continue
            s = l.find('[', i); e = l.find(']', s)
            if s < 0 or e < 0: continue
            try: arr = json.loads(l[s:e+1])
            except Exception: continue
            for b in arr:
                t = b.get("time")
                if t is None: continue
                if t not in bars: bars[t] = [b["open"], b["high"], b["low"], b["close"]]
                else: bars[t][1] = max(bars[t][1], b["high"]); bars[t][2] = min(bars[t][2], b["low"]); bars[t][3] = b["close"]
T = sorted(bars); O=[bars[t][0] for t in T]; H=[bars[t][1] for t in T]; L=[bars[t][2] for t in T]; C=[bars[t][3] for t in T]
N = len(T); ATR=[None]*N; trs=[]
for i in range(N):
    if i > 0: trs.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
    ATR[i] = sum(trs[-14:])/14 if len(trs) >= 14 else None
def outc(ei, sl, tgt):
    for m in range(ei+1, min(N, ei+HORIZON+1)):
        if L[m] <= sl: return "LOSS", m-ei
        if H[m] >= tgt: return "WIN", m-ei
    return "OPEN", None
def mb3_after(a):
    for k in range(a+1, min(N, a+TRIG_WIN+1)):
        if C[k] > O[k] and C[k] > H[k-1]: return k
    return None

def research(j):
    al = min(range(max(0, j-LOWBACK), min(N, j+LOWFWD+1)), key=lambda k: L[k])
    ei = mb3_after(al)
    if ei is None: return None
    low = L[al]; atr = ATR[al] or 5.0; sl = round(low-0.1*atr, 2); ent = C[ei]; r = ent-sl
    if r <= 0.05*atr: return None
    o, b = outc(ei, sl, ent+3*r)
    return {"ei": ei, "ent": round(ent, 2), "sl": sl, "R": round(r, 2), "o": o, "b": b}
def causal(j):
    # entry = 1º MB3 a partir de j-? — o gatilho tem de disparar APÓS a marca (marca ~no low, live).
    # SL = (min L em [j-LOWBACK, ENTRY]) − 0.1ATR (âncora só até à entrada; ZERO barras à frente).
    ei = mb3_after(j-1)                          # 1º MB3 a partir de j (inclusive j)
    if ei is None: return None
    lo0 = max(0, j-LOWBACK); alc = min(range(lo0, ei+1), key=lambda k: L[k])   # min low ATÉ à entrada
    low = L[alc]; atr = ATR[alc] or 5.0; sl = round(low-0.1*atr, 2); ent = C[ei]; r = ent-sl
    if r <= 0.05*atr: return None
    o, b = outc(ei, sl, ent+3*r)
    return {"ei": ei, "ent": round(ent, 2), "sl": sl, "R": round(r, 2), "o": o, "b": b}

GT = json.load(open(HERE/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
for layer in ("A1_pullback_fundo", "A2_pullback_raso"):
    F = sorted([f for f in GT["fundos"] if f.get("subclasse") == layer], key=lambda x: x["t"])
    print(f"\n{'='*78}\n{layer} (N={len(F)})  RESEARCH([j-16,j+8]) vs ESTRITO-CAUSAL(âncora só até entrada)\n{'='*78}")
    print(f"  {'#':<3}{'dt':16}{'RESEARCH':>26}{'CAUSAL':>26}  {'muda?'}")
    wr = wc = diff = 0
    for n, f in enumerate(F, 1):
        j = bisect.bisect_right(T, int(f["t"]))-1
        R, Cz = research(j), causal(j)
        rr = f"ent{R['ent']} SL{R['sl']} {R['o']}" if R else "—"
        cc = f"ent{Cz['ent']} SL{Cz['sl']} {Cz['o']}" if Cz else "—"
        ro = R["o"] if R else None; co = Cz["o"] if Cz else None
        ch = "" if ro == co and (R and Cz and abs(R['sl']-Cz['sl']) < 0.5 and R['ei'] == Cz['ei']) else " <== DIVERGE"
        if ro == "WIN": wr += 1
        if co == "WIN": wc += 1
        if ch: diff += 1
        print(f"  {n:<3}{ds(int(f['t'])):16}{rr:>26}{cc:>26} {ch}")
    print(f"  RESUMO: RESEARCH {wr} WIN · CAUSAL {wc} WIN · {diff}/{len(F)} divergem")
