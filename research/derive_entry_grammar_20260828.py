#!/usr/bin/env python3
"""Derivar a GRAMÁTICA de entrada do Cris a partir do chart (ordem 28/08 'está tudo marcado'):
para cada LONG desenhado, imprime a fita 15M em volta, o nível $$$ mais próximo abaixo, a barra que
furou, quantas velas até à entrada, e onde a entrada assenta (nível/fecho/reclaim). py3 stdlib."""
import json,datetime as dt
LX=dt.timezone(dt.timedelta(hours=1))
dd=json.load(open('/Users/cristrein/tradingview-mcp/research/liq_drawings_15m_20260828.json'))
bars=[json.loads(l) for l in open('/Users/cristrein/tradingview-mcp/my-strategy/core/bar_store/store/bars_15m.jsonl') if l.strip()]
T=[b['t'] for b in bars]
lev=[]
for d in dd:
    if d['name'] in ('info_line','horizontal_line') and d['points']:
        ps=[p['price'] for p in d['points'] if p.get('price')]
        if ps and (max(ps)-min(ps))<2.0:          # nível ~horizontal
            lev.append((sum(ps)/len(ps), d.get('text') or ''))
curves=[d for d in dd if d['name']=='curve']
import bisect
for d in dd:
    if d['name']!='long_position' or not d['points']: continue
    p=d['points'][0]; e=p.get('price'); t0=p.get('t')
    if not e or not t0: continue
    below=sorted([l for l in lev if l[0]<e+1], key=lambda x:e-x[0])[:2]
    i0=bisect.bisect_left(T,t0)
    print(f"\n### LONG @{e} · barra {dt.datetime.fromtimestamp(t0,LX).strftime('%a %d/%m %H:%M')} · níveis abaixo: "+" | ".join(f"{round(l,1)} {tx[:14]}" for l,tx in below))
    lo_lv=below[0][0] if below else None
    for i in range(max(0,i0-8),min(len(bars),i0+3)):
        b=bars[i]
        mark="◀ ENTRY" if T[i]==t0 else ""
        pier="FURA" if lo_lv and b['l']<lo_lv else ""
        rec="fecha>nível" if lo_lv and b['c']>lo_lv else ""
        print(f"  {dt.datetime.fromtimestamp(b['t'],LX).strftime('%H:%M')} o{b['o']:.1f} h{b['h']:.1f} l{b['l']:.1f} c{b['c']:.1f} {pier:>5} {rec} {mark}")
    near_c=[c for c in curves if c['points'] and abs((c['points'][0].get('t') or 0)-t0)<6*3600]
    for c in near_c:
        print("  curve:"," → ".join(f"{dt.datetime.fromtimestamp(p['t'],LX).strftime('%H:%M')}@{p['price']:.1f}" for p in c['points'] if p.get('t')))
