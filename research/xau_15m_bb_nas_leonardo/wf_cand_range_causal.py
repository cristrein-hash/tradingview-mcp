#!/usr/bin/env python3
"""CANDIDATO: filtro macro-contextual CAUSAL — DETETOR DE RANGE + demanda-do-range.

Hipotese estrutural (Cris):
  Um range e um estado de mercado que CAMINHA ao longo de K barras: choppiness/overlap alto,
  eficiencia direcional baixa. Dois usos:
   (i)  REJEITAR entries que ocorrem dentro de um range (mercado sem direcao -> demanda fraca).
   (ii) Em range, MANTER so os entries que entram PERTO DO FUNDO CAUSAL do range
        (min LO das ultimas K barras ate j) — a "demanda do range".

Causalidade: para cada entry, a barra de decisao e j. TODA a feature usa APENAS barras com
indice em [j-K, j] (inclusive). Nunca LO[j:...]/HI[j:...] futuros, nunca last_t de zona,
nunca confirmacao de pivo por movimento futuro, nunca o outcome. eff/overlap/pos sao
estados que se acumulam bar-a-bar ao longo da janela -> ESTRUTURAL, nao snapshot.

Feature por entry:
  win = CL/HI/LO em [j-K .. j]  (K barras de historia + a propria barra j)
  eff = |CL[j]-CL[j-K]| / sum_{m=j-K+1..j} |CL[m]-CL[m-1]|   (Kaufman efficiency ratio, 0..1)
        eff baixo = choppy/range ; eff alto = trend limpo
  rlo = min(LO[j-K..j]) ; rhi = max(HI[j-K..j])
  pos = (ent - rlo)/(rhi-rlo)    posicao do preco de entrada dentro do range causal (0=fundo,1=topo)
  is_range = eff < EFF_THR
"""
import sys, itertools
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S, TS, HI, LO, CL, ATR, EMA, RSI, N, ENTRIES, score

def feats(e, K):
    j = e["j"]
    a = j - K
    if a < 0:
        return None
    diffs = sum(abs(CL[m] - CL[m-1]) for m in range(a+1, j+1))
    net = abs(CL[j] - CL[a])
    eff = net / diffs if diffs > 0 else 1.0
    rlo = min(LO[a:j+1]); rhi = max(HI[a:j+1])
    rng = rhi - rlo
    pos = (e["ent"] - rlo) / rng if rng > 0 else 0.5
    return {"eff": eff, "pos": pos, "rlo": rlo, "rhi": rhi, "rng_atr": rng / (ATR[j] or 5.0)}

def variant_reject_range(K, EFF_THR):
    """(i) REJEITA entries em range: mantem so os que NAO estao em range (eff>=thr)."""
    keep = []
    for e in ENTRIES:
        f = feats(e, K)
        if f is None:
            keep.append(e["n"]); continue          # sem historia suficiente -> nao filtra (conservador)
        if f["eff"] >= EFF_THR:                      # trend limpo -> mantem
            keep.append(e["n"])
    return keep

def variant_range_demand(K, EFF_THR, POS_THR):
    """(ii) Em range mantem SO fundo causal: trend->keep; range&pos<=POS_THR->keep; range&topo->cut."""
    keep = []
    for e in ENTRIES:
        f = feats(e, K)
        if f is None:
            keep.append(e["n"]); continue
        if f["eff"] >= EFF_THR:                      # trend -> mantem sempre
            keep.append(e["n"])
        elif f["pos"] <= POS_THR:                     # range mas perto do fundo -> demanda do range
            keep.append(e["n"])
        # range & topo -> corta
    return keep

def show(tag, keep):
    sc = score(keep)
    ok = (sc["N_kept"] >= 20 and sc["poison_ratio"] < 0.9 and sc["hit3r_kept"] >= 0.60)
    y25 = sc["y2025"]; y26 = sc["y2026"]
    print(f"{tag:42s} N={sc['N_kept']:2d} hit={sc['hit3r_kept']:.3f} "
          f"pois={sc['poison_ratio']:.2f} Wcut={sc['winners_cut']} Lcut={sc['losers_cut']} "
          f"y25={y25} y26={y26} {'<<<' if ok else ''}")
    return sc, ok

if __name__ == "__main__":
    baseW = sum(e["out"] for e in ENTRIES)
    print(f"BASE: {len(ENTRIES)} entries · {baseW}W/{len(ENTRIES)-baseW}L · hit-3R {baseW/len(ENTRIES):.1%}")
    print("="*110)
    results = []

    print("--- VARIANTE (i) REJEITAR RANGE (mantem eff>=thr) ---")
    for K in (10, 20, 30, 40):
        for EFF in (0.20, 0.25, 0.30, 0.35, 0.40):
            keep = variant_reject_range(K, EFF)
            sc, ok = show(f"reject_range K={K} eff>={EFF}", keep)
            results.append(("reject", K, EFF, None, keep, sc, ok))

    print("--- VARIANTE (ii) RANGE-DEMANDA (trend OU fundo do range) ---")
    for K in (10, 20, 30, 40):
        for EFF in (0.25, 0.30, 0.35):
            for POS in (0.25, 0.33, 0.40, 0.50):
                keep = variant_range_demand(K, EFF, POS)
                sc, ok = show(f"range_demand K={K} eff<{EFF} pos<={POS}", keep)
                results.append(("demand", K, EFF, POS, keep, sc, ok))

    print("="*110)
    # escolher melhor entre os que passam gate (ok): maximiza hit, depois N, depois -poison
    passers = [r for r in results if r[6]]
    def rank(r):
        sc = r[5]
        both_pos = ("/0" not in sc["y2025"].split("/")[0]+"x") # placeholder
        return (sc["hit3r_kept"], sc["N_kept"], -sc["poison_ratio"])
    def years_pos(sc):
        w25 = int(sc["y2025"].split("/")[0]); n25 = int(sc["y2025"].split("/")[1])
        w26 = int(sc["y2026"].split("/")[0]); n26 = int(sc["y2026"].split("/")[1])
        # "ambos anos positivos" = hit>50% em cada ano com N>0
        p25 = (n25 > 0 and w25/n25 > 0.5)
        p26 = (n26 > 0 and w26/n26 > 0.5)
        return p25, p26, (w25,n25,w26,n26)
    strict = []
    for r in results:
        sc = r[5]
        p25, p26, ynums = years_pos(sc)
        if r[6] and p25 and p26:
            strict.append((r, ynums))
    print(f"PASSERS (gate N>=20 & poison<0.9 & hit>=0.60): {len(passers)}")
    print(f"STRICT  (+ ambos anos hit>50%):               {len(strict)}")
    if strict:
        best = max(strict, key=lambda x: rank(x[0]))[0]
        print(">>> MELHOR (strict):", best[0], "K=",best[1],"EFF=",best[2],"POS=",best[3])
        print("    score:", best[5])
        print("    keep_ns:", sorted(best[4]))
    elif passers:
        best = max(passers, key=rank)
        print(">>> MELHOR (gate, mas anos nao ambos>50%):", best[0], "K=",best[1],"EFF=",best[2],"POS=",best[3])
        print("    score:", best[5])
        print("    keep_ns:", sorted(best[4]))
    else:
        print(">>> NENHUM passa o gate. Reporto o menos-mau por hit3r com N>=20:")
        cand = [r for r in results if r[5]["N_kept"] >= 20]
        best = max(cand, key=lambda r: (r[5]["hit3r_kept"], -r[5]["poison_ratio"]))
        print("   ", best[0], "K=",best[1],"EFF=",best[2],"POS=",best[3], best[5])
        print("    keep_ns:", sorted(best[4]))
