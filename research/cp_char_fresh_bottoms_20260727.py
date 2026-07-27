#!/usr/bin/env python3
"""GAP #2 — CARACTERIZAÇÃO (read-only, NÃO toca no Cp congelado). Mede os FUNDOS IDEAIS do Cris
(os 9 winners validados da semana + fundo de hoje) com os gates VERBATIM do cp_engine_live (import
direto, zero reimplementação), decompostos gate-a-gate, p/ caracterizar a classe "fundo fresco" que
o Cp não apanha. Contraste = GT profundo do Cp (legMag 18-32×, medido na sessão Cp — fora do buffer).
Multi-fatorial+trajetória (perna+auction+reclaim), não snapshot. Diagnóstico p/ DESENHO; árbitro=forward."""
import sys, json, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
R = "/Users/cristrein/tradingview-mcp/"
sys.path.insert(0, R + "my-strategy/strategies/xau_15m_long/reversal/CP_CAPITULATION")
import cp_engine_live as cp

hm = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%d/%m %H:%M")

bars = sorted([json.loads(l) for l in open(R + "my-strategy/core/bar_store/store/bars_15m.jsonl") if l.strip()], key=lambda b: b["t"])
T = [b["t"] for b in bars]; O = [b["o"] for b in bars]; H = [b["h"] for b in bars]
L = [b["l"] for b in bars]; C = [b["c"] for b in bars]
N = len(T)
ATR = cp.atr_series(H, L, C)
pairs = [(r["t"], r["plot"]) for r in (json.loads(l) for l in open(R + "my-strategy/core/bar_store/store/bubbles_15m.jsonl") if l.strip())]
BUYS, SELLS = cp.bubbles_from_pairs(pairs)
BT = [x["t"] for x in BUYS]; ST = [x["t"] for x in SELLS]

# FUNDOS IDEAIS (janelas Lisboa; o script acha o LOW mínimo e o swing-low fractal na janela)
def w(d0, h0, d1, h1):
    return (dt.datetime(2026, 7, d0, h0, 0, tzinfo=LX).timestamp(),
            dt.datetime(2026, 7, d1, h1, 0, tzinfo=LX).timestamp())
FUNDOS = [
    ("A fundo semana 16-17/07 (~3968, winners #1-#4)", w(16, 20, 17, 4)),
    ("B demanda 20/07 (~4000, winners #7-#9)",         w(20, 14, 21, 2)),
    ("C pullback 24/07 (~4048, teu long sexta)",       w(24, 11, 24, 16)),
    ("D fundo HOJE 27/07 (~4065, NY Low)",             w(27, 14, 27, 17)),
]

sls = set(cp.swing_lows(H, L, N))
print("=== CARACTERIZAÇÃO: fundos ideais × gates VERBATIM do Cp (LEGMIN=15, buy_dens>=0.25 OU leg_sell>=180) ===\n")
rows = []
for nome, (t0, t1) in FUNDOS:
    win = [i for i in range(N) if t0 <= T[i] <= t1]
    if not win:
        print(f"{nome}: SEM BARRAS na janela"); continue
    p = min(win, key=lambda i: L[i])                      # o low real da janela
    p_sl = p if p in sls else next((q for q in sorted(sls, key=lambda q: abs(q - p)) if abs(q - p) <= 6), p)
    p = p_sl
    hb = max(range(max(0, p - cp.LEGWIN), p + 1), key=lambda k: H[k])
    atr = ATR[p] or 5.0
    dur = max(1, p - hb)
    legmag = (H[hb] - L[p]) / atr
    is_lb = L[p] <= min(L[max(0, p - 192):p + 1]) + 1e-9
    bdens = cp.sz(BUYS, BT, T[hb], T[p]) / dur
    lsell = cp.sz(SELLS, ST, T[hb], T[p])
    g_leg = legmag >= cp.LEGMIN
    g_auc = (bdens >= 0.25) or (lsell >= 180)
    e = cp.entry_first(p, T, O, H, L, C, ATR, N)
    rows.append((nome, p, legmag, atr))
    print(f"{nome}")
    print(f"   fundo: low {L[p]} @ {hm(T[p])} (swing-low fractal {'sim' if p in sls else 'aprox'}) · perna desde {H[hb]:.1f} @ {hm(T[hb])} ({dur} barras)")
    print(f"   GATE legMag: {legmag:.1f}×ATR (precisa >=15) -> {'PASSA' if g_leg else 'FALHA'}   | ATR {atr:.2f}")
    print(f"   GATE is_leg_bottom(192): {'PASSA' if is_lb else 'FALHA'}")
    print(f"   GATE auction: buy_dens {bdens:.2f} (>=0.25?) · leg_sell {lsell} (>=180?) -> {'PASSA' if g_auc else 'FALHA'}")
    if e:
        print(f"   reclaim (entry_first): SIM @ {hm(T[e['k']])} ent {e['ent']} sl {e['sl']} tgt {e['tgt']}")
    else:
        print(f"   reclaim (entry_first): (ainda) NÃO em p+3..p+96")
    verdict = "APANHADO pelo Cp" if (g_leg and is_lb and g_auc and e) else \
              ("classe FRESCA (só legMag falha)" if (is_lb and g_auc and not g_leg) else "falha múltipla")
    print(f"   => {verdict}\n")

print("=== CONTRASTE (GT profundo do Cp, medições da sessão Cp — fora do buffer atual) ===")
print("   5 GT bear-2026: legMag 18-32×ATR · act_dens mediana 0,82 · todos APANHADOS pelo baseline\n")
print("=== RESUMO DA CLASSE ===")
for nome, p, legmag, atr in rows:
    print(f"   {nome[:44]:46s} legMag {legmag:5.1f}×  ({'>=15 Cp' if legmag>=15 else '<15 FRESCO'})")
