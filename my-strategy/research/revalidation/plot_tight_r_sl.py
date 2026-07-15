#!/usr/bin/env python3
"""PLOT das 8 ops tight-R cujo SL MUDOU (ordem Cris 2026-07-15): mostra no chart 15M o ENTRY (MB3),
o SL ANTIGO (fractal raso, linha tracejada vermelha) e o SL NOVO (low-real, roxo) + alvo 3R novo +
label com o resultado (flip LOSS->WIN / WIN->LOSS / mantém). Apaga plotagens anteriores (mantém
retângulos macro). NÃO faz screenshot (Cris faz o visual). Pausa obrigatória. RAW 15M direto do HD."""
import json, bisect, sys, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = Path("/Users/cristrein/tradingview-mcp"); sys.path.insert(0, str(REPO/"alert-bridge")); sys.path.insert(0, str(HERE))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
from a1_causal_entry import load_series, _is_swinglow, M_FRAC, TRIG_WIN, LOWBACK, HORIZON
PAUSE = Path("/tmp/claude_recheck.paused"); BAR = 900
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
BLK = ["XAUUSD_15m_replay_2025-02-25_to_2025-05-25.jsonl.gz", "XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz",
       "XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz", "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz"]
# (layer, idx_1based) das 8 tight-R
OPS = [("A1_pullback_fundo", 1), ("A1_pullback_fundo", 10), ("A1_pullback_fundo", 13),
       ("A2_pullback_raso", 6), ("A2_pullback_raso", 10), ("A2_pullback_raso", 13),
       ("A2_pullback_raso", 15), ("A2_pullback_raso", 16)]
# resultados SELADOS autoritativos (painéis a1_causal_entry): losers por regra
OLD_LOSERS = {"A1": {1, 10, 13}, "A2": {10, 13, 15, 16}}   # SL fractal raso
NEW_LOSERS = {"A1": {1}, "A2": {6, 13}}                     # SL low-real (versão aprovada)
S = load_series(BLK); T, O, H, L, C, ATR, N = S["T"], S["O"], S["H"], S["L"], S["C"], S["ATR"], S["N"]
GT = json.load(open(HERE/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))

def outcome(ei, sl, tgt):
    for m in range(ei+1, min(N, ei+HORIZON+1)):
        if L[m] <= sl: return "LOSS"
        if H[m] >= tgt: return "WIN"
    return "OPEN"

def op_detail(layer, idx):
    F = sorted([f for f in GT["fundos"] if f.get("subclasse") == layer], key=lambda x: x["t"])
    j = bisect.bisect_right(T, int(F[idx-1]["t"]))-1
    fr_low = float("inf"); fr_bar = None
    for p in range(max(M_FRAC, j-LOWBACK), j-M_FRAC+1):
        if _is_swinglow(L, p, M_FRAC) and L[p] < fr_low: fr_low, fr_bar = L[p], p
    for k in range(j, min(N, j+TRIG_WIN)):
        p = k-M_FRAC
        if p >= max(M_FRAC, j-LOWBACK) and _is_swinglow(L, p, M_FRAC) and L[p] < fr_low: fr_low, fr_bar = L[p], p
        if fr_bar is None or k <= fr_bar: continue
        if not (C[k] > O[k] and C[k] > H[k-1]): continue
        lo0 = max(0, j-LOWBACK); rb = min(range(lo0, k+1), key=lambda z: L[z]); real_low = L[rb]
        atr_f, atr_r = ATR[fr_bar] or 5.0, ATR[rb] or 5.0
        old_sl = round(fr_low-0.1*atr_f, 2); new_sl = round(real_low-0.1*atr_r, 2); ent = round(C[k], 2)
        new_tgt = round(ent+3*(ent-new_sl), 2)
        lay = "A1" if layer.startswith("A1") else "A2"
        oo = "LOSS" if idx in OLD_LOSERS[lay] else "WIN"; no = "LOSS" if idx in NEW_LOSERS[lay] else "WIN"
        flip = f"{oo}->{no}" if oo != no else f"{no} (mantém)"
        return {"t_ent": T[k], "ent": ent, "old_sl": old_sl, "new_sl": new_sl, "new_tgt": new_tgt,
                "R_new": round(ent-new_sl, 2), "oo": oo, "no": no, "flip": flip,
                "old_valid": old_sl < ent}   # A2#6: SL fractal ficou ACIMA do entry (entry tb mudou)
    return None

def main():
    assert PAUSE.exists(), "pause flag ausente"
    c = MCPClient(); c.start()
    try:
        st = c.call_tool("chart_get_state")
        if "XAUUSD" not in str(st.get("symbol", "")):
            print(json.dumps({"HARD_STOP_symbol": st.get("symbol")})); return 1
        if str(st.get("resolution")) not in ("15", "15m"): c.call_tool("chart_set_timeframe", {"timeframe": "15"})
        rm = kp = 0
        for it in c.call_tool("draw_list").get("shapes", []):
            if it.get("name") == "rectangle": kp += 1; continue
            if c.call_tool("draw_remove_one", {"entity_id": it["id"]}).get("success"): rm += 1
        print(json.dumps({"removidos_nao_retangulo": rm, "retangulos_mantidos": kp}))
        first_t = None
        for layer, idx in OPS:
            tag = ("A1#%d" % idx) if layer.startswith("A1") else ("A2#%d" % idx)
            d = op_detail(layer, idx)
            if not d: print(f"{tag}: SEM-ENTRY"); continue
            if first_t is None: first_t = d["t_ent"]
            print(f"{tag} {ds(d['t_ent'])}: entry {d['ent']} | SL {d['old_sl']}->{d['new_sl']} (R {d['R_new']}pt) | 3R {d['new_tgt']} | {d['flip']}")
            c.call_tool("draw_shape", {"shape": "long_position",
                "point": {"time": d["t_ent"], "price": d["ent"]},
                "point2": {"time": d["t_ent"]+20*BAR, "price": d["new_tgt"]},
                "overrides": json.dumps({"stopLevel": price_to_ticks_offset(d["ent"], d["new_sl"]),
                                          "profitLevel": price_to_ticks_offset(d["ent"], d["new_tgt"])})})
            lines = [(d["new_sl"], f"{tag} SL NOVO low-real R={d['R_new']}pt", "#6a1b9a"),
                     (d["ent"], f"{tag} ENTRY MB3 {d['ent']} | {d['flip']}", "#1a8917")]
            if d["old_valid"]:  # só desenha o SL antigo quando era válido (abaixo do entry)
                lines.insert(0, (d["old_sl"], f"{tag} SL ANTIGO (fractal raso)", "#c62828"))
            else:
                lines[1] = (d["ent"], f"{tag} ENTRY MB3 {d['ent']} | {d['flip']} (entry+SL mudaram)", "#1a8917")
            for price, txt, col in lines:
                c.call_tool("draw_shape", {"shape": "horizontal_line", "point": {"time": d["t_ent"], "price": price},
                    "overrides": json.dumps({"color": col, "linewidth": 1})})
                c.call_tool("draw_shape", {"shape": "text", "point": {"time": d["t_ent"], "price": price},
                    "text": txt, "overrides": json.dumps({"color": col, "fontsize": 10, "bold": True})})
        if first_t: c.call_tool("chart_scroll_to_date", {"date": ds(first_t)[:10]})
        print(json.dumps({"plotadas": len(OPS)}))
    finally:
        try: c.stop()
        except Exception: pass

if __name__ == "__main__":
    main()
