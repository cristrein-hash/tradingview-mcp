#!/usr/bin/env python3
"""SUB-DISCRIMINAÇÃO do GT único de fundos em CAMADAS DE ENTRY específicas (ordem Cris 2026-07-14:
sub-camadas separadas = assertividade real). Parte de REGIME_GT_FUNDOS_UNIFIED_20260714.json.
 A (long em BULL) -> A1 pullback FUNDO (leg ACUMULACAO/PULLBACK_BEAR = correção mais profunda)
                     A2 pullback RASO em impulso (leg IMPULSO_UP = continuação de momentum)
 B fundo de RANGE (mantém)
 C (BEAR) -> C_DEEP capitulação PROFUNDA (o que vale pegar) · C_SHALLOW bounce raso (à parte)
Profundidade CAUSAL do fundo (1D): dd252 = queda do topo móvel 252d até ao PREÇO do fundo;
pull20 = queda do topo dos últimos 20 dias. Sem lookahead. RAW: preço do fundo = low 15M do GT."""
import sys, json, bisect, datetime as dt
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import macro_structural_v3 as M

GT = json.load(open(HERE / "results" / "REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
T1, H1, C1 = M.T, M.H, M.C; KN1 = [t + 86400 for t in T1]
ds = lambda t: dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")

def depth(t, price):
    j = bisect.bisect_right(KN1, t) - 1
    if j < 252: return None, None
    hi252 = max(H1[j - 252:j + 1]); hi20 = max(H1[j - 20:j + 1])
    return round((hi252 - price) / hi252 * 100, 1), round((hi20 - price) / hi20 * 100, 1)

# threshold de capitulação profunda (C): mediana das dd252 dos fundos C como corte natural
Cdds = []
for f in GT["fundos"]:
    if f["classe"] == "C":
        dd, _ = depth(f["t"], f["price"]);  Cdds.append((f, dd))
Cvals = sorted(x[1] for x in Cdds if x[1] is not None)
C_THR = Cvals[len(Cvals) // 2] if Cvals else 8.0        # (legado, não usado)
PANIC_PULL20 = 18.0     # capitulação AGUDA: queda >=18% do topo 20d (pânico rápido/recente)
GRIND_DD = 25.0         # fundo PROFUNDO lento: drawdown 252d >=25% (esgotamento, pull20 baixo)

def subclass(f, dd, pull20):
    m, leg = f["macro"], f["leg"]
    if m == "BULL":
        return "A1_pullback_fundo" if leg in ("ACUMULACAO", "PULLBACK_BEAR") else "A2_pullback_raso"
    if m == "RANGE":
        return "B_range"
    if m == "BEAR":
        # Cris 2026-07-14: DUAS subcamadas profundas SEPARADAS + shallow à parte.
        # C_PANIC = capitulação AGUDA (queda rápida/recente: pull20 alto).
        # C_GRIND = fundo PROFUNDO mas lento (dd252 muito alto, pull20 baixo).
        if pull20 is not None and pull20 >= PANIC_PULL20: return "C_PANIC_aguda"
        if dd is not None and dd >= GRIND_DD: return "C_GRIND_profundo"
        return "C_shallow_bounce"
    return "?"

def main():
    print(f"SUB-DISCRIMINAÇÃO do GT único ({GT['n']} fundos) · corte C_DEEP dd252>={C_THR}% (mediana C)")
    print(f"  {'#':>2} {'data':11} {'preço':>7} {'MACRO':6} {'LEG':14} {'dd252':>6} {'pull20':>6} SUBCLASSE")
    rows = []
    for i, f in enumerate(sorted(GT["fundos"], key=lambda x: x["t"]), 1):
        dd, p20 = depth(f["t"], f["price"]); sc = subclass(f, dd, p20)
        f2 = dict(f); f2["dd252"] = dd; f2["pull20"] = p20; f2["subclasse"] = sc; rows.append(f2)
        print(f"  {i:2d} {ds(f['t']):11} {f['price']:7.0f} {f['macro']:6} {f['leg']:14} "
              f"{str(dd):>6} {str(p20):>6} {sc}")
    cc = Counter(r["subclasse"] for r in rows); n = len(rows)
    print("\n  CAMADAS DE ENTRY (candidatas):")
    for k in ("A1_pullback_fundo", "A2_pullback_raso", "B_range",
              "C_PANIC_aguda", "C_GRIND_profundo", "C_shallow_bounce"):
        print(f"    {k:22} {cc[k]:2d} ({100*cc[k]/n:.0f}%)")
    # detalhe C ordenado por profundidade (para validar os cortes)
    print(f"\n  CLASSE C ordenada por dd252: [PANIC pull20>={PANIC_PULL20} · GRIND dd252>={GRIND_DD}]")
    for r in sorted([r for r in rows if r["classe"] == "C"], key=lambda r: -(r["dd252"] or 0)):
        print(f"    {ds(r['t'])} {r['price']:.0f}  dd252 {r['dd252']}%  pull20 {r['pull20']}%  -> {r['subclasse']}")
    out = dict(GT); out["subdiscriminated"] = "2026-07-14"; out["C_deep_thr_dd252"] = C_THR
    out["fundos"] = rows
    outp = HERE / "results" / "REGIME_GT_FUNDOS_UNIFIED_20260714.json"
    json.dump(out, open(outp, "w"), ensure_ascii=False, indent=1)
    print(f"\n  GT enriquecido (subclasse) salvo: {outp.relative_to(HERE)}")

if __name__ == "__main__":
    main()
