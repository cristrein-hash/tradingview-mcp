#!/usr/bin/env python3
"""ESTUDO CONCEITUAL — engine de ENTRADA de B (Cris 2026-07-15). Fundamenta no RAW os 12 KEEP B
(ORDERLY, long-viáveis sob o b_macro_gate). Pergunta-âncora: o mecanismo A1/A2 (MB3 + SL low-real + 3R)
serve, ou o RANGE exige mecânica própria? Mede, por fundo B:
 (1) MB3 causal (a1_causal_entry): entry, SL, R, alvo 3R, desfecho SL-first.
 (2) geometria do range local: RH/RL (janela), posição% do fundo, estrutura na entrada (HL/EQL/sweep).
 (3) ESPAÇO AO TETO: quantos R cabem até ao topo recente (RH). Se <3R, o alvo 3R está ACIMA da
     resistência => precisa rutura (o R:R do range é diferente do pullback-em-tendência).
RAW 15M direto do HD. Só entender a natureza; nada é feature ainda."""
import json, bisect, statistics, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
from a1_causal_entry import load_series, causal_entry, _is_swinglow, M_FRAC, LOWBACK
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
BLK = ["XAUUSD_15m_replay_2025-02-25_to_2025-05-25.jsonl.gz", "XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz",
       "XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz", "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz"]
RNGWIN = 480   # janela do range local (~5 dias 15M) p/ RH/RL
S = load_series(BLK); T, O, H, L, C, ATR, N = S["T"], S["O"], S["H"], S["L"], S["C"], S["ATR"], S["N"]
GT = json.load(open(HERE/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
B = sorted([f for f in GT["fundos"] if f.get("subclasse") == "B_range"], key=lambda x: x["t"])[:12]  # KEEP 1-12

def struct_into(j):
    # estrutura na entrada: compara o low-âncora com o swing-low anterior (HL / EQL / LL) + sweep
    lows = []
    for p in range(max(M_FRAC, j-LOWBACK), j+1):
        if _is_swinglow(L, p, M_FRAC): lows.append((p, L[p]))
    if len(lows) < 2: return "poucos-pivos", 0
    (p1, l1), (p0, l0) = lows[-1], lows[-2]
    atr = ATR[p1] or 5.0
    rel = (l1-l0)/atr
    kind = "HL" if rel > 0.15 else ("LL/sweep" if rel < -0.15 else "EQL")
    # sweep = varreu abaixo do low anterior e recuperou (low intrusão)
    swept = any(L[k] < l0-0.05*atr for k in range(p0+1, p1+1)) and L[p1] >= l0-0.6*atr
    return (kind + ("+sweep" if swept else "")), round(rel, 2)

print(f"{'#':>3} {'data':16} {'MB3':>4} {'R':>6} {'RATR':>5} {'pos%':>5} {'R→teto':>7} {'3R<teto?':>8} {'estrutura':>14}")
wins = 0; room = []; below3 = 0; rows = []
for n, f in enumerate(B, 1):
    j = bisect.bisect_right(T, int(f["t"]))-1
    e = causal_entry(S, j, "MB3")
    lo0 = max(0, j-RNGWIN); RH = max(H[lo0:j+1]); RL = min(L[lo0:j+1])
    if not e:
        print(f"{n:>3} {ds(int(f['t'])):16}  sem-entry"); continue
    ent, R, o = e["ent"], e["R"], e["o"]; wins += o == "WIN"
    pos = 100*(ent-RL)/max(1e-9, RH-RL)
    r_to_ceil = (RH-ent)/R if R > 0 else 0        # quantos R até ao topo recente
    fits = r_to_ceil >= 3.0; below3 += 0 if fits else 1
    room.append(r_to_ceil)
    st, rel = struct_into(j)
    rows.append((n, o, pos, r_to_ceil, fits, st))
    print(f"{n:>3} {ds(int(f['t'])):16} {o:>4} {R:>6.1f} {e['RATR']:>5} {pos:>4.0f}% {r_to_ceil:>6.1f}R {str(fits):>8} {st:>14}")

print(f"\nMB3 hit-3R nos 12 KEEP B: {wins}/12 ({100*wins/12:.0f}%)")
print(f"ESPAÇO AO TETO: mediana {statistics.median(room):.1f}R · casos com 3R ACIMA do topo recente (precisa rutura): {below3}/12")
print(f"posição no range: mediana {statistics.median([r[2] for r in rows]):.0f}% (baixo=fundo de suporte, alto=topo de sub-range/escada)")
from collections import Counter
print("estruturas na entrada:", dict(Counter(r[5].split('+')[0] for r in rows)))