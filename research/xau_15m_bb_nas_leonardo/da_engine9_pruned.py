#!/usr/bin/env python3
"""DA follow-up: decisive direction/redundancy test. Drop the 9 wrong/zero-signed
predicates found in da_engine9_audit.py Test4; rebuild frontier. Compare a 4-strong-
feature stack. Shows whether the 20-lens 'confluence' is just noise-dilution of a few
correctly-signed features. Output saved (committed) for reproducibility."""
import engine9_full_gatilho as E
RS=[r["R"] for r in E.base]; YR=[r["yr"] for r in E.base]
PV=[list(E.preds(r).values()) for r in E.base]
NAMES=list(E.preds(E.base[0]).keys()); nrow=len(E.base)
wrong={"h4_demanda","nas_long","rsi_min8<35","sell_bubble_absorb","sem_buy_exaustao",
       "perto_demanda","rsi_low<40","demand_reclaim","reclaim_forte"}
keep=[j for j,n in enumerate(NAMES) if n not in wrong]
def front(scorefn,label):
    sc=[scorefn(i) for i in range(nrow)]
    print(label)
    for k in sorted(set(sc),reverse=True):
        idx=[i for i in range(nrow) if sc[i]>=k]
        if len(idx)<30: continue
        rs=[RS[i] for i in idx]
        py={y:round(sum(RS[i] for i in idx if YR[i]==y),1) for y in (2024,2025,2026)}
        print("  >=%2d N=%4d WR=%4.1f sumR=%6.1f avgR=%.3f yr=%s"%(
            k,len(idx),100*sum(1 for x in rs if x>0)/len(idx),sum(rs),sum(rs)/len(idx),py))
print("PRUNED STACK (drop 9 wrong/zero-signed predicates, keep %d of 20):"%len(keep))
front(lambda i:sum(PV[i][j] for j in keep),"pruned-conv frontier:")
strong=[NAMES.index(n) for n in ("legpos90_alto","h4_up","pullback_raso","clean_sky")]
front(lambda i:sum(PV[i][j] for j in strong),"\n4-strong-feature stack (legpos90/h4_up/pullback_raso/clean_sky):")
