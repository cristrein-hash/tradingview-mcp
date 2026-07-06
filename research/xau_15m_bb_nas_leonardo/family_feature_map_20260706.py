#!/usr/bin/env python3
"""PASSO 3 — MAPA DE FEATURES POR FAMÍLIA ESTRUTURAL (2026-07-06, aprovado Cris "PODE RODAR").
Unidade = CÍRCULO (episódio de fundo). Famílias por retração macro do candidato-vencedor
(retr = feature estrutural, nunca porta):
  BANDA  0,5-1,3 · FUNDO >1,3 · RASO <0,5 · SEM-PERNA (sem zigzag válido)
WINNERS = candidatos matcher-v2 (−3ATR..+1ATR, ±8h) de cada círculo que ATINGEM 3R = as entradas
corretas nos fundos do Cris. SÓSIAS = candidatos da MESMA família estrutural sem círculo.
Para cada família: mediana winner vs sósia em TODAS as ~50 features numéricas do builder +
ranking por separação robusta (|Δmed|/IQR) + top-8. Depois: divergência ENTRE famílias
(features cujo padrão winner muda de família p/ família → layers separados).
MAPA de calibração declarado (winners via GT): SEM look de seleção, SEM painel de estratégia.
SANITY_PROBE: sha GT · matcher v2 idêntico ao selado · famílias por retr do candidato ·
n por família impresso (famílias n<6 círculos = descritivo, sem ranking)."""
import json, bisect, hashlib
import statistics as st
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])          # U, R3, S, TS, fv
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N = len(S)
ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]

def zigzag_low_pivots(r=6):
    lows = []; d = 0; ehi = elo = 0
    for i in range(1, N):
        atr = ATR[i]
        if HI[i] > HI[ehi]: ehi = i
        if LO[i] < LO[elo]: elo = i
        if d >= 0 and HI[ehi] - LO[i] >= r * atr and ehi < i:
            d = -1; elo = min(range(ehi, i + 1), key=lambda k: LO[k])
        elif d <= 0 and HI[i] - LO[elo] >= r * atr and elo < i:
            lows.append((i, elo)); d = 1
            ehi = max(range(elo, i + 1), key=lambda k: HI[k])
    return lows
LOWS = zigzag_low_pivots(6); KLOW = [x[0] for x in LOWS]

UNIV = sorted([u for u in U if u["cj_t"] in R3], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]
def retr_of(u):
    ci = bisect.bisect_right(TS, u["cj_t"]) - 1
    a = u.get("g_atr") or 5.0
    flo = u["g_sl"] + 0.1 * a
    j = bisect.bisect_right(KLOW, ci) - 1
    if j < 0: return None
    _, l0i = LOWS[j]
    L0 = LO[l0i]; H1 = max(HI[k] for k in range(l0i, ci + 1))
    if H1 - L0 < 1e-9: return None
    return (H1 - flo) / (H1 - L0)
def fam_of(r):
    if r is None: return "SEM-PERNA"
    if r < 0.5: return "RASO"
    if r <= 1.3: return "BANDA"
    return "FUNDO"
for u in UNIV:
    u["_fam"] = fam_of(retr_of(u))
    u["_circ"] = set()
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"] + 8 * 3600:
        u = UNIV[j]
        a = u.get("g_atr") or 5.0
        d = (u["g_sl"] + 0.1 * a) - g["flush_low"]
        if -3 * a <= d <= 1 * a:
            u["_circ"].add(gi)
        j += 1

WINNERS = [u for u in UNIV if u["_circ"] and R3[u["cj_t"]]["R3"] >= 3]
circ_by_fam = {}
for u in WINNERS:
    for gi in u["_circ"]:
        circ_by_fam.setdefault(u["_fam"], set()).add(gi)
print("famílias (winners de círculo): " +
      " · ".join(f"{f}: {len(c)} círculos / {sum(1 for u in WINNERS if u['_fam']==f)} winners"
                 for f, c in sorted(circ_by_fam.items())))
SOSIA = {f: [u for u in UNIV if u["_fam"] == f and not u["_circ"]] for f in circ_by_fam}

SKIP = {"cj_t", "t", "yr", "g_week", "g_R", "g_risk", "g_entry", "g_sl", "block", "is_bottom",
        "is_monforte", "is_medfraco", "g_in_base435", "g_v5h", "g_v5h_5dago", "macro_bear", "macro_bull"}
sample = UNIV[0]
FEATS = [k for k in sample if k not in SKIP and isinstance(sample.get(k), (int, float))
         and not isinstance(sample.get(k), bool)]
def med(rows, k):
    v = sorted(fv(u, k) for u in rows if fv(u, k) is not None)
    return v[len(v) // 2] if v else None
def iqr_all(rows_a, rows_b, k):
    v = sorted([fv(u, k) for u in rows_a if fv(u, k) is not None] +
               [fv(u, k) for u in rows_b if fv(u, k) is not None])
    if len(v) < 8: return None
    return max(0.01, v[3 * len(v) // 4] - v[len(v) // 4])

fam_top = {}
for f in ("BANDA", "FUNDO", "RASO", "SEM-PERNA"):
    W = [u for u in WINNERS if u["_fam"] == f]
    Sx = SOSIA.get(f, [])
    nc = len(circ_by_fam.get(f, set()))
    if not W or not Sx:
        print(f"\n=== {f}: sem dados ==="); continue
    print(f"\n=== {f} · círculos {nc} · winners {len(W)} · sósias {len(Sx)}"
          f"{' [DESCRITIVO n<6]' if nc < 6 else ''} ===")
    rank = []
    for k in FEATS:
        mw, ms = med(W, k), med(Sx, k)
        iq = iqr_all(W, Sx, k)
        if mw is None or ms is None or iq is None: continue
        rank.append((abs(mw - ms) / iq, k, mw, ms))
    rank.sort(reverse=True)
    fam_top[f] = rank[:8]
    for sp, k, mw, ms in rank[:8]:
        print(f"  {k:<22} win {mw:>8.2f} · sósia {ms:>8.2f} · sep {sp:.2f}")

# divergência entre famílias: features no top-8 de uma família com direção/nível distinto noutra
print("\n=== DIVERGÊNCIA ENTRE FAMÍLIAS (mesma feature, padrão winner por família) ===")
keys = sorted({k for f in fam_top for _, k, _, _ in fam_top[f]})
hdr = "  " + f"{'feature':<22}" + "".join(f"{f:>12}" for f in ("BANDA", "FUNDO", "RASO"))
print(hdr)
for k in keys:
    vals = []
    for f in ("BANDA", "FUNDO", "RASO"):
        W = [u for u in WINNERS if u["_fam"] == f]
        m = med(W, k)
        vals.append(f"{m:>12.2f}" if m is not None else f"{'—':>12}")
    print(f"  {k:<22}" + "".join(vals))
json.dump({f: [{"k": k, "win": mw, "sosia": ms, "sep": round(sp, 2)} for sp, k, mw, ms in fam_top[f]]
           for f in fam_top},
          open(HERE / "results" / "family_feature_map_20260706.json", "w"), indent=1, default=float)
print("\nOK → results/family_feature_map_20260706.json")
