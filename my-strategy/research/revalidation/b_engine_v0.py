#!/usr/bin/env python3
"""ENGINE DE B v0 (Cris aprovou caminho (a) 2026-07-15) — retomada no FUNDO do range. Composição:
  GATE MACRO (b_macro_gate): RANGE_ORDERLY (crash-born=SKIP).
  GATE DE POSIÇÃO (novo, lição de streak do Cris): posição no range macro (causal onset->fundo) <= 40%
    => só entra na porção BAIXA (suporte), rejeita continuação perto do topo (o streak-killer).
  MECÂNICA (reusa a1_causal_entry, verificada em A1/A2): MB3 + SL low-real + alvo 3R, SL-first causal.
Verifica nos 12 B (mostra gate a KEEP B#1-4 fundo, SKIP o resto) + caracteriza B#1-4 (spring vs HL,
espaço-ao-teto DENTRO do range) + null (buy-any-dip na porção baixa). RAW-only. Nada selado ainda."""
import json, bisect, random, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import macro_structural_v3 as MM
import b_macro_gate as BG
from a1_causal_entry import load_series, causal_entry, _is_swinglow, M_FRAC, LOWBACK, TRIG_WIN, HORIZON
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
POS_MAX = 40.0
BLK = ["XAUUSD_15m_replay_2025-02-25_to_2025-05-25.jsonl.gz", "XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz",
       "XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz", "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz"]
S = load_series(BLK); T, O, H, L, C, ATR, N = S["T"], S["O"], S["H"], S["L"], S["C"], S["ATR"], S["N"]
random.seed(20260715)
# range macro (1D) onset causal
reg = MM.build_layer1(); T1 = MM.T; KN1 = [x+86400 for x in T1]
_epis = []
for i in range(len(reg)):
    if _epis and _epis[-1][0] == reg[i]: _epis[-1][2] = i
    else: _epis.append([reg[i], i, i])
def macro_range(t0):
    """(onset_t, rlo, rhi, pos%) do range macro corrente até t0, causal. None se não RANGE."""
    i = bisect.bisect_right(KN1, t0)-1
    for s, a, b in _epis:
        if a <= i <= b and s == "RANGE":
            a15 = bisect.bisect_left(T, T1[a]); j = bisect.bisect_right(T, t0)-1
            rlo = min(L[a15:j+1]); rhi = max(H[a15:j+1])
            return T1[a], rlo, rhi, 100*(C[j]-rlo)/max(1e-9, rhi-rlo)
    return None

GT = json.load(open(HERE/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
B = sorted([f for f in GT["fundos"] if f.get("subclasse") == "B_range"], key=lambda x: x["t"])[:12]

def characterize(j, rlo):
    lows = [(p, L[p]) for p in range(max(M_FRAC, j-LOWBACK), j+1) if _is_swinglow(L, p, M_FRAC)]
    atr = ATR[j] or 5.0
    ab = min(range(max(0, j-LOWBACK), j+1), key=lambda z: L[z])
    swept = (rlo - L[ab])/atr if L[ab] < rlo else 0.0   # varreu abaixo do suporte macro?
    reclaim = (C[j]-L[ab])/atr
    is_spring = L[ab] <= rlo+0.1*atr and C[j] > rlo      # tocou/varreu suporte e fechou acima
    if len(lows) >= 2:
        rel = (lows[-1][1]-lows[-2][1])/atr
        st = "HL" if rel > 0.15 else ("LL/sweep" if rel < -0.15 else "EQL")
    else: st = "?"
    return round(swept, 2), round(reclaim, 2), is_spring, st

def null_lowerrange(j, sl, atr, tgt_mult=3):
    ab = min(range(max(0, j-LOWBACK), j+1), key=lambda z: L[z]); wins = nn = 0
    for _ in range(500):
        ei = random.randint(ab+1, min(N-2, ab+TRIG_WIN)); ent = C[ei]; r = ent-sl
        if r <= 0.05*atr: continue
        nn += 1; t = ent+tgt_mult*r
        for m in range(ei+1, min(N, ei+HORIZON+1)):
            if L[m] <= sl: break
            if H[m] >= t: wins += 1; break
    return round(100*wins/max(1, nn))

print(f"{'#':>3} {'data':16} {'gate-macro':>11} {'posMACRO%':>9} {'gate-pos':>8} {'=> ENGINE':>10} {'MB3':>12} {'R→teto':>7}")
kept = []
for n, f in enumerate(B, 1):
    t0 = int(f["t"]); j = bisect.bisect_right(T, t0)-1
    g = BG.gate_at(t0); mr = macro_range(t0)
    pos = mr[3] if mr else None; rlo, rhi = (mr[1], mr[2]) if mr else (None, None)
    pass_macro = g["b_long_allowed"]; pass_pos = pos is not None and pos <= POS_MAX
    engine_on = pass_macro and pass_pos
    e = causal_entry(S, j, "MB3")
    mb = f"{e['o']}({e['RATR']}A)" if e else "—"
    r2c = round((rhi-e["ent"])/e["R"], 1) if (e and rhi and e["R"] > 0) else None
    print(f"{n:>3} {ds(t0):16} {str(g['range_subtype']):>11} {(f'{pos:.0f}%' if pos is not None else '—'):>9} "
          f"{str(pass_pos):>8} {('ON' if engine_on else 'off'):>10} {mb:>12} {str(r2c):>6}R")
    if engine_on and e: kept.append((n, f, j, e, rlo, ATR[j] or 5.0))

print(f"\n== ENGINE ON em {len(kept)}/12 (esperado: B#1-4 fundo) ==")
w = 0
for n, f, j, e, rlo, atr in kept:
    sw, rc, spr, st = characterize(j, rlo)
    nl = null_lowerrange(j, e["sl"], atr)
    w += e["o"] == "WIN"
    print(f"  B#{n:<2} {ds(int(f['t']))}  MB3 {e['o']} R{e['R']}({e['RATR']}A) lag{e['lag']} | spring={spr} swept={sw} reclaim={rc} struct={st} | null-3R {nl}%")
print(f"  PAINEL B-engine: MB3 3R {w}/{len(kept)} WIN  (N={len(kept)} = seed; forward cresce)")