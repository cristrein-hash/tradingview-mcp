#!/usr/bin/env python3
"""bubnas family exploration: win/loss separation of bubble/NAS region features
on the BASE_TAKEN trades, used to pick thresholds. Metrics of record always come
from filter_harness.py (single source of truth)."""
import statistics as st
from filter_harness import BASE_TAKEN

FEATS = ['buy_bub_w_leg','sell_bub_w_leg','buy_bub_L_leg','buy_bub_w_w24',
         'sell_bub_w_w24','buy_bub_L_w24','nas_short_leg','nas_long_leg',
         'nas_short_w24','nas_long_w24']

def wr(sel):
    if not sel: return (0,0,0)
    w=sum(c['win'] for c in sel); sm=sum(c['R'] for c in sel)
    return (len(sel),round(100*w/len(sel),1),round(sm,1))

if __name__=='__main__':
    wins=[c for c in BASE_TAKEN if c['win']]; loss=[c for c in BASE_TAKEN if not c['win']]
    print('BASE wins',len(wins),'loss',len(loss))
    for f in FEATS:
        wv=[c.get(f) for c in wins if c.get(f) is not None]
        lv=[c.get(f) for c in loss if c.get(f) is not None]
        if not wv or not lv: continue
        print(f'{f:16s} WIN mean={st.mean(wv):6.1f} | LOSS mean={st.mean(lv):6.1f}')
    # KEY FINDING: winners have MORE buy-bubbles/NAS-short than losers (means).
    # Cris literal "block buy-bubble tops" CUTS WINNERS. The edge is the INVERSE:
    # keep longs where SELL pressure is present relative to BUY in the leg.
    print('\n-- sell-dominance threshold scan (blocked vs kept) --')
    for c0 in [1,2,3]:
        for add in [5,10]:
            blk=[c for c in BASE_TAKEN if (c.get('buy_bub_w_leg') or 0) > c0*(c.get('sell_bub_w_leg') or 0)+add]
            kep=[c for c in BASE_TAKEN if (c.get('buy_bub_w_leg') or 0) <= c0*(c.get('sell_bub_w_leg') or 0)+add]
            print(f'buy<= {c0}*sell+{add}: blocked',wr(blk),'kept',wr(kep))
