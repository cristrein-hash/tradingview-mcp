#!/usr/bin/env python3
"""N96 · D-BEAR-ACTIVE FILTER ROUND (2026-07-08). Research-only, RAW-first, LONG-only.
Familia D (bear ativo). O intra-BEAR ja corta o repique RASO (1D_px_vs_ema>=0). Aqui: o problema DIFICIL =
dentro do bear PROFUNDO (1D_px_vs_ema<0, que o filtro MANTEM), separar FACA CAINDO / CAPITULACAO VALIDA /
LOWER-HIGH bounce. Subfamilias D1 faca / D2 repique raso (=ja cortado) / D3 lower-high / D4 capitulacao valida /
D5 gestao. Cruza RAW/MTF por contexto (regime v5 causal). Reusa features auction (n96_range_distribution_filter_results.csv)
+ exhaustive (SMC/bubbles/RSI). SVP unavailable. Fail-loud se N96 nao reproduz. SEM veredito — DA arbitra."""
import csv, sys, json, statistics as st, datetime as dt
import numpy as np
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from n96_mtf_kit import HERE, FAM, famof
from agent_ctx_kit import ENTRIES
assert len(ENTRIES)==96 and sum(e["out"] for e in ENTRIES)==52, "FAIL-LOUD: N96 nao reproduz"
REG={int(k):v for k,v in json.load(open(HERE+"/results/n96_causal_regime.json")).items()}
EX={int(r["n"]):r for r in csv.DictReader(open(HERE+"/results/n96_exhaustive_mtf_features.csv"))}
AU={int(r["n"]):r for r in csv.DictReader(open(HERE+"/results/n96_range_distribution_filter_results.csv"))}
OUT={int(r["n"]):int(r["out"]) for r in EX.values()}
TBYN={e["n"]:e["t"] for e in ENTRIES}
def gx(n,k):
    try: return float(EX[n].get(k))
    except: return None
def ga(n,k):
    try: return float(AU[n].get(k))
    except: return None
def d(n): return dt.datetime.utcfromtimestamp(TBYN[n]).strftime("%Y-%m-%d")
def yr(n): return dt.datetime.utcfromtimestamp(TBYN[n]).year

D=sorted(FAM["D"])
CUT_INTRABEAR=[n for n in sorted(OUT) if REG[n]=="BEAR" and (gx(n,"1D_px_vs_ema") or -99)>=0]

# ---- 1. listar todos os D ----
print("="*88); print("FAMILIA D (bear ativo) — 14 losers"); print("="*88)
print(f"{'#':>4} {'data':<11}{'regime':<7}{'1D_pxEMA':>9}{'1D_trend':>9}{'1D_rsi':>7}{'reclaim?':>9}{'cut_intraBEAR':>14}")
for n in D:
    cut="SIM" if n in CUT_INTRABEAR else "nao"
    print(f"#{n:>3} {d(n):<11}{REG[n]:<7}{str(gx(n,'1D_px_vs_ema')):>9}{str(gx(n,'1D_ema_trend')):>9}{str(gx(n,'1D_rsi')):>7}{'':>9}{cut:>14}")
# D winners nao existem (D=familia loser). "winners intra-bear a preservar" = winners no regime BEAR:
BEARWIN=[n for n in sorted(OUT) if REG[n]=="BEAR" and OUT[n]==1]
print(f"\nD losers: {len(D)} | ja cortados pelo intra-BEAR: {[n for n in D if n in CUT_INTRABEAR]} | permanecem: {[n for n in D if n not in CUT_INTRABEAR]}")
print(f"winners no regime BEAR (a PRESERVAR): {BEARWIN} (N={len(BEARWIN)})")

# ---- 2. POOL DEEP-BEAR = o problema dificil: BEAR & 1D_px_vs_ema<0 (o que o intra-BEAR MANTEM) ----
DEEP=[n for n in sorted(OUT) if REG[n]=="BEAR" and (gx(n,"1D_px_vs_ema") or 9)<0]
Dwin=[n for n in DEEP if OUT[n]==1]; Dlos=[n for n in DEEP if OUT[n]==0]
print("\n"+"="*88); print("POOL DEEP-BEAR (BEAR & preco ABAIXO da EMA 1D = o filtro MANTEM) — capitulacao vs faca"); print("="*88)
print(f"  N={len(DEEP)}  winners(capitulacao valida)={len(Dwin)} {Dwin}  losers(faca/lower-high)={len(Dlos)} {Dlos}")

# ---- 3. subfamilias (heuristica estrutural, causal) ----
def subfam(n):
    px=gx(n,"1D_px_vs_ema") or 0; tr=gx(n,"1D_ema_trend") or 0; rs1h=gx(n,"1H_rsi_slope") or 0
    absб=ga(n,"absorption") or 0; disp=ga(n,"displacement_15m") or 0
    if REG[n]=="BEAR" and px>=0: return "D2_repique_raso"           # ja cortado intra-BEAR
    if tr< -3.0 and rs1h< -8: return "D1_faca_caindo"              # 1D a cair forte + momentum 1H despenca
    if px< -5 and rs1h>0: return "D4_capitulacao_valida"          # fundo + momentum a virar
    if -5<=px<0: return "D3_lower_high_bounce"                    # repique meio-profundo
    return "D5_outro"
print("\nsubfamilias dos D losers (heuristica):")
from collections import defaultdict
sub=defaultdict(list)
for n in D: sub[subfam(n)].append(n)
for k in sorted(sub): print(f"  {k:<22} {sub[k]}")

# ---- 4. discriminacao DENTRO do DEEP-BEAR: capitulacao(win) vs faca/failed(los) ----
def auc(a,b):
    if not a or not b: return 0.5
    c=t=0
    for x in a:
        for y in b:
            t+=1; c+=1 if x>y else (0.5 if x==y else 0)
    return c/t
FEATS_EX=[c for c in next(iter(EX.values())) if c not in ("n","out","fam")]
FEATS_AU=[c for c in next(iter(AU.values())) if c not in ("n","out","fam","regime")]
def val(n,k): return ga(n,k) if k in FEATS_AU else gx(n,k)
ALLK=FEATS_AU+FEATS_EX
print("\n"+"="*88); print("DISCRIMINACAO DEEP-BEAR: winner(capitulacao) vs loser(faca/failed) — top separadores"); print("="*88)
ranked=[]
for k in ALLK:
    wv=[val(n,k) for n in Dwin if val(n,k) is not None]; lv=[val(n,k) for n in Dlos if val(n,k) is not None]
    if len(wv)<5 or len(lv)<4: continue
    a=auc(wv,lv); ranked.append((abs(a-0.5),k,round(st.median(wv),3),round(st.median(lv),3),round(a,3)))
ranked.sort(reverse=True)
print(f"   {'feature':<20}{'WIN(capit)':>11}{'LOS(faca)':>11}{'AUC':>7}  sep")
for sp,k,wm,lm,a in ranked[:12]: print(f"   {k:<20}{wm:>11}{lm:>11}{a:>7}  {sp:.2f}")

# ---- 5. candidato de corte DENTRO do deep-bear + null honesto ----
print("\n"+"="*88); print("CANDIDATO corte intra-DEEP-BEAR — cortar o LADO DOS LOSERS (knife) + null aleatorio"); print("="*88)
def Rof(ns):
    w=sum(OUT[n] for n in ns); return w,len(ns)-w,w*3-(len(ns)-w)
base=Rof(sorted(OUT))[2]
outs_dp=np.array([OUT[n] for n in DEEP])
def null_p(k,obs_dR):
    rng=np.random.default_rng(9); nul=[]
    for _ in range(4000):
        idx=rng.choice(len(DEEP),k,replace=False); ww=outs_dp[idx].sum(); nul.append(-(ww*3-(k-ww)))
    nul=np.array(nul); return float((nul>=obs_dR).mean()), np.quantile(nul,0.95)
# testar top-4 features, cada uma cortando o LADO ONDE O LOSER CONCENTRA (AUC>0.5 => loser=baixo => cortar baixos)
for sp,topk,wm,lm,a in ranked[:4]:
    vals_dp={n:val(n,topk) for n in DEEP if val(n,topk) is not None}
    loser_low = a>0.5   # winner>loser => losers no lado BAIXO => cortar <= thr
    for q in (0.4,0.5,0.6):
        thr=np.quantile(list(vals_dp.values()), q if loser_low else 1-q)
        cut=[n for n in DEEP if n in vals_dp and ((vals_dp[n]<=thr) if loser_low else (vals_dp[n]>=thr))]
        if not cut: continue
        cw,cl,_=Rof(cut); kR=Rof([n for n in sorted(OUT) if n not in cut])[2]
        p,q95=null_p(len(cut), kR-base)
        print(f"  {topk:<18} corta lado-loser q={q}: cut={len(cut)} (win {cw} los {cl}) dR={kR-base:+d} | null q95={q95:+.1f} P={p:.3f}")

# ---- persist ----
outrows=[]
for n in D+Dwin:
    outrows.append({"n":n,"out":OUT[n],"regime":REG[n],"subfam":subfam(n) if n in D else "WIN_bear",
                    "1D_px_vs_ema":gx(n,"1D_px_vs_ema"),"1D_ema_trend":gx(n,"1D_ema_trend"),"1D_rsi":gx(n,"1D_rsi"),
                    "1H_rsi_slope":gx(n,"1H_rsi_slope"),"absorption":ga(n,"absorption"),"displacement_15m":ga(n,"displacement_15m"),
                    "cut_intraBEAR":("SIM" if n in CUT_INTRABEAR else "nao")})
with open(HERE+"/results/n96_d_bear_active_filter_results.csv","w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=list(outrows[0])); w.writeheader(); w.writerows(outrows)
summ={"D_losers":D,"cut_by_intraBEAR":[n for n in D if n in CUT_INTRABEAR],"remain":[n for n in D if n not in CUT_INTRABEAR],
      "deep_bear_pool":{"N":len(DEEP),"winners_capitulation":Dwin,"losers_knife":Dlos},
      "subfamilies":{k:sub[k] for k in sub},"top_discriminators_deep":[(k,a) for sp,k,wm,lm,a in ranked[:6]],
      "note":"SEM veredito. DA arbitra gate/review/management vs intra-BEAR ja basta."}
json.dump(summ, open(HERE+"/results/n96_d_bear_active_filter_summary.json","w"), indent=1, default=str)
print("\nsaved results/n96_d_bear_active_filter_{results.csv,summary.json}")
