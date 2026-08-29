#!/usr/bin/env python3
"""P0 v2 — GROUND TRUTH ÚNICO (ordem Cris 29/08): SÓ esta semana, do chart 15M reorganizado.
3 classes: (A) posições long/short ajustadas às velas de entrada; (B) ENTRY_*_LIMIT info_lines — a
VELA-ÂNCORA onde o limit devia ser SINALIZADO antes do preço chegar (t do 1º ponto) + o nível (preço);
(C) pools $$$ e LIQ_BLOCKs (as regiões que pedem limits). Materializado. py3 stdlib."""
import json, datetime as dt
from pathlib import Path
REPO=Path("/Users/cristrein/tradingview-mcp"); HERE=Path(__file__).resolve().parent
LX=dt.timezone(dt.timedelta(hours=1))
W0=dt.datetime(2026,8,21,tzinfo=dt.timezone.utc).timestamp()   # semana alargada 21/08→
dd=json.load(open(REPO/"research/liq_drawings_15m_20260828.json"))
gt=dict(positions=[],limits=[],pools=[],blocks=[])
for d in dd:
    pts=[p for p in (d.get('points') or []) if p.get('t') and p.get('price')]
    if not pts: continue
    t0=min(p['t'] for p in pts)
    txt=str(d.get('text') or '')
    if d['name'] in ('long_position','short_position'):
        gt['positions'].append(dict(dir='LONG' if d['name']=='long_position' else 'SHORT',
                                    t=pts[0]['t'],entry=pts[0]['price']))
    elif d['name']=='info_line' and 'LIMIT' in txt.upper():
        side='BUY' if 'BUY' in txt.upper() else 'SELL'
        # ancora = ponto mais CEDO (a vela onde sinalizar); nivel = preco do ponto mais tardio (o limit)
        early=min(pts,key=lambda p:p['t']); late=max(pts,key=lambda p:p['t'])
        gt['limits'].append(dict(side=side,anchor_t=early['t'],level=late['price'],txt=txt))
    elif d['name']=='info_line' and '$$$' in txt and 'LIQ_BLOCK' not in txt:
        prices=[p['price'] for p in pts]
        gt['pools'].append(dict(level=round(sum(prices)/len(prices),2),weight=txt.count('$'),t0=t0))
    elif 'LIQ_BLOCK' in txt:
        gt['blocks'].append(dict(level=round(pts[0]['price'],2),weight=txt.count('$'),t0=t0))
# filtrar semana
for k in gt: gt[k]=[x for x in gt[k] if (x.get('t') or x.get('anchor_t') or x.get('t0') or 0)>=W0]
out=HERE/"ground_truth_v2.json"; out.write_text(json.dumps(gt,indent=1))
print(f"posições {len(gt['positions'])} · limits {len(gt['limits'])} · pools $$$ {len(gt['pools'])} · blocks {len(gt['blocks'])}")
def hm(t): return dt.datetime.fromtimestamp(t,LX).strftime('%d/%m %H:%M')
print("\nLIMITS (vela-âncora → nível):")
for l in sorted(gt['limits'],key=lambda x:x['anchor_t']):
    print(f"  {l['side']:<5} âncora {hm(l['anchor_t'])} → nível {l['level']:.1f}  [{l['txt'][:20]}]")
print("\nPOSIÇÕES:")
for p in sorted(gt['positions'],key=lambda x:x['t']):
    print(f"  {p['dir']:<6} {hm(p['t'])} @ {p['entry']:.1f}")
