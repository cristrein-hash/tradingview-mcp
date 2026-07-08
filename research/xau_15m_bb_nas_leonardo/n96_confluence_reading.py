#!/usr/bin/env python3
"""N96 · CONFLUENCIA + LEITURA CONTEXTUAL (2026-07-08). Cris: 'discriminar sem confluir e pouco produtivo'.
Le n96_exhaustive_mtf_features.csv (RAW-native, causal). Constroi CONFLUENCIA por familia (convergencia de
sub-estados ORTOGONAIS, nao eixo isolado) e mede os DOIS objetivos: (1) cortar a familia loser,
(2) POUPAR winners. Reporta composicao do conjunto disparado + precisao + winner-kill por threshold.
Depois: leitura contextual dos disparos (o que cada confluencia realmente captura). SEM veredito — DA arbitra."""
import csv, sys
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from n96_mtf_kit import HERE, FAM, famof
rows=list(csv.DictReader(open(HERE+"/results/n96_exhaustive_mtf_features.csv")))
def g(r,k):
    v=r.get(k)
    try: return float(v)
    except: return None
BYN={int(r["n"]):r for r in rows}
NS=sorted(BYN)
def fam(n): return famof(n)
WIN=[n for n in NS if fam(n)=="WIN"]

# ---- sub-estados ORTOGONAIS por familia (derivados das medianas disc; causais) ----
def D_subs(r):
    return [ (g(r,"4H_ema_trend") or 0)<0,          # tendencia 4H p/ baixo
             (g(r,"4H_px_vs_ema") or 9)<0,          # preco < EMA 4H
             (g(r,"1D_px_vs_ema") or 9)<0,          # preco < EMA 1D
             (g(r,"mtf_bull_align") or 9)<=1,       # ~nenhum TF bullish
             (g(r,"4H_dem_below") or 9)<1.5 ]       # colado a demanda 4H (fundo de correcao)
def C_subs(r):
    return [ (g(r,"4H_rsi") or 0)>58,               # sobrecomprado 4H
             (g(r,"4H_px_vs_ema") or -9)>2,         # esticado acima EMA 4H
             (g(r,"4H_dem_below") or 0)>3,          # LONGE da demanda (topo)
             (g(r,"1D_ema_trend") or 0)>3,          # 1D esticado
             (g(r,"1H_rsi_slope") or 9)<-5 ]        # momentum 1H a virar p/ baixo
def R_subs(r):
    return [ (g(r,"4H_atr_rel") or 9)<0.006,        # baixa volatilidade (compressao)
             (g(r,"15M_px_vs_ema") or -9)>0.6,      # esticado LTF 15M
             (g(r,"30M_px_vs_ema") or -9)>0.6,      # esticado LTF 30M
             (g(r,"4H_smc_CHoCH") or 0)>=1 ]        # CHoCH 4H (range/whipsaw)
SUBS={"D":D_subs,"C":C_subs,"R":R_subs}

def report(famtag, thr):
    subf=SUBS[famtag]
    fired=[n for n in NS if sum(subf(BYN[n]))>=thr]
    comp={f:sum(1 for n in fired if fam(n)==f) for f in ("WIN","C","D","R","MGMT")}
    tgt=comp[famtag]; losers=comp["C"]+comp["D"]+comp["R"]; wins=comp["WIN"]
    prec=losers/len(fired) if fired else 0
    recall=tgt/len(FAM[famtag]) if FAM.get(famtag) else 0
    return {"thr":thr,"n_fired":len(fired),"comp":comp,"target_hit":tgt,
            "loser_prec":round(prec,3),"target_recall":round(recall,3),"winners_killed":wins,"fired":fired}

print("="*80); print("CONFLUENCIA por familia — composicao do conjunto disparado (2 objetivos)"); print("="*80)
print("familia | thr | n_fired |  WIN   C   D   R MGMT | prec_loser recall_fam winners_killed")
for famtag in ("D","C","R"):
    for thr in (2,3,4,5):
        if thr> len(SUBS[famtag]({})): continue
        R=report(famtag,thr); c=R["comp"]
        print(f"   {famtag}    |  {thr}  |   {R['n_fired']:>3}   | {c['WIN']:>4}{c['C']:>4}{c['D']:>4}{c['R']:>4}{c['MGMT']:>4} | "
              f"   {R['loser_prec']:.2f}      {R['target_recall']:.2f}       {R['winners_killed']}")
    print()

# ---- filtro combinado bear (D OR C) — o candidato operacional (skip topo/bear ativo) ----
print("="*80); print("FILTRO COMBINADO 'SKIP BEAR-TOP' = D>=3 OR C>=3  (nos 96)"); print("="*80)
def dscore(n): return sum(D_subs(BYN[n]))
def cscore(n): return sum(C_subs(BYN[n]))
skip=[n for n in NS if dscore(n)>=3 or cscore(n)>=3]
keep=[n for n in NS if n not in skip]
def stat(sub):
    w=sum(1 for n in sub if BYN[n]["out"]=="1"); return w,len(sub),(round(w/len(sub),3) if sub else 0)
kw,kn,kr=stat(keep); sw,sn,sr=stat(skip)
comp={f:sum(1 for n in skip if fam(n)==f) for f in ("WIN","C","D","R","MGMT")}
print(f"  SKIP (n={sn}): winners_dentro={sw} hit3r={sr} | composicao {comp}")
print(f"  KEEP (n={kn}): winners={kw} hit3r={kr}  (base 96 = 0.542)")
print(f"  --> filtro corta {sn} trades; sacrifica {sw} winners; hit-3R do que fica = {kr}")
print(f"  winners perdidos (skip): {sorted(n for n in skip if BYN[n]['out']=='1')}")
print(f"  losers cortados (skip):  {sorted(n for n in skip if BYN[n]['out']=='0')}")

# ---- leitura contextual: sub-estados que cada familia realmente acende (medias) ----
print("\n"+"="*80); print("LEITURA CONTEXTUAL — quantos sub-estados acende cada familia (media)"); print("="*80)
for famtag in ("D","C","R"):
    subf=SUBS[famtag]
    for f in ("WIN","C","D","R","MGMT"):
        ns=[n for n in NS if fam(n)==f]
        if not ns: continue
        avg=sum(sum(subf(BYN[n])) for n in ns)/len(ns)
        print(f"  {famtag}-confluencia | familia {f:<4} n={len(ns):>2} score_medio={avg:.2f}")
    print()
print("SEM veredito. Proximo: DA sobre winners-sacrificados vs losers-cortados + forward.")
