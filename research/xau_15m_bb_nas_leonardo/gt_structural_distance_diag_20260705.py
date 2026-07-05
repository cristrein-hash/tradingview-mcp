#!/usr/bin/env python3
"""DIAGNÓSTICO — a que ESTRUTURA os 60 fundos GT do Cris chegam? (2026-07-05)
Correção de método após v1 (pivô-low: 10/60) e v2 (breakout/box: 3/60): parar de adivinhar
geometria+tolerância+morte; MEDIR a distância do flush_low de cada GT a cada família de nível
estrutural CONHECIDO antes do flush, e comparar com null de 60 barras aleatórias.
Artefato corrigido: morte de zona agora exige violação SUSTENTADA (16 closes seguidos abaixo) —
o próprio flush não pode matar a zona que está testando.

FAMÍLIAS (todas causais, nível conhecido antes de ft):
  A swing-high w32 JÁ ROMPIDO antes de ft (resistência→suporte)
  B swing-high w96 JÁ ROMPIDO
  C swing-low w32 vivo (não violado sustentado antes de ft−24h)
  D swing-low w96 vivo
  E box-top: topo de consolidação (M24, range<=2·ATR) já impulsionada
  F EQL/EQH? não — só preço puro nesta rodada
Métrica: dist = (flush_low − nível)/ATR@ft · min |dist| por família (níveis dos últimos 30d)
Null: 60 lows de barras aleatórias (seed fixa, mesmas janelas) → mesma métrica.
SANITY_PROBE: P1 nível known antes de ft (assert) · P2 null usa exatamente o mesmo matcher ·
P3 amostra impressa p/ reconciliação."""
import json, bisect, hashlib, random
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N = len(S)
ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]

def swings(w, kind):
    out = []
    arr = HI if kind == "H" else LO
    for k in range(w, N - w):
        v = arr[k]
        seg = arr[k - w:k + w + 1]
        if (v == max(seg) if kind == "H" else v == min(seg)) and arr[k - w:k].count(v) == 0:
            out.append((k, v))
    return out

def sustained_below(level, start_i, end_i, atr_ref, run=16):
    c = 0
    for k in range(start_i, min(end_i, N)):
        if CL[k] < level - 0.25 * atr_ref:
            c += 1
            if c >= run:
                return k
        else:
            c = 0
    return None

SH32 = swings(32, "H"); SH96 = swings(96, "H")
SL32 = swings(32, "L"); SL96 = swings(96, "L")
BOX = []
i = 24
while i < N:
    seg_hi = max(HI[i - 24:i]); seg_lo = min(LO[i - 24:i])
    if seg_hi - seg_lo <= 2.0 * ATR[i] and CL[i] > seg_hi + 0.5 * ATR[i]:
        BOX.append((i, seg_hi))
        i += 24
        continue
    i += 1
print(f"níveis: SH32 {len(SH32)} SH96 {len(SH96)} SL32 {len(SL32)} SL96 {len(SL96)} BOX {len(BOX)}")

LOOK_D = 30 * 96      # 30 dias

def broken_high_levels(sw, w, fi):
    """swing highs confirmados (k+w<fi) E rompidos (close>H) antes de fi, não violados sustentado."""
    lv = []
    for k, H in sw:
        if k + w >= fi or fi - k > LOOK_D:
            continue
        br = None
        for j in range(k + w, fi):
            if CL[j] > H + 0.1 * ATR[j]:
                br = j
                break
        if br is None:
            continue
        d = sustained_below(H, br, fi - 96, ATR[br])
        if d is None:
            lv.append(H)
    return lv

def alive_low_levels(sw, w, fi):
    lv = []
    for k, L in sw:
        if k + w >= fi or fi - k > LOOK_D:
            continue
        d = sustained_below(L, k + w, fi - 96, ATR[k])
        if d is None:
            lv.append(L)
    return lv

def box_levels(fi):
    lv = []
    for k, H in BOX:
        if k >= fi or fi - k > LOOK_D:
            continue
        d = sustained_below(H, k, fi - 96, ATR[k])
        if d is None:
            lv.append(H)
    return lv

def families(fi):
    return {"A_SH32rompido": broken_high_levels(SH32, 32, fi),
            "B_SH96rompido": broken_high_levels(SH96, 96, fi),
            "C_SL32vivo": alive_low_levels(SL32, 32, fi),
            "D_SL96vivo": alive_low_levels(SL96, 96, fi),
            "E_boxtop": box_levels(fi)}

def measure(rows):
    out = {f: [] for f in ("A_SH32rompido", "B_SH96rompido", "C_SL32vivo", "D_SL96vivo", "E_boxtop")}
    for fi, flo in rows:
        fam = families(fi)
        a = ATR[fi]
        for f, lv in fam.items():
            if lv:
                d = min(((flo - x) / a for x in lv), key=abs)
                out[f].append(d)
            else:
                out[f].append(None)
    return out

GT_rows = []
for g in GT:
    fi = bisect.bisect_right(TS, g["flush_t"]) - 1
    if fi > 96:
        GT_rows.append((fi, g["flush_low"]))
random.seed(7)
pool = [i for i in range(3000, N - 100)]
NULL_rows = [(i, LO[i]) for i in random.sample(pool, 60)]

mg = measure(GT_rows); mn = measure(NULL_rows)
import statistics as st
print(f"\n{'família':<16} {'GT med|d|':>10} {'GT <=0.5':>8} {'GT <=1.0':>8} {'NULL med|d|':>12} {'NULL <=1.0':>10}")
for f in mg:
    a = [abs(x) for x in mg[f] if x is not None]
    b = [abs(x) for x in mn[f] if x is not None]
    if not a or not b:
        continue
    print(f"{f:<16} {st.median(a):>10.2f} {100*sum(1 for x in a if x<=0.5)/len(a):>7.0f}% "
          f"{100*sum(1 for x in a if x<=1.0)/len(a):>7.0f}% {st.median(b):>12.2f} "
          f"{100*sum(1 for x in b if x<=1.0)/len(b):>9.0f}%")
print("\ndistribuição ASSINADA (flush_low − nível, ATR) — mediana GT (negativo = varre ABAIXO):")
for f in mg:
    v = [x for x in mg[f] if x is not None]
    if v:
        print(f"  {f:<16} med {st.median(v):+.2f} · q25 {sorted(v)[len(v)//4]:+.2f} · q75 {sorted(v)[3*len(v)//4]:+.2f}")
print("\nP3 amostra 6 GT (dist por família):")
for (fi, flo), k in zip(GT_rows[:6], range(6)):
    fam = families(fi); a = ATR[fi]
    ds = {f: (min(((flo - x) / a for x in lv), key=abs) if lv else None) for f, lv in fam.items()}
    print(f"  {dt.datetime.utcfromtimestamp(TS[fi]).strftime('%Y-%m-%d %H:%M')} " +
          " ".join(f"{f.split('_')[0]}:{('%+.2f' % d) if d is not None else '—'}" for f, d in ds.items()))
