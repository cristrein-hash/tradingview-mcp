#!/usr/bin/env python3
"""N96 · RANGE/DISTRIBUTION FILTER ROUND — AUCTION-THEORY, ESTRUTURAL-PRIMEIRO (2026-07-08).
Research-only, RAW-first, LONG-only. Tese (Cris): os losers de RANGE e BULL TEM features discriminantes
ESPECIFICAS do regime, por logica de AUCTION THEORY — distintas do BEAR e distintas ENTRE BULL e RANGE.
Metodo: classificar estrutura (regime v5 causal) PRIMEIRO, depois cruzar indicadores DENTRO da familia
C/RANGE-DISTRIBUTION vs winners comparaveis NO MESMO regime. Nao "RSI separa loser globalmente?".
Features de auction (causais, RAW/primitives): range-position (premio/desconto), balance-vs-imbalance
(rotacao SMC), excess/exaustao (RSI extremo+rejeicao), supply overhead / clean-sky, demand room,
displacement (aceitacao vs rejeicao), absorcao (bubbles), volume relativo. SVP=unavailable (NULL). SEM veredito."""
import csv, sys, json, statistics as st, datetime as dt
import numpy as np
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from n96_mtf_kit import HERE, FAM, famof, bars_upto
from agent_ctx_kit import ENTRIES, ATR
assert len(ENTRIES)==96 and sum(e["out"] for e in ENTRIES)==52, "FAIL-LOUD: N96 nao reproduz"
REG={int(k):v for k,v in json.load(open(HERE+"/results/n96_causal_regime.json")).items()}
rows=list(csv.DictReader(open(HERE+"/results/n96_exhaustive_mtf_features.csv")))
BYN={int(r["n"]):r for r in rows}; OUT={int(r["n"]):int(r["out"]) for r in rows}
TBYN={e["n"]:e["t"] for e in ENTRIES}; ENTof={e["n"]:e for e in ENTRIES}
def g(r,k):
    try: return float(r.get(k))
    except: return None

# ---------- AUCTION FEATURES (causais) ----------
AUC={}
for e in ENTRIES:
    n=e["n"]; px=e["ent"]; t=e["t"]; a=ATR[e["j"]] or 5; r=BYN[n]; f={}
    # range-position 15M (premio/desconto dentro da balanca recente) — 96 barras fechadas
    b15=bars_upto("15M", t)
    if len(b15)>=96:
        seg=b15[-96:]; hi=max(x["h"] for x in seg); lo=min(x["l"] for x in seg)
        f["rangepos_15m"]=round((px-lo)/(hi-lo),3) if hi>lo else 0.5
        f["rangewidth_atr_15m"]=round((hi-lo)/a,2)
    b4=bars_upto("4H", t)
    if len(b4)>=30:
        seg=b4[-30:]; hi=max(x["h"] for x in seg); lo=min(x["l"] for x in seg)
        f["rangepos_4h"]=round((px-lo)/(hi-lo),3) if hi>lo else 0.5
    # displacement 15M: impulso recente (net move / atr sobre 8 barras) e maior barra
    if len(b15)>=9:
        seg=b15[-8:]; net=abs(seg[-1]["c"]-seg[0]["o"])/a
        maxbar=max((x["h"]-x["l"]) for x in seg)/a
        f["displacement_15m"]=round(net,2); f["maxbar_atr_15m"]=round(maxbar,2)
    # balance vs imbalance: rotacao SMC (CHoCH+EQH+EQL) menos BOS (do CSV, 15M+30M)
    rot=sum((g(r,f"{tf}_smc_{tag}") or 0) for tf in ("15M","30M") for tag in ("CHoCH","EQH","EQL"))
    bos=sum((g(r,f"{tf}_smc_BOS") or 0) for tf in ("15M","30M"))
    f["rotational_smc"]=rot-bos     # alto=rotacional(range/balanca) ; baixo/neg=impulso(trend)
    # excess/exaustao: RSI HTF extremo
    f["excess_rsi_htf"]=max((g(r,"4H_rsi") or 0),(g(r,"1D_rsi") or 0))
    # supply overhead / clean-sky: menor distancia a supply acima entre TFs (baixo=capped)
    sups=[g(r,f"{tf}_sup_above") for tf in ("15M","30M","1H","4H") if g(r,f"{tf}_sup_above") is not None]
    f["supply_overhead_min"]=round(min(sups),2) if sups else 9.0
    f["clean_sky"]=1 if (sups and min(sups)>1.5) else 0
    # demand room abaixo (4H)
    f["demand_room_4h"]=g(r,"4H_dem_below")
    # absorcao: buy falhando no topo menos sell absorvido no fundo (do CSV)
    f["absorption"]=(g(r,"bub_buy_at_high") or 0)-(g(r,"bub_sell_absorbed_low") or 0)
    f["bub_net"]=g(r,"bub_net")
    # momentum a virar
    f["rsi_slope_1h"]=g(r,"1H_rsi_slope")
    AUC[n]=f
AUCF=sorted({k for f in AUC.values() for k in f})

# ---------- discriminacao INTRA-REGIME (familia C/R vs winners comparaveis) ----------
def auc_stat(a,b):
    if not a or not b: return 0.5
    c=t=0
    for x in a:
        for y in b:
            t+=1; c+=1 if x>y else (0.5 if x==y else 0)
    return c/t
def sig(win_ns, los_ns, feats=AUCF, top=10):
    out=[]
    for k in feats:
        wv=[AUC[n].get(k) for n in win_ns if AUC[n].get(k) is not None]
        lv=[AUC[n].get(k) for n in los_ns if AUC[n].get(k) is not None]
        if len(wv)<5 or len(lv)<4: continue
        a=auc_stat(wv,lv); out.append((abs(a-0.5),k,round(st.median(wv),3),round(st.median(lv),3),round(a,3)))
    out.sort(reverse=True); return out[:top]

WIN=[e["n"] for e in ENTRIES if e["out"]==1]
C=sorted(FAM["C"]); R=sorted(FAM["R"])
print("="*84); print("ASSINATURA AUCTION-THEORY POR REGIME — winners vs losers-da-familia DENTRO do regime"); print("="*84)
SIGS={}
for reg,fam_target,tag in [("BULL",C,"C-distribuicao"),("RANGE",C+R,"C+R range/distrib"),("BEAR",C,"C(ref: repique raso)")]:
    wr=[n for n in WIN if REG[n]==reg]; lr=[n for n in fam_target if REG[n]==reg]
    print(f"\n### REGIME {reg} — WIN={len(wr)} vs {tag}={len(lr)} {sorted(lr)}")
    if len(wr)<5 or len(lr)<4:
        print("   (n insuficiente — reportado, nao induzido)"); SIGS[reg]=[]; continue
    s=sig(wr,lr); SIGS[reg]=[(k,wm,lm,a,round(sp,2)) for sp,k,wm,lm,a in s]
    print(f"   {'auction_feature':<20}{'WIN':>9}{'LOSER':>9}{'AUC':>7}  sep  leitura")
    READ={"rangepos_15m":"premio(topo balanca)","rangepos_4h":"premio HTF","excess_rsi_htf":"exaustao/excess",
          "supply_overhead_min":"offer overhead","clean_sky":"ceu limpo","demand_room_4h":"longe da demanda",
          "rotational_smc":"rotacao(balanca)","displacement_15m":"deslocamento","maxbar_atr_15m":"impulso barra",
          "absorption":"absorcao/falha","bub_net":"fluxo bubbles","rsi_slope_1h":"momentum 1H","rangewidth_atr_15m":"largura range"}
    for sp,k,wm,lm,a in s:
        print(f"   {k:<20}{wm:>9}{lm:>9}{a:>7}  {sp:.2f}  {READ.get(k,'')}")

# ---------- CONTRASTE explicito: as 3 assinaturas sao DISTINTAS? ----------
print("\n"+"="*84); print("CONTRASTE DE ASSINATURAS (top-4 por regime) — distintas entre BULL / RANGE / BEAR?"); print("="*84)
for reg in ("BULL","RANGE","BEAR"):
    top=SIGS.get(reg,[])[:4]
    print(f"  {reg:<6}: "+" | ".join(f"{k}(W{wm}/L{lm},AUC{a})" for k,wm,lm,a,sp in top) if top else f"  {reg}: (n insuf)")

# ---------- persist ----------
outrows=[]
for n in sorted(BYN):
    row={"n":n,"out":OUT[n],"fam":famof(n),"regime":REG[n]}; row.update({k:AUC[n].get(k) for k in AUCF})
    outrows.append(row)
with open(HERE+"/results/n96_range_distribution_filter_results.csv","w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=list(outrows[0])); w.writeheader(); w.writerows(outrows)
summ={"method":"structural-first (regime v5 causal) + auction-theory features intra-regime",
      "auction_signatures_top":{reg:SIGS[reg][:5] for reg in SIGS},
      "target":{"C":C,"R":R},"C_by_regime":{r:[n for n in C if REG[n]==r] for r in ("BULL","BEAR","RANGE")},
      "svp":"unavailable (poc/vah/val NULL)","note":"SEM veredito — assinatura por regime entregue como dado; DA arbitra gate/review/management."}
json.dump(summ, open(HERE+"/results/n96_range_distribution_filter_summary.json","w"), indent=1, default=str)
print("\nsaved results/n96_range_distribution_filter_{results.csv,summary.json}")
