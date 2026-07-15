#!/usr/bin/env python3
"""ENGINE DE B v1.1 (Cris 2026-07-15, caminho (a) + refino spring aprovado) — retomada no FUNDO de range
plano. Composição causal:
  ① GATE MACRO   = b_macro_gate: RANGE_ORDERLY (crash-born=SKIP).
  ② BANDA CAUSAL = [p10 dos lows, p90 dos highs] do range-so-far (aterra ~[3245-3450] do Cris sem
                   hardcode; exclui a cauda do crash de Maio).
  ③ GATE POSIÇÃO = posição do LOW de demanda (anchor low) na banda <= 40% -> só a porção BAIXA
                   (suporte); rejeita continuação perto do topo (o streak-killer do Cris).
  ④ GATILHO      = MB3 + SPRING (o low varreu o suporte imediato e o MB3 reclamou acima) — refino
                   testado vs null (spring 45% vs 39% baseline; absorção REJEITADA por piorar). SL
                   low-real + alvo 3R (a1_causal_entry, mecânica A1/A2 já verificada).
Verifica nos 12 B (KEEP esperado = B#1-4 fundo, todos springs) + null. RAW-only 15M.
API: b_signal(t, S) -> dict. Nada selado; forward = árbitro. N=4 seed."""
import json, bisect, random, statistics, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import macro_structural_v3 as MM
import b_macro_gate as BG
from a1_causal_entry import load_series, causal_entry, _is_swinglow, M_FRAC, LOWBACK, TRIG_WIN, HORIZON
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
POS_MAX = 40.0; P_LO, P_HI = 10, 90
random.seed(20260715)
# range macro (1D) — episódios causais
_reg = MM.build_layer1(); _T1 = MM.T; _KN1 = [x+86400 for x in _T1]
_epis = []
for _i in range(len(_reg)):
    if _epis and _epis[-1][0] == _reg[_i]: _epis[-1][2] = _i
    else: _epis.append([_reg[_i], _i, _i])
def _pct(a, p):
    a = sorted(a); k = (len(a)-1)*p/100; f = int(k)
    return a[f]+(a[min(f+1, len(a)-1)]-a[f])*(k-f)

def _onset(t0):
    i = bisect.bisect_right(_KN1, t0)-1
    for s, a, b in _epis:
        if a <= i <= b and s == "RANGE": return _T1[a]
    return None

def causal_band(t0, S):
    """(support=p10 lows, resist=p90 highs) do range-so-far [onset, t0], causal. None se não RANGE."""
    o = _onset(t0)
    if o is None: return None
    T, H, L = S["T"], S["H"], S["L"]
    a = bisect.bisect_left(T, o); j = bisect.bisect_right(T, t0)-1
    if j-a < 20: return None
    return _pct(L[a:j+1], P_LO), _pct(H[a:j+1], P_HI)

def is_spring(e, S):
    """SPRING causal: o low-âncora varreu ABAIXO do suporte imediato (penúltimo swing-low) e o MB3
    fechou de volta ACIMA dele (grab de liquidez + reclaim). Refino aprovado (bate o null; absorção não)."""
    L, ATR = S["L"], S["ATR"]; ab = e["anchor_bar"]; atr = ATR[ab] or 5.0
    lows = [L[p] for p in range(max(M_FRAC, ab-64), ab) if _is_swinglow(L, p, M_FRAC)]
    if not lows: return False
    support = lows[-1]
    return L[ab] < support-0.1*atr and e["ent"] > support

def b_signal(t0, S):
    """Sinal causal do engine de B v1.1. dict(engine, reason, pos, band, entry, spring)."""
    j = bisect.bisect_right(S["T"], t0)-1
    g = BG.gate_at(t0)
    if not g["b_long_allowed"]:
        return {"engine": False, "reason": f"macro:{g['range_subtype'] or g['regime']}"}
    band = causal_band(t0, S)
    if band is None: return {"engine": False, "reason": "sem-banda"}
    sup, res = band
    e = causal_entry(S, j, "MB3")
    if not e: return {"engine": False, "reason": "sem-MB3"}
    anchor_low = S["L"][e["anchor_bar"]]
    pos = 100*(anchor_low-sup)/max(1e-9, res-sup)
    if pos > POS_MAX:
        return {"engine": False, "reason": f"pos {pos:.0f}%>topo", "pos": round(pos, 1), "band": (round(sup, 1), round(res, 1))}
    if not is_spring(e, S):
        return {"engine": False, "reason": "sem-spring", "pos": round(pos, 1), "band": (round(sup, 1), round(res, 1))}
    return {"engine": True, "pos": round(pos, 1), "band": (round(sup, 1), round(res, 1)), "entry": e, "spring": True,
            "room_to_res_R": round((res-e["ent"])/e["R"], 1) if e["R"] > 0 else None}

def _null(j, sl, atr, S):
    T, L, H, C, N = S["T"], S["L"], S["H"], S["C"], S["N"]
    ab = min(range(max(0, j-LOWBACK), j+1), key=lambda z: L[z]); wins = nn = 0
    for _ in range(500):
        ei = random.randint(ab+1, min(N-2, ab+TRIG_WIN)); ent = C[ei]; r = ent-sl
        if r <= 0.05*atr: continue
        nn += 1; tg = ent+3*r
        for m in range(ei+1, min(N, ei+HORIZON+1)):
            if L[m] <= sl: break
            if H[m] >= tg: wins += 1; break
    return round(100*wins/max(1, nn))

if __name__ == "__main__":
    BLK = ["XAUUSD_15m_replay_2025-02-25_to_2025-05-25.jsonl.gz", "XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz",
           "XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz", "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz"]
    S = load_series(BLK)
    GT = json.load(open(HERE/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
    B = sorted([f for f in GT["fundos"] if f.get("subclasse") == "B_range"], key=lambda x: x["t"])[:12]
    print(f"{'#':>3} {'data':16} {'ENGINE':>6} {'pos%':>6} {'banda':>15} {'MB3':>12} {'R→res':>6} {'null3R':>7} {'motivo':>16}")
    kept = []
    for n, f in enumerate(B, 1):
        r = b_signal(int(f["t"]), S)
        if r["engine"]:
            e = r["entry"]; j = bisect.bisect_right(S["T"], int(f["t"]))-1
            nl = _null(j, e["sl"], S["ATR"][j] or 5.0, S)
            kept.append((n, f, e, nl))
            print(f"{n:>3} {ds(int(f['t'])):16} {'ON':>6} {r['pos']:>5}% {str(r['band']):>15} {e['o']+'('+str(e['RATR'])+'A)':>12} {str(r['room_to_res_R']):>5}R {nl:>6}% {'':>16}")
        else:
            print(f"{n:>3} {ds(int(f['t'])):16} {'off':>6} {str(r.get('pos','-')):>6} {str(r.get('band','-')):>15} {'':>12} {'':>6} {'':>7} {r['reason']:>16}")
    w = sum(1 for _, _, e, _ in kept if e["o"] == "WIN")
    op = sum(1 for _, _, e, _ in kept if e["o"] == "OPEN")
    print(f"\n== PAINEL B-ENGINE v1 (N={len(kept)} seed) ==")
    print(f"  MB3 3R: {w} WIN · {sum(1 for _,_,e,_ in kept if e['o']=='LOSS')} LOSS · {op} OPEN")
    if kept:
        print(f"  null-3R médio: {statistics.mean([nl for *_ , nl in kept]):.0f}% (MB3 tem de bater)")
        print(f"  KEEP = " + ", ".join(f"B#{n}" for n, *_ in kept))
