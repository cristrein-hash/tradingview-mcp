#!/usr/bin/env python3
"""A1A2_FUNDO_LAB · Stage 3b/4c — CONTEXTO DE REGIÃO (regime v5 + leg 4H TOP/MIDDLE/BOTTOM) + re-medição.
Enriquece cada evento com: regime_v5 (engine_4h_regime_gate_RAW, hour-causal, 100% RAW) + leg4h_region
(posição do low do pullback dentro da leg BULL 4H corrente: BOTTOM<0.33 / MIDDLE / TOP>0.66 / BROKEN / NO_LEG).
Depois responde (Cris 2026-07-17): (1) a região separa GT vs CAND? (2) a região ADICIONA além da depth
(profundidade-controlada)? (3) convergência depth×região×reclaim dá precisão >> base? (4) jackknife semestre.
depth = sinal legítimo a priori (ordem Cris). Causal, RAW-first. py3.9 stdlib.
Output: results/a1a2_region_table.csv + stdout.
"""
import sys, json, csv, bisect, random, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from a1_causal_entry import load_series, _is_swinglow, M_FRAC
sys.path.insert(0, str(HERE))
from s2b_seq_features import feats, auc, perm_p, blocks, BUCKET
import importlib
REG = importlib.import_module("engine_4h_regime_gate_RAW")   # regime_at(t) hour-causal RAW
RES = HERE / "results"
random.seed(20260717)

# --- swings fractais 4H (m=3) do RAW 4H (mesmos bars do detetor) ---
B4 = REG.B4
T4 = [b["t"] for b in B4]; H4 = [b["h"] for b in B4]; L4 = [b["l"] for b in B4]
M4 = 3


BAR4 = 14400
def swings4h():
    # CAUSAL FIX (DA 2026-07-17): o pivot fractal m=3 só é conhecido no FECHO da barra confirmadora q+3
    # = T4[q+3]+BAR4 (o t do RAW é a ABERTURA). Espelha o ovr_at −dur do engine_4h_regime_gate_RAW.
    hi = []; lo = []
    for q in range(M4, len(B4) - M4):
        if H4[q] == max(H4[q - M4:q + M4 + 1]) and H4[q] > max(H4[q - M4:q]):
            hi.append((T4[q + M4] + BAR4, T4[q], H4[q]))   # (confirm_close_t, pivot_t, price)
        if L4[q] == min(L4[q - M4:q + M4 + 1]) and L4[q] < min(L4[q - M4:q]):
            lo.append((T4[q + M4] + BAR4, T4[q], L4[q]))
    return hi, lo


HI4, LO4 = swings4h()
HIC = [x[0] for x in HI4]; LOC = [x[0] for x in LO4]


def leg4h_region(t, ev_low):
    """Região do low do pullback na leg BULL 4H corrente (pivots confirmados <= t)."""
    ih = bisect.bisect_right(HIC, t) - 1
    il = bisect.bisect_right(LOC, t) - 1
    if ih < 0 or il < 0:
        return "NO_LEG", None
    peak_t, _, peak_p = HI4[ih]; orig_t, _, orig_p = LO4[il]
    if peak_t <= orig_t or peak_p <= orig_p:      # último confirmado é um low (a cair) ou leg inválida
        return "NO_LEG", None
    span = peak_p - orig_p
    pos = (ev_low - orig_p) / span
    if pos < 0:
        return "BROKEN", round(pos, 3)             # furou a base da leg (faca)
    if pos > 1.05:
        return "ABOVE", round(pos, 3)
    reg = "BOTTOM" if pos < 0.33 else ("TOP" if pos > 0.66 else "MIDDLE")
    return reg, round(pos, 3)


def main():
    print("load 15M + bucket + regime RAW...", flush=True)
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
        fv = feats(S, json.load(open(RES / "bubble_map.json")) if False else {}, p, "fix48") if False else None
        # feats precisa do bubble map só p/ H1; aqui usamos só H2 -> passar {} (H1 vira 0, ignoramos)
        fv = feats(S, {}, p, "fix48")
        if not fv:
            continue
        reg5 = REG.regime_at(int(T[p]))
        legreg, legpos = leg4h_region(int(T[p]), L[p])
        events.append({"t": T[p], "kind": info[0], "regime_v5": reg5, "leg4h_region": legreg,
                       "leg4h_pos": legpos, **{k: fv[k] for k in FEATS}})
    # escrever tabela
    with open(RES / "a1a2_region_table.csv", "w", newline="") as fh:
        cols = ["t", "kind", "regime_v5", "leg4h_region", "leg4h_pos"] + FEATS
        w = csv.writer(fh); w.writerow(cols)
        for e in events:
            w.writerow([e[c] for c in cols])

    pos = [e for e in events if e["kind"] in ("GT_A1", "GT_A2")]
    neg = [e for e in events if e["kind"] == "CAND"]
    base = len(pos) / (len(pos) + len(neg))
    print(f"\n=== STAGE 3b — REGIÃO + CONTEXTO (macro-BULL bucket) ===")
    print(f"positivos={len(pos)} · negativos={len(neg)} · base rate={100*base:.2f}%")

    def dist(evs, key):
        from collections import Counter
        c = Counter(str(e[key]) for e in evs); n = len(evs) or 1
        return {k: f"{v}({100*v/n:.0f}%)" for k, v in c.most_common()}
    print(f"\n[regime_v5] GT: {dist(pos,'regime_v5')}")
    print(f"[regime_v5] CAND: {dist(neg,'regime_v5')}")
    print(f"\n[leg4h_region] GT: {dist(pos,'leg4h_region')}")
    print(f"[leg4h_region] CAND: {dist(neg,'leg4h_region')}")

    # (1) região separa? precisão/recall por região
    print("\n(1) PRECISÃO/RECALL por leg4h_region (lift vs base):")
    from collections import Counter
    gc = Counter(e["leg4h_region"] for e in pos); nc = Counter(e["leg4h_region"] for e in neg)
    for rg in ("BOTTOM", "MIDDLE", "TOP", "BROKEN", "ABOVE", "NO_LEG"):
        tot = gc[rg] + nc[rg]
        if tot == 0:
            continue
        prec = gc[rg] / tot; rec = gc[rg] / len(pos)
        print(f"  {rg:8} GT {gc[rg]:2}/{tot:4}  precisão {100*prec:.1f}% (lift {prec/base:.1f}x)  recall {100*rec:.0f}%")

    # (2) depth-controlled: dentro de quartis de depth, região/reclaim ainda separam?
    print("\n(2) PROFUNDIDADE-CONTROLADA — AUC de leg4h_pos e reclaim dentro de quartis de depth:")
    alld = sorted(e["depth"] for e in events)
    q = [alld[int(len(alld) * f)] for f in (0.25, 0.5, 0.75)]
    def qz(d): return 0 if d < q[0] else 1 if d < q[1] else 2 if d < q[2] else 3
    for qi in range(4):
        pp = [e for e in pos if qz(e["depth"]) == qi]; nn = [e for e in neg if qz(e["depth"]) == qi]
        if len(pp) < 3 or len(nn) < 10:
            print(f"  Q{qi} depth: n_pos={len(pp)} (poucos p/ AUC)"); continue
        # leg4h_pos: menor pos = mais fundo na leg = mais GT? testamos AUC (invertendo p/ direção)
        lp_pos = [e["leg4h_pos"] for e in pp if e["leg4h_pos"] is not None]
        lp_neg = [e["leg4h_pos"] for e in nn if e["leg4h_pos"] is not None]
        rc_pos = [e["reclaim"] for e in pp]; rc_neg = [e["reclaim"] for e in nn]
        a_lp = auc(lp_pos, lp_neg) if lp_pos and lp_neg else 0.5
        a_rc = auc(rc_pos, rc_neg)
        print(f"  Q{qi} depth (n_pos={len(pp)}): AUC leg4h_pos={a_lp:.3f} · AUC reclaim={a_rc:.3f}")

    # (3) convergência: BOTTOM/MIDDLE (não TOP/BROKEN) + reclaim>mediana-GT + depth>mediana-GT
    print("\n(3) CONVERGÊNCIA (região válida ∧ reclaim rápido ∧ fundo) — precisão/recall:")
    med_rc = st.median([e["reclaim"] for e in pos]); med_dp = st.median([e["depth"] for e in pos])
    def sig(e, use_reg=True, use_rc=True, use_dp=True, rc=None, dp=None):
        rc = med_rc if rc is None else rc; dp = med_dp if dp is None else dp
        ok = True
        if use_reg: ok = ok and e["leg4h_region"] in ("BOTTOM", "MIDDLE")
        if use_rc: ok = ok and e["reclaim"] >= rc
        if use_dp: ok = ok and e["depth"] >= dp
        return ok
    for label, kw in [("região só", dict(use_rc=False, use_dp=False)),
                      ("região+reclaim", dict(use_dp=False)),
                      ("região+reclaim+depth", dict())]:
        gp = sum(1 for e in pos if sig(e, **kw)); npv = sum(1 for e in neg if sig(e, **kw))
        tot = gp + npv
        if tot:
            print(f"  {label:24} GT {gp:2}/{tot:4}  precisão {100*gp/tot:.1f}% (lift {(gp/tot)/base:.1f}x)  recall {100*gp/len(pos):.0f}%")

    # (4) jackknife por semestre (largar 1 semestre, a convergência aguenta?)
    print("\n(4) JACKKNIFE por semestre (convergência região+reclaim+depth):")
    import datetime as dt
    def sem(t): d = dt.datetime.utcfromtimestamp(int(t)); return f"{d.year}H{1 if d.month<=6 else 2}"
    sems = sorted(set(sem(e["t"]) for e in pos))
    print("  (thresholds REFIT no fold de treino = out-of-fold honesto; avalia no semestre largado)")
    for drop in sems:
        pp = [e for e in pos if sem(e["t"]) != drop]; nn = [e for e in neg if sem(e["t"]) != drop]
        rc_tr = st.median([e["reclaim"] for e in pp]); dp_tr = st.median([e["depth"] for e in pp])
        te_p = [e for e in pos if sem(e["t"]) == drop]; te_n = [e for e in neg if sem(e["t"]) == drop]
        gp = sum(1 for e in te_p if sig(e, rc=rc_tr, dp=dp_tr)); npv = sum(1 for e in te_n if sig(e, rc=rc_tr, dp=dp_tr))
        tot = gp + npv; b2 = len(te_p) / (len(te_p) + len(te_n)) if (te_p or te_n) else 0
        if tot:
            print(f"  teste={drop}: GT {gp}/{tot} precisão {100*gp/tot:.1f}% (lift {(gp/tot)/b2:.1f}x) recall {100*gp/max(1,len(te_p)):.0f}% (n_pos_teste={len(te_p)})")
        else:
            print(f"  teste={drop}: 0 sinais no semestre (n_pos_teste={len(te_p)})")


if __name__ == "__main__":
    main()
