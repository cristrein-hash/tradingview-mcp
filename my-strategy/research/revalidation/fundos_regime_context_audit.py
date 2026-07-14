#!/usr/bin/env python3
"""AUDITORIA COMPARATIVA: contexto de REGIME dos fundos do Cris nos 2 conjuntos (42 notas
"VELA DE FUNDO" vs 50 círculos) sob o STACK COMPLETO — macro 1D (Layer1) + leg 4H v3. Objetivo:
ver se os 2 conjuntos vivem em REGIÕES macro+leg diferentes (=> categorias distintas) ou iguais
(=> mesmo fenómeno). Alinhamento CAUSAL: macro = rótulo 1D conhecido ao fecho <= t; leg = último
bar 4H COMPLETO (close <= t). Sem lookahead. RAW: macro/leg = stack aprovado; fundos = marcas Cris."""
import sys, json, bisect, datetime as dt
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import macro_structural_v3 as M
import leg_v3 as LV

CAT = Path("/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/results/catalog_manual_tags_20260707.json")
cat = json.load(open(CAT))
NOTES = cat["notes"]["FUNDO"]          # 42 "VELA DE FUNDO"
CIRCLES = cat["circles"]               # 50 círculos
BAR4 = 14400
ds = lambda t: dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M")

# macro 1D causal
_lab1d = M.build_layer1(); _T1 = M.T; _KN1 = [t + 86400 for t in _T1]
def macro_at(t):
    j = bisect.bisect_right(_KN1, t) - 1
    return _lab1d[j] if j >= 0 else None
def macro_block(t):
    """(início_do_bloco_macro, dias_dentro) causal."""
    j = bisect.bisect_right(_KN1, t) - 1
    if j < 0: return None, None
    reg = _lab1d[j]; k = j
    while k > 0 and _lab1d[k - 1] == reg: k -= 1
    return _T1[k], round((t - _T1[k]) / 86400, 0)

# leg 4H v3 causal (último bar COMPLETO)
_v3 = LV.build_leg_v3()
_lc = [r["t"] + BAR4 for r in _v3]         # tempo de FECHO de cada bar 4H
def leg_at(t):
    i = bisect.bisect_right(_lc, t) - 1
    return _v3[i] if i >= 0 else {}

def ctx_tag(mac, leg):
    if mac == "BULL":
        if leg in ("PULLBACK_BEAR", "ACUMULACAO"): return "pullback/AC-em-BULL (long limpo)"
        if leg == "IMPULSO_UP": return "meio-de-impulso-BULL"
        return f"BULL+{leg}"
    if mac == "BEAR": return f"contra-macro (fundo em BEAR/{leg})"
    if mac == "RANGE": return f"fundo-de-RANGE ({leg})"
    return f"{mac}+{leg}"

def analyse(name, items):
    rows = []
    for x in items:
        t = x["t"]; mac = macro_at(t); lg = leg_at(t)
        leg = lg.get("leg", "?"); ld = lg.get("leg_dir")
        b0, din = macro_block(t)
        rows.append({"t": t, "price": x.get("price"), "macro": mac, "leg": leg, "dir": ld,
                     "din": din, "tag": ctx_tag(mac, leg)})
    rows.sort(key=lambda r: r["t"])
    print(f"\n{'='*90}\n{name} — N={len(rows)}  ({ds(rows[0]['t'])} -> {ds(rows[-1]['t'])})\n{'='*90}")
    # per-fundo compacto
    print(f"  {'#':>2} {'data':16} {'preço':>8} {'MACRO':6} {'dias':>4} {'LEG(4Hv3)':14} {'dir':4} contexto")
    for i, r in enumerate(rows, 1):
        print(f"  {i:2d} {ds(r['t']):16} {r['price']:8.1f} {str(r['macro']):6} {str(r['din']):>4} "
              f"{r['leg']:14} {str(r['dir']):4} {r['tag']}")
    # agregados
    mc = Counter(r["macro"] for r in rows); n = len(rows) or 1
    lc = Counter(r["leg"] for r in rows)
    print(f"  --- MACRO: " + " · ".join(f"{k} {100*v/n:.0f}%" for k, v in mc.most_common()))
    print(f"  --- LEG:   " + " · ".join(f"{k} {100*v/n:.0f}%" for k, v in lc.most_common()))
    return rows, mc, lc

def main():
    print("AUDITORIA COMPARATIVA DE FUNDOS × REGIME (stack macro 1D + leg 4H v3, causal)")
    rN, mcN, lcN = analyse("CONJUNTO A — 42 NOTAS 'VELA DE FUNDO'", NOTES)
    rC, mcC, lcC = analyse("CONJUNTO B — 50 CÍRCULOS", CIRCLES)
    # comparação lado-a-lado
    print(f"\n{'='*90}\nCOMPARAÇÃO (o que decide se são a MESMA coisa ou categorias distintas)\n{'='*90}")
    nN, nC = len(rN) or 1, len(rC) or 1
    print(f"  {'MACRO':8} {'notas%':>8} {'círculos%':>10}")
    for reg in ("BULL", "BEAR", "RANGE"):
        print(f"  {reg:8} {100*mcN[reg]/nN:8.0f} {100*mcC[reg]/nC:10.0f}")
    print(f"\n  {'LEG':16} {'notas%':>8} {'círculos%':>10}")
    for leg in sorted(set(lcN) | set(lcC)):
        print(f"  {leg:16} {100*lcN[leg]/nN:8.0f} {100*lcC[leg]/nC:10.0f}")
    # veredito heurístico de similaridade (distância L1 das distribuições macro)
    l1 = sum(abs(mcN[r]/nN - mcC[r]/nC) for r in ("BULL", "BEAR", "RANGE"))
    print(f"\n  distância L1 das distribuições MACRO: {l1:.2f}  "
          f"(~0 = mesmo fenómeno/unir · alto = categorias distintas)")

if __name__ == "__main__":
    main()
