#!/usr/bin/env python3
"""AUTÓPSIA DOS CÍRCULOS INVISÍVEIS (2026-07-06, passo 1 do plano aprovado pelo Cris).
5 círculos GT sem NENHUM candidato no universo (±8h & |flush−low|<=1ATR). O gerador raiz
(lab_entry_candidates.py) emite toda mínima fractal k=3 confirmada em p+3, com portas:
  A p>=96 dentro do BLOCO (24h de warmup por bloco)   B cj>=nn-1 (fim de bloco)
  C dedup cj-last_cj<3                                D atr ausente na barra
  E a mínima não é fractal k=3 (low vizinho menor)    F fractal existe mas >1ATR do low do círculo
Para cada círculo invisível: bloco, posição no bloco, teste de cada porta, candidato mais próximo
no universo (Δt, Δpreço/ATR). SEM outcome — é diagnóstico de gerador.
SANITY_PROBE: círculos identificados pela MESMA convenção do truelow (índice 0-based do json
selado, matcher ±8h & <=1ATR, sha-check)."""
import json, bisect, hashlib
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: 1 for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
UNIV = sorted([u for u in U if u["cj_t"] in R3], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]

# invisíveis = círculos sem candidato (mesma regra do truelow)
invis = []
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    hit = False
    while j < len(UNIV) and UT[j] <= g["flush_t"] + 8 * 3600:
        u = UNIV[j]
        if abs((u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0)) - g["flush_low"]) <= (u.get("g_atr") or 5.0):
            hit = True; break
        j += 1
    if not hit:
        invis.append(gi)
print(f"invisíveis: {invis}")

import glob
PRIM = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    k = Path(p).name.split(".")[0].replace("XAUUSD_15m_replay_", "")[:10]
    PRIM[k] = json.load(open(p))

for gi in invis:
    g = GT[gi]
    ft, flo = g["flush_t"], g["flush_low"]
    print(f"\n=== círculo {gi} · {dt.datetime.utcfromtimestamp(ft).strftime('%Y-%m-%d %H:%M')} · low {flo:.1f} ===")
    # blocos que contêm ft
    homes = []
    for k, pr in PRIM.items():
        s = pr["series"]
        if s and s[0]["t"] <= ft <= s[-1]["t"]:
            homes.append((k, pr))
    if not homes:
        print("  !!! NENHUM bloco contém o timestamp — buraco de cobertura RAW")
        continue
    for k, pr in homes:
        s = pr["series"]; nn = len(s)
        TSb = [b["t"] for b in s]; L = [b["l"] for b in s]
        i0 = bisect.bisect_right(TSb, ft) - 1
        # low real perto do círculo (±16 barras)
        lo_w = range(max(0, i0 - 16), min(nn, i0 + 17))
        pbest = min(lo_w, key=lambda q: abs(L[q] - flo))
        dlow = abs(L[pbest] - flo)
        atr_p = s[pbest].get("atr")
        print(f"  bloco {k}: nn={nn} · barra do círculo i={i0} ({i0} do início, {nn-1-i0} do fim)"
          f" · low mais próximo Δ={dlow:.1f} em i={pbest}")
        # portas
        fails = []
        if pbest < 96: fails.append(f"A: p={pbest}<96 (warmup do bloco)")
        if pbest + 3 >= nn - 1: fails.append(f"B: cj=p+3={pbest+3}>=nn-1={nn-1} (fim de bloco)")
        if atr_p is None: fails.append("D: atr ausente")
        isfr = 3 <= pbest < nn - 4 and L[pbest] == min(L[pbest - 3:pbest + 4])
        if not isfr:
            # onde está o fractal k3 mais próximo que capturaria o círculo?
            frs = [q for q in range(max(3, i0 - 32), min(nn - 4, i0 + 33)) if L[q] == min(L[q - 3:q + 4])]
            near = min(frs, key=lambda q: abs(L[q] - flo)) if frs else None
            extra = ""
            if near is not None:
                a2 = s[near].get("atr") or 5.0
                extra = f"; fractal vizinho i={near} Δt={(TSb[near]-ft)/3600:+.1f}h Δlow={(L[near]-flo)/a2:+.2f}ATR"
            fails.append("E: barra do low NÃO é fractal k=3" + extra)
        if not fails:
            fails.append("F/dedup: fractal ok e portas ok — perdido por dedup cj-last_cj<3 OU flush do candidato ficou >1ATR (verificar)")
        for x in fails:
            print(f"    PORTA {x}")
    # candidato mais próximo no tempo, qualquer preço
    j = bisect.bisect_left(UT, ft)
    best = None
    for jj in (j - 1, j, j + 1):
        if 0 <= jj < len(UNIV):
            u = UNIV[jj]
            if best is None or abs(u["cj_t"] - ft) < abs(best["cj_t"] - ft):
                best = u
    if best:
        a = best.get("g_atr") or 5.0
        fl = best["g_sl"] + 0.1 * a
        print(f"  candidato + próximo: Δt={(best['cj_t']-ft)/3600:+.1f}h · flush Δ={(fl-flo)/a:+.2f}ATR")
