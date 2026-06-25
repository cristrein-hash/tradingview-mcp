#!/usr/bin/env python3
"""Plota p/ REVISÃO VISUAL do aggregator v1: 42 novos TAKE (VERDE) + 40 fatal-skip winners (LARANJA).
CANÔNICO (docs/CANONICAL_TRADE_PLOTTING.md): long_position largura 20 barras + label text; stop/profit em
TICKS (mintick 0.01); SEM screenshot; SEM draw_clear (Cris limpa manual). Cor = CATEGORIA (instrução do Cris):
verde=#1a8917 (TAKE), laranja=#e8730c (fatal-skip). SL estrutural = entry − sl_atr×ATR; target = +2R.
Pré-req: /tmp/claude_recheck.paused + 3 LaunchAgents pausados.
"""
import os, sys, csv, json, time
AB = "/Users/cristrein/tradingview-mcp/alert-bridge"
sys.path.insert(0, AB)
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
QD = os.path.dirname(os.path.abspath(__file__))
D = os.path.normpath(os.path.join(QD, "..", "..", "results"))
RR = os.path.normpath(os.path.join(QD, "..", "..", "repro_recovery"))
SYMBOL, TF, BAR_S, WIDTH = "PEPPERSTONE:XAUUSD", "240", 14400, 20
GREEN, ORANGE = "#1a8917", "#e8730c"

led = list(csv.DictReader(open(f"{D}/l2_bpt_aggregator_v1_decisions.csv")))
pk = {int(json.loads(l)['bar_idx']): json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
out = {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
new_take = [r for r in led if r['agg_v1_decision'] == 'TAKE' and r['old_decision'] != 'TAKE']
fatal_skip = [r for r in led if r['agg_v1_decision'] == 'SKIP' and r['final_reason'].startswith('FATAL') and r['outcome'] == 'WIN']

def build(rows, prefix, color):
    items = []
    for n, r in enumerate(sorted(rows, key=lambda x: x['datetime']), 1):
        i = int(r['episode_id']); p = pk[i]
        entry = float(p['price']); atr = float(p['atr']); ts = int(p['ts'])
        sl_atr = float(out[i]['sl_atr']); Rd = sl_atr * atr
        items.append(dict(label=f"{prefix}{n}", color=color, entry_time=ts, entry=entry,
                          stop=entry - Rd, target=entry + 2.0 * Rd, Rd=Rd))
    return items

plan = build(new_take, "T", GREEN) + build(fatal_skip, "S", ORANGE)
print(f"plano: {sum(1 for x in plan if x['color']==GREEN)} TAKE verde + {sum(1 for x in plan if x['color']==ORANGE)} fatal-skip laranja = {len(plan)}")

cli = MCPClient(); cli.start()
try:
    st = cli.call_tool("chart_get_state"); print(f"chart: {st.get('symbol')} {st.get('resolution')}")
    # PRESERVA a view (Cris carregou 2020 manualmente). Só ajusta se símbolo/TF divergirem.
    if st.get('symbol') != SYMBOL:
        cli.call_tool("chart_set_symbol", {"symbol": SYMBOL}); time.sleep(1)
    if str(st.get('resolution')) != TF:
        cli.call_tool("chart_set_timeframe", {"timeframe": TF}); time.sleep(1)
    nlp = nlbl = 0
    for t in plan:
        assert t['entry'] > t['stop'] and t['target'] > t['entry']
        r1 = cli.call_tool("draw_shape", {
            "shape": "long_position",
            "point": {"time": t['entry_time'], "price": t['entry']},
            "point2": {"time": t['entry_time'] + WIDTH * BAR_S, "price": t['target']},
            "overrides": json.dumps({
                "stopLevel": price_to_ticks_offset(t['entry'], t['stop']),
                "profitLevel": price_to_ticks_offset(t['entry'], t['target']),
            })})
        if r1.get('success'): nlp += 1
        else: print(f"  {t['label']} long_position FALHOU: {r1}")
        r2 = cli.call_tool("draw_shape", {
            "shape": "text",
            "point": {"time": t['entry_time'], "price": t['entry'] + 0.5 * t['Rd']},
            "text": t['label'],
            "overrides": json.dumps({"color": t['color'], "bold": True, "fontsize": 12})})
        if r2.get('success'): nlbl += 1
        else: print(f"  {t['label']} label FALHOU: {r2}")
    print(f"\nDESENHADO: {nlp} long_position + {nlbl} labels (de {len(plan)})")
    dl = cli.call_tool("draw_list")
    print(f"draw_list count: {dl.get('count') if isinstance(dl, dict) else dl}")
finally:
    cli.stop(); print("MCP stopped. (chart em XAU 4H)")
