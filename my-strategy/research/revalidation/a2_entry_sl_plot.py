#!/usr/bin/env python3
"""PLOT VISUAL A2 (ordem Cris 2026-07-14): mostra CONCRETAMENTE, para 3 fundos A2, o ENTRY (MB3) e as
DUAS versões de SL — SL-dip (low−0.1ATR, SELADO, degenerado p/ dip raso) vs SL-ESTRUTURAL
(low−0.75ATR, R real) — + alvo 3R (estrutural). Para o Cris VER a diferença no chart 15M.
long_position (entry→SL-estrutural→3R) + linhas dos 2 SL + labels. NÃO apaga nada. Pausa obrigatória."""
import gzip, json, bisect, sys, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = Path("/Users/cristrein/tradingview-mcp"); sys.path.insert(0, str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
BLOCKS = ["XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz", "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz"]
PAUSE = Path("/tmp/claude_recheck.paused"); BAR = 900; LOWBACK, LOWFWD, TRIG_WIN = 16, 8, 48
PICK = [4, 11, 17]        # A2 index (out / dez-undercut / jan-parabólico)
STRUCT_BUF = 0.75         # SL estrutural = low − 0.75ATR (engine: 0.5-1ATR abaixo do sweep)
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")

bars = {}
for blk in BLOCKS:
    with gzip.open(RAW/blk, "rt") as fh:
        for l in fh:
            i = l.find('"ohlcv":')
            if i < 0: continue
            s = l.find('[', i); e = l.find(']', s)
            if s < 0 or e < 0: continue
            try: arr = json.loads(l[s:e+1])
            except Exception: continue
            for b in arr:
                t = b.get("time")
                if t is None: continue
                if t not in bars: bars[t] = [b["open"], b["high"], b["low"], b["close"]]
                else: bars[t][1] = max(bars[t][1], b["high"]); bars[t][2] = min(bars[t][2], b["low"]); bars[t][3] = b["close"]
T = sorted(bars); O=[bars[t][0] for t in T]; H=[bars[t][1] for t in T]; L=[bars[t][2] for t in T]; C=[bars[t][3] for t in T]
N = len(T); ATR=[None]*N; trs=[]
for i in range(N):
    if i > 0: trs.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
    ATR[i] = sum(trs[-14:])/14 if len(trs) >= 14 else None
GT = json.load(open(HERE/"results"/"REGIME_GT_FUNDOS_UNIFIED_20260714.json"))
A2 = sorted([f for f in GT["fundos"] if f.get("subclasse") == "A2_pullback_raso"], key=lambda x: x["t"])

def setup(f):
    t0 = int(f["t"]); j = bisect.bisect_right(T, t0)-1
    lo0, hi0 = max(0, j-LOWBACK), min(N, j+LOWFWD+1); al = min(range(lo0, hi0), key=lambda k: L[k])
    low = L[al]; atr = ATR[al] or 5.0
    ei = next((k for k in range(al+1, min(N, al+TRIG_WIN+1)) if C[k] > O[k] and C[k] > H[k-1]), None)
    if ei is None: return None
    ent = C[ei]; dip_sl = round(low-0.1*atr, 2); str_sl = round(low-STRUCT_BUF*atr, 2)
    return {"t_low": T[al], "t_ent": T[ei], "ent": round(ent, 2), "atr": round(atr, 1),
            "dip_sl": dip_sl, "str_sl": str_sl, "R_dip": round(ent-dip_sl, 2), "R_str": round(ent-str_sl, 2),
            "tgt3R": round(ent+3*(ent-str_sl), 2), "tgt3R_dip": round(ent+3*(ent-dip_sl), 2)}

def main():
    assert PAUSE.exists()
    c = MCPClient(); c.start()
    try:
        st = c.call_tool("chart_get_state")
        if st.get("symbol") != "PEPPERSTONE:XAUUSD": print(json.dumps({"HARD_STOP": st.get("symbol")})); return 1
        if str(st.get("resolution")) not in ("15", "15m"): c.call_tool("chart_set_timeframe", {"timeframe": "15"})
        # LIMPAR só as plotagens dos fundos (long_position/text/linhas); MANTER retângulos (blocos macro)
        rm = kp = 0
        for it in c.call_tool("draw_list").get("shapes", []):
            if it.get("name") == "rectangle": kp += 1; continue
            if c.call_tool("draw_remove_one", {"entity_id": it["id"]}).get("success"): rm += 1
        print(json.dumps({"removidos_nao_retangulo": rm, "retangulos_mantidos": kp}))
        drawn = 0
        for idx in PICK:
            f = A2[idx-1]; sx = setup(f)
            if not sx: continue
            print(f"A2_{idx:02d} {ds(f['t'])}: entry {sx['ent']} | SL-dip {sx['dip_sl']} (R={sx['R_dip']}pt) | "
                  f"SL-estrut {sx['str_sl']} (R={sx['R_str']}pt) | 3R-estrut {sx['tgt3R']}")
            # long_position: entry -> SL-estrutural -> 3R-estrutural
            c.call_tool("draw_shape", {"shape": "long_position",
                "point": {"time": sx["t_ent"], "price": sx["ent"]},
                "point2": {"time": sx["t_ent"]+20*BAR, "price": sx["tgt3R"]},
                "overrides": json.dumps({"stopLevel": price_to_ticks_offset(sx["ent"], sx["str_sl"]),
                                          "profitLevel": price_to_ticks_offset(sx["ent"], sx["tgt3R"])})})
            # linhas dos 2 SL + label do entry
            for price, txt, col in ((sx["dip_sl"], f"A2#{idx} SL-dip 0.1ATR R={sx['R_dip']}pt (DEGENERADO)", "#c62828"),
                                     (sx["str_sl"], f"A2#{idx} SL-estrutural 0.75ATR R={sx['R_str']}pt", "#6a1b9a"),
                                     (sx["ent"], f"A2#{idx} ENTRY MB3 {sx['ent']}", "#1a8917")):
                c.call_tool("draw_shape", {"shape": "horizontal_line",
                    "point": {"time": sx["t_ent"], "price": price},
                    "overrides": json.dumps({"color": col, "linewidth": 1})})
                c.call_tool("draw_shape", {"shape": "text", "point": {"time": sx["t_ent"], "price": price},
                    "text": txt, "overrides": json.dumps({"color": col, "fontsize": 10, "bold": True})})
                drawn += 1
        c.call_tool("chart_scroll_to_date", {"date": ds(A2[PICK[0]-1]["t"])[:10]})
        print(json.dumps({"drawn_levels": drawn}))
    finally:
        try: c.stop()
        except Exception: pass

if __name__ == "__main__":
    main()
