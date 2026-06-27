#!/usr/bin/env python3
"""Perfil de convexidade da base A2 5ATR long (taken/dedup): distribuicao de R dos winners.
Confirma perfil SCALP (poucos/nenhum runner) => cortar winners curtos e barato. RAW-causal."""
from filter_harness import BASE_TAKEN
R=sorted([c["R"] for c in BASE_TAKEN if c["win"]], reverse=True)
print("winners:",len(R),"| top10 R:",[round(x,1) for x in R[:10]])
print("R>=5:",sum(1 for x in R if x>=5),"| R>=3:",sum(1 for x in R if x>=3),
      "| R>=2:",sum(1 for x in R if x>=2),"| 1<=R<2:",sum(1 for x in R if 1<=x<2),
      "| 0<R<1:",sum(1 for x in R if 0<x<1))
