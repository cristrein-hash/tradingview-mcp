#!/usr/bin/env python3
"""BEAR-PULLBACK design · PROBE 1 (read-only, sem outcomes novos).
Extrai os 4 trades BEAR do Cris (#19 #20 #33 #34) de results/cris_trades_analysis_20260704.json,
imprime o registro completo, e caracteriza o CONTEXTO CAUSAL a CLOSE REAL na barra de entrada:
- regime v5h (via engine hour-causal, exec)
- âncora: candidato flush mais próximo <= entry no universo selado lab_g (dt em barras, features)
- prova de virada a close: closes acima/abaixo EMA21, sequência de up-closes, higher-low micro,
  posição no leg, RSI, ATR-regime, distância EMA21 em ATR
Nenhum R3 de sinais novos é lido. R3/outcome dos 4 dele = permitido (já publicado).
"""
import json, bisect, datetime as dt, io, contextlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ns = {"__name__": "engine", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
with contextlib.redirect_stdout(io.StringIO()):  # suprime painel publicado do engine (não é backtest novo)
    exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "engine", "exec"), ns)
regime_h = ns["regime_hourcausal"]

# timeline global
import glob
series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]

U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
U.sort(key=lambda r: r["cj_t"]); UT = [r["cj_t"] for r in U]

TRADES = json.load(open(HERE / "results" / "cris_trades_analysis_20260704.json"))
BEAR_IDS = {19, 20, 33, 34}

def asof(t): return bisect.bisect_right(TS, t) - 1

def ctx(i):
    """contexto causal a close real na barra i (usa só <= i)"""
    b = S[i]; atr = b.get("atr") or 1.0; ema = b.get("ema21")
    win = S[max(0, i - 19):i + 1]
    lo20 = min(x["l"] for x in win); hi20 = max(x["h"] for x in win)
    pos20 = (b["c"] - lo20) / ((hi20 - lo20) or atr)
    up3 = sum(1 for k in range(i - 2, i + 1) if k > 0 and S[k]["c"] > S[k - 1]["c"])
    closes_above_ema = sum(1 for k in range(i - 2, i + 1) if S[k].get("ema21") and S[k]["c"] > S[k]["ema21"])
    # higher-low micro: low das últimas 3 barras > min low das 8 anteriores
    hl = min(x["l"] for x in S[i - 2:i + 1]) > min(x["l"] for x in S[i - 10:i - 2]) if i >= 10 else None
    # flush recente: menor low das 96 barras e quantas barras atrás
    lows96 = [x["l"] for x in S[max(0, i - 95):i + 1]]
    j = lows96.index(min(lows96)); bars_since_low96 = len(lows96) - 1 - j
    dist_ema = (b["c"] - ema) / atr if ema else None
    return dict(t=b["t"], utc=dt.datetime.utcfromtimestamp(b["t"]).strftime("%Y-%m-%d %H:%M"),
                c=b["c"], atr=round(atr, 2), rsi=b.get("rsi"),
                dist_ema21_atr=round(dist_ema, 2) if dist_ema is not None else None,
                close_gt_ema21=int(b["c"] > ema) if ema else None,
                closes_above_ema_last3=closes_above_ema, up_closes_last3=up3,
                micro_higher_low=hl, pos20=round(pos20, 2),
                bars_since_low96=bars_since_low96,
                low96=min(lows96), depth_from_low96_atr=round((b["c"] - min(lows96)) / atr, 2))

for tr in TRADES:
    if tr["n"] not in BEAR_IDS: continue
    print("=" * 100)
    print(f"TRADE #{tr['n']}  {tr['utc']}  entry {tr['entry']} sl {tr['sl']} tgt {tr['tgt']} "
          f"risk {tr['risk']} rr {tr['rr']}  regime(file)={tr['regime']}  plan={tr['plan_outcome']} R={tr['plan_R']}")
    print(f"  cand_match={tr.get('cand_match')} cand_dt_bars={tr.get('cand_dt_bars')} in_base435={tr.get('in_base435')} "
          f"sysA={tr.get('sysA')} fb2_fundo={tr.get('fb2_fundo')}")
    print(f"  regime_hourcausal(recomputado) = {regime_h(tr['t'])}")
    i = asof(tr["t"])
    print(f"  barra timeline: idx {i} t {TS[i]} ({dt.datetime.utcfromtimestamp(TS[i]).strftime('%Y-%m-%d %H:%M')})")
    print("  CONTEXTO ENTRY:", json.dumps(ctx(i)))
    # risco em ATR
    atr = S[i].get("atr") or 1.0
    print(f"  risco/ATR = {tr['risk'] / atr:.2f}")
    # âncora: candidatos do universo com cj_t <= t, últimos 3
    k = bisect.bisect_right(UT, tr["t"]) - 1
    print("  ANCORAS (últimos 3 candidatos <= entry):")
    for kk in range(max(0, k - 2), k + 1):
        r = U[kk]; dtb = (tr["t"] - r["cj_t"]) // 900
        keep = {x: r.get(x) for x in ("cj_t", "g_v5h", "reclaim_atr", "g_atr_spike", "g_downrun",
                                      "g_sweep_depth", "g_flush_wick", "swept_prior_low", "sell_bub_w",
                                      "buy_bub_w", "g_rsi_div", "rsi_low", "g_knife", "falling_knife",
                                      "h1n_trend", "h1n_choch_up_rec", "htf_demand_any", "in_demand",
                                      "downleg_eff", "atr_regime", "g_ema21_dist", "legpos60", "up_closes_pc",
                                      "micro_hl", "g_bear_pullback_ok", "killzone", "g_hour")}
        print(f"    dt={dtb:>4} barras  {dt.datetime.utcfromtimestamp(r['cj_t']).strftime('%m-%d %H:%M')}  {json.dumps(keep)}")
    # feat do próprio trade (mapa MTF do arquivo)
    print("  feat(file):", json.dumps(tr.get("feat"))[:600])
