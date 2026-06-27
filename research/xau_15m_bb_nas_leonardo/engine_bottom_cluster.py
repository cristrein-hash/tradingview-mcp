#!/usr/bin/env python3
"""PHASE 3-4 — Fingerprint clustering + twins contrastivos (Cris 2026-06-27). Determinístico (numpy, k-means próprio).
CLUSTER: z-score das features numéricas (impute mediana) → k-means k=5 → composição de tier por cluster (descobre
'famílias de fundo' que os dados nomeiam; quais carregam MONSTRO/FORTE vs FRACO).
TWINS: pares de fundos PRÓXIMOS no espaço (euclid) com tier OPOSTO (MON/FORTE vs FRACO) → feature de maior diferença
= o eixo diferenciador naquele contexto. Tier = label forward (nunca entra no vetor). -> bottom_cluster_report.txt"""
import json,numpy as np
from pathlib import Path
HERE=Path(__file__).parent
ROWS=[json.loads(l) for l in (HERE/"bottom_features.jsonl").read_text().splitlines()]
META={'block','t','yr','tier','tier_clean','leg_atr','power_score','session'}
F=[k for k in ROWS[0] if k not in META and isinstance(ROWS[0][k],(int,float))]
X=np.array([[ (r[f] if r.get(f) is not None else np.nan) for f in F] for r in ROWS],float)
# impute mediana por coluna + z-score
for j in range(X.shape[1]):
    col=X[:,j]; m=np.nanmedian(col); col[np.isnan(col)]=m
    sd=col.std() or 1; X[:,j]=(col-col.mean())/sd
tier=np.array([r["tier"] for r in ROWS]); yr=np.array([r["yr"] for r in ROWS])
strong2=np.array([1 if t in("MONSTRO","FORTE") else 0 for t in tier])
fraco=np.array([1 if t=="FRACO" else 0 for t in tier])

def kmeans(X,k,iters=50,seed_idx=None):
    rng_idx=seed_idx if seed_idx is not None else [int(i) for i in np.linspace(0,len(X)-1,k)]
    C=X[rng_idx].copy()
    for _ in range(iters):
        d=((X[:,None,:]-C[None,:,:])**2).sum(2); lab=d.argmin(1)
        newC=np.array([X[lab==c].mean(0) if (lab==c).any() else C[c] for c in range(k)])
        if np.allclose(newC,C): C=newC; break
        C=newC
    return lab,C
lab,C=kmeans(X,5)

L=[]
base2=strong2.mean(); basef=fraco.mean()
L.append(f"N={len(ROWS)} | base MON+FORTE={base2:.2f}  base FRACO={basef:.2f} | features={len(F)} | k=5")
L.append("\n=== CLUSTERS (família de fundo; rate MON+FORTE vs FRACO; eixos médios mais salientes) ===")
for c in range(5):
    m=lab==c; n=int(m.sum())
    if n==0: continue
    mf=strong2[m].mean(); fr=fraco[m].mean()
    cen=C[c]; top=sorted(range(len(F)),key=lambda j:-abs(cen[j]))[:6]
    desc=", ".join(f"{F[j]}{'+' if cen[j]>0 else '-'}{abs(cen[j]):.1f}" for j in top)
    yrs={int(y):int((m&(yr==y)).sum()) for y in (2024,2025,2026)}
    L.append(f" C{c}: n={n:>3} MON+FORTE={mf:.2f}(x{mf/base2:.2f}) FRACO={fr:.2f}(x{fr/basef:.2f}) yr{yrs}")
    L.append(f"     eixos: {desc}")

# ---- TWINS contrastivos ----
D=np.sqrt(((X[:,None,:]-X[None,:,:])**2).sum(2))
np.fill_diagonal(D,1e9)
pairs=[]
for i in range(len(ROWS)):
    for j in range(i+1,len(ROWS)):
        ti,tj=tier[i],tier[j]
        opp=((ti in("MONSTRO","FORTE")) and tj=="FRACO") or ((tj in("MONSTRO","FORTE")) and ti=="FRACO")
        if opp: pairs.append((D[i,j],i,j))
pairs.sort()
from collections import Counter
diffcnt=Counter()
L.append("\n=== TWINS contrastivos (fundos próximos, tier oposto) — top 12 + eixo diferenciador ===")
for d,i,j in pairs[:12]:
    diffs=sorted(range(len(F)),key=lambda k:-abs(X[i,k]-X[j,k]))[:2]
    for k in diffs: diffcnt[F[k]]+=1
    si= "MON/FORTE" if tier[i] in("MONSTRO","FORTE") else "FRACO"
    L.append(f" d={d:.2f} | {ROWS[i]['t']}({tier[i]}) vs {ROWS[j]['t']}({tier[j]}) | difere: "+
             ", ".join(f"{F[k]}({X[i,k]-X[j,k]:+.1f})" for k in diffs))
L.append("\n  features que mais diferenciam twins (freq no top-40 pares):")
for f,c in Counter([F[k] for d,i,j in pairs[:40] for k in sorted(range(len(F)),key=lambda k:-abs(X[i,k]-X[j,k]))[:2]]).most_common(8):
    L.append(f"    {f}: {c}")
rep="\n".join(L); print(rep)
(HERE/"bottom_cluster_report.txt").write_text(rep)
print("\n-> bottom_cluster_report.txt")
