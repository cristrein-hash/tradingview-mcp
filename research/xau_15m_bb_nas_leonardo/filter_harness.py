#!/usr/bin/env python3
"""Harness UNICO de metricas p/ o engine de filtro LONG. Fonte de verdade (agentes nao fazem aritmetica).
Uso:
  python3 filter_harness.py "EXPR"        -> EXPR = expressao python booleana KEEP sobre dict r (mantem se True)
  python3 filter_harness.py "EXPR" --by   -> idem + WR por ano e por bloco
Imprime JSON: N, WR, sumR, DD, streak, vs BASE (winners_lost, losers_cut, dWR, dSumR, dDD).
KEEP = ficar com o trade. Filtro do Cris = BLOQUEAR perigo => KEEP = (not perigo).
Trades identificados por (block, low_t). Dedup uma-posicao por bloco (cj/exi). Look-ahead: features ja causais."""
import json, sys
from pathlib import Path
HERE = Path(__file__).parent
ROWS=[json.loads(l) for l in (HERE/"filter_dataset.jsonl").read_text().splitlines()]

def dedup(cands):
    byblk={}
    for c in cands: byblk.setdefault(c["block"],[]).append(c)
    taken=[]
    for blk,cs in byblk.items():
        cs.sort(key=lambda x:x["cj"]); busy=-10**9
        for c in cs:
            if c["cj"]<=busy: continue
            busy=c["exi"]; taken.append(c)
    taken.sort(key=lambda x:x["t"]); return taken

def stats(taken):
    n=len(taken)
    if not n: return dict(n=0,wr=0,sumr=0,dd=0,streak=0)
    w=sum(c["win"] for c in taken); sm=sum(c["R"] for c in taken)
    eq=pk=dd=0; stk=mstk=0
    for c in taken:
        eq+=c["R"]; pk=max(pk,eq); dd=min(dd,eq-pk)
        if c["R"]<=0: stk+=1; mstk=max(mstk,stk)
        else: stk=0
    span=(taken[-1]["t"]-taken[0]["t"])/(7*86400) if n>1 else 1
    bigwin=sum(1 for c in taken if c["R"]>=3); maxR=round(max((c["R"] for c in taken),default=0),1)
    return dict(n=n,wr=round(100*w/n,1),sumr=round(sm,1),dd=round(dd,1),streak=mstk,
                winners=w,bigwin=bigwin,maxR=maxR,freq=round(n/max(span,1e-9),2))

BASE_TAKEN=dedup(ROWS)
BASE=stats(BASE_TAKEN)
BASE_WIN_IDS={(c["block"],c["low_t"]) for c in BASE_TAKEN if c["win"]}
BASE_BIG_IDS={(c["block"],c["low_t"]) for c in BASE_TAKEN if c["R"]>=3}  # winners GRANDES: proteger
BASE_IDS={(c["block"],c["low_t"]) for c in BASE_TAKEN}

def run(keep_fn):
    kept=[c for c in ROWS if keep_fn(c)]
    taken=dedup(kept); s=stats(taken)
    tk_ids={(c["block"],c["low_t"]) for c in taken}
    tk_win={(c["block"],c["low_t"]) for c in taken if c["win"]}
    winners_lost=len(BASE_WIN_IDS - tk_win)          # winners da base que sumiram (curtos OK cortar)
    big_winners_lost=len(BASE_BIG_IDS - tk_ids)      # winners GRANDES R>=3 perdidos: NAO pode
    losers_cut=len([c for c in BASE_TAKEN if not c["win"] and (c["block"],c["low_t"]) not in tk_ids])
    new_trades=len(tk_ids - BASE_IDS)                # entradas novas liberadas pelo dedup
    s.update(winners_lost=winners_lost, big_winners_lost=big_winners_lost, losers_cut=losers_cut, new_trades=new_trades,
             dWR=round(s["wr"]-BASE["wr"],1), dSumR=round(s["sumr"]-BASE["sumr"],1),
             dDD=round(s["dd"]-BASE["dd"],1))
    return s, taken

def by_splits(taken):
    yr={}
    for c in taken:
        yr.setdefault(c["yr"],[0,0]); yr[c["yr"]][0]+=1; yr[c["yr"]][1]+=c["win"]
    blk={}
    for c in taken:
        blk.setdefault(c["block"],[0,0]); blk[c["block"]][0]+=1; blk[c["block"]][1]+=c["win"]
    return ({y:[v[0],round(100*v[1]/v[0],1)] for y,v in sorted(yr.items())},
            {b:[v[0],round(100*v[1]/v[0],1)] for b,v in sorted(blk.items())})

if __name__=="__main__":
    if len(sys.argv)<2:
        print(json.dumps({"BASE":BASE})); sys.exit(0)
    expr=sys.argv[1]; show_by="--by" in sys.argv[2:]
    try:
        keep_fn=eval("lambda r: ("+expr+")")
        s,taken=run(keep_fn)
        out={"keep_expr":expr,"BASE":BASE,"FILTERED":s}
        if show_by:
            yr,blk=by_splits(taken); out["by_year"]=yr; out["by_block"]=blk
        print(json.dumps(out))
    except Exception as e:
        print(json.dumps({"error":str(e),"expr":expr}))
