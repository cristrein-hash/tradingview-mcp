#!/usr/bin/env python3
"""SUBSTRATO B (engine de entrada de B, Cris 2026-07-15) — dossiês RAW CAUSAIS dos 12 KEEP B (ORDERLY,
long-viáveis sob b_macro_gate), extraídos pelos ÂNGULOS de B para a leitura contextual ampla:
 ① banda do range (RH/RL causal) + posição% do fundo   ② SPRING/SWEEP do suporte (varreu low e recuperou?)
 ③ maturidade (nº de testes do suporte que seguraram)   ④ absorção no fundo (mecha/rejeição/close-in-bar)
 ⑤ estrutura na entrada (HL/EQL/LL sweep)               ⑥ espaço-ao-teto (R até RH) — R:R do range
Tudo causal close-only (pivôs fractais confirmados, sem espreitar). RAW 15M direto do HD. NADA é feature
ainda — é o material da leitura. Grava results/B_CONTEXT_KEEP12.json + imprime painel."""
import json, bisect, statistics, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
from a1_causal_entry import load_series, causal_entry, _is_swinglow, M_FRAC, LOWBACK
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
BLK = ["XAUUSD_15m_replay_2025-02-25_to_2025-05-25.jsonl.gz", "XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz",
       "XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz", "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz"]
RNGWIN = 480   # janela do range local (~5d 15M)
S = load_series(BLK); T, O, H, L, C, ATR, N = S["T"], S["O"], S["H"], S["L"], S["C"], S["ATR"], S["N"]
GT = json.load(open(HERE/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
B = sorted([f for f in GT["fundos"] if f.get("subclasse") == "B_range"], key=lambda x: x["t"])[:12]

def swing_lows(j, back):
    return [(p, L[p]) for p in range(max(M_FRAC, j-back), j+1) if _is_swinglow(L, p, M_FRAC)]
def swing_highs(j, back):
    def _sh(p, m): return p-m >= 0 and p+m < N and H[p] == max(H[p-m:p+m+1]) and H[p] > max(H[p-m:p])
    return [(p, H[p]) for p in range(max(M_FRAC, j-back), j+1) if _sh(p, M_FRAC)]

def dossier(f, n):
    j = bisect.bisect_right(T, int(f["t"]))-1
    lo0 = max(0, j-RNGWIN); RH = max(H[lo0:j+1]); RL = min(L[lo0:j+1]); band = RH-RL
    atr = ATR[j] or 5.0
    sl = swing_lows(j, RNGWIN); sh = swing_highs(j, RNGWIN)
    # ② SPRING/SWEEP: suporte = penúltimo swing-low (o nível testado); varreu abaixo e recuperou?
    support = sl[-2][1] if len(sl) >= 2 else RL
    anchor_bar = min(range(lo0, j+1), key=lambda z: L[z]); anchor_low = L[anchor_bar]
    swept_depth = round((support-anchor_low)/atr, 2)          # >0 = varreu abaixo do suporte
    reclaim = round((C[j]-anchor_low)/atr, 2)                 # recuperação desde o low-âncora
    is_spring = swept_depth > 0.1 and C[j] > support           # varreu e fechou de volta acima
    # ③ MATURIDADE: nº de swing-lows dentro de ~0.6ATR do suporte (testes que seguraram)
    tests = sum(1 for _, lv in sl if abs(lv-support) <= 0.6*atr)
    # ④ ABSORÇÃO no low-âncora: fração de mecha inferior + posição do close na barra
    ab = anchor_bar; rng = max(1e-9, H[ab]-L[ab])
    lower_wick = round((min(O[ab], C[ab])-L[ab])/rng, 2); close_pos = round((C[ab]-L[ab])/rng, 2)
    # ⑤ ESTRUTURA: HL / EQL / LL do último swing-low vs anterior
    if len(sl) >= 2:
        rel = (sl[-1][1]-sl[-2][1])/atr
        struct = "HL" if rel > 0.15 else ("LL/sweep" if rel < -0.15 else "EQL")
    else: struct = "poucos-pivos"
    # ⑥ posição + espaço-ao-teto (usa entry estimado = close de j, R = entry - (anchor-0.1ATR))
    ent = C[j]; slp = anchor_low-0.1*atr; R = ent-slp
    pos = round(100*(ent-RL)/max(1e-9, band))
    r_to_ceil = round((RH-ent)/R, 1) if R > 0 else 0
    # gatilho MB3 causal (referência) + desfecho 3R
    e = causal_entry(S, j, "MB3")
    return {"n": n, "date": ds(int(f["t"])), "price": f["price"],
            "range": {"RH": round(RH, 1), "RL": round(RL, 1), "band_atr": round(band/atr, 1), "pos_pct": pos},
            "spring": {"support": round(support, 1), "swept_depth_atr": swept_depth, "reclaim_atr": reclaim, "is_spring": is_spring},
            "maturity_tests": tests, "absorption": {"lower_wick": lower_wick, "close_pos": close_pos},
            "structure": struct, "room_to_ceiling_R": r_to_ceil,
            "mb3": None if not e else {"o": e["o"], "R": e["R"], "RATR": e["RATR"], "lag": e["lag"]}}

doss = [dossier(f, n) for n, f in enumerate(B, 1)]
json.dump({"fundos": doss}, open(HERE/"results"/"B_CONTEXT_KEEP12.json", "w"), indent=1)
print(f"{'#':>3} {'data':16} {'pos%':>5} {'band':>5} {'spring':>7} {'swept':>6} {'reclaim':>7} {'tests':>5} {'lwick':>5} {'struct':>10} {'R→teto':>7} {'MB3':>10}")
for d in doss:
    r, s, a = d["range"], d["spring"], d["absorption"]
    mb = f"{d['mb3']['o']}({d['mb3']['RATR']}A)" if d["mb3"] else "—"
    print(f"{d['n']:>3} {d['date']:16} {r['pos_pct']:>4}% {r['band_atr']:>4} {str(s['is_spring']):>7} {s['swept_depth_atr']:>6} {s['reclaim_atr']:>7} {d['maturity_tests']:>5} {a['lower_wick']:>5} {d['structure']:>10} {d['room_to_ceiling_R']:>6}R {mb:>10}")
print(f"\nAGREGADO: pos% med {statistics.median([d['range']['pos_pct'] for d in doss]):.0f} · springs {sum(d['spring']['is_spring'] for d in doss)}/12 · "
      f"R→teto med {statistics.median([d['room_to_ceiling_R'] for d in doss]):.1f} · MB3 3R {sum(1 for d in doss if d['mb3'] and d['mb3']['o']=='WIN')}/12")
from collections import Counter
print("estrutura:", dict(Counter(d['structure'] for d in doss)), "· maturidade(med tests):", statistics.median([d['maturity_tests'] for d in doss]))