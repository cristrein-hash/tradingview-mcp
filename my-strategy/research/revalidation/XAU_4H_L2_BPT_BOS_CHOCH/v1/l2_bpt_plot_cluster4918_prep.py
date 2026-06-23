#!/usr/bin/env python3
"""PREP (read-only, NÃO toca chart) dos 6 trades do cluster 4918 p/ plotagem CANÔNICA blind.
Convenção: long_position + label AZUL. entry=close do bar de entrada. SL=estrutural (sl_atr contextual demanda-4H,
de l2_bpt_sl_context_policy_results.csv — SÓ a coluna sl_atr; outcome IGNORADO). TP=2:1 neutro (nunca >2R) = blind.
Saída: /tmp/cluster4918_trades.json (entry/stop/target/ts/id/label_color — SEM outcome)."""
import json, csv
RR = "repro_recovery"; D = "results"
F = [json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
H = [r['high'] for r in F]; L = [r['low'] for r in F]; C = [r['close'] for r in F]; TS = [r['ts_epoch'] for r in F]
ATR = [None] * len(F); trs = []
for i in range(1, len(F)):
    trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
    if i >= 14:
        ATR[i] = sum(trs[i - 14:i]) / 14
# SL estrutural por episódio: SÓ sl_atr (ignora exit_type/R = outcome)
SL = {}
for r in csv.DictReader(open(f"{D}/l2_bpt_sl_context_policy_results.csv")):
    try:
        SL[int(r['i'])] = float(r['sl_atr'])
    except (ValueError, KeyError):
        continue
# fallback demand-anchored (causal) p/ episódios sem sl_atr validado: dist_4h_demand_low_atr do qual_packet
DEM = {}
for l in open(f"{RR}/qual_packets.jsonl"):
    r = json.loads(l)
    try:
        v = r.get('dist_4h_demand_low_atr')
        if v is not None:
            DEM[int(r['bar_idx'])] = float(v)
    except (ValueError, KeyError, TypeError):
        continue
# cluster 3a (24) completo = 8 sósias de superfície + 4926 (continuação 3b). ALREADY = já plotados na 1ª rodada.
CLUSTER = [4918, 1661, 5701, 6887, 7426, 8878, 8923, 8940, 4926]
ALREADY = {4918, 4926, 1661, 5701, 8878, 6887}
BLUE = "#1a73e8"
trades = []
print(f"{'bar':>5} {'entry_ts':>16} {'entry':>9} {'SL_atr':>7} {'risk$':>7} {'SL':>9} {'TP(2R)':>9}  status")
for b in CLUSTER:
    entry = C[b]; atr = ATR[b]; sl_atr = SL.get(b); sl_src = "sl_atr_validado"
    if sl_atr is None:                       # fallback causal demand-anchored (rotulado)
        sl_atr = DEM.get(b); sl_src = "demand_anchored(dist_4h_demand)"
    if sl_atr is None or atr is None:
        print(f"{b:>5}  SEM sl_atr nem dist_demand — UNKNOWN, pular"); continue
    risk = sl_atr * atr
    stop = round(entry - risk, 2)
    target = round(entry + 2 * risk, 2)   # R:R 2:1 fixo (blind: nunca revela TP maior)
    import datetime as dt
    ets = dt.datetime.utcfromtimestamp(TS[b]).strftime('%Y-%m-%d %H:%M')
    label_price = round(entry + 0.5 * risk, 2)
    p2_time = int(TS[b]) + 20 * 14400
    st_stop = int(round(risk / 0.01)); st_tgt = int(round(2 * risk / 0.01))
    trades.append({"id": b, "ts": int(TS[b]), "entry": round(entry, 2), "stop": stop,
                   "target": target, "label_price": label_price, "p2_time": p2_time,
                   "ticks_stop": st_stop, "ticks_target": st_tgt, "sl_source": sl_src,
                   "label_color": BLUE, "rr": "2:1", "already_plotted": b in ALREADY})
    print(f"{b:>5} {ets:>16} {entry:>9.2f} {sl_atr:>7.2f} {risk:>7.2f} {stop:>9.2f} {target:>9.2f}  "
          f"{'(já plotado)' if b in ALREADY else 'NOVO':>12}  SL_src={sl_src}")
json.dump(trades, open("/tmp/cluster4918_trades.json", "w"), indent=2)
print("\nNOVOS a plotar (cluster 24 completo):")
for t in trades:
    if not t["already_plotted"]:
        print(f"  #{t['id']} ts={t['ts']} entry={t['entry']} stop={t['stop']} target={t['target']} "
              f"label_price={t['label_price']} p2_time={t['p2_time']} ticks_stop={t['ticks_stop']} ticks_target={t['ticks_target']}")
print(f"\n{len(trades)} trades -> /tmp/cluster4918_trades.json")
print("Blind: TP=2:1 fixo (sem revelar runner), label AZUL, SEM R/cor win-loss/outcome. SL=estrutural real p/ noção.")
