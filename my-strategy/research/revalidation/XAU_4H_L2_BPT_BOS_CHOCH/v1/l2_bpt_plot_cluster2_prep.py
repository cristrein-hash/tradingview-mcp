#!/usr/bin/env python3
"""PREP (read-only, NAO toca chart) — Cluster 2 'Macro negativo: runner legitimo vs bear-pullback trap'.
10 episodios em 5 pares, sub-blocos A/B/C/D. entry=close; SL estrutural (sl_atr; fallback demand-anchored rotulado);
TP=2:1 fixo (blind). + checagem pre-plot: macro condition (weekly<0, casc<=-2), superficie, e campos que DIFEREM
fora da superficie (RSI, dist_supply, acceptance, flush, base, dist_POC, structure). Saida: /tmp/cluster2_trades.json"""
import json, csv, datetime as dt
RR = "repro_recovery"; D = "results"
F = [json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
H = [r['high'] for r in F]; L = [r['low'] for r in F]; C = [r['close'] for r in F]; TS = [r['ts_epoch'] for r in F]
ATR = [None] * len(F); trs = []
for i in range(1, len(F)):
    trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
    if i >= 14: ATR[i] = sum(trs[i - 14:i]) / 14
SL = {}
for r in csv.DictReader(open(f"{D}/l2_bpt_sl_context_policy_results.csv")):
    try: SL[int(r['i'])] = float(r['sl_atr'])
    except (ValueError, KeyError): continue
DEM = {}
for l in open(f"{RR}/qual_packets.jsonl"):
    r = json.loads(l)
    try:
        v = r.get('dist_4h_demand_low_atr')
        if v is not None: DEM[int(r['bar_idx'])] = float(v)
    except (ValueError, KeyError, TypeError): continue
DOSS = {int(json.loads(l)['bar_idx']): json.loads(l) for l in open(f"{D}/l2_bpt_reader_dossier_276.jsonl")}
def fn(v):
    try: return float(v)
    except (TypeError, ValueError): return None
# pares por sub-bloco (RUNNER, trap) — seleção aprovada pelo Cris
SUBBLOCKS = {
    "A. macro negativo + clean sky":        [(5826, "R"), (1623, "trap")],
    "B. macro negativo + supply perto":     [(4401, "R"), (3825, "trap")],
    "C. macro negativo + flush sob supply": [(1522, "R"), (1873, "trap"), (5627, "R"), (1775, "trap")],
    "D. macro negativo extremo / excecao":  [(3949, "R"), (3929, "trap")],
}
BLUE = "#1a73e8"
trades = []
for blk, members in SUBBLOCKS.items():
    print("\n" + "=" * 110); print(blk)
    print(f"  {'bar':>5} {'date':10} {'wk':>6} {'casc':>5} {'flush':>14} {'accept':>18} {'rsi':>5} {'distSup':>8} {'distPOC':>8} {'struct':>16} | {'SL':>9} {'TP2R':>9} {'risk':>6} src")
    for b, role in members:
        d = DOSS[b]; c1 = d["camada_1_backbone"]; c0 = d["camada_0_form"]
        pf = c0.get("path_form_276", {}); mic = c0.get("micro_fields_276", {}); rb = c1.get("regime_B", {})
        wk = c1.get("weekly_1d_context", {})
        weekly = fn(wk.get("weekly_slope_decisions")); weekly = weekly if weekly is not None else fn(wk.get("weekly_slope_20pct"))
        entry = C[b]; atr = ATR[b]; sl_atr = SL.get(b); src = "sl_atr"
        if sl_atr is None:
            sl_atr = DEM.get(b); src = "demand_anchored"
        if sl_atr is None or atr is None:
            print(f"  {b:>5} SEM SL — pular"); continue
        risk = sl_atr * atr; stop = round(entry - risk, 2); target = round(entry + 2 * risk, 2)
        ets = dt.datetime.utcfromtimestamp(TS[b]).strftime('%Y-%m-%d')
        print(f"  {b:>5} {ets:10} {weekly:>6} {rb.get('cascade_score'):>5} {str(pf.get('flush')):>14} {str(pf.get('acceptance')):>18} "
              f"{str(mic.get('rsi')):>5} {str(mic.get('dist_4h_supply_low_atr')):>8} {str(pf.get('dist_poc_atr')):>8} {str(pf.get('structure')):>16} | "
              f"{stop:>9.2f} {target:>9.2f} {risk:>6.1f} {src}")
        trades.append({"id": b, "role": role, "subblock": blk[:1], "ts": int(TS[b]), "entry": round(entry, 2),
                       "stop": stop, "target": target, "label_price": round(entry + 0.5 * risk, 2),
                       "p2_time": int(TS[b]) + 20 * 14400, "ticks_stop": int(round(risk / 0.01)),
                       "ticks_target": int(round(2 * risk / 0.01)), "sl_source": src, "label_color": BLUE})
json.dump(trades, open("/tmp/cluster2_trades.json", "w"), indent=2)
fb = [t['id'] for t in trades if t['sl_source'] != 'sl_atr']
print(f"\n{len(trades)} trades -> /tmp/cluster2_trades.json | SL fallback (demand-anchored): {fb or 'nenhum'}")
print("Blind: TP=2:1 fixo, label AZUL, SEM outcome/R/win-loss. Macro: weekly<0 e cascade<=-2 em TODOS (confirmar acima).")
