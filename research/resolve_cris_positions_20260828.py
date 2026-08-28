#!/usr/bin/env python3
"""Resolver as posições marcadas pelo Cris na tab 15M (liq_drawings dump) contra bars_15m — SL/TP
derivados dos níveis do desenho (stopLevel/profitLevel /100 = $). py3 stdlib."""
import json,datetime as dt
LX=dt.timezone(dt.timedelta(hours=1))
dd=json.load(open('/Users/cristrein/tradingview-mcp/research/liq_drawings_15m_20260828.json'))
bars=[json.loads(l) for l in open('/Users/cristrein/tradingview-mcp/my-strategy/core/bar_store/store/bars_15m.jsonl') if l.strip()]
T=[b['t'] for b in bars];H=[b['h'] for b in bars];L=[b['l'] for b in bars]
print(f"{'quando':<13}{'dir':<6}{'entry':>8}{'SL':>8}{'TP':>8}{'res':>7}{'R':>6}")
tot=0.0;w=l=op=0
for d in dd:
    if d['name'] not in ('long_position','short_position'): continue
    p=d['points'][0] if d['points'] else {}
    e=p.get('price');t0=p.get('t')
    if not e or not t0: continue
    lng=d['name']=='long_position'
    sd=(d['props'].get('stopLevel') or 0)/100.0; td=(d['props'].get('profitLevel') or 0)/100.0
    if not sd or not td: continue
    sl=e-sd if lng else e+sd; tp=e+td if lng else e-td
    i0=next((i for i,t in enumerate(T) if t>t0),None)
    if i0 is None: continue
    res="OPEN";R=0.0
    for i in range(i0,len(T)):
        if lng:
            if L[i]<=sl: res,R="LOSS",-1.0;break
            if H[i]>=tp: res,R="WIN",round(td/sd,1);break
        else:
            if H[i]>=sl: res,R="LOSS",-1.0;break
            if L[i]<=tp: res,R="WIN",round(td/sd,1);break
    hm=dt.datetime.fromtimestamp(int(t0),LX).strftime('%a %d/%m %H:%M')
    print(f"{hm:<13}{('LONG' if lng else 'SHORT'):<6}{e:>8.1f}{sl:>8.1f}{tp:>8.1f}{res:>7}{R:>6.1f}")
    tot+=R;w+=res=='WIN';l+=res=='LOSS';op+=res=='OPEN'
print(f"\nTOTAL: {w}W-{l}L-{op}open · sumR {tot:+.1f} (R = TP/SL do próprio desenho)")
