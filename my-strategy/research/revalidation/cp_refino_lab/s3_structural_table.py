#!/usr/bin/env python3
"""STAGE-3 estrutural (protocolo XAU_15M) — tabela causal por candidato Cp: macro_regime + leg_v3 +
leg_age + posição-perna + espaço-abaixo + classe-faca + GT. RAW-first, causal, close-only. SEM P&L novo.
Objetivo ÚNICO deste passo: MEDIR se as 10 facas caem em IMPULSO_DOWN (H1) e quantos WIN/GT seriam mortos
por um gate leg. Reutiliza cp_plot_window (trades) + cp_knife_diag (classe) + leg_v3 (leg/macro 4H).
Mapeamento 15M->4H = bar-close-causal: leg da última barra 4H FECHADA (TS4+14400 <= etime)."""
import sys, bisect, datetime as dt
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
REV = HERE.parent                                   # .../revalidation
LAB = REV / "a1a2_fundo_lab"
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(REV))
import cp_plot_window as CP                          # trades + série 15M (carga pesada 4 blocos)
import cp_knife_diag as KD                           # classify()
import leg_v3, leg_refine_harness as LH             # leg/macro 4H (RAW vivo)

T, H, L, C, N, ATR = CP.T, CP.H, CP.L, CP.C, CP.N, CP.ATR
SLB, sz, BUYS, BT, SELLS, ST = CP.SLB, CP.sz, CP.BUYS, CP.BT, CP.SELLS, CP.ST
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
DUR4 = 14400

# --- leg_v3 4H (bar-close-causal) ---
V3 = leg_v3.build_leg_v3()
TS4 = [r["t"] for r in V3]; LEG = [r["leg"] for r in V3]; MAC = [r.get("macro") for r in V3]
AGE = {r["t"]: LH.BASE_LEG.get(r["t"], {}).get("leg_age") for r in V3}
def leg_at(etime):
    j = bisect.bisect_right(TS4, etime - DUR4) - 1   # última 4H fechada antes de etime
    if j < 0: return (None, None, None)
    return (LEG[j], MAC[j], AGE.get(TS4[j]))

# --- GT = 5 janelas hardcoded do cp_refined (bear2026, marcadas pelo Cris) ---
GT_WIN = [(1770015600, 1770210000), (1770339600, 1771448400), (1774242000, 1774270800),
          (1781128800, 1781128800), (1782781200, 1782907200)]
GT = []
for a, b in GT_WIN:
    aa = bisect.bisect_left(T, min(a, b) - 12*3600); bb = bisect.bisect_right(T, max(a, b) + 12*3600)
    GT.append(T[min(range(aa, bb), key=lambda k: L[k])])
def is_gt(tp): return any(abs(tp - g) < 6*3600 for g in GT)

# --- espaço-estrutural-abaixo (lição L2/BPT): swing-low 15M mais alto ABAIXO do fundo; dist em ATR ---
def space_below(p):
    below = [L[q] for q in SLB if q < p and L[q] < L[p]]
    if not below: return None                        # VAZIO = nada abaixo = máxima sala p/ cair
    nb = max(below); atr = ATR[p] or 5.0
    return round((L[p] - nb) / atr, 2)

# --- reconstruir trades COM p (fundo) e k (entry), regras verbatim do cp_plot_window ---
def trades_with_index():
    out = []
    for p in SLB:
        if not (CP.T_LO <= T[p] <= CP.T_HI): continue
        hb = max(range(max(0, p - CP.LEGWIN), p + 1), key=lambda k: H[k]); atr = ATR[p] or 5.0; dur = max(1, p - hb)
        if (H[hb] - L[p]) / atr < CP.LEGMIN or not (L[p] <= min(L[max(0, p - 192):p + 1]) + 1e-9): continue
        if not (sz(BUYS, BT, T[hb], T[p]) / dur >= 0.25 or sz(SELLS, ST, T[hb], T[p]) >= 180): continue
        e = CP.entry_first(p)
        if not e: continue
        out.append({"p": p, "k": e["k"], "etime": int(T[e["k"]]), "ent": e["ent"], "sl": e["sl"],
                    "tgt": round(e["ent"] + 3 * (e["ent"] - e["sl"]), 2)})
    return out


def main():
    tr = trades_with_index()
    rows = []
    for i, s in enumerate(tr, 1):
        cls, depth = KD.classify(s["etime"], s["ent"], s["sl"], s["tgt"])
        leg, mac, age = leg_at(s["etime"])
        rows.append({"i": i, "fundo": T[s["p"]], "etime": s["etime"], "cls": cls, "depth": depth,
                     "leg": leg, "mac": mac, "age": age, "sb": space_below(s["p"]), "gt": is_gt(T[s["p"]])})
    print(f"N={len(rows)} candidatos Cp (26 esperados). Leg 4H = bar-close-causal (leg_v3).\n")
    hdr = f"{'#':>3} {'entry':<16} {'cls':<5} {'leg_4h':<13} {'macro':<6} {'age':>3} {'sb(ATR)':>8} {'GT':>3}"
    print(hdr); print("-" * len(hdr))
    for r in rows:
        sb = "VAZIO" if r["sb"] is None else f"{r['sb']:.1f}"
        gt = "GT" if r["gt"] else ""
        dep = f" −{r['depth']:.1f}R" if r["cls"] in ("KNIFE", "GRAB") else ""
        print(f"{r['i']:>3} {ds(r['etime']):<16} {r['cls']:<5} {str(r['leg']):<13} {str(r['mac']):<6} "
              f"{str(r['age']):>3} {sb:>8} {gt:>3}{dep}")

    # ---- CROSS-TABS (o que decide H1) ----
    def bucket(pred):
        return {k: sum(1 for r in rows if r["cls"] == k and pred(r)) for k in ("KNIFE", "GRAB", "WIN", "OPEN")}
    print("\n=== CROSS-TAB leg_v3 × classe ===")
    for leg in ("IMPULSO_DOWN", "PULLBACK_BEAR", "ACUMULACAO", "DISTRIBUICAO", "IMPULSO_UP", "PULLBACK_BULL", "None"):
        b = bucket(lambda r, lg=leg: str(r["leg"]) == lg)
        tot = sum(b.values())
        if tot: print(f"  {leg:<14} tot={tot:>2}  KNIFE={b['KNIFE']} GRAB={b['GRAB']} WIN={b['WIN']} OPEN={b['OPEN']}")

    print("\n=== H1 (gate = cortar IMPULSO_DOWN) — impacto ===")
    kn = [r for r in rows if r["cls"] == "KNIFE"]
    kn_id = [r for r in kn if str(r["leg"]) == "IMPULSO_DOWN"]
    win = [r for r in rows if r["cls"] == "WIN"]
    win_id = [r for r in win if str(r["leg"]) == "IMPULSO_DOWN"]
    gt = [r for r in rows if r["gt"]]
    gt_id = [r for r in gt if str(r["leg"]) == "IMPULSO_DOWN"]
    print(f"  facas cortadas por IMPULSO_DOWN: {len(kn_id)}/{len(kn)}  (#: {[r['i'] for r in kn_id]})")
    print(f"  WIN mortos por IMPULSO_DOWN:     {len(win_id)}/{len(win)}  (#: {[r['i'] for r in win_id]})")
    print(f"  GT mortos por IMPULSO_DOWN:      {len(gt_id)}/{len(gt)}   (#: {[r['i'] for r in gt_id]})  <- TEM de ser 0")

    print("\n=== CROSS-TAB MACRO REGIME × classe (engine_4h_regime_gate_RAW) ===")
    for mac in ("BULL", "RANGE", "BEAR", "None"):
        b = bucket(lambda r, mm=mac: str(r["mac"]) == mm)
        tot = sum(b.values()); ng = sum(1 for r in rows if str(r["mac"]) == mac and r["gt"])
        if tot: print(f"  {mac:<6} tot={tot:>2}  KNIFE={b['KNIFE']} GRAB={b['GRAB']} WIN={b['WIN']} OPEN={b['OPEN']}  GT={ng}")
    print("  --- teste: algum macro ISOLA as facas? ---")
    for mac in ("BULL", "RANGE", "BEAR"):
        kn = sum(1 for r in rows if str(r["mac"]) == mac and r["cls"] == "KNIFE")
        good = sum(1 for r in rows if str(r["mac"]) == mac and (r["cls"] == "WIN" or r["gt"]))
        print(f"  {mac:<6}: facas={kn}  WIN/GT={good}  -> {'faca minoria' if good >= kn else 'faca maioria'}")
    kn_bear = sum(1 for r in rows if str(r["mac"]) == "BEAR" and r["cls"] == "KNIFE")
    gt_bear = sum(1 for r in rows if str(r["mac"]) == "BEAR" and r["gt"])
    gt_tot = sum(1 for r in rows if r["gt"])
    print(f"  GATE 'só BEAR': mantém GT {gt_bear}/{gt_tot} mas mantém {kn_bear}/10 facas | GATE 'fora BEAR' mata {gt_bear}/{gt_tot} GT")

    print("\n=== espaço-abaixo (H4) × classe ===  (VAZIO ou grande = sala p/ cair)")
    for r in sorted(rows, key=lambda x: (-1 if x["sb"] is None else x["sb"])):
        if r["cls"] in ("KNIFE", "WIN", "GRAB"):
            sb = "VAZIO" if r["sb"] is None else f"{r['sb']:.1f}"
            print(f"  #{r['i']:>2} {r['cls']:<5} sb={sb:>6} {'GT' if r['gt'] else ''}")


if __name__ == "__main__":
    main()
