#!/usr/bin/env python3
"""A1/A2 forward eval (Cris 2026-08-21 'aprender algo que traga valor'). Read-only sobre o ledger
alerted.jsonl + bars_15m. 3 cortes DESCRITIVOS (N=21 forward — nada disto é validação; hipóteses
para research futura se algum corte for grande):
  1. gestão BE@+1R vs 3R-fixo (o leak nº1 do Cris é SAÍDA — quanto valia mecanizar o BE?)
  2. profundidade do pullback (depth_atr) — o A1 fundo demais é faca?
  3. antes/depois dos guards de 14/08 (choch+sweep-reject) — os guards já cortam as facas?
  4. A2 (raso ≤2 ATR) disparou alguma vez?"""
import json
import datetime

LX = datetime.timezone(datetime.timedelta(hours=1))
led = [json.loads(l) for l in open('/Users/cristrein/tradingview-mcp/my-strategy/strategies/xau_15m_long/continuation_A1A2/.a1a2_state/alerted.jsonl') if l.strip()]
bars = [json.loads(l) for l in open('/Users/cristrein/tradingview-mcp/my-strategy/core/bar_store/store/bars_15m.jsonl') if l.strip()]
T = [b['t'] for b in bars]; H = [b['h'] for b in bars]; L = [b['l'] for b in bars]

GUARDS_TS = datetime.datetime(2026, 8, 14, tzinfo=LX).timestamp()


def sim(e, sl, tgt, i0, be_at=None):
    """Devolve (outcome, R). be_at=+1R: quando MFE>=be_at, SL sobe para entry (0R se voltar)."""
    risk = e - sl
    cur_sl = sl
    armed = False
    for i in range(i0, len(T)):
        if H[i] >= e + (be_at or 0) * risk and be_at and not armed:
            cur_sl = e; armed = True
        if L[i] <= cur_sl:
            return ('BE' if armed and cur_sl == e else 'LOSS'), (0.0 if armed and cur_sl == e else -1.0)
        if H[i] >= tgt:
            return 'WIN', 3.0
    return 'OPEN', 0.0


rows = []
for r in led:
    t, e, sl, tgt = r.get('entry_t'), r.get('ent'), r.get('sl'), r.get('tgt')
    if not (t and e and sl and tgt):
        continue
    i0 = next((i for i, tt in enumerate(T) if tt > t), None)
    if i0 is None:
        continue
    o_fix, r_fix = sim(e, sl, tgt, i0)
    o_be, r_be = sim(e, sl, tgt, i0, be_at=1.0)
    rows.append(dict(t=t, depth=r.get('depth_atr'), fix=(o_fix, r_fix), be=(o_be, r_be),
                     post_guards=t >= GUARDS_TS))

tot_fix = sum(x['fix'][1] for x in rows)
tot_be = sum(x['be'][1] for x in rows)
n_be_saved = sum(1 for x in rows if x['fix'][0] == 'LOSS' and x['be'][0] == 'BE')
n_be_cost = sum(1 for x in rows if x['fix'][0] == 'WIN' and x['be'][0] != 'WIN')
print(f"1) GESTÃO (N={len(rows)}): 3R-fixo {tot_fix:+.0f}R · BE@+1R {tot_be:+.0f}R · "
      f"losses→BE salvos {n_be_saved} · wins perdidos p/ BE {n_be_cost}")

for lo, hi, tag in [(0, 4, 'raso <4ATR'), (4, 8, 'médio 4-8'), (8, 99, 'fundo >8ATR')]:
    g = [x for x in rows if x['depth'] is not None and lo <= x['depth'] < hi]
    w = sum(1 for x in g if x['fix'][0] == 'WIN')
    print(f"2) depth {tag}: N={len(g)} · {w}W-{sum(1 for x in g if x['fix'][0]=='LOSS')}L · "
          f"sumR {sum(x['fix'][1] for x in g):+.0f}")

for tag, sel in [('pré-guards (<14/08)', [x for x in rows if not x['post_guards']]),
                 ('pós-guards (>=14/08)', [x for x in rows if x['post_guards']])]:
    w = sum(1 for x in sel if x['fix'][0] == 'WIN')
    print(f"3) {tag}: N={len(sel)} · {w}W-{sum(1 for x in sel if x['fix'][0]=='LOSS')}L · "
          f"sumR {sum(x['fix'][1] for x in sel):+.0f}")

n_a2 = sum(1 for r in led if r.get('layer') == 'A2')
print(f"4) A2 (raso ≤2ATR) disparos no forward: {n_a2} de {len(led)}")
