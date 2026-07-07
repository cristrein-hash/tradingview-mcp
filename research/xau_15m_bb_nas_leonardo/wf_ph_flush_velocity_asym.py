#!/usr/bin/env python3
"""FASE-DO-CICLO via ASSIMETRIA DE VELOCIDADE (flush vs drift) — XAU 15M LONG 3R engine.

Ideia (rule 5): WINNER = Fase A (markup ativo, HH) U Fase B (iniciacao: flush fundo a
demanda + reclaim + CHoCH-up). LOSER = Fase C (distribuicao-topo, drift/overlap, chase)
U Fase D (bear ativo, LH/BOS-down).

Lente = ASSIMETRIA DE VELOCIDADE, medida SO com barras indice<=j (CAUSAL, SEQUENCIAL):
  - down_vel  : velocidade da queda ate ao entry-low (ATR/barra) na perna de descida.
  - eff       : eficiencia direcional da descida (queda liquida / caminho percorrido).
                Flush limpo => alto; drift choppy/overlap => baixo.
  - rec_vel   : velocidade da RECUPERACAO do low ao reclaim (CL[j]-LO[i])/(j-i)/ATR.
  - vsnap     : rec_vel / down_vel  => "V-snap": bounce absorve rapido a demanda.
  - hh_struct : ultimo swing-high confirmado (conf<=j) > penultimo => markup (Fase A).
                Se < => bear/LH (candidato Fase D). Estrutural, so pivos com conf_bar<=j.

DESCOBERTA HONESTA (medida, nao assumida): o naive "flush sharp => keep" e FALSO nestes
dados — losers tem short-flush MAIS agudo (violencia de BOS-down / distribuicao). O eixo
de velocidade que separa na direcao certa e a ASSIMETRIA DESCIDA-vs-RECUPERACAO: iniciacao
genuina (Fase B) faz V rapido (rec_vel domina, reclaim pronto); distribuicao/bear faz drift
lento OU quebra sem recuperacao. Ergo classificador = V-snap + descida direcional, com
guarda estrutural de markup para Fase A.

REGRAS: nenhuma logica usa e['out'] nem os numeros-alvo. Thresholds sao ESTRUTURAIS
(vsnap>=1 = recupera tao rapido quanto cai; eff em torno da neutralidade direcional),
NAO varridos para maximizar o label. score() da os numeros reais + null by-year.
"""
import sys
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import (S, TS, HI, LO, CL, ATR, EMA, RSI, N, ENTRIES,
                           score, causal_swings_upto)


def feat(e):
    """Todas as features usam SO barras indice<=j (i<=j sempre). CAUSAL + SEQUENCIAL."""
    i = e["i"]; j = e["j"]; a = ATR[i] or 5.0
    sw = causal_swings_upto(j)                      # pivos confirmados (conf_bar<=j)
    Ls = [idx for (tp, idx, pr, cb) in sw if tp == "L" and idx < i]
    Hs = [(idx, pr) for (tp, idx, pr, cb) in sw if tp == "H" and idx < i]
    # ancora = ultimo swing-low confirmado antes de i (inicio da perna de subida->topo)
    A = Ls[-1] if Ls else max(0, i - 60)
    if A >= i:
        A = max(0, i - 60)
    # pico da perna = HH bruto em [A,i] (barras<=i<=j => causal)
    peak = A
    for k in range(A, i + 1):
        if HI[k] >= HI[peak]:
            peak = k
    dbars = max(i - peak, 1); drop = HI[peak] - LO[i]
    down_vel = drop / dbars / a
    path = sum(abs(CL[k] - CL[k - 1]) for k in range(peak + 1, i + 1)) or 1e-9
    eff = drop / path                                # direcionalidade da descida
    rbars = max(j - i, 1); recov = CL[j] - LO[i]
    rec_vel = recov / rbars / a                      # velocidade da recuperacao (V-snap up)
    vsnap = rec_vel / max(down_vel, 1e-9)
    # estrutura de fase: HH markup (ultimo H conf > penultimo H conf)
    if len(Hs) >= 2:
        hh_struct = 1 if Hs[-1][1] > Hs[-2][1] else -1
    else:
        hh_struct = 0
    return dict(down_vel=down_vel, eff=eff, rec_vel=rec_vel, vsnap=vsnap,
                hh_struct=hh_struct, rlag=e["reclaim_lag"])


F = {e["n"]: feat(e) for e in ENTRIES}


def classify(rule):
    return {n for n, f in F.items() if rule(f)}


# ---- variantes ESTRUTURAIS (nao varridas ao label) ----------------------------
VARIANTS = {
    # V-snap puro: recupera tao rapido quanto (ou mais que) caiu => bounce/absorcao real
    "A_vsnap>=1":        lambda f: f["vsnap"] >= 1.0,
    # V-snap + descida direcional (flush limpo, nao drift overlap)
    "B_vsnap>=1&eff>=.45": lambda f: f["vsnap"] >= 1.0 and f["eff"] >= 0.45,
    # markup OU iniciacao-Vsnap: Fase A (HH) unida a Fase B (flush+snap)
    "C_HHorVsnap":       lambda f: f["hh_struct"] >= 0 and (f["vsnap"] >= 1.0 or f["down_vel"] >= 0.20),
    # corta drift-topo/bear: fora se recuperacao lenta E descida lenta (drift) OU bear+sem-snap
    "D_notDrift":        lambda f: not ((f["rec_vel"] < 0.45 and f["down_vel"] < 0.20)
                                        or (f["hh_struct"] < 0 and f["vsnap"] < 1.0)),
    # composite: markup-structure guard + V-snap OU descida direcional forte
    "E_struct+Vsnap":    lambda f: f["hh_struct"] >= 0 and (f["vsnap"] >= 1.0 or f["eff"] >= 0.50)
                                   and f["rlag"] <= 12,
}

results = {}
for name, rule in VARIANTS.items():
    keep = classify(rule)
    results[name] = (keep, score(keep))

print("BASE:", score([e["n"] for e in ENTRIES])["base"])
print("=" * 96)
for name, (keep, sc) in results.items():
    print(f"{name:22s} N{sc['N_kept']:3d} hit {sc['hit3r_kept']:.3f} "
          f"poison {sc['poison_ratio']:.2f} Wcut {sc['winners_cut']:2d} Lcut {sc['losers_cut']:2d} "
          f"y25 {sc['y2025']:>6s} y26 {sc['y2026']:>6s}")


# ---- seleccao pela regra dada: hit alto & poison<0.9 & ambos anos+ & N>=20 ----
def ok(sc):
    y25 = tuple(int(x) for x in sc["y2025"].split("/"))
    y26 = tuple(int(x) for x in sc["y2026"].split("/"))
    yr_pos = y25[0] > 0 and y26[0] > 0
    return (sc["N_kept"] >= 20 and sc["poison_ratio"] < 0.9 and yr_pos)


elig = {n: (k, s) for n, (k, s) in results.items() if ok(s)}
print("=" * 96)
if elig:
    best = max(elig.items(), key=lambda kv: kv[1][1]["hit3r_kept"])
    bname, (bkeep, bsc) = best
    print("SELECTED:", bname, bsc)
else:
    # nenhuma passa gate duro; reporta a de maior hit com N>=20 como HONESTO-NEGATIVO
    cand = {n: (k, s) for n, (k, s) in results.items() if s["N_kept"] >= 20}
    bname, (bkeep, bsc) = max(cand.items(), key=lambda kv: kv[1][1]["hit3r_kept"])
    print("NO VARIANT PASSES HARD GATE — best-by-hit (N>=20):", bname, bsc)

# ---- SANITY-CHECK post-hoc (NAO usado na logica) -----------------------------
loser_targets = [21,23,31,49,50,55,56,57,59,60,65,66,67,68,69,79,83,84,85,89,93,94]
winner_keys   = [1,11,12,13,14,26,28,29,30,44,45,61,62,63,71,72,73,74,75,82,95,96]
lt_cut = sum(1 for n in loser_targets if n not in bkeep)
wk_kept = sum(1 for n in winner_keys if n in bkeep)
print("-" * 96)
print(f"SANITY (post-hoc): loser-targets cortados {lt_cut}/{len(loser_targets)} | "
      f"winners-chave mantidos {wk_kept}/{len(winner_keys)}")
print("KEEP_NS:", sorted(bkeep))
