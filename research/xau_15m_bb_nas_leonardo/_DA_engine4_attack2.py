#!/usr/bin/env python3
"""DEVIL'S ADVOCATE attack #2 — refina null-of-max (small-n inflation), e cruza
sentinel x stationarity x concentration nos sobreviventes (R_CONV genuine, R_ROOM)."""
import json,statistics as st,random,bisect,math,io,contextlib,importlib.util
from pathlib import Path
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location("e4",HERE/"engine4_eval.py")
e4=importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(e4)
G=e4.G; MFtot=e4.MFtot; RULES=e4.RULES; f=e4.f
def stats(sel):
    rs=[r["R"] for r in sel]; n=len(rs)
    if not n: return dict(n=0,avgR=None,sumR=0,dd=0,mf=0)
    sm=sum(rs); w=sum(1 for x in rs if x>0); eq=pk=dd=0
    for x in rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    return dict(n=n,wr=round(100*w/n,1),sumR=round(sm,1),avgR=round(sm/n,4),dd=round(dd,1),mf=sum(r["is_monforte"] for r in sel))
sky=lambda r: f(r,"h4n_clean_sky_atr",0)

# --- 1b: null-of-max RESTRITO às regras com n>=300 (remove inflação small-n) ---
print("### ATTACK 1b: null-of-max restrito a regras n>=300 (small-n rules inflam o max)")
allR=[r["R"] for r in G]
rule_names=[nm for nm in RULES]
masks={nm:[RULES[nm](r) for r in G] for nm in rule_names}
idx_by_rule={nm:[i for i,m in enumerate(masks[nm]) if m] for nm in rule_names}
big=[nm for nm in rule_names if 300<=len(idx_by_rule[nm])]  # tradeable size, exclude take-all-ish
big=[nm for nm in big if nm!="TAKE-ALL"]
print(f"  regras n>=300 (excl take-all): {big}")
obs={nm:stats([r for r in G if RULES[nm](r)])["avgR"] for nm in rule_names}
K=3000; random.seed(202)
maxnull=[]
for _ in range(K):
    shuf=allR[:]; random.shuffle(shuf)
    b=max(sum(shuf[i] for i in idx_by_rule[nm])/len(idx_by_rule[nm]) for nm in big)
    maxnull.append(b)
maxnull.sort()
p=lambda x: sum(1 for d in maxnull if d>=x)/len(maxnull)
print(f"  null-of-max(n>=300): mean={st.mean(maxnull):.4f} p95={maxnull[int(.95*K)]:.4f} p99={maxnull[int(.99*K)]:.4f}")
for nm in ["R_ROOM sky>=1.5","R_CONV fresh+room","KK + R_ROOM","KNIFEKILL_v2(flow)"]:
    print(f"    {nm:<22} obs={obs[nm]:.4f} maxnull_p={p(obs[nm]):.4f} {'CLEARS' if p(obs[nm])<0.05 else 'FAILS'}")

# --- R_CONV genuine: best avgR thing. Test it through all controls ---
print("\n### R_CONV GENUINE (q4_fresh<=30 & 1.5<=sky<99) — full gauntlet")
cg=[r for r in G if f(r,'q4_fresh',999)<=30 and 1.5<=sky(r)<98.9]
print(f"  base: {stats(cg)}")
ex=[r for r in cg if r['yr']!=2025]; print(f"  ex-2025: {stats(ex)}  (base ex2025 avgR={stats([r for r in G if r['yr']!=2025])['avgR']})")
# concentration
rs=sorted([r['R'] for r in cg],reverse=True); tot=sum(rs)
order=sorted(range(len(cg)),key=lambda i:cg[i]['R'],reverse=True)
no5=stats([cg[i] for i in set(range(len(cg)))-set(order[:5])])
print(f"  top5 share={round(100*sum(rs[:5])/tot,1)}% rm-top5 avgR={no5['avgR']} max={round(rs[0],1)}")
# leave-block
blocks=sorted(set(r['block'] for r in G))
loo=[(bk,stats([r for r in cg if r['block']!=bk])['avgR']) for bk in blocks]
print(f"  LOO avgR min={min(x[1] for x in loo)} max={max(x[1] for x in loo)}")
# null single
n=len(cg); a=stats(cg)['avgR']; random.seed(5); c=sum(1 for _ in range(2000) if st.mean(random.sample(allR,n))>=a)/2000
print(f"  single null p={c:.4f}  | maxnull_p={p(a):.4f}")

# --- Is sentinel = ATH/strong-uptrend beta? sentinel rows: what is h4n_trend / h1n_trend dist ---
print("\n### SENTINEL CHARACTER: is 'no supply above' = strong-uptrend/ATH beta?")
sent=[r for r in G if sky(r)>=98.9]; nonsent=[r for r in G if sky(r)<98.9]
def trd(sel,k):
    vals=[f(r,k) for r in sel if f(r,k) is not None]
    return Counter_like(vals)
from collections import Counter
for k in ("h4n_trend","h1n_trend"):
    cs=Counter(f(r,k) for r in sent); cn=Counter(f(r,k) for r in nonsent)
    tot_s=sum(cs.values()); tot_n=sum(cn.values())
    print(f"  {k}: SENTINEL up%={round(100*cs.get(1,0)/tot_s,1)} dn%={round(100*cs.get(-1,0)/tot_s,1)} | NONSENT up%={round(100*cn.get(1,0)/tot_n,1)} dn%={round(100*cn.get(-1,0)/tot_n,1)}")
# fraction of sentinel rows that are also in 2025
print(f"  sentinel year dist: 2024={sum(1 for r in sent if r['yr']==2024)} 2025={sum(1 for r in sent if r['yr']==2025)} 2026={sum(1 for r in sent if r['yr']==2026)}")
print(f"  sentinel ex-2025 avgR={stats([r for r in sent if r['yr']!=2025])['avgR']}  vs nonsent ex-2025 avgR={stats([r for r in nonsent if r['yr']!=2025])['avgR']}")
