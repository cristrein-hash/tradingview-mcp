#!/usr/bin/env python3
"""Filtro LONG recomendado (pos-engine + DA): ANTI-RANGE causal h1_eff>=X.
DA: h1_eff e a unica peca robusta (corta DD pela metade + ~todo o ganho de WR);
bubble/NAS/RSI/dist_ema adicionam 1-3pp = ruido (p=0.46, CIs sobrepoem, thresholds faca-de-ponta).
Mostra metricas completas + por ano + por bloco p/ 0.15 e 0.14. Calibracao IN-SAMPLE (nao OFICIAL)."""
from filter_harness import run, by_splits, BASE
print("BASE:",BASE)
for thr in (0.15,0.14):
    expr=f"r['h1_eff']>={thr}"
    s,taken=run(eval("lambda r: ("+expr+")"))
    yr,blk=by_splits(taken)
    print(f"\n=== h1_eff>={thr} ===")
    print(f"  N={s['n']} WR={s['wr']}% sumR={s['sumr']:+} DD={s['dd']} streak={s['streak']} bigwin(R>=3)={s['bigwin']} maxR={s['maxR']} freq={s['freq']}/sem")
    print(f"  vs BASE: dWR={s['dWR']:+} dDD={s['dDD']:+} dSumR={s['dSumR']:+} | losers_cut={s['losers_cut']} winners_lost(curtos)={s['winners_lost']} big_winners_lost={s['big_winners_lost']} new_trades={s['new_trades']}")
    print(f"  por ano [n,WR]: {yr}")
    print(f"  por bloco [n,WR]: {blk}")
