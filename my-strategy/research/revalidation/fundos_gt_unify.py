#!/usr/bin/env python3
"""GT ÚNICO DE FUNDOS — unificação (regras Cris 2026-07-14):
 1. União notas 'VELA DE FUNDO' ∪ círculos, menos os 4 INVALIDO.
 2. PRIORIDADE À VELA: onde há vela E círculo (mesmo fundo, <=MERGE_W), fica a VELA (t/preço da vela).
 3. FUNDO SÓ-CÍRCULO: buscar a VELA MAIS BAIXA da região (menor low 15M em ±SNAP_R do círculo) =
    o fundo real.
 4. Discriminar cada fundo em classe A/B/C pelo stack (macro 1D + leg 4H v3, causal):
    A = pullback/AC em BULL (long limpo) · B = fundo de RANGE · C = contra-macro em BEAR (separado).
RAW 15M = raw_replay/XAUUSD/15M no HD externo (fonte canónica, dataset_registry). Causal p/ tags."""
import sys, json, gzip, glob, bisect, datetime as dt
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import macro_structural_v3 as M
import leg_v3 as LV

CAT = Path("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/results/catalog_manual_tags_20260707.json")
RAW15_DIR = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
INV_TOL = 4 * 3600        # remover nota/círculo a <=4h de um INVALIDO
MERGE_W = 12 * 3600       # círculo a <=12h de uma vela = mesmo fundo => fica a vela
SNAP_R = 6 * 3600         # fundo só-círculo: menor low 15M em ±6h
BAR4 = 14400
ds = lambda t: dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M")

# --- RAW 15M do HD (snapshots de replay: extrair só o array `ohlcv` por substring — flat, rápido;
#     reconstruir a série por dedup de time). Só ficheiros que cobrem o range dos fundos (2025+). ---
def load_15m():
    import sys as _s; _s.path.insert(0, "/Users/cristrein/tradingview-mcp/my-strategy/core"); import raw_reader as RR
    files = [f for f in sorted(glob.glob(str(RAW15_DIR / "*.jsonl.gz"))) if "2024-" not in Path(f).name]
    bars = RR.series_flat(files, merge=False)     # keep-first; formato original (low,high,close) = [2],[1],[3] de [o,h,l,c]
    T = sorted(bars)
    return T, [bars[t][2] for t in T], [bars[t][1] for t in T], [bars[t][3] for t in T], len(files)
T15, L15, H15, C15, NF = load_15m()

def lowest_in_region(t, r=SNAP_R):
    i0 = bisect.bisect_left(T15, t - r); i1 = bisect.bisect_right(T15, t + r)
    if i1 <= i0: return t, None
    seg = range(i0, i1)
    k = min(seg, key=lambda j: L15[j] if L15[j] is not None else 9e9)
    return T15[k], L15[k]

# --- stack causal (macro 1D + leg 4H v3) ---
_lab1d = M.build_layer1(); _T1 = M.T; _KN1 = [t + 86400 for t in _T1]
def macro_at(t):
    j = bisect.bisect_right(_KN1, t) - 1
    return _lab1d[j] if j >= 0 else None
_v3 = LV.build_leg_v3(); _lc = [r["t"] + BAR4 for r in _v3]
def leg_at(t):
    i = bisect.bisect_right(_lc, t) - 1
    return _v3[i].get("leg", "?") if i >= 0 else "?"
def klass(mac, leg):
    if mac == "BULL": return "A"          # long limpo (pullback/AC/impulso em bull)
    if mac == "RANGE": return "B"         # fundo de range
    if mac == "BEAR": return "C"          # contra-macro (separado)
    return "?"

def main():
    cat = json.load(open(CAT))
    NOTES = cat["notes"]["FUNDO"]; CIR = cat["circles"]; INV = [x["t"] for x in cat["notes"]["INVALIDO"]]
    print(f"RAW 15M: {NF} blocos · N={len(T15)} barras · {ds(T15[0])} -> {ds(T15[-1])}")
    def near_inv(t): return any(abs(t - v) <= INV_TOL for v in INV)
    # 1) velas (mantêm-se; removendo perto de INVALIDO)
    velas = [{"t": x["t"], "price": x["price"], "src": "vela"} for x in NOTES if not near_inv(x["t"])]
    vts = sorted(v["t"] for v in velas)
    # 2) círculos: perto de vela => descartar; senão snap ao menor low da região
    circ_only = []
    for c in CIR:
        t = c["t"]
        if near_inv(t): continue
        if any(abs(t - vt) <= MERGE_W for vt in vts): continue     # vela cobre => prioridade à vela
        st, sl = lowest_in_region(t)
        circ_only.append({"t": st, "price": sl if sl is not None else c.get("price"),
                          "src": "circulo->low", "orig": t})
    # dedup círculos-only entre si (mesmo low <=1 barra 15M)
    circ_only.sort(key=lambda r: r["t"]); dedup = []
    for r in circ_only:
        if dedup and abs(r["t"] - dedup[-1]["t"]) <= 900: continue
        dedup.append(r)
    fundos = velas + dedup
    fundos.sort(key=lambda r: r["t"])
    # 3) tag A/B/C
    for r in fundos:
        r["macro"] = macro_at(r["t"]); r["leg"] = leg_at(r["t"]); r["classe"] = klass(r["macro"], r["leg"])
    # --- relatório ---
    print(f"\nUNIFICAÇÃO: {len(velas)} velas + {len(dedup)} círculos-só (de {len(CIR)}) = {len(fundos)} fundos "
          f"(removidos perto de INVALIDO; círculos perto de vela descartados por prioridade)")
    print(f"  {'#':>2} {'data':16} {'preço':>8} {'src':12} {'MACRO':6} {'LEG':14} {'cl'}")
    for i, r in enumerate(fundos, 1):
        print(f"  {i:2d} {ds(r['t']):16} {r['price']:8.1f} {r['src']:12} {str(r['macro']):6} {r['leg']:14} {r['classe']}")
    kc = Counter(r["classe"] for r in fundos); n = len(fundos) or 1
    print(f"\n  CLASSES: " + " · ".join(f"{k} {kc[k]} ({100*kc[k]/n:.0f}%)" for k in ("A", "B", "C")))
    print(f"    A = pullback/AC em BULL (long limpo) · B = fundo de RANGE · C = contra-macro BEAR (separado)")
    # salvar GT único
    out = {"built": "2026-07-14", "rule": "velas>circulos; circulo-only=menor-low-15M-±6h; -INVALIDO",
           "raw15_source": "HD raw_replay/XAUUSD/15M", "n": len(fundos),
           "classes": {k: kc[k] for k in ("A", "B", "C")},
           "fundos": [{"t": r["t"], "date": ds(r["t"]), "price": round(r["price"], 2), "src": r["src"],
                       "macro": r["macro"], "leg": r["leg"], "classe": r["classe"]} for r in fundos]}
    outp = HERE / "results" / "REGIME_GT_FUNDOS_UNIFIED_20260714.json"
    outp.parent.mkdir(exist_ok=True)
    json.dump(out, open(outp, "w"), ensure_ascii=False, indent=1)
    print(f"\n  GT único salvo: {outp.relative_to(HERE)}")

if __name__ == "__main__":
    main()
