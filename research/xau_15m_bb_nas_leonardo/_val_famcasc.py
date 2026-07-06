import json, bisect, hashlib, random
import numpy as np
exec(open("event_cascade_filter_curve_20260706.py").read().split('X=np.array')[0])
# reusa EV com anotações; recomputa arrays
X=np.array([ev[0]["_vec"] for ev in EV]); isf=np.array([ev[0]["_isf"] for ev in EV]); efam=np.array([ev[0]["_efam"] for ev in EV]); cmax=np.array([ev[0]["_cmax"] for ev in EV]); NF=int(isf.sum())
def fam_env(fm):
    m=np.zeros(len(EV),bool)
    for fam in ("RASO","BANDA","FUNDO","SEM"):
        idx=np.where(efam==fam)[0]; fidx=np.where((efam==fam)&fm)[0]
        if len(fidx)<3: m[idx]=True; continue
        lo=X[fidx].min(0); hi=X[fidx].max(0)
        for i in idx:
            if np.all((X[i]>=lo)&(X[i]<=hi)): m[i]=True
    return m
FAM=fam_env(isf)
for T in (2,3):
    mask=FAM&(cmax>=T)
    pe=[ev for k,ev in zip(mask,EV) if k]
    def fst(ev):
        for u in ev:
            if u["_casc"]>=3 and u["_hl"]==1 and u["_reclaim"]==1: return u
        return None
    fired=[ev for ev in pe if fst(ev)]; rows=[fst(ev) for ev in fired]
    obs=sum(1 for r in rows if R3[r["cj_t"]]["R3"]>=3)/len(rows)
    # null-episódio: candidato aleatório dentro de cada evento-disparado
    random.seed(1100+T); ge=0
    for _ in range(4000):
        hh=sum(1 for ev in fired if R3[random.choice(ev)["cj_t"]]["R3"]>=3)
        if hh/len(fired)>=obs: ge+=1
    # null-seleção: E6 em eventos aleatórios do pool família (mesmo N de disparos)
    fam_ev=[ev for k,ev in zip(FAM,EV) if k]
    random.seed(1200+T); ge2=0
    e6_all=[fst(ev) for ev in fam_ev if fst(ev)]
    hits=[1 if R3[r["cj_t"]]["R3"]>=3 else 0 for r in e6_all]
    for _ in range(4000):
        if sum(random.sample(hits,len(rows)))/len(rows)>=obs: ge2+=1
    # streak dist
    nets=[R3[r["cj_t"]]["net3"] for r in sorted(rows,key=lambda x:x["cj_t"])]; random.seed(1300+T); q=[]
    for _ in range(2000):
        sq=random.choices(nets,k=len(nets)); c2=m2=0
        for x in sq:
            c2=c2+1 if x<=0 else 0; m2=max(m2,c2)
        q.append(m2)
    q.sort()
    print(f"família&casc>={T}→E6: N{len(rows)} WR{100*sum(1 for x in nets if x>0)/len(rows):.0f}% hit{100*obs:.0f}% · P(null-episódio)={ge/4000:.3f} · P(null-seleção-E6-no-pool)={ge2/4000:.3f} · streak q95 {q[int(.95*2000)]} P(>5) {sum(1 for x in q if x>5)/2000:.2f}")
