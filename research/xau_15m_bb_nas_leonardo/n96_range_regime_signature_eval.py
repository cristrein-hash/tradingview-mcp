#!/usr/bin/env python3
"""N96 · avaliacao das ASSINATURAS regime-especificas (2026-07-08). Quantifica os discriminadores de auction
achados por regime (BULL=excess no topo; RANGE=perseguir spike/iniciativa-falhada), com as metricas do Cris:
coverage, losers/winners cortados, dR (SB nao disponivel N96), WR impact, null aleatorio de mesmo tamanho, por-ano.
NAO decide gate/review/management — entrega numeros p/ DA. Le results/n96_range_distribution_filter_results.csv."""
import csv, sys, json, datetime as dt
import numpy as np
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from n96_mtf_kit import HERE, famof, FAM
from agent_ctx_kit import ENTRIES
assert len(ENTRIES)==96 and sum(e["out"] for e in ENTRIES)==52, "FAIL-LOUD: N96 nao reproduz"
rows=list(csv.DictReader(open(HERE+"/results/n96_range_distribution_filter_results.csv")))
BYN={int(r["n"]):r for r in rows}; OUT={int(r["n"]):int(r["out"]) for r in rows}
TBYN={e["n"]:e["t"] for e in ENTRIES}
def g(r,k):
    try: return float(r.get(k))
    except: return None
def yr(n): return dt.datetime.utcfromtimestamp(TBYN[n]).year
def evalcut(cut, pool_name, pool):
    cut=[n for n in cut]; cw=sum(OUT[n] for n in cut); cl=len(cut)-cw
    poolW=sum(OUT[n] for n in pool);
    # dR de cortar (3:1): winner cortado custa +3, loser cortado poupa +1
    dR=-(cw*3-cl)
    # null: cortes aleatorios do MESMO tamanho dentro do pool
    outs=np.array([OUT[n] for n in pool]); k=len(cut); rng=np.random.default_rng(7); vals=[]
    for _ in range(3000):
        idx=rng.choice(len(pool),k,replace=False); ww=outs[idx].sum(); ll=k-ww; vals.append(-(ww*3-ll))
    vals=np.array(vals); p=float((vals>=dR).mean())
    # precisao (fracao loser no corte)
    prec=cl/len(cut) if cut else 0
    y={yy:(sum(1 for n in cut if yr(n)==yy and OUT[n]==0),sum(1 for n in cut if yr(n)==yy)) for yy in (2025,2026)}
    print(f"  [{pool_name}] cut={len(cut)} (loser={cl} win={cw}) prec_loser={prec:.2f} dR={dR:+d} | null media={vals.mean():+.1f} q95={np.quantile(vals,0.95):+.1f} P(null>=obs)={p:.3f} | por-ano loser/total {y}")
    return {"pool":pool_name,"cut":cut,"loser":cl,"win":cw,"prec":round(prec,2),"dR":dR,"null_p":round(p,3),"per_year":{str(k):list(v) for k,v in y.items()}}

REG={int(k):v for k,v in json.load(open(HERE+"/results/n96_causal_regime.json")).items()}
res={}
print("="*84); print("BULL — assinatura EXCESS (excess_rsi_htf alto = topo de distribuicao)"); print("="*84)
BULL=[n for n in sorted(BYN) if REG[n]=="BULL"]
for X in (75,78,80):
    cut=[n for n in BULL if (g(BYN[n],"excess_rsi_htf") or 0)>=X]
    res[f"BULL_rsi{X}"]=evalcut(cut,f"BULL excess_rsi>={X}",BULL)
print("\n"+"="*84); print("RANGE — assinatura INICIATIVA-FALHADA (displacement/maxbar alto = perseguir spike)"); print("="*84)
RANGE=[n for n in sorted(BYN) if REG[n]=="RANGE"]
for feat,X in (("displacement_15m",0.7),("displacement_15m",1.0),("maxbar_atr_15m",1.8)):
    cut=[n for n in RANGE if (g(BYN[n],feat) or 0)>=X]
    res[f"RANGE_{feat}_{X}"]=evalcut(cut,f"RANGE {feat}>={X}",RANGE)
# combinacao RANGE: spike + premio (rangepos alto seria melhor, mas rangepos_4h WIN>LOSER; usar displacement+demanda-perto)
print("\ncomposicao RANGE (perseguir spike E perto de demanda ja tocada):")
cut=[n for n in RANGE if (g(BYN[n],"displacement_15m") or 0)>=0.7 and (g(BYN[n],"demand_room_4h") or 9)<1.0]
res["RANGE_spike_neardem"]=evalcut(cut,"RANGE displacement>=0.7 & demand_room<1.0",RANGE)

json.dump(res, open(HERE+"/results/n96_range_regime_signature_eval.json","w"), indent=1)
print("\nsaved results/n96_range_regime_signature_eval.json · SEM veredito — DA classifica gate/review/management.")
