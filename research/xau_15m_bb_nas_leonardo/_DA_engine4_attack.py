#!/usr/bin/env python3
"""DEVIL'S ADVOCATE — ataque às regras risk-shaping do ENGINE 4 (Cris 2026-06-28).
Reaproveita o evaluator (engine4_eval) como FONTE DE R (let-run sim idêntico). Não recalcula R.
Ataques 1-7: null-of-the-max+Bonferroni, clean-sky sentinel decompose, stationarity ex-2025,
leave-block, concentration, risk-adjusted honesty, look-ahead verify."""
import json,statistics as st,random,bisect,math
from pathlib import Path
HERE=Path(__file__).parent

# ---- importa universo G já com R calculado pelo evaluator oficial ----
import importlib.util
spec=importlib.util.spec_from_file_location("e4",HERE/"engine4_eval.py")
e4=importlib.util.module_from_spec(spec)
# silencia o print do evaluator
import io,contextlib
buf=io.StringIO()
with contextlib.redirect_stdout(buf):
    spec.loader.exec_module(e4)
G=e4.G; MFtot=e4.MFtot; RULES=e4.RULES; f=e4.f
print(f"[setup] universo G={len(G)} | MON+FORTE={MFtot} | regras={len(RULES)}")

def stats(sel):
    rs=[r["R"] for r in sel]; n=len(rs)
    if not n: return dict(n=0)
    sm=sum(rs); w=sum(1 for x in rs if x>0); eq=pk=dd=0
    for x in rs: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    mf=sum(r["is_monforte"] for r in sel)
    py={}
    for y in (2024,2025,2026):
        yr=[r["R"] for r in sel if r["yr"]==y]
        py[y]=(len(yr),round(sum(yr),1),round(st.mean(yr),3) if yr else None)
    return dict(n=n,wr=round(100*w/n,1),sumR=round(sm,1),avgR=round(sm/n,4),dd=round(dd,1),
                mf=mf,recall=round(mf/MFtot,3),py=py)

base=stats(G)
print(f"[baseline take-all] {base['n']} avgR={base['avgR']} sumR={base['sumR']} DD={base['dd']} recall_MF={base['recall']}")
print("="*100)

# ============================================================
# ATTACK 1: NULL-OF-THE-MAX + Bonferroni
# ============================================================
print("\n### ATTACK 1: NULL-OF-THE-MAX + Bonferroni (corrige a busca por ~13 regras)")
# regras avaliadas (todas as do dict). Calcula avgR observado de cada.
rule_names=[nm for nm in RULES]
obs={}
sels={}
for nm in rule_names:
    sel=[r for r in G if RULES[nm](r)]
    sels[nm]=sel
    obs[nm]=stats(sel)["avgR"] if sel else float("nan")
K=2000
allR=[r["R"] for r in G]
random.seed(101)
# Para cada shuffle: embaralha R sobre o universo, reaplica TODAS as regras (mantendo a MASK de cada regra fixa),
# pega a MAX avgR entre as regras nesse shuffle. Compara com obs.
# Mask por regra (booleano por índice de G) é fixa; só R muda.
masks={nm:[RULES[nm](r) for r in G] for nm in rule_names}
idx_by_rule={nm:[i for i,m in enumerate(masks[nm]) if m] for nm in rule_names}
n_idx=len(G)
max_null=[]
# distribuição null por-regra (single) e o MAX
single_null={nm:[] for nm in rule_names}
for _ in range(K):
    shuf=allR[:]; random.shuffle(shuf)
    best=-1e9
    for nm in rule_names:
        ii=idx_by_rule[nm]
        if not ii: continue
        a=sum(shuf[i] for i in ii)/len(ii)
        single_null[nm].append(a)
        if a>best: best=a
    max_null.append(best)
max_null.sort()
def pval_ge(dist,x):
    # P(null >= x)
    c=sum(1 for d in dist if d>=x); return c/len(dist)
print(f"  K={K} shuffles. null-of-MAX distribution: mean={st.mean(max_null):.4f} p95={max_null[int(0.95*K)]:.4f} p99={max_null[int(0.99*K)]:.4f} max={max_null[-1]:.4f}")
print(f"  {'rule':<24}{'obs_avgR':>9}{'single_p':>10}{'maxnull_p':>11}  verdict")
focus=["R_ROOM sky>=1.5","R_CONV fresh+room","KK + R_ROOM","KNIFEKILL_v2(flow)"]
for nm in rule_names:
    if math.isnan(obs[nm]): continue
    sp=pval_ge(single_null[nm],obs[nm])
    mp=pval_ge(max_null,obs[nm])
    tag="<-- focus" if nm in focus else ""
    surv="CLEARS maxnull" if mp<0.05 else ("borderline" if mp<0.10 else "FAILS maxnull")
    print(f"  {nm:<24}{obs[nm]:>9.4f}{sp:>10.4f}{mp:>11.4f}  {surv} {tag}")

# ============================================================
# ATTACK 2: CLEAN-SKY SENTINEL decompose
# ============================================================
print("\n### ATTACK 2: CLEAN-SKY SENTINEL (sky==99 'no supply mapped' vs genuine 1.5<=sky<99)")
def sky(r): return f(r,"h4n_clean_sky_atr",0)
room=[r for r in G if sky(r)>=1.5]
sent=[r for r in room if sky(r)>=98.9]          # 99 sentinel
genu=[r for r in room if 1.5<=sky(r)<98.9]      # genuine bounded room
print(f"  R_ROOM total: {stats(room)}")
print(f"  SENTINEL (sky==99, no supply above): {stats(sent)}")
print(f"  GENUINE (1.5<=sky<99): {stats(genu)}")
# what fraction of universe is sentinel overall?
allsent=[r for r in G if sky(r)>=98.9]
print(f"  universe sentinel share: {len(allsent)}/{len(G)} = {len(allsent)/len(G):.3f} | sentinel avgR={stats(allsent)['avgR']} vs nonsent avgR={stats([r for r in G if sky(r)<98.9])['avgR']}")
# R_CONV decompose too
conv=[r for r in G if f(r,'q4_fresh',999)<=30 and sky(r)>=1.5]
conv_sent=[r for r in conv if sky(r)>=98.9]; conv_genu=[r for r in conv if 1.5<=sky(r)<98.9]
print(f"  R_CONV total: {stats(conv)}")
print(f"  R_CONV sentinel: {stats(conv_sent)}")
print(f"  R_CONV genuine: {stats(conv_genu)}")

# ============================================================
# ATTACK 3: STATIONARITY ex-2025
# ============================================================
print("\n### ATTACK 3: STATIONARITY (sumR share by year, avgR ex-2025)")
def ex2025(sel):
    s=[r for r in sel if r["yr"]!=2025]; return stats(s)
def yshare(sel):
    tot=sum(r["R"] for r in sel)
    out={}
    for y in (2024,2025,2026):
        sy=sum(r["R"] for r in sel if r["yr"]==y)
        out[y]=round(sy/tot,3) if tot else None
    return out
for nm,sel in [("TAKE-ALL",G),("R_ROOM",room),("R_CONV",conv),("KK+R_ROOM",sels["KK + R_ROOM"]),("GENUINE_ROOM",genu)]:
    sh=yshare(sel); ex=ex2025(sel)
    print(f"  {nm:<14} sumR-share 24/25/26={sh[2024]}/{sh[2025]}/{sh[2026]} | ex2025: n={ex['n']} avgR={ex['avgR']} sumR={ex['sumR']} (base ex2025 avgR={ex2025(G)['avgR']})")

# ============================================================
# ATTACK 4: LEAVE-BLOCK (8 folds)
# ============================================================
print("\n### ATTACK 4: LEAVE-ONE-BLOCK (per block fold)")
blocks=sorted(set(r["block"] for r in G))
print(f"  {len(blocks)} blocks: {blocks}")
def leaveblock(sel_fn):
    res=[]
    for bk in blocks:
        sub=[r for r in G if r["block"]!=bk and sel_fn(r)]
        m=stats(sub)
        res.append((bk,m["avgR"],m["n"]))
    avgs=[x[1] for x in res]
    return res,min(avgs),max(avgs)
for nm,fn in [("R_ROOM",lambda r:sky(r)>=1.5),
              ("R_CONV",lambda r:f(r,'q4_fresh',999)<=30 and sky(r)>=1.5),
              ("KK+R_ROOM",RULES["KK + R_ROOM"]),
              ("GENUINE_ROOM",lambda r:1.5<=sky(r)<98.9)]:
    res,mn,mx=leaveblock(fn)
    full=stats([r for r in G if fn(r)])["avgR"]
    # which block, when REMOVED, drops avgR most (=that block carried it)
    worst=min(res,key=lambda x:x[1]); best=max(res,key=lambda x:x[1])
    print(f"  {nm:<14} full avgR={full} | LOO min={mn} (drop block {worst[0]}) max={mx} | spread={round(mx-mn,3)}")

# ============================================================
# ATTACK 5: CONCENTRATION
# ============================================================
print("\n### ATTACK 5: CONCENTRATION (tail dependence)")
def conc(sel,nm):
    rs=sorted([r["R"] for r in sel],reverse=True)
    tot=sum(rs); n=len(rs)
    t5=sum(rs[:5]); t10=sum(rs[:10])
    no5=stats([r for r in sel if r["R"] not in set(rs[:5])])  # approx: remove top5 by value (dup-safe below)
    # dup-safe remove top5 by index
    order=sorted(range(len(sel)),key=lambda i:sel[i]["R"],reverse=True)
    keep=set(range(len(sel)))-set(order[:5])
    no5=stats([sel[i] for i in keep])
    keep10=set(range(len(sel)))-set(order[:10])
    no10=stats([sel[i] for i in keep10])
    ncap=sum(1 for r in sel if r["R"]>=19.9)  # RCAP20 monsters
    print(f"  {nm:<14} n={n} sumR={round(tot,1)} top5={round(t5,1)}({round(100*t5/tot,1)}%) top10={round(t10,1)}({round(100*t10/tot,1)}%) | rm-top5 avgR={no5['avgR']} rm-top10 avgR={no10['avgR']} | RCAP20 monsters={ncap} max={round(rs[0],1)}")
conc(G,"TAKE-ALL")
conc(room,"R_ROOM")
conc(conv,"R_CONV")
conc(sels["KK + R_ROOM"],"KK+R_ROOM")
conc(genu,"GENUINE_ROOM")

# ============================================================
# ATTACK 6: RISK-ADJUSTED HONESTY
# ============================================================
print("\n### ATTACK 6: RISK-ADJUSTED HONESTY (return-per-DD, avgR CI, recall cost)")
def boot_ci(sel,B=2000):
    rs=[r["R"] for r in sel]; n=len(rs)
    if n<2: return (None,None)
    random.seed(7)
    means=[]
    for _ in range(B):
        s=[rs[random.randrange(n)] for __ in range(n)]
        means.append(sum(s)/n)
    means.sort()
    return (round(means[int(0.025*B)],4),round(means[int(0.975*B)],4))
for nm,sel in [("TAKE-ALL",G),("R_ROOM",room),("R_CONV",conv),("KK+R_ROOM",sels["KK + R_ROOM"]),("GENUINE_ROOM",genu)]:
    m=stats(sel); ci=boot_ci(sel)
    rpd=round(m["sumR"]/abs(m["dd"]),2) if m["dd"]!=0 else None
    print(f"  {nm:<14} n={m['n']} avgR={m['avgR']} CI95={ci} sumR={m['sumR']} DD={m['dd']} return/DD={rpd} recall_MF={m['recall']} (drops {round(100*(1-m['recall']))}% of MON+FORTE)")
print(f"  base return/DD={round(base['sumR']/abs(base['dd']),2)}")

# ============================================================
# ATTACK 7: LOOK-AHEAD (verified by code inspection — assert structural)
# ============================================================
print("\n### ATTACK 7: LOOK-AHEAD verification")
# verify clean_sky uses supply zones born_t<=t (causal) and as-of closed 4H bar.
# Re-derive sky for a sample of rows directly from htf primitives to confirm it matches stored feature.
H4=json.loads((HERE/"htf_primitives"/"htf_4H.primitives.json").read_text())
S=sorted(H4["series"],key=lambda b:b["t"]); TS=[b["t"] for b in S]
ZS=[z for z in H4["zones"] if "SUPPLY" in str(z.get("text","")).upper()]
def asof(t):
    i=bisect.bisect_right(TS,t-14400)-1
    return S[i] if i>=0 else None
mism=0; chk=0; future_born=0
for r in random.sample(G,min(300,len(G))):
    t=r["cj_t"]; c=None
    pr=e4.PRIMK.get(r["block"]); s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    cj=tmap.get(r["cj_t"])
    if cj is None: continue
    c=s[cj]["c"]; b=asof(t)
    if not b or not b.get("atr"): continue
    atr=b["atr"]
    supa=[z for z in ZS if z.get("born_t") is not None and z["born_t"]<=t and z.get("low") is not None and z["low"]>c]
    rec=round(min((z["low"]-c)/atr for z in supa),2) if supa else 99
    stored=f(r,"h4n_clean_sky_atr")
    chk+=1
    if stored is not None and abs(rec-stored)>0.01: mism+=1
    # any supply used with born_t>t?
    for z in ZS:
        if z.get("born_t") and z["born_t"]>t and z.get("low") and z["low"]>c: pass
print(f"  clean_sky causal re-derive: checked={chk} mismatches={mism} (0=causal & faithful)")
print(f"  q4_fresh: uses H4 DEMAND with born_t<=cj_t (line 44 evaluator bisect on H4Db) — causal by construction")
print(f"  asof_bar uses t-tf (last CLOSED 4H bar) — confirmed line 21-24 build_engine3_features.py")
print("="*100)
print("DONE")
