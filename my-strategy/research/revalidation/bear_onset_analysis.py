#!/usr/bin/env python3
"""ANÁLISE DOS INÍCIOS DE BEAR MACRO (ordem Cris 2026-07-13) — há um padrão ESTRUTURAL CAUSAL que
sinaliza um macro bear? Diagnóstico (NÃO regra): para cada uma das 5 janelas BEAR do GT Layer 1,
medir no INÍCIO (primeiros dias) features estruturais + exógenas causais, e comparar com a
distribuição das MESMAS features em todos os outros dias (não-início-de-bear). Se separar, existe
assinatura. Sem P&L, sem fit."""
import json, sys, bisect, statistics, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
GT = json.load(open(HERE/"results/REGIME_GT_LAYER1_CRIS_1D_20260713.json"))
D1 = [json.loads(l) for l in open(HERE/"raw_1d_ohlc.jsonl")]
T = [b["t"] for b in D1]; H = [b["h"] for b in D1]; L = [b["l"] for b in D1]; C = [b["c"] for b in D1]
N = len(T); KNOWN = [t+86400 for t in T]

def daily_feat(fn):
    rows = [json.loads(l) for l in open(HERE/fn)]
    kt = [r["t"]+86400 for r in rows]; c = [r["c"] for r in rows]
    ret20 = [None if i < 20 else 100*(c[i]/c[i-20]-1) for i in range(len(c))]
    chg20 = [None if i < 20 else c[i]-c[i-20] for i in range(len(c))]
    return kt, ret20, chg20
DXY_K, DXY_RET, _ = daily_feat("raw_dxy_1d.jsonl")
Y_K, _, Y_CHG = daily_feat("raw_us10y_1d.jsonl")
def _at(kt, v, t):
    j = bisect.bisect_right(kt, t)-1
    return v[j] if j >= 0 else None

def feats_at(i):
    """features CAUSAIS no dia i (fecho de i)."""
    if i < 130: return None
    peak120 = max(H[i-120:i+1]); dd_peak = (peak120-C[i])/peak120*100      # drawdown do pico 120d
    ipk = max(range(i-120, i+1), key=lambda k: H[k]); days_since_peak = i-ipk
    run120 = (C[i]/C[i-120]-1)*100                                          # corrida prévia 120d
    ret20 = (C[i]/C[i-20]-1)*100
    # lower-high macro: high dos últimos 20d < high dos 20d anteriores (perda de momento no topo)
    lh = 1 if max(H[i-20:i+1]) < max(H[i-40:i-20]) else 0
    below_ema50 = 1 if C[i] < (sum(C[i-49:i+1])/50) else 0
    t = KNOWN[i]
    dxy = _at(DXY_K, DXY_RET, t); ych = _at(Y_K, Y_CHG, t)
    return {"dd_peak": dd_peak, "days_since_peak": days_since_peak, "run120": run120,
            "ret20": ret20, "lh": lh, "below_ema50": below_ema50,
            "dxy_ret20": dxy, "y_chg20": ych}

def onset_idxs(w, ndays=15):
    """índices diários dos primeiros ndays da janela w."""
    return [i for i in range(N) if w["t0"] <= KNOWN[i] <= w["t0"]+ndays*86400]

def main():
    bears = [w for w in GT["windows"] if w["regime"] == "BEAR"]
    bear_onset_ranges = [(w["t0"]-2*86400, w["t0"]+20*86400) for w in bears]
    def is_onset(t): return any(a <= t <= b for a, b in bear_onset_ranges)
    keys = ["dd_peak", "days_since_peak", "run120", "ret20", "lh", "below_ema50", "dxy_ret20", "y_chg20"]
    onset_vals = {k: [] for k in keys}; base_vals = {k: [] for k in keys}
    print("== INÍCIO DE CADA BEAR (medianas dos primeiros ~15 dias) ==")
    for w in bears:
        idx = onset_idxs(w)
        fs = [feats_at(i) for i in idx if feats_at(i)]
        if not fs:
            print(f"  {w['d0']} ({w['dur_dias']:.0f}d): sem features (warmup)"); continue
        med = {k: statistics.median([f[k] for f in fs if f[k] is not None]) for k in keys}
        print(f"  {w['d0']}→{w['d1']} ({w['dur_dias']:.0f}d): "
              f"dd_pico {med['dd_peak']:.1f}% · dias_desde_pico {med['days_since_peak']:.0f} · "
              f"run120 {med['run120']:+.1f}% · ret20 {med['ret20']:+.1f}% · LH {med['lh']:.0f} · "
              f"<EMA50 {med['below_ema50']:.0f} · DXYret20 {med['dxy_ret20'] if med['dxy_ret20'] is None else round(med['dxy_ret20'],2)} · "
              f"Ychg20 {med['y_chg20'] if med['y_chg20'] is None else round(med['y_chg20'],2)}")
    # distribuições: onset vs base (todos os outros dias)
    for i in range(130, N):
        f = feats_at(i)
        if not f: continue
        tgt = onset_vals if is_onset(KNOWN[i]) else base_vals
        for k in keys:
            if f[k] is not None: tgt[k].append(f[k])
    print("\n== SEPARAÇÃO onset-BEAR vs resto (mediana [p25,p75]) ==")
    def q(xs, p): s = sorted(xs); return s[min(len(s)-1, int(p*len(s)))]
    for k in keys:
        o, b = onset_vals[k], base_vals[k]
        if len(o) < 3: continue
        mo, mb = statistics.median(o), statistics.median(b)
        # sobreposição: fração do base além da mediana do onset (no sentido do onset)
        if mo >= mb: ov = 100*sum(1 for x in b if x >= mo)/len(b); sent = ">="
        else: ov = 100*sum(1 for x in b if x <= mo)/len(b); sent = "<="
        verd = "SEPARA" if ov < 15 else ("PARCIAL" if ov <= 35 else "não")
        print(f"  {k:<16} onset med {mo:7.2f} [{q(o,.25):.2f},{q(o,.75):.2f}] | "
              f"base med {mb:7.2f} | base {sent} onset: {ov:.0f}% -> {verd}")

if __name__ == "__main__":
    main()
