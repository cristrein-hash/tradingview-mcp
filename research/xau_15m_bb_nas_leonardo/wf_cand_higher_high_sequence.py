#!/usr/bin/env python3
"""CAND: SEQUENCIA DE HIGHER-HIGHS causal (escada de markup viva).
Usa SO swings confirmados ate j (causal_swings_upto). Verifica se os ultimos
swing-highs formam higher-highs (ascendente). MANTEM onde a sequencia esta ascendente;
CORTA onde um lower-high ja se formou (topo/quebra de estrutura).

Causalidade: causal_swings_upto(j) devolve so swings com conf_bar<=j. Nenhuma barra
> j entra na feature. Nao usa e['out'] na decisao. Feature = trajetoria multi-barra
(sequencia dos ultimos highs), nao snapshot.
"""
import sys
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import ENTRIES, score, causal_swings_upto

def last_highs(j, k=3):
    """ultimos k swing-highs CONFIRMADOS ate j, em ordem temporal (idx crescente)."""
    sw = causal_swings_upto(j)
    highs = [(idx, pr) for (tp, idx, pr, ci) in sw if tp == "H"]
    highs.sort(key=lambda x: x[0])
    return highs[-k:]

def ascending(hs):
    """True se a sequencia de precos dos highs e estritamente ascendente."""
    if len(hs) < 2:
        return None  # indeterminado
    prs = [p for _, p in hs]
    return all(prs[m] > prs[m-1] for m in range(1, len(prs)))

variants = {
    # (k highs olhados, politica p/ indeterminado <2 highs)
    "HH2_keepindet": (2, True),
    "HH2_cutindet":  (2, False),
    "HH3_keepindet": (3, True),
    "HH3_cutindet":  (3, False),
    "HH_lastpair":   (2, True),   # so o ultimo par
}

print("base score:", score([e["n"] for e in ENTRIES]))
print()
results = {}
for name, (k, keep_indet) in variants.items():
    keep = set()
    for e in ENTRIES:
        hs = last_highs(e["j"], k=k)
        asc = ascending(hs)
        if asc is None:
            if keep_indet:
                keep.add(e["n"])
        elif asc:
            keep.add(e["n"])
    sc = score(keep)
    results[name] = (keep, sc)
    print(f"=== {name} (k={k}, keep_indet={keep_indet}) ===")
    print(sc)
    print()

# escolhe melhor: hit3r alto & poison<0.9 & ambos anos+ & N>=20
def ok(sc):
    if sc["N_kept"] < 20: return False
    if sc["poison_ratio"] >= 0.9: return False
    y25 = int(sc["y2025"].split("/")[0]); y25n = int(sc["y2025"].split("/")[1])
    y26 = int(sc["y2026"].split("/")[0]); y26n = int(sc["y2026"].split("/")[1])
    # ambos anos positivos = hit-rate > 0 e (idealmente) acima da base; exigimos winners>0 em ambos
    if y25n > 0 and y25 == 0: return False
    if y26n > 0 and y26 == 0: return False
    return True

cands = [(n, sc) for n, (keep, sc) in results.items() if ok(sc)]
cands.sort(key=lambda x: (x[1]["hit3r_kept"], -x[1]["poison_ratio"]), reverse=True)
print("### CANDIDATOS que passam gate:", [c[0] for c in cands])
if cands:
    best = cands[0][0]
    keep, sc = results[best]
    print(f"### MELHOR = {best}")
    print("score:", sc)
    print("keep_ns:", sorted(keep))
else:
    print("### NENHUM passa gate. Reportando o de menor poison com N>=20:")
    fb = sorted([(sc["poison_ratio"], n) for n, (keep, sc) in results.items() if sc["N_kept"] >= 20])
    if fb:
        best = fb[0][1]; keep, sc = results[best]
        print(f"### FALLBACK = {best}")
        print("score:", sc)
        print("keep_ns:", sorted(keep))
