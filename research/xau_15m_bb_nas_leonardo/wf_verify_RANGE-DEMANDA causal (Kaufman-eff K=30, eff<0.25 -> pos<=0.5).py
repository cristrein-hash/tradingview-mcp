#!/usr/bin/env python3
"""VERIFY estrito-causal do candidato RANGE-DEMANDA (Kaufman-eff K=30, eff<0.25 -> pos<=0.5).

Re-implementacao independente. Auditoria de lookahead:
  - janela SOMENTE [j-K, j] (bar j = barra de decisao/entry, close conhecido no momento da decisao).
  - eff (Kaufman efficiency), rlo, rhi, pos: todos derivados dessa janela.
  - ZERO uso de futuro (nada de LO[j:]/HI[j:]/last_t/pivot-por-movimento-futuro/outcome).
  - ASSERTS anti-lookahead: max index tocado <= j sempre.
  - ROBUSTEZ: alem da janela canonica [j-K, j], testo variante [j-K, j-1] (exclui a propria
    barra j) para ver se a separacao depende de incluir a barra de decisao.
"""
import sys
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S, TS, HI, LO, CL, ATR, N, ENTRIES, score

MAX_IDX_SEEN = [-1]

def feats_strict(e, K, include_j=True):
    """Feature estrito-causal. include_j=True -> janela [j-K, j]; False -> [j-K, j-1]."""
    j = e["j"]
    end = j if include_j else j - 1       # ultimo indice tocado
    a = j - K
    if a < 0 or end <= a:
        return None
    # anti-lookahead assert: nada pode ultrapassar j
    assert end <= j, f"LOOKAHEAD: end {end} > j {j}"
    MAX_IDX_SEEN[0] = max(MAX_IDX_SEEN[0], end - j)  # deve ficar <= 0
    diffs = sum(abs(CL[m] - CL[m-1]) for m in range(a+1, end+1))
    net = abs(CL[end] - CL[a])
    eff = net / diffs if diffs > 0 else 1.0
    rlo = min(LO[a:end+1]); rhi = max(HI[a:end+1])
    rng = rhi - rlo
    pos = (e["ent"] - rlo) / rng if rng > 0 else 0.5
    return {"eff": eff, "pos": pos}

def range_demand(K, EFF_THR, POS_THR, include_j=True):
    keep = []
    for e in ENTRIES:
        f = feats_strict(e, K, include_j)
        if f is None:
            keep.append(e["n"]); continue
        if f["eff"] >= EFF_THR:            # trend -> mantem
            keep.append(e["n"])
        elif f["pos"] <= POS_THR:          # range & fundo -> demanda
            keep.append(e["n"])
        # range & topo -> corta
    return keep

def reject_range(K, EFF_THR):
    keep = []
    for e in ENTRIES:
        f = feats_strict(e, K, True)
        if f is None:
            keep.append(e["n"]); continue
        if f["eff"] >= EFF_THR:
            keep.append(e["n"])
    return keep

def show(tag, keep):
    sc = score(keep)
    print(f"{tag:52s} N={sc['N_kept']:2d} hit={sc['hit3r_kept']:.3f} "
          f"pois={sc['poison_ratio']:.2f} Wcut={sc['winners_cut']} Lcut={sc['losers_cut']} "
          f"y25={sc['y2025']} y26={sc['y2026']}")
    return sc

if __name__ == "__main__":
    baseW = sum(e["out"] for e in ENTRIES)
    print(f"BASE: {len(ENTRIES)} entries · {baseW}W/{len(ENTRIES)-baseW}L · hit-3R {baseW/len(ENTRIES):.1%}")
    print("="*130)

    print("--- CANONICO (janela [j-K, j], inclui barra de decisao) ---")
    sc_main = show("range_demand K=30 eff<0.25 pos<=0.50", range_demand(30, 0.25, 0.50, True))
    # varredura de vizinhanca para ver estabilidade
    for K in (20, 30, 40):
        for EFF in (0.25, 0.30):
            for POS in (0.40, 0.50):
                show(f"range_demand K={K} eff<{EFF} pos<={POS}", range_demand(K, EFF, POS, True))

    print("--- REJEITAR RANGE (variante i, referencia) ---")
    for K in (20, 30):
        for EFF in (0.25, 0.30):
            show(f"reject_range K={K} eff>={EFF}", reject_range(K, EFF))

    print("--- ROBUSTEZ: janela [j-K, j-1] (EXCLUI a propria barra de decisao) ---")
    show("range_demand K=30 eff<0.25 pos<=0.50 [no-j]", range_demand(30, 0.25, 0.50, False))

    print("="*130)
    print(f"anti-lookahead check: max(end-j) visto = {MAX_IDX_SEEN[0]} (deve ser <= 0)")
    print("STRICT_MAIN:", sc_main)
