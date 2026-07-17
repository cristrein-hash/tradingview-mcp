#!/usr/bin/env python3
"""A1A2_FUNDO_LAB · Stage 4b — FEATURES SEQUENCIAIS (H1+H2) + separação GT-vs-null intra-bucket.
Universo = fractais m=3 confirmados no bucket macro-BULL (BULL_pullback ∪ BULL_impulse) da tabela do s1.
Positivos = GT_A1/GT_A2 (32). Negativos = CAND no mesmo bucket. 2 janelas (swinghigh cap60 · fix48).
Features: H2 (6, só OHLCV) + H1 (5, bubbles buffer 3b). Métrica = AUC(GT vs CAND) + p permutação (shuffle
labels, 5000). Feature-search: 22 looks (2 janelas × 11) → min-p e Bonferroni. NÃO afina threshold, NÃO
combina score. Congelado no manifest (EMENDA Stage 4 GRID). py3.9 stdlib.
Output: results/a1a2_seq_features.csv (por evento) + results/a1a2_discrimination.csv (AUC/p por feature×janela).
"""
import sys, json, csv, bisect, random, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from a1_causal_entry import load_series, _is_swinglow, M_FRAC
import glob

RAW15 = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/XAUUSD_15m_replay_*.jsonl.gz"
RES = HERE / "results"
BUFFER = 3           # bubbles: bar b conta se b <= p (lido em p+3) -> janela [a,p] já respeita
CAP_SH = 60          # cap da âncora swing-high
BUCKET = {"BULL_pullback", "BULL_impulse"}
random.seed(20260717)


def blocks():
    return [f for f in sorted(glob.glob(RAW15)) if "superseded" not in f]


def swing_high(H, p, m):
    if p - m < 0 or p + m >= len(H):
        return False
    return H[p] == max(H[p - m:p + m + 1]) and H[p] > max(H[p - m:p])


def wsum_b(bm, T, a, b):
    """(buy_weight, sell_weight, large_buy_count) no intervalo de índices [a,b]."""
    bw = sw = lg = 0
    for i in range(max(0, a), b + 1):
        r = bm.get(str(T[i]))
        if not r:
            continue
        bw += r["b"][0] * 1 + r["b"][1] * 2 + r["b"][2] * 3
        sw += r["s"][0] * 1 + r["s"][1] * 2 + r["s"][2] * 3
        lg += r["b"][2]
    return bw, sw, lg


def feats(S, bm, p, win):
    """11 features causais para o evento no bar p, janela 'swinghigh'|'fix48'. None se inválido."""
    T, O, H, L, C, ATR, N = S["T"], S["O"], S["H"], S["L"], S["C"], S["ATR"], S["N"]
    if p + M_FRAC >= N or ATR[p] is None or ATR[p] <= 0:
        return None
    atr = ATR[p]
    if win == "fix48":
        a = max(0, p - 48)
    else:
        a = None
        for q in range(p - M_FRAC, max(M_FRAC, p - CAP_SH) - 1, -1):
            if swing_high(H, q, M_FRAC):
                a = q; break
        if a is None:
            a = max(0, p - CAP_SH)
    if p - a < 6:
        return None
    seg = list(range(a, p + 1)); mid = a + (p - a) // 2
    hi_win = max(H[a:p + 1]); lo_p = L[p]
    # --- H2 (OHLCV) ---
    d_early = (hi_win - min(L[a:mid + 1])) / max(1, mid - a)
    d_late = (H[mid] - lo_p) / max(1, p - mid)
    f_decel = d_early / d_late if d_late > 0 else 3.0
    tr = lambda i: max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])) if i > 0 else H[i] - L[i]
    tr_last = st.mean([tr(i) for i in range(max(1, p - 2), p + 1)])
    tr_win = st.mean([tr(i) for i in seg if i > 0]) or 1.0
    f_contract = tr_last / tr_win
    rng = (H[p] - L[p]) or 1e-9
    f_wick = (min(O[p], C[p]) - L[p]) / rng
    f_reclaim = (C[p + M_FRAC] - lo_p) / atr
    f_depth = (hi_win - lo_p) / atr
    ll = 0
    for i in range(p, a, -1):
        if L[i] < L[i - 1]:
            ll += 1
        else:
            break
    f_llcount = ll
    # --- H1 (bubbles, buffer já implícito: janela termina em p, lido em p+3) ---
    bw, sw, lg = wsum_b(bm, T, a, p)
    bw1, sw1, _ = wsum_b(bm, T, a, mid)
    bw2, sw2, _ = wsum_b(bm, T, mid + 1, p)
    nb = p - a + 1
    f_buydens = bw / nb
    f_accum = (bw2 / max(1, p - mid)) / ((bw1 / max(1, mid - a + 1)) or 0.01) if bw1 else (2.0 if bw2 > 0 else 1.0)
    f_absorp = bw / (bw + sw) if (bw + sw) > 0 else 0.5
    brw, _, _ = wsum_b(bm, T, p - 8, p)
    f_buyrecent = brw
    f_large = lg
    return {"decel": round(f_decel, 3), "contract": round(f_contract, 3), "wick": round(f_wick, 3),
            "reclaim": round(f_reclaim, 3), "depth": round(f_depth, 3), "llcount": f_llcount,
            "buydens": round(f_buydens, 3), "accum": round(f_accum, 3), "absorp": round(f_absorp, 3),
            "buyrecent": f_buyrecent, "large": f_large}


def auc(pos, neg):
    """AUC = P(rank pos > rank neg). 0.5 = sem separação."""
    if not pos or not neg:
        return 0.5
    allv = sorted([(v, 0) for v in neg] + [(v, 1) for v in pos])
    rank = 0.0; i = 0; n = len(allv)
    ranks = [0.0] * n
    while i < n:
        j = i
        while j < n and allv[j][0] == allv[i][0]:
            j += 1
        r = (i + j - 1) / 2.0 + 1
        for k in range(i, j):
            ranks[k] = r
        i = j
    spos = sum(ranks[k] for k in range(n) if allv[k][1] == 1)
    np_, nn = len(pos), len(neg)
    return (spos - np_ * (np_ + 1) / 2.0) / (np_ * nn)


def perm_p(pos, neg, obs_auc, iters=5000):
    """p permutação: fração de shuffles com |AUC-0.5| >= |obs-0.5| (2-lados)."""
    pool = pos + neg; npos = len(pos); target = abs(obs_auc - 0.5); ge = 0
    for _ in range(iters):
        random.shuffle(pool)
        a = auc(pool[:npos], pool[npos:])
        if abs(a - 0.5) >= target:
            ge += 1
    return (ge + 1) / (iters + 1)


def main():
    print("load series + bucket table + bubble map...", flush=True)
    S = load_series(blocks()); T = S["T"]; N = S["N"]
    bm = json.load(open(RES / "bubble_map.json"))
    # tabela do s1: t -> (kind, family)
    tab = {}
    with open(RES / "a1a2_bucket_table.csv") as fh:
        for r in csv.DictReader(fh):
            tab[int(r["t"])] = (r["kind"], r["family_label"])
    # enumerar fractais e casar ao bucket
    FEATS = ["decel", "contract", "wick", "reclaim", "depth", "llcount",
             "buydens", "accum", "absorp", "buyrecent", "large"]
    rows = {"swinghigh": [], "fix48": []}   # (kind, feats)
    for p in range(M_FRAC, N - M_FRAC):
        if not _is_swinglow(S["L"], p, M_FRAC):
            continue
        info = tab.get(T[p])
        if not info or info[1] not in BUCKET:
            continue
        kind = info[0]
        for win in ("swinghigh", "fix48"):
            fv = feats(S, bm, p, win)
            if fv:
                rows[win].append((T[p], kind, fv))
    # escrever features por evento (janela swinghigh como principal)
    with open(RES / "a1a2_seq_features.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["t", "kind", "window"] + FEATS)
        for win in ("swinghigh", "fix48"):
            for t, kind, fv in rows[win]:
                w.writerow([t, kind, win] + [fv[k] for k in FEATS])
    # discriminação
    print("\n=== STAGE 4b — SEPARAÇÃO GT vs NULL intra-bucket (macro-BULL) ===")
    out = []
    for win in ("swinghigh", "fix48"):
        R = rows[win]
        pos = [(kind, fv) for _, kind, fv in R if kind in ("GT_A1", "GT_A2")]
        neg = [(kind, fv) for _, kind, fv in R if kind == "CAND"]
        print(f"\n[janela {win}] positivos={len(pos)} · negativos={len(neg)}")
        for f in FEATS:
            pv = [fv[f] for _, fv in pos]; nv = [fv[f] for _, fv in neg]
            a = auc(pv, nv); pp = perm_p(pv, nv, a)
            out.append((win, f, len(pos), a, pp, st.median(pv), st.median(nv)))
            flag = " *" if pp < 0.01 else (" ." if pp < 0.05 else "")
            print(f"  {f:10} AUC {a:.3f}  p={pp:.4f}  medGT {st.median(pv):.3f} vs medNull {st.median(nv):.3f}{flag}")
    with open(RES / "a1a2_discrimination.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["window", "feature", "n_pos", "auc", "perm_p", "med_gt", "med_null"])
        for r in out:
            w.writerow(r)
    # feature-search
    ps = sorted(r[4] for r in out)
    minp = ps[0]; K = len(out)
    bonf = min(1.0, minp * K)
    print(f"\nFEATURE-SEARCH: {K} looks · min-p={minp:.4f} · Bonferroni={bonf:.3f}")
    print(f"  E[min-p sob null uniforme] ~ {1/(K+1):.3f}")
    surv = [r for r in out if r[4] * K < 0.05]
    if surv:
        print("  SOBREVIVEM feature-search (p*K<0.05):")
        for r in surv:
            print(f"    {r[0]}/{r[1]} AUC {r[3]:.3f} p={r[4]:.4f} (p*K={r[4]*K:.3f})")
    else:
        print("  NENHUMA feature sobrevive feature-search → sem assinatura univariada (esperado; testar convergência a seguir)")


if __name__ == "__main__":
    main()
