#!/usr/bin/env python3
"""A1A2_FUNDO_LAB · Stage 3b-v2 — REGIÃO pela LEG APROVADA (zigzag R=6, esqueleto selado do leg_v3).
Substitui o leg ad-hoc m=3 do s3 (que dava 38% NO_LEG) pelo esqueleto de pivôs zigzag(6) causal
(gt_pivot_structural_harness_r2; confirmed_at = fecho, nunca revisto) — o MESMO que o GT/leg_v3 usam.
Leg = última UP-leg confirmada (low->high). região = pos do low do pullback nela. Re-mede (1)-(4).
depth=sinal legítimo a priori. Causal, RAW-first. py3.9 stdlib. Output: results/a1a2_zzregion_table.csv.
"""
import sys, csv, bisect, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from a1_causal_entry import load_series, _is_swinglow, M_FRAC
sys.path.insert(0, str(HERE))
from s2b_seq_features import feats, auc, blocks, BUCKET
import gt_pivot_structural_harness_r2 as ZZ
import importlib
REG = importlib.import_module("engine_4h_regime_gate_RAW")
RES = HERE / "results"

# --- pivôs zigzag R=6 (SELADOS, causais): merge cronológico por confirmed_at ---
HI6, LO6 = ZZ.zigzag(6)   # cada = (confirmed_at, price, atr)
PIVS = sorted([(c, "H", p) for c, p, _ in HI6] + [(c, "L", p) for c, p, _ in LO6])
PC = [x[0] for x in PIVS]


def zzleg_region(t, ev_low):
    """Região do low na última UP-leg confirmada (low->high) do esqueleto zigzag(6), causal (conf<=t)."""
    k = bisect.bisect_right(PC, t) - 1
    if k < 1:
        return "NO_LEG", None
    # procurar o último HIGH confirmado <=t e o LOW imediatamente anterior (origem da up-leg)
    ih = None
    for j in range(k, 0, -1):
        if PIVS[j][1] == "H":
            ih = j; break
    if ih is None or ih == 0:
        return "NO_LEG", None
    # o pivot anterior ao high é um low (alternam)
    il = ih - 1
    if PIVS[il][1] != "L":
        return "NO_LEG", None
    orig = PIVS[il][2]; peak = PIVS[ih][2]
    if peak <= orig:
        return "NO_LEG", None
    pos = (ev_low - orig) / (peak - orig)
    if pos < 0:
        return "BROKEN", round(pos, 3)
    if pos > 1.05:
        return "ABOVE", round(pos, 3)
    return ("BOTTOM" if pos < 0.33 else "TOP" if pos > 0.66 else "MIDDLE"), round(pos, 3)


def main():
    print(f"pivôs zigzag(6): {len(PIVS)} ({len(HI6)}H + {len(LO6)}L)", flush=True)
    S = load_series(blocks()); T, L, N = S["T"], S["L"], S["N"]
    tab = {}
    with open(RES / "a1a2_bucket_table.csv") as fh:
        for r in csv.DictReader(fh):
            tab[int(r["t"])] = (r["kind"], r["family_label"])
    FEATS = ["depth", "reclaim", "decel", "contract", "llcount"]
    events = []
    for p in range(M_FRAC, N - M_FRAC):
        if not _is_swinglow(L, p, M_FRAC):
            continue
        info = tab.get(T[p])
        if not info or info[1] not in BUCKET:
            continue
        fv = feats(S, {}, p, "fix48")
        if not fv:
            continue
        reg, pos = zzleg_region(int(T[p]), L[p])
        events.append({"t": T[p], "kind": info[0], "zzregion": reg, "zzpos": pos,
                       **{k: fv[k] for k in FEATS}})
    with open(RES / "a1a2_zzregion_table.csv", "w", newline="") as fh:
        cols = ["t", "kind", "zzregion", "zzpos"] + FEATS
        w = csv.writer(fh); w.writerow(cols)
        for e in events:
            w.writerow([e[c] for c in cols])

    pos = [e for e in events if e["kind"] in ("GT_A1", "GT_A2")]
    neg = [e for e in events if e["kind"] == "CAND"]
    base = len(pos) / (len(pos) + len(neg))
    print(f"\n=== STAGE 3b-v2 — LEG APROVADA zigzag(6) ===")
    print(f"positivos={len(pos)} · negativos={len(neg)} · base={100*base:.2f}%")
    from collections import Counter
    def dist(evs):
        c = Counter(e["zzregion"] for e in evs); n = len(evs) or 1
        return {k: f"{v}({100*v/n:.0f}%)" for k, v in c.most_common()}
    print(f"[zzregion] GT: {dist(pos)}")
    print(f"[zzregion] CAND: {dist(neg)}")

    print("\n(1) PRECISÃO/RECALL por zzregion (lift vs base):")
    gc = Counter(e["zzregion"] for e in pos); nc = Counter(e["zzregion"] for e in neg)
    for rg in ("BOTTOM", "MIDDLE", "TOP", "BROKEN", "ABOVE", "NO_LEG"):
        tot = gc[rg] + nc[rg]
        if tot:
            print(f"  {rg:8} GT {gc[rg]:2}/{tot:4}  precisão {100*gc[rg]/tot:.1f}% (lift {(gc[rg]/tot)/base:.1f}x)  recall {100*gc[rg]/len(pos):.0f}%")

    print("\n(2) PROFUNDIDADE-CONTROLADA — AUC zzpos e reclaim dentro de quartis de depth:")
    alld = sorted(e["depth"] for e in events)
    q = [alld[int(len(alld) * f)] for f in (0.25, 0.5, 0.75)]
    def qz(d): return 0 if d < q[0] else 1 if d < q[1] else 2 if d < q[2] else 3
    for qi in range(4):
        pp = [e for e in pos if qz(e["depth"]) == qi]; nn = [e for e in neg if qz(e["depth"]) == qi]
        if len(pp) < 3 or len(nn) < 10:
            print(f"  Q{qi}: n_pos={len(pp)} (poucos)"); continue
        zp = [e["zzpos"] for e in pp if e["zzpos"] is not None]; zn = [e["zzpos"] for e in nn if e["zzpos"] is not None]
        rp = [e["reclaim"] for e in pp]; rn = [e["reclaim"] for e in nn]
        print(f"  Q{qi} (n_pos={len(pp)}): AUC zzpos={auc(zp,zn) if zp and zn else 0.5:.3f} · AUC reclaim={auc(rp,rn):.3f}")

    print("\n(3) CONVERGÊNCIA (zzregion∈BOTTOM/MIDDLE ∧ reclaim≥medGT ∧ depth≥medGT):")
    med_rc = st.median([e["reclaim"] for e in pos]); med_dp = st.median([e["depth"] for e in pos])
    def sig(e, reg=True, rc=True, dp=True, mrc=None, mdp=None):
        mrc = med_rc if mrc is None else mrc; mdp = med_dp if mdp is None else mdp
        ok = True
        if reg: ok = ok and e["zzregion"] in ("BOTTOM", "MIDDLE")
        if rc: ok = ok and e["reclaim"] >= mrc
        if dp: ok = ok and e["depth"] >= mdp
        return ok
    for lbl, kw in [("região só", dict(rc=False, dp=False)), ("+reclaim", dict(dp=False)), ("+reclaim+depth", dict())]:
        gp = sum(1 for e in pos if sig(e, **kw)); nv = sum(1 for e in neg if sig(e, **kw)); tot = gp + nv
        if tot:
            print(f"  {lbl:16} GT {gp:2}/{tot:4} precisão {100*gp/tot:.1f}% (lift {(gp/tot)/base:.1f}x) recall {100*gp/len(pos):.0f}%")

    print("\n(4) JACKKNIFE OUT-OF-FOLD por semestre (refit thresholds no treino):")
    import datetime as dt
    def sem(t): d = dt.datetime.utcfromtimestamp(int(t)); return f"{d.year}H{1 if d.month<=6 else 2}"
    for drop in sorted(set(sem(e["t"]) for e in pos)):
        pp = [e for e in pos if sem(e["t"]) != drop]; tp = [e for e in pos if sem(e["t"]) == drop]
        tn = [e for e in neg if sem(e["t"]) == drop]
        mrc = st.median([e["reclaim"] for e in pp]); mdp = st.median([e["depth"] for e in pp])
        gp = sum(1 for e in tp if sig(e, mrc=mrc, mdp=mdp)); nv = sum(1 for e in tn if sig(e, mrc=mrc, mdp=mdp)); tot = gp + nv
        b2 = len(tp) / (len(tp) + len(tn)) if (tp or tn) else 0
        print(f"  teste={drop}: GT {gp}/{tot} precisão {100*gp/tot if tot else 0:.1f}% (lift {(gp/tot)/b2 if tot and b2 else 0:.1f}x) recall {100*gp/max(1,len(tp)):.0f}% (n_pos={len(tp)})")


if __name__ == "__main__":
    main()
