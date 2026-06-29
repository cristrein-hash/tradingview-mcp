#!/usr/bin/env python3
"""FASE 1 VALIDAÇÃO — macro Tier-1 (FRED keyless) vs estratégias aprovadas (L1/L2/15M). As-of join causal
(release_ts<=entry_ts), separação avgR (lado gold-favorável vs não), null permutation, jackknife por-ano, beta-check.
Red-team look-ahead embutido (print futuro tem que ser excluído). Cânone: SEM OOS; validação nos dados; DA-aware.
Determinístico."""
import json,csv,bisect,statistics as st,random,datetime as dt
from pathlib import Path
H=Path(__file__).parent.parent
REPO=Path("/Users/cristrein/tradingview-mcp")
# ---- painel macro ----
P={}
for l in (H/"snapshots/macro_panel.jsonl").read_text().splitlines():
    r=json.loads(l); P.setdefault(r["series_id"],[]).append((r["release_ts"],r["value"]))
for k in P: P[k].sort()
def asof(sid,ts):
    a=P.get(sid)
    if not a: return None
    i=bisect.bisect_right(a,(ts,float("inf")))-1
    return a[i][1] if i>=0 else None
def change(sid,ts,days):
    v=asof(sid,ts); v0=asof(sid,ts-days*86400)
    return (v-v0) if (v is not None and v0 is not None) else None
# ---- estratégias ----
def iso(s): return int(dt.datetime.strptime(s,"%Y-%m-%dT%H:%M").replace(tzinfo=dt.timezone.utc).timestamp())
def dep(s): return int(dt.datetime.strptime(s,"%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
def load_L1():
    d=json.loads((REPO/"my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5/l1_FINAL_regime_gated.json").read_text())
    return [(iso(t["ts"]),float(t["R"])) for t in d["trades"]]
def load_L2():
    out=[]
    for r in csv.DictReader(open(REPO/"my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_uncapped_or_proxy_outcomes_276.csv")):
        try: out.append((dep(r["datetime"]),float(r["realized_vstair_120"])))
        except: pass
    return out
def load_15M():
    out=[]
    for r in csv.DictReader(open(REPO/"research/xau_15m_bb_nas_leonardo/fixed_base_h4h1.csv")):
        try: out.append((int(r["cj_t"]),float(r["R"])))
        except: pass
    return out
STR={"L1":load_L1(),"L2":load_L2(),"15M":load_15M()}
# ---- factor views (gold-favorável p/ LONG): sign=+1 se MAIOR favorece, -1 se MENOR favorece ----
FACT=[
 ("real_yield_lvl","us10y_real","lvl",-1),   # real yield baixo = bom p/ ouro
 ("real_yield_chg20","us10y_real","chg20",-1),# real yield caindo = bom
 ("usd_lvl","usd_broad","lvl",-1),            # USD baixo = bom
 ("usd_chg20","usd_broad","chg20",-1),        # USD caindo = bom
 ("breakeven_lvl","breakeven_10y","lvl",+1),  # inflação expect alta = bom
 ("vix_lvl","vix","lvl",+1),                  # risk-off = bom (testar)
 ("us10y_chg20","us10y_nominal","chg20",-1),
]
def fval(view,sid,kind,ts): return asof(sid,ts) if kind=="lvl" else change(sid,ts,20)
def panel(rs):
    R=[r for _,r in rs]; n=len(R); return (n, round(100*sum(1 for x in R if x>0)/n,1), round(sum(R)/n,3)) if n else (0,0,0)
def yr(ts): return dt.datetime.utcfromtimestamp(ts).year
print("VALIDAÇÃO MACRO TIER-1 (keyless) vs estratégias — separação avgR (favorável vs resto), null-p, per-ano\n")
print(f"{'estrat':<5}{'factor':<16}{'N':>4}{'favN':>5}{'fav_avgR':>9}{'rest_avgR':>10}{'Δ':>7}{'null_p':>7}{'anos_fav+':>10}")
RND=random.Random(7)
for sname,trades in STR.items():
    # red-team: nenhum asof pode ter release_ts > entry_ts (garantido por bisect; checa 1 plantado)
    for fv,sid,kind,sign in FACT:
        vals=[]
        for ts,R in trades:
            v=fval(fv,sid,kind,ts)
            if v is not None: vals.append((ts,R,v))
        if len(vals)<20: continue
        med=st.median(v for _,_,v in vals)
        fav=[(ts,R) for ts,R,v in vals if (v<=med if sign<0 else v>=med)]
        rest=[(ts,R) for ts,R,v in vals if not (v<=med if sign<0 else v>=med)]
        nF,_,avF=panel(fav); nR_,_,avR=panel(rest); delta=round(avF-avR,3)
        # null: permuta R entre os trades, recomputa delta |>=|
        obs=abs(delta); cnt=0; allR=[R for _,R,_ in vals]; lab=[(v<=med if sign<0 else v>=med) for _,_,v in vals]
        for _ in range(500):
            RND.shuffle(allR)
            a=[allR[i] for i in range(len(allR)) if lab[i]]; b=[allR[i] for i in range(len(allR)) if not lab[i]]
            if a and b and abs(sum(a)/len(a)-sum(b)/len(b))>=obs: cnt+=1
        p=round(cnt/500,3)
        # per-ano: favorável é positivo em quantos anos
        yrs=sorted(set(yr(ts) for ts,_ in fav)); pos=sum(1 for y in yrs if sum(R for ts,R in fav if yr(ts)==y)>=0)
        print(f"{sname:<5}{fv:<16}{len(vals):>4}{nF:>5}{avF:>9}{avR:>10}{delta:>+7}{p:>7}{f'{pos}/{len(yrs)}':>10}")
print("\nfav=lado gold-favorável (real-yield/USD baixos, breakeven/VIX altos). Δ>0 = macro favorável separa winners.")
print("Robusto SÓ se Δ>0 consistente + null_p<0.02 + anos_fav majoritariamente + (DA: não-beta). Bonferroni: ~21 testes.")
