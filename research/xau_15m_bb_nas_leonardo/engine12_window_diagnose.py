#!/usr/bin/env python3
"""ENGINE 12 (Cris 2026-06-28): diagnóstico da JANELA ago2025->01jan2026 (base fixa 3120+h4_up&h1d_up).
Testa 2 percepções do Cris: (A) RANGE pior que BULL (gatilho de continuação compra alto em range);
(B) interpolação excessiva = clusters de trades em chop, poucos ganham. Usa fixed_base_h4h1.csv (tem reg)."""
import csv,statistics as st,datetime as dt
from pathlib import Path
HERE=Path(__file__).parent
LO=dt.datetime(2025,8,1).timestamp(); HI=dt.datetime(2026,1,1).timestamp()
rows=[r for r in csv.DictReader(open(HERE/"fixed_base_h4h1.csv")) if LO<=int(r["cj_t"])<HI]
rows.sort(key=lambda r:int(r["cj_t"]))
for i,r in enumerate(rows,1): r["num"]=i; r["Rf"]=float(r["R"])
def panel(rs,tag):
    n=len(rs)
    if not n: print(f"{tag}: vazio"); return
    R=[x["Rf"] for x in rs]; sm=sum(R); w=sum(1 for x in R if x>0)
    eq=pk=dd=0
    for x in R: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    mL=mW=cl=cw=0
    for x in R:
        if x>0: cw+=1;cl=0
        else: cl+=1;cw=0
        mW=max(mW,cw);mL=max(mL,cl)
    top=sorted(R,reverse=True)
    rd=abs(sm/dd) if dd<0 else float('inf')
    print(f"{tag:<22} N{n:>4} | WR {100*w/n:>4.1f}% | sumR {sm:>6.1f} | avgR {sm/n:>6.3f} | DD {dd:>5.1f} | r/DD {rd:>5.2f} | streak -{mL}/+{mW} | top5 {100*sum(top[:5])/sm:.0f}%" if sm>0 else f"{tag:<22} N{n:>4} | WR {100*w/n:>4.1f}% | sumR {sm:>6.1f} | avgR {sm/n:>6.3f} | DD {dd:>5.1f} | streak -{mL}/+{mW}")
print("=== (A) REGIME SPLIT — janela ago2025->jan2026 ===")
panel(rows,"TODOS")
panel([r for r in rows if r["reg"]=="BULL"],"BULL")
panel([r for r in rows if r["reg"]=="RANGE"],"RANGE")
# (B) CLUSTERING / interpolação: gap em barras (15m=900s) ao trade anterior
print("\n=== (B) INTERPOLAÇÃO — clusters por proximidade temporal ===")
for G in (8,12,16):  # barras
    # agrupa em clusters: novo cluster quando gap > G barras
    clusters=[]; cur=[rows[0]]
    for a,b in zip(rows,rows[1:]):
        gap=(int(b["cj_t"])-int(a["cj_t"]))/900
        if gap<=G: cur.append(b)
        else: clusters.append(cur); cur=[b]
    clusters.append(cur)
    iso=[c for c in clusters if len(c)==1]; multi=[c for c in clusters if len(c)>=2]; big=[c for c in clusters if len(c)>=4]
    def wr(trs):
        R=[t["Rf"] for t in trs]; return (100*sum(1 for x in R if x>0)/len(R),sum(R)) if R else (0,0)
    iso_t=[t for c in iso for t in c]; multi_t=[t for c in multi for t in c]; big_t=[t for c in big for t in c]
    wI,sI=wr(iso_t); wM,sM=wr(multi_t); wB,sB=wr(big_t)
    print(f"G={G}b: clusters={len(clusters)} (isolados {len(iso)}, >=2 {len(multi)}, >=4 {len(big)})")
    print(f"   ISOLADOS  N{len(iso_t):>3} WR {wI:.1f}% sumR {sI:.1f} | EM-CLUSTER(>=2) N{len(multi_t):>3} WR {wM:.1f}% sumR {sM:.1f} | CLUSTER-GRANDE(>=4) N{len(big_t):>3} WR {wB:.1f}% sumR {sB:.1f}")
# dentro de clusters grandes (>=4, G=12): quantos ganham por cluster
print("\n=== (B2) dentro de clusters grandes (>=4 trades, G=12b): proporção que ganha ===")
G=12; clusters=[]; cur=[rows[0]]
for a,b in zip(rows,rows[1:]):
    gap=(int(b["cj_t"])-int(a["cj_t"]))/900
    if gap<=G: cur.append(b)
    else: clusters.append(cur); cur=[b]
clusters.append(cur)
big=[c for c in clusters if len(c)>=4]
wins_per=[sum(1 for t in c if t["Rf"]>0) for c in big]; sz=[len(c) for c in big]
print(f"clusters grandes={len(big)} | tamanho medio {st.mean(sz):.1f} | vencedores/cluster medio {st.mean(wins_per):.1f} ({100*st.mean(wins_per)/st.mean(sz):.0f}% do cluster)")
print(f"R medio por cluster grande: {st.mean([sum(t['Rf'] for t in c) for c in big]):.2f} | clusters grandes em RANGE: {sum(1 for c in big if sum(1 for t in c if t['reg']=='RANGE')>=len(c)/2)}/{len(big)}")
