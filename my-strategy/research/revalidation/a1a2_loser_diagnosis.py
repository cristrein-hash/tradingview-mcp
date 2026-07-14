#!/usr/bin/env python3
"""DIAGNÓSTICO dos LOSERS A1/A2 (Cris 2026-07-15): "os losers são por SL pequeno ou entry em região
errada?". Para cada entrada causal (a1_causal_entry): (1) IGNORANDO o SL, o preço chega ao 3R dentro
do horizonte? (recupera => SL-pequeno, região OK). (2) Com SL MAIS FUNDO (âncora = MENOR low até à
entrada − 0.1ATR, e variante buffer 0.5ATR), o loser vira WIN? E o agregado piora os winners? RAW HD."""
import json, bisect, statistics
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
from a1_causal_entry import load_series, causal_entry, HORIZON, LOWBACK
import datetime as dt
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
BLK = ["XAUUSD_15m_replay_2025-02-25_to_2025-05-25.jsonl.gz", "XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz",
       "XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz", "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz"]
S = load_series(BLK); T, O, H, L, C, ATR, N = S["T"], S["O"], S["H"], S["L"], S["C"], S["ATR"], S["N"]

def slfirst(ei, sl, tgt):
    for m in range(ei+1, min(N, ei+HORIZON+1)):
        if L[m] <= sl: return "LOSS", m-ei
        if H[m] >= tgt: return "WIN", m-ei
    return "OPEN", None
def reaches_tgt_ignoring_sl(ei, tgt):
    for m in range(ei+1, min(N, ei+HORIZON+1)):
        if H[m] >= tgt: return True, m-ei
    return False, None

GT = json.load(open(HERE/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
for layer in ("A1_pullback_fundo", "A2_pullback_raso"):
    F = sorted([f for f in GT["fundos"] if f.get("subclasse") == layer], key=lambda x: x["t"])
    print(f"\n{'='*84}\n{layer} (N={len(F)}) — diagnóstico dos LOSERS (SL-pequeno vs região-errada) + SL-fundo\n{'='*84}")
    losers = []; orig_w = deep_w = wide_w = 0; deep_flip = 0; deep_break = 0
    for n, f in enumerate(F, 1):
        j = bisect.bisect_right(T, int(f["t"]))-1
        e = causal_entry(S, j, "MB3")
        if not e: continue
        ei, ent, sl, tgt, o, ab = e["ei"], e["ent"], e["sl"], e["tgt"], e["o"], e["anchor_bar"]
        orig_w += o == "WIN"
        # SL mais fundo: âncora = menor low em [j-16, ei] (o low real, não o fractal raso)
        lo0 = max(0, j-LOWBACK); kdeep = min(range(lo0, ei+1), key=lambda k: L[k]); deep_low = L[kdeep]
        atr = ATR[kdeep] or 5.0; sl_deep = round(deep_low-0.1*atr, 2); tgt_deep = round(ent+3*(ent-sl_deep), 2)
        od, _ = slfirst(ei, sl_deep, tgt_deep); deep_w += od == "WIN"
        # variante buffer largo 0.5ATR sobre o mesmo low fractal
        sl_wide = round(L[ab]-0.5*(ATR[ab] or 5.0), 2); tgt_wide = round(ent+3*(ent-sl_wide), 2)
        ow, _ = slfirst(ei, sl_wide, tgt_wide); wide_w += ow == "WIN"
        if o == "LOSS":
            rec, bb = reaches_tgt_ignoring_sl(ei, tgt)
            losers.append((n, ds(int(f['t'])), e["RATR"], rec, bb, od, ow))
            if od == "WIN": deep_flip += 1
        if o == "WIN" and od != "WIN": deep_break += 1
    print(f"  ORIGINAL WIN {orig_w}/{len(F)} · SL-fundo(low real) WIN {deep_w}/{len(F)} · SL-buffer0.5ATR WIN {wide_w}/{len(F)}")
    print(f"  LOSERS (RATR · recupera-3R-ignorando-SL? · SL-fundo · SL-0.5ATR):")
    for n, d, ratr, rec, bb, od, ow in losers:
        print(f"    #{n:2d} {d}  R/ATR {ratr:>4}  recupera-3R={'SIM(+%s b)'%bb if rec else 'NÃO'}  | SL-fundo={od}  SL-0.5ATR={ow}")
    nrec = sum(1 for x in losers if x[3])
    print(f"  => dos {len(losers)} losers: {nrec} RECUPERAM ao 3R ignorando o SL (=SL-pequeno, região OK) · "
          f"{len(losers)-nrec} NÃO (=região errada). SL-fundo converteu {deep_flip} losers mas partiu {deep_break} winners.")
