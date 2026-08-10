#!/usr/bin/env python3
"""A1A2_FVG_LAB v4 — FIX do anchor-lag (prereg FRESH_ANCHOR_PREREG_20260810.md). Baseline (argmax-global da
perna, = detect_at de v2, verbatim) vs Candidato A (topo-da-perna = swing-high fractal recente) vs B (janela
MB3 alargada). Mede R1-R5 na população BULL-gated. Motor/régua-mãe read-only, thresholds congelados — só
muda a DEFINIÇÃO do anchor. NÃO toca nada live. py3.9 stdlib.

Nota: blocos RAW terminam 2026-07-04 → o bounce de hoje é live-only (spot-check à parte via runtime store).
Aqui valida-se a CLASSE de desync-rejeições sobre 2025-02→2026-07."""
import sys, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from a1_causal_entry import load_series, causal_entry, HORIZON, M_FRAC
from fvg_localization_study import panel, r_of, BLK
from fvg_localization_study_v2 import HH_WIN, HH_GAP, PB_WIN, PB_MIN_ATR, A2_MAX_ATR, SCALE_ATR, detect_at as detect_base
from fvg_localization_study_v3 import build_regime_lookup, regime_at
MB3_WIN = 4   # candidato B: aceita MB3 até W barras atrás


def _is_swinghigh(H, p, m):
    if p - m < 0 or p + m >= len(H):
        return False
    return H[p] == max(H[p - m:p + m + 1]) and H[p] > max(H[p - m:p])


def _resolve(S, ei, ent, sl):
    L, Hh, N = S["L"], S["H"], S["N"]
    rr = ent - sl; tgt = ent + 3 * rr
    for m in range(ei + 1, min(N, ei + HORIZON + 1)):
        if L[m] <= sl: return "LOSS"
        if Hh[m] >= tgt: return "WIN"
    return "OPEN"


def _finish(S, i, hh_i, mb3_win=0):
    """Da âncora hh_i em diante: fundo j, gates, MB3, outcome. mb3_win>0 = aceita ei em [i-mb3_win, i].
    Devolve dict do disparo (catalogado em i) ou None. Idêntico ao baseline exceto anchor + janela MB3."""
    H, L, ATR, N = S["H"], S["L"], S["ATR"], S["N"]
    atr = ATR[i] or 5.0
    j = min(range(hh_i + 1, i + 1), key=lambda z: L[z])
    if i - j > PB_WIN:
        return None
    hh = H[hh_i]; depth = (hh - L[j]) / atr
    if depth < PB_MIN_ATR:
        return None
    start = max(0, j - 3)
    Sx = {k: (v[start:i + 1] if isinstance(v, list) else v) for k, v in S.items()}
    Sx["N"] = len(Sx["T"])
    r = causal_entry(Sx, j - start, kind="MB3")
    if not r:
        return None
    ei = r["ei"] + start
    if not (i - mb3_win <= ei <= i):        # baseline: mb3_win=0 → ei==i
        return None
    if r["R"] > SCALE_ATR * atr:
        return None
    ent, sl = r["ent"], r["sl"]
    o = _resolve(S, ei, ent, sl)
    pb_low = L[j]
    bounce = 100 * (ent - pb_low) / (hh - pb_low) if hh > pb_low else 0.0
    depth_r = round(depth, 2)
    return dict(ei=ei, cat_i=i, t=S["T"][i], ent=ent, sl=sl, R=round(ent - sl, 2), o=o,
                depth=depth_r, layer=("A2" if depth <= A2_MAX_ATR else "A1"), bounce=bounce, j=j, hh_i=hh_i)


def anchor_recent_fractal_high(S, i):
    """Candidato A: topo-da-perna = swing-high fractal confirmado mais recente (<= i-m), lookback HH_WIN.
    Fallback = argmax global (baseline) se não houver fractal."""
    H = S["H"]
    for p in range(i - M_FRAC, max(0, i - HH_WIN) - 1, -1):
        if p + M_FRAC <= i and _is_swinghigh(H, p, M_FRAC):
            return p
    return max(range(max(0, i - HH_WIN), i - HH_GAP), key=lambda z: H[z])


def detect_A(S, i):
    if i - HH_GAP <= 0:
        return None
    return _finish(S, i, anchor_recent_fractal_high(S, i), mb3_win=0)


def detect_B(S, i):
    """Baseline geometry + janela MB3 alargada (só comparação)."""
    if i - HH_GAP <= 0:
        return None
    hh_i = max(range(max(0, i - HH_WIN), i - HH_GAP), key=lambda z: S["H"][z])
    return _finish(S, i, hh_i, mb3_win=MB3_WIN)


def base_reason_fundo_velho(S, i):
    """True se o baseline rejeita nesta barra por 'fundo velho' (i-j>PB_WIN) — o modo de dessincronização."""
    H, L = S["H"], S["L"]
    if i - HH_GAP <= 0:
        return False
    hh_i = max(range(max(0, i - HH_WIN), i - HH_GAP), key=lambda z: H[z])
    j = min(range(hh_i + 1, i + 1), key=lambda z: L[z])
    return (i - j) > PB_WIN


def sweep(S, fn):
    out = {}
    for i in range(HH_WIN + 4, S["N"]):
        r = fn(S, i)
        if r and r["o"] in ("WIN", "LOSS"):
            out[i] = r
    return out


def main():
    S = load_series(BLK); N = S["N"]
    known, REG = build_regime_lookup()
    for r in [None]:
        pass
    base = sweep(S, detect_base)
    A = sweep(S, detect_A)
    B = sweep(S, detect_B)
    for d in (base, A, B):
        for i, r in d.items():
            r["regime"] = regime_at(known, REG, r["t"])
    bull = lambda d: {i: r for i, r in d.items() if r["regime"] == "BULL"}
    bB, bA, bBw = bull(base), bull(A), bull(B)
    print(f"{'='*80}\nA1A2 ANCHOR-FIX — baseline {len(base)} firings ({len(bB)} BULL) · "
          f"A {len(A)} ({len(bA)} BULL) · B {len(B)} ({len(bBw)} BULL)\n{'='*80}")

    def rep(name, bull_d, all_d):
        res = [r_of(r["o"]) for r in bull_d.values()]
        p = panel(res)
        print(f"\n[{name} · BULL] {p['s']}")
        return p

    pbase = rep("BASELINE", bB, base)
    pA = rep("A (fractal recente)", bA, A)
    pB = rep("B (janela MB3+4)", bBw, B)

    # ---- R1 recovery: firings do candidato NÃO no baseline, na barra onde o baseline rejeitou por fundo-velho
    def recovery(cand_all):
        cand_only = [i for i in cand_all if i not in base]
        desync = [i for i in cand_only if base_reason_fundo_velho(S, i)]
        return cand_only, desync
    for name, cand in (("A", A), ("B", B)):
        conly, desync = recovery(cand)
        wr = 100 * sum(1 for i in desync if cand[i]["o"] == "WIN") / len(desync) if desync else 0
        print(f"\n[R1 {name}] firings-extra {len(conly)} · desync-recuperados {len(desync)} (WR {wr:.0f}%) "
              f"· share bounce>60 {100*sum(1 for i in desync if cand[i]['bounce']>60)/len(desync) if desync else 0:.0f}%")

    # ---- R4: firings incrementais (A vs base) na população BULL — pagam?
    inc = [i for i in bA if i not in base]
    if inc:
        incwr = 100 * sum(1 for i in inc if A[i]["o"] == "WIN") / len(inc)
        late = 100 * sum(1 for i in inc if A[i]["bounce"] > 60) / len(inc)
        print(f"\n[R4] firings incrementais A-BULL: {len(inc)} · WR {incwr:.0f}% (base {pbase['wr']:.0f}%) "
              f"· late-band(>60) {late:.0f}%")

    # ---- NULL BULL (R5) reaproveitado do padrão v2
    import random; random.seed(42); null = []
    for i, r in bB.items():
        k = min(N - 1, r["ei"] + random.randint(1, 48)); ent = S["C"][k]; sl = r["sl"]
        if ent - sl <= 0: continue
        null.append(r_of(_resolve(S, k, ent, sl)))
    print(f"\n[R5 NULL BULL] {panel([x for x in null if x != 0])['s']}")

    # ---- VEREDITO R1-R5 (A é o primário)
    conly, desync = recovery(A)
    r1 = len(desync) >= 1   # recovery real existe (limiar %: reportado; hoje é spot-check à parte)
    r3 = pA["sumR"] >= pbase["sumR"] - 1e-9 and pA["avg"] >= pbase["avg"] - 1e-9 and \
        (pA["rdd"] >= pbase["rdd"] - 1e-9 or pA["rdd"] == float("inf"))
    print(f"\n{'='*80}\nVEREDITO (A primário) — R2/GT kills exige harness GT (correr fvg_localization_study com anchor A à parte)\n{'='*80}")
    print(f"  R1 recovery desync: {len(desync)} recuperados (>0 = existe classe real)")
    print(f"  R3 agregado A≥base: sumR {pA['sumR']:+.0f}v{pbase['sumR']:+.0f} · avgR {pA['avg']:+.2f}v{pbase['avg']:+.2f} · "
          f"ret/DD {pA['rdd']:.1f}v{pbase['rdd']:.1f} => {'OK' if r3 else 'FAIL'}")
    print(f"  R4/R5 acima. R2 (GT 32) + spot-check live = passos seguintes.")


if __name__ == "__main__":
    main()
