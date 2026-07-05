#!/usr/bin/env python3
"""DISCRIMINADOR DE CAPITULAÇÃO — rodada 1 supervisionada contra o rótulo do Cris (2026-07-05).
Formulação correta (pós-DA): entrar no flush-reclaim causal em TODOS os flushes rende 36,5% hit-3R
(+0,46R/tent). Os 34 fundos do Cris são ~11% dos flushes e DENTRO deles a mesma entrada dá ~97%.
Pergunta: que feature ex-ante (known-at-entry) separa flush-Cris de flush-comum?

UNIVERSO (zero tuning, pré-declarado):
  flush = barra cujo low é o mínimo das últimas 96 barras (novo low 24h), dedup por episódio
  (novo flush só após 16 barras sem novo low). ENTRADA CAUSAL = 1ª barra seguinte (≤16 barras)
  com close ≥ flush_low + 0,3*ATR_flush. SL = flush_low − 0,3*ATR_flush. Alvo = entry + 3*risco.
  Outcome = first-touch em 192 barras (48h); timeout = R a mercado no fim.
LABEL is_cris: flush do universo a ≤12h E ≤1,0% de preço de um flush do GT selado (v3, sha check).
FEATURES no momento da ENTRADA (todas causais, close-only):
  drop_atr        queda high(96b antes do flush)→flush_low em ATR (profundidade da capitulação)
  stretch_ema21   (ema21 − flush_low)/ATR no flush (esticão abaixo da média)
  rsi_flush       RSI na barra do flush (exaustão)
  vol_climax      volume da barra do flush / média 96b (clímax vendedor)
  wick_frac       pavio inferior da barra do flush / range dela (rejeição)
  bars_to_reclaim nº de barras flush→entrada (velocidade da virada)
  reclaim_atr     (close_entrada − flush_low)/ATR (força do reclaim)
  accel_drop      queda das últimas 16b pré-flush / queda das 96b (aceleração final = capitulação)
  sess            hora UTC do flush (sessão)
  sweep_ext       flush_low abaixo do low prévio (96b antes, excl. últimas 16) em ATR (extensão do sweep)
ANÁLISE: por feature, quartis do universo → taxa is_cris e hit-3R por quartil (lift univariado).
Sem conjunções nesta rodada (evitar garden-of-forking-paths); ledger = 10 features declaradas."""
import json, glob, bisect, hashlib, statistics as st
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent

GT = HERE / "results" / "ground_truth_bottoms_20260705.json"
sha = hashlib.sha256(GT.read_bytes()).hexdigest()
assert sha == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
gt = json.load(open(GT))  # v4: rótulo expandido pelo Cris (60 fundos)

series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]:
        series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); N = len(S)

# --- universo de flushes: MÁQUINA EPISÓDICA SEQUENCIAL (v2 pós-auto-DA) ---
# v1 movia o flush retroativamente quando vinha low mais fundo em ≤16b, APAGANDO entradas que já
# teriam ocorrido (reclaim antes do low novo) = survivorship look-ahead. v2 processa barra-a-barra:
# flush abre episódio; a cada barra seguinte, PRIMEIRO testa reclaim (close≥flo+0,3ATR → ENTRADA,
# trade travado, episódio fecha), DEPOIS low novo (flo/ATR movem, relógio de 16b reinicia).
# 16 barras sem reclaim nem low novo → episódio morre sem entrada.
pairs = []  # (flush_i, entry_i)
i = 96
while i < N:
    lo96 = min(S[j]["l"] for j in range(i - 96, i))
    if S[i]["l"] < lo96:
        fi = i; flo = S[i]["l"]; atr0 = S[i].get("atr") or 5.0
        k = i + 1; clock = 0; entry_i = None
        while k < N and clock < 16:
            if S[k]["c"] >= flo + 0.3 * atr0:
                entry_i = k; break
            if S[k]["l"] < flo:
                fi = k; flo = S[k]["l"]; atr0 = S[k].get("atr") or 5.0; clock = 0
            else:
                clock += 1
            k += 1
        if entry_i is not None:
            pairs.append((fi, entry_i))
        i = (entry_i if entry_i is not None else k) + 1
    else:
        i += 1

rows = []
for fi, entry_i in pairs:
    fb = S[fi]; atr = fb.get("atr") or 5.0
    flo = fb["l"]
    e = S[entry_i]["c"]; sl = flo - 0.3 * atr; risk = e - sl
    if risk <= 0:
        continue
    tgt = e + 3 * risk; r = None
    for k in range(entry_i + 1, min(N, entry_i + 193)):
        if S[k]["l"] <= sl: r = -1.0; break
        if S[k]["h"] >= tgt: r = 3.0; break
    if r is None:
        k = min(N - 1, entry_i + 192); r = (S[k]["c"] - e) / risk
    hi96 = max(S[j]["h"] for j in range(fi - 96, fi))
    hi16 = max(S[j]["h"] for j in range(fi - 16, fi))
    rng = fb["h"] - fb["l"]
    prev_lo = min(S[j]["l"] for j in range(fi - 96, fi - 16))
    vols = [S[j]["v"] for j in range(fi - 96, fi) if S[j].get("v")]
    rows.append({
        "t": fb["t"], "flush_low": round(flo, 2), "entry_t": S[entry_i]["t"], "r": round(r, 2),
        "drop_atr": (hi96 - flo) / atr,
        "stretch_ema21": ((fb.get("ema21") or flo) - flo) / atr,
        "rsi_flush": fb.get("rsi") or 50.0,
        "vol_climax": (fb.get("v") or 0) / (st.mean(vols) if vols else 1),
        "wick_frac": (min(fb["o"], fb["c"]) - flo) / rng if rng > 0 else 0,
        "bars_to_reclaim": entry_i - fi,
        "reclaim_atr": (e - flo) / atr,
        "accel_drop": (hi16 - flo) / max(0.001, hi96 - flo),
        "sess": dt.datetime.utcfromtimestamp(fb["t"]).hour,
        "sweep_ext": (prev_lo - flo) / atr,
    })

# --- label is_cris ---
for r in rows:
    r["is_cris"] = 0
for g in gt:
    best = None
    for r in rows:
        dtm = abs(r["t"] - g["flush_t"])
        if dtm <= 12 * 3600 and abs(r["flush_low"] - g["flush_low"]) / g["flush_low"] <= 0.010:
            if best is None or dtm < abs(best["t"] - g["flush_t"]):
                best = r
    if best:
        best["is_cris"] = 1

nc = sum(r["is_cris"] for r in rows)
hits = sum(1 for r in rows if r["r"] >= 3)
print(f"UNIVERSO FLUSH-RECLAIM CAUSAL: N{len(rows)} · hit-3R base {100*hits/len(rows):.1f}% · "
      f"NET {sum(r['r'] for r in rows):+.1f}R · label is_cris coberto {nc}/{len(gt)}")
cr = [r for r in rows if r["is_cris"]]
if cr:
    print(f"  dentro do rótulo Cris: hit-3R {sum(1 for r in cr if r['r']>=3)}/{len(cr)} · "
          f"NET {sum(r['r'] for r in cr):+.1f}R")
print()

FEATS = ["drop_atr", "stretch_ema21", "rsi_flush", "vol_climax", "wick_frac",
         "bars_to_reclaim", "reclaim_atr", "accel_drop", "sess", "sweep_ext"]
base_cris = nc / len(rows)
print(f"{'feature':<16} {'Q':>2} {'range':>16} {'N':>5} {'cris%':>6} {'lift':>5} {'hit3R%':>7} {'NET':>8}")
summary = {}
for f in FEATS:
    vals = sorted(r[f] for r in rows)
    qs = [vals[int(len(vals) * q)] for q in (0.25, 0.5, 0.75)]
    best_lift = 0
    for qi in range(4):
        lo = vals[0] if qi == 0 else qs[qi - 1]
        hi = qs[qi] if qi < 3 else vals[-1]
        grp = [r for r in rows if (r[f] >= lo if qi > 0 else True) and (r[f] <= hi if qi < 3 else r[f] >= lo)]
        # particao limpa:
        grp = [r for r in rows if (lo <= r[f] <= hi if 0 < qi < 3 else (r[f] <= hi if qi == 0 else r[f] >= lo))]
        if not grp:
            continue
        crq = sum(r["is_cris"] for r in grp) / len(grp)
        lift = crq / base_cris if base_cris else 0
        h3 = 100 * sum(1 for r in grp if r["r"] >= 3) / len(grp)
        net = sum(r["r"] for r in grp)
        best_lift = max(best_lift, lift)
        print(f"{f:<16} Q{qi+1:>1} {lo:>7.2f}–{hi:>7.2f} {len(grp):>5} {100*crq:>5.1f}% {lift:>5.2f} {h3:>6.1f}% {net:>+8.1f}")
    summary[f] = round(best_lift, 2)
    print()
print("melhor lift univariado por feature:", dict(sorted(summary.items(), key=lambda kv: -kv[1])))
json.dump({"universe_n": len(rows), "base_hit3r": round(hits / len(rows), 3),
           "label_coverage": nc, "best_lifts": summary,
           "rows": rows}, open(HERE / "results" / "capitulation_discriminator_20260705.json", "w"))
print("OK → results/capitulation_discriminator_20260705.json")
