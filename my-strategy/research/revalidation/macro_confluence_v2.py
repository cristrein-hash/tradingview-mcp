#!/usr/bin/env python3
"""MACRO CONFLUÊNCIA v2 — 2 correções contextuais (pontos anotados pelo Cris nos prints 2026-07-13):
 P2 SUPRESSÃO POR CONTEXTO-RANGE: detetar contexto de range (banda longa: canal Donchian W_ctx com
   largura relativa <= band% => estamos num range). Dentro do range, BEAR só se o preço QUEBRA
   abaixo do fundo do range (close < range_low); BULL só se ROMPE acima do topo (close > range_high).
   Oscilação dentro da banda = RANGE (mata false-bear-em-range 13,5%).
 P1 GATE DE RECONQUISTA PARA BULL: depois de BEAR, BULL só reacende com NOVO MÁXIMO de N dias
   (reconquista real), não com "acima da SMA + perto do topo" (mata falso-bull no declínio 2026).
Núcleo de confluência do v1 mantido (trend SMA + drawdown + dólar + crash). Prioridade:
crash>BEAR>BULL>contexto-RANGE>persistência. Causal close-only. Scorer AUDITADO. Sem P&L."""
import json, sys, bisect, statistics
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import layer1_audit_metrics as A
D1 = [json.loads(l) for l in open(HERE/"raw_1d_ohlc.jsonl")]
T = [b["t"] for b in D1]; H = [b["h"] for b in D1]; L = [b["l"] for b in D1]; C = [b["c"] for b in D1]
N = len(T)
def sma(i, n): seg = C[max(0, i-n+1):i+1]; return sum(seg)/len(seg)
DXY = [json.loads(l) for l in open(HERE/"raw_dxy_1d.jsonl")]
DXY_K = [r["t"]+86400 for r in DXY]; DXY_C = [r["c"] for r in DXY]
def dxy_ret(t, w):
    j = bisect.bisect_right(DXY_K, t)-1
    return (DXY_C[j]/DXY_C[j-w]-1)*100 if j >= w else 0.0

def build(sma_n, dd_thr, near_thr, dxy_w, crash_thr, W_ctx, band_pct, reclaim_n, brk_k=3, flat_slope=3.0,
          sma_med=50, rally_thr=5.0):
    state = "RANGE"; out = []
    for i in range(N):
        if i < 360:
            out.append("RANGE"); continue
        s = sma(i, sma_n)
        hi252 = max(H[i-252:i+1]); dd = (hi252-C[i])/hi252*100
        rising = dxy_ret(T[i]+86400, dxy_w) > 0
        crash = (C[i]/C[i-2]-1)*100 <= crash_thr
        # contexto de range: canal Donchian longo (barras fechadas <= i-1) E SMA longa PLANA
        # (consolidação dentro de bull/bear = SMA em tendência -> NÃO é range macro; mantém tendência)
        rh = max(H[i-W_ctx:i]); rl = min(L[i-W_ctx:i])
        sma_slope = (s - sma(i-60, sma_n))/s*100        # inclinação da SMA em 60 dias (% do preço)
        in_range_ctx = (rh-rl)/C[i-1] <= band_pct/100.0 and abs(sma_slope) < flat_slope
        # reconquista (novo máximo de reclaim_n dias, causal): close de i é o maior dos reclaim_n
        new_high = C[i] >= max(H[i-reclaim_n:i])
        # rompimento SUSTENTADO do range: brk_k closes seguidos além da banda (causal, <= i)
        brk_up = all(C[i-q] > max(H[i-W_ctx-q:i-q]) for q in range(brk_k))
        brk_dn = all(C[i-q] < min(L[i-W_ctx-q:i-q]) for q in range(brk_k))
        # leituras de confluência
        bear_conf = C[i] < s and dd >= dd_thr and rising
        bull_conf = C[i] > s and dd <= near_thr
        # rollover de bear LENTO (assinatura da análise de onsets): fora do contexto-range,
        # abaixo da SMA + drawdown moderado + dólar a subir + lower-highs (topo a perder força)
        lower_high = max(H[i-20:i+1]) < max(H[i-40:i-20])
        bear_rollover = (not in_range_ctx) and C[i] < s and dd >= 6 and rising and lower_high
        # recuperação BULL (espelho do bear-rollover): a cauda de um BEAR que já virou para CIMA
        # — fundo a subir (higher-low) + SMA média reconquistada + rally do fundo recente — deve
        # virar BULL antes de reconquistar a SMA200 (senão a recuperação fica colada em BEAR).
        smed = sma(i, sma_med); smed_rising = smed > sma(i-20, sma_med)
        higher_low = min(L[i-20:i+1]) > min(L[i-40:i-20])
        rally_off_low = (C[i]/min(L[i-40:i+1]) - 1)*100 >= rally_thr
        bull_recovery = (state == "BEAR" and C[i] > smed and smed_rising and higher_low
                         and rally_off_low and not in_range_ctx)
        # --- prioridade com correções contextuais ---
        if crash:
            state = "BEAR"
        elif in_range_ctx:
            # P2: dentro do range, só sai por QUEBRA SUSTENTADA de extremo (brk_k dias)
            if brk_dn: state = "BEAR"
            elif brk_up and new_high: state = "BULL"
            else: state = "RANGE"
        elif bull_recovery:
            state = "BULL"
        elif bear_conf or bear_rollover:
            state = "BEAR"
        elif bull_conf:
            # P1: se vínhamos de BEAR, exige reconquista (novo máximo) para virar BULL
            if state == "BEAR":
                state = "BULL" if new_high else "BEAR"
            else:
                state = "BULL"
        # senão mantém (persistência contextual)
        out.append(state)
    return out

GRID = [(sn, dd, nr, dw, cr, wc, bp, rc, bk, fs)
        for sn in (200,) for dd in (10,) for nr in (5,) for dw in (90,)
        for cr in (-6.0,) for wc in (120,) for bp in (16, 20) for rc in (60,) for bk in (3, 5)
        for fs in (2.0, 3.0, 4.0)]

def main():
    rows = []
    for cfg in GRID:
        lab = build(*cfg)
        m = A.audit(lab); sc = A.coherence_score(m)
        rows.append({"cfg": cfg, "m": m, "sc": sc, "lab": lab})
    rows.sort(key=lambda r: -r["sc"])
    print("== CONFLUÊNCIA v2 (contexto-range + reclaim-gate) · scorer AUDITADO ==")
    print(f"  {'cfg':<38} {'coh':>6} {'runs':>4} {'FB_bull':>7} {'FB_range':>8} {'FBull_bear':>10} {'2026':>5} {'bears':>5} {'bal':>4}")
    for r in rows:
        m = r["m"]
        print(f"  {str(r['cfg']):<38} {r['sc']:6.1f} {m['n_runs']:4d} "
              f"{str(m['false_bear_in_bull_pct']):>7} {str(m['false_bear_in_range_pct']):>8} "
              f"{str(m['false_bull_in_bear_pct']):>10} {str(m['coherence_2026_bear_pct']):>5} "
              f"{m['bears_detected']:>5} {m['bal']:4.0f}")
    best = rows[0]; m = best["m"]
    print(f"\n== BEST {best['cfg']} · coherence {best['sc']} ==")
    print(f"  runs {m['n_runs']} medDur {m['med_dur_d']}d | onset-lag med {m['onset_lag_med']} | bears {m['bears_detected']}")
    print(f"  false: bear-in-bull {m['false_bear_in_bull_pct']}% · bear-in-range {m['false_bear_in_range_pct']}% · bull-in-bear {m['false_bull_in_bear_pct']}%")
    print(f"  2026 bear held {m['coherence_2026_bear_pct']}% · onset por bear {m['onset_lag_by_bear']}")
    print("  per-janela:")
    for w in A.GT["windows"]:
        print(f"    {w['d0']}→{w['d1']} {w['regime']:<6}{' [nest]' if w['nested'] else '      '} {m['per_window'][w['d0']]}%")

if __name__ == "__main__":
    main()
