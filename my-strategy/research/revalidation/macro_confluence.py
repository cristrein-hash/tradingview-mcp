#!/usr/bin/env python3
"""DETECTOR MACRO por CONFLUÊNCIA + LEITURA CONTEXTUAL (ordem Cris 2026-07-13: o que funciona é
confluência, não eixo-único mágico). Do zero, simples. Cada ESTADO exige convergência de leituras
ortogonais causais; o estado PERSISTE (contextual) e só vira quando a confluência oposta ocorre;
CRASH = entrada imediata em BEAR (override). Leituras (todas causais, close do dia i):
  R_trend   : close vs SMA_longa (acima/abaixo)
  R_dd      : drawdown do topo móvel 252d (bear profundo) · runup do fundo móvel (bull)
  R_dollar  : retorno do DXY em W dias (dólar a subir = vento contra ouro)
  R_crash   : queda 2 dias <= crash% (sinal bear causal forte — a dica do Cris para 2026)
Confluência:
  BEAR_conf = abaixo da SMA & dd>=dd_thr & dólar a subir   (OU crash = imediato)
  BULL_conf = acima da SMA & dd<=near_thr (perto do topo)
  RANGE_conf= preço colado à SMA (|close/SMA-1|<flat_thr) — sem tendência
FSM contextual: crash|BEAR_conf->BEAR · BULL_conf->BULL · RANGE_conf->RANGE · senão MANTÉM (persiste).
Medição = scorer AUDITADO (layer1_audit_metrics), nunca %-por-barra sozinho. Sem P&L. RAW-nativo."""
import json, sys, bisect, statistics
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import layer1_audit_metrics as A
D1 = [json.loads(l) for l in open(HERE/"raw_1d_ohlc.jsonl")]
T = [b["t"] for b in D1]; H = [b["h"] for b in D1]; L = [b["l"] for b in D1]; C = [b["c"] for b in D1]
N = len(T)
def sma(i, n): return sum(C[max(0, i-n+1):i+1])/len(C[max(0, i-n+1):i+1])
DXY = [json.loads(l) for l in open(HERE/"raw_dxy_1d.jsonl")]
DXY_K = [r["t"]+86400 for r in DXY]; DXY_C = [r["c"] for r in DXY]
def dxy_ret(t, w):
    j = bisect.bisect_right(DXY_K, t)-1
    if j < w: return 0.0
    return (DXY_C[j]/DXY_C[j-w]-1)*100

def build(sma_n, dd_thr, near_thr, flat_thr, dxy_w, crash_thr):
    state = "RANGE"; out = []
    for i in range(N):
        if i < 260:
            out.append("RANGE"); continue
        s = sma(i, sma_n)
        hi252 = max(H[i-252:i+1]); dd = (hi252-C[i])/hi252*100
        rising = dxy_ret(T[i]+86400, dxy_w) > 0
        crash = (C[i]/C[i-2]-1)*100 <= crash_thr
        bear_conf = C[i] < s and dd >= dd_thr and rising
        bull_conf = C[i] > s and dd <= near_thr
        range_conf = abs(C[i]/s-1)*100 < flat_thr
        if crash or bear_conf: state = "BEAR"
        elif bull_conf: state = "BULL"
        elif range_conf: state = "RANGE"
        # senão: mantém (persistência contextual)
        out.append(state)
    return out

GRID = [(sn, dd, nr, fl, dw, cr)
        for sn in (150, 200) for dd in (8, 12) for nr in (5,) for fl in (3, 5)
        for dw in (90,) for cr in (-6.0,)]

def main():
    rows = []
    for cfg in GRID:
        lab = build(*cfg)
        m = A.audit(lab); sc = A.coherence_score(m)
        rows.append({"cfg": cfg, "m": m, "sc": sc, "lab": lab})
    rows.sort(key=lambda r: -r["sc"])
    print("== CONFLUÊNCIA MACRO · scorer AUDITADO (ordenado por coherence_score) ==")
    print(f"  {'cfg(sma,dd,near,flat,dxyW,crash)':<34} {'coh':>6} {'runs':>4} {'medD':>4} {'onsetLag':>8} {'bears':>5} {'2026bear':>8} {'FBinBull':>8} {'bal':>4}")
    for r in rows:
        m = r["m"]
        print(f"  {str(r['cfg']):<34} {r['sc']:6.1f} {m['n_runs']:4d} {m['med_dur_d']:4.0f} "
              f"{str(m['onset_lag_med']):>8} {m['bears_detected']:>5} {str(m['coherence_2026_bear_pct']):>8} "
              f"{str(m['false_bear_in_bull_pct']):>8} {m['bal']:4.0f}")
    best = rows[0]; m = best["m"]
    print(f"\n== BEST {best['cfg']} — auditoria completa ==")
    print("onset-lag por BEAR (dias do início GT ao 1º disparo):", m["onset_lag_by_bear"])
    print("per-janela (todas 16):")
    for w in A.GT["windows"]:
        print(f"  {w['d0']}→{w['d1']} {w['regime']:<6}{' [nest]' if w['nested'] else '      '} {m['per_window'][w['d0']]}%")
    # timeline dos blocos macro do best (spot-check visual)
    lab = best["lab"]; runs = []
    for i in range(N):
        if runs and runs[-1][0] == lab[i]: runs[-1][2] = i
        else: runs.append([lab[i], i, i])
    import datetime as dt
    print("\nBLOCOS MACRO 2019+ (spot-check):")
    for s, a, b in runs:
        if T[b] < int(dt.datetime(2019,1,1,tzinfo=dt.timezone.utc).timestamp()): continue
        print(f"  {dt.datetime.utcfromtimestamp(T[a]).strftime('%Y-%m-%d')}→{dt.datetime.utcfromtimestamp(T[b]).strftime('%Y-%m-%d')} {s} ({C[a]:.0f}->{C[b]:.0f})")

if __name__ == "__main__":
    main()
