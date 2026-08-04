#!/usr/bin/env python3
"""ESTUDO — que LEITURAS/FEATURES separam winners de losers no AMD H4 (Cris 2026-08-04, pós-auditoria
0/2/1 dos 3 sinais live). OBJETIVO: aumentar precisão MANTENDO a lógica base (sweep+reclaim H4 na killzone).
NÃO é aprovação de nada — é medição para desenho. Resolução MECÂNICA fiel (entry=retest do nível, SL além
do sweep_wick+0.1ATR, alvo=2R, horizonte 48h em 1H). Amostra = catálogo com cobertura 1H (2024-05→hoje).
Reprodutível: `python3 research/amd_feature_separation_study_20260804.py`. Painel completo + sub-janelas + null.
CAVEATS (ver Devil's Advocate no fim): N pequeno; múltiplas comparações; proxy de entry != FVG-retest exato."""
import json, sys
from pathlib import Path

R = Path("/Users/cristrein/tradingview-mcp")


def load(f): return [json.loads(l) for l in open(R / f) if l.strip()]


def norm(b): return {"t": b.get("t") or b.get("time"), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]}


H1 = sorted((norm(b) for b in load("my-strategy/research/revalidation/raw_1h_ohlc.jsonl")), key=lambda b: b["t"])
H4 = sorted((norm(b) for b in load("my-strategy/research/revalidation/raw_4h_ohlc.jsonl")), key=lambda b: b["t"])
SETUPS = load("my-strategy/strategies/xau_amd/amd_live/.amd_state/amd_setups.jsonl")


def atr4(t, n=14):
    past = [b for b in H4 if b["t"] < t][-n - 1:]
    if len(past) < n + 1: return None
    trs = [max(b["h"] - b["l"], abs(b["h"] - p["c"]), abs(b["l"] - p["c"])) for p, b in zip(past, past[1:])]
    return sum(trs) / len(trs)


def resolve(s):
    """Entry = retest do nível após reclaim; SL além do sweep_wick+0.1ATR; alvo 2R; 48h em 1H."""
    t0 = s["h4_bar_t"] + 4 * 3600
    lvl, wick, d = s["level"], s["sweep_wick"], s["dir"]
    a = atr4(s["h4_bar_t"])
    if a is None: return None
    buf = 0.1 * a
    if d == "short": sl = wick + buf; entry = lvl; tgt = entry - 2 * (sl - entry)
    else: sl = wick - buf; entry = lvl; tgt = entry + 2 * (entry - sl)
    risk = abs(entry - sl)
    if risk <= 0: return None
    seq = [b for b in H1 if t0 <= b["t"] <= t0 + 48 * 3600]
    if len(seq) < 6: return None
    filled = False; res = None; mfe = mae = 0
    for b in seq:
        if not filled:
            if b["l"] <= entry <= b["h"]: filled = True
            else: continue
        if d == "short":
            mfe = max(mfe, (entry - b["l"]) / risk); mae = max(mae, (b["h"] - entry) / risk)
            if b["h"] >= sl: res = "LOSS"; break
            if b["l"] <= tgt: res = "WIN"; break
        else:
            mfe = max(mfe, (b["h"] - entry) / risk); mae = max(mae, (entry - b["l"]) / risk)
            if b["l"] <= sl: res = "LOSS"; break
            if b["h"] >= tgt: res = "WIN"; break
    if not filled: return {"fill": False}
    if res is None: return {"fill": True, "res": "OPEN"}
    return {"fill": True, "res": res, "mfe": round(mfe, 2), "mae": round(mae, 2), "R": 2 if res == "WIN" else -1}


def feats(s):
    t, lvl, d = s["h4_bar_t"], s["level"], s["dir"]
    a = atr4(t)
    past4 = [b for b in H4 if b["t"] <= t][-20:]
    if len(past4) < 20 or not a: return None
    hi = max(b["h"] for b in past4); lo = min(b["l"] for b in past4); rng = hi - lo or 1
    rpos = (s["h4_close"] - lo) / rng
    ema = sum(b["c"] for b in past4) / 20
    with_trend = (d == "long" and s["h4_close"] > ema) or (d == "short" and s["h4_close"] < ema)
    return {"close_pos": s["close_pos"], "sweep_depth": round(abs(s["sweep_wick"] - lvl) / a, 2),
            "range_pos": round(rpos, 2), "with_4h_trend": with_trend, "killzone": s.get("killzone"),
            "dir": d, "ts": s["h4_bar_ts"]}


def build(min_ts="2024-05-25"):
    rows = []
    for s in SETUPS:
        if s["h4_bar_ts"] < min_ts: continue
        r = resolve(s); f = feats(s)
        if r is None or f is None or not r.get("fill") or r.get("res") == "OPEN": continue
        rows.append({**f, **r})
    return rows


def panel(name, bk):
    print(f"\n— {name} —")
    for lbl, sub in bk:
        if not sub: continue
        w = sum(1 for x in sub if x["res"] == "WIN"); N = len(sub); sr = sum(x["R"] for x in sub)
        print(f"   {lbl:24} N={N:3} WR={w / N * 100:3.0f}% sumR={sr:+5.0f} avgR={sr / N:+.2f}")


def main():
    rows = build()
    n = len(rows); wins = sum(1 for x in rows if x["res"] == "WIN")
    print(f"AMOSTRA (fill+fechado, 1H, 2024-05→hoje): N={n} | WR={wins / n * 100:.0f}% | "
          f"sumR={sum(x['R'] for x in rows):+.0f} | avgR={sum(x['R'] for x in rows) / n:+.2f}")
    print(f"  base: shorts {sum(1 for x in rows if x['dir'] == 'short')} / longs {sum(1 for x in rows if x['dir'] == 'long')}")
    panel("DIREÇÃO", [("long", [x for x in rows if x["dir"] == "long"]), ("short", [x for x in rows if x["dir"] == "short"])])
    panel("COM/CONTRA tendência 4H", [("com-tendência", [x for x in rows if x["with_4h_trend"]]),
                                       ("contra-tendência", [x for x in rows if not x["with_4h_trend"]])])
    panel("RANGE POS", [("fundo <0.33", [x for x in rows if x["range_pos"] < 0.33]),
                        ("meio", [x for x in rows if 0.33 <= x["range_pos"] < 0.66]),
                        ("topo >=0.66", [x for x in rows if x["range_pos"] >= 0.66])])
    panel("CLOSE_POS", [("fraco <0.3", [x for x in rows if x["close_pos"] < 0.3]),
                        ("médio", [x for x in rows if 0.3 <= x["close_pos"] < 0.7]),
                        ("forte >=0.7", [x for x in rows if x["close_pos"] >= 0.7])])
    panel("SWEEP DEPTH", [("raso <0.5", [x for x in rows if x["sweep_depth"] < 0.5]),
                          ("médio", [x for x in rows if 0.5 <= x["sweep_depth"] < 1.0]),
                          ("fundo >=1.0", [x for x in rows if x["sweep_depth"] >= 1.0])])
    panel("KILLZONE", [(kz, [x for x in rows if x["killzone"] == kz]) for kz in ("London", "NY", "London/NY")])
    # VALIDAÇÃO 1 — sub-janelas temporais (a separação range-meio sobrevive fora da amostra completa?)
    mid = sorted(x["ts"] for x in rows)[len(rows) // 2]
    for lbl, sub in (("1ª metade", [x for x in rows if x["ts"] < mid]), ("2ª metade", [x for x in rows if x["ts"] >= mid])):
        rmid = [x for x in sub if 0.33 <= x["range_pos"] < 0.66]
        if rmid:
            w = sum(1 for x in rmid if x["res"] == "WIN")
            print(f"\n[sub-janela {lbl}] range-meio: N={len(rmid)} WR={w / len(rmid) * 100:.0f}% "
                  f"sumR={sum(x['R'] for x in rmid):+.0f}")
    # VALIDAÇÃO 2 — null: baseline global vs melhor bucket (quão fácil é obter isto por acaso?)
    best = [x for x in rows if 0.33 <= x["range_pos"] < 0.66]
    print(f"\n[null] baseline global avgR={sum(x['R'] for x in rows) / n:+.2f} vs "
          f"range-meio avgR={sum(x['R'] for x in best) / len(best):+.2f} (N_bucket={len(best)}; "
          f"buckets testados ~18 → esperado 1 spurious por acaso)")
    return rows


if __name__ == "__main__":
    main()
