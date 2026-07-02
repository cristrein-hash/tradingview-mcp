#!/usr/bin/env python3
"""DA (2026-07-01) — Devil's Advocate sobre GATE-BEAR (phase32). Orfão: só análise/reprodução, não toca produção.
Ordem de prioridade (ponto 1 = make-or-break):
 1. CAUSALIDADE de reg[bar_idx]: reg[i] retornado por run() no book completo == reg[i] recomputado
    truncando os bars > entry (nenhuma barra futura visível)? Se divergir em ALGUM bar de entrada => LOOK-AHEAD.
 2. f7_cascade_now causal (D-1 shift no daily) — só confirmar shift, guarda vale +4.2R.
 3. Concentração do ganho +15R (bear trades) e +4.2R (keep-capit sobre 1 trade 2023-10-06).
 4. Robustez por ano.
 5. threshold casc<=-3 fitado? sensibilidade -2/-3/-4.
 6. seleção/streak honesty."""
import json,csv,io,contextlib,sys,datetime as dt
from pathlib import Path
from collections import defaultdict,Counter
COST=0.35
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
T=P.T
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
path={int(r["bar_idx"]):r for r in csv.DictReader(open(D/"l2_bpt_dspa_path_features_276.csv"))}
def num(v):
    try: return float(v)
    except: return None

# ---- carregar book (mesma lógica do phase32) ----
reg_full=P.run(0.03,1.15,0.88)
rows=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    casc=num((path.get(bi) or {}).get("f7_cascade_now"))
    rows.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),
                 "ym":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m"),
                 "yr":y,"reg":reg_full[bi],
                 "R":round(float(r["letrun_struct"])-COST,2),"casc":casc})
rows.sort(key=lambda x:x["bi"])

# ============================================================
# PONTO 1 — TESTE DE CAUSALIDADE POR TRUNCAMENTO (make-or-break)
# Recompute run() sobre uma cópia do módulo com os arrays cortados em [0:bi+1].
# Se reg_trunc[bi] != reg_full[bi] para qualquer bar de entrada => run() usa futuro (look-ahead).
# ============================================================
print("="*72)
print("PONTO 1 — CAUSALIDADE reg[bar_idx] (truncated-recompute — make-or-break)")
print("="*72)
import importlib,types
def run_truncated(bi):
    """Recarrega phase10 num namespace fresco com bars cortados em bi+1 e roda run()."""
    import phase10_hybrid_regime as src
    # reconstruir o módulo com n=bi+1: mais barato = copiar as funções e reexecutar o pipeline com slices.
    # Fazemos manualmente o que o topo do módulo faz, mas com C/H/L/T truncados.
    C=src.C[:bi+1];H=src.H[:bi+1];L=src.L[:bi+1];Tt=src.T[:bi+1];n=len(C)
    B4=[{"t":Tt[k],"c":C[k],"h":H[k],"l":L[k],"o":src.B4[k]["o"]} for k in range(n)]
    rsi=src.rsi;cusum=src.cusum;bear_exp_fn=src.bear_exp;ema=src.ema;zigzag_src=src.zigzag
    # bear_exp usa C/H/L globais do módulo -> precisamos versão local. Reimplementa usando closures do src?
    # src.bear_exp lê src.C/src.H/src.L (globais). Para truncar, monkeypatch temporário desses globais.
    saveC,saveH,saveL,saveT,saveB4,saven=src.C,src.H,src.L,src.T,src.B4,src.n
    src.C,src.H,src.L,src.T,src.B4,src.n=C,H,L,Tt,B4,n
    try:
        EMAL=ema(C,300);R4=rsi(C);cd4=cusum(C,-1);cu4=cusum(C,1)
        be=bear_exp_fn(B4)
        expdiv4=[i for i in be if H[max(range(i-8,i-3),key=lambda k:H[k])]>H[max(range(i-22,i-9),key=lambda k:H[k])]
                 and R4[max(range(i-8,i-3),key=lambda k:H[k])]<R4[max(range(i-22,i-9),key=lambda k:H[k])]]
        STRONG_TOP=set(cd4);MILD_TOP=set(expdiv4)-set(cd4);BOT_EV=set(cu4)
        # patch os globais que run() usa
        src.EMAL,src.R4,src.cd4,src.cu4,src.expdiv4=EMAL,R4,cd4,cu4,expdiv4
        src.STRONG_TOP,src.MILD_TOP,src.BOT_EV=STRONG_TOP,MILD_TOP,BOT_EV
        reg=src.run(0.03,1.15,0.88)
        return reg[bi]
    finally:
        src.C,src.H,src.L,src.T,src.B4,src.n=saveC,saveH,saveL,saveT,saveB4,saven
        src.EMAL=ema(saveC,300);src.R4=rsi(saveC)
        src.cd4=cusum(saveC,-1);src.cu4=cusum(saveC,1)
        be2=bear_exp_fn(saveB4)
        src.expdiv4=[i for i in be2 if saveH[max(range(i-8,i-3),key=lambda k:saveH[k])]>saveH[max(range(i-22,i-9),key=lambda k:saveH[k])]
                     and src.R4[max(range(i-8,i-3),key=lambda k:saveH[k])]<src.R4[max(range(i-22,i-9),key=lambda k:saveH[k])]]
        src.STRONG_TOP=set(src.cd4);src.MILD_TOP=set(src.expdiv4)-set(src.cd4);src.BOT_EV=set(src.cu4)

mismatches=[];bear_mismatch=0
for x in rows:
    bi=x["bi"]
    rt=run_truncated(bi)
    if rt!=x["reg"]:
        mismatches.append((x["date"],x["reg"],rt))
        if x["reg"]=="BEAR" or rt=="BEAR": bear_mismatch+=1
print(f"  entradas testadas: {len(rows)}")
print(f"  MISMATCH reg_full[bi] vs reg_truncated[bi]: {len(mismatches)}  (bear-envolvidos: {bear_mismatch})")
if mismatches:
    print("  *** LOOK-AHEAD DETECTADO — o gate usa labels revisados retroativamente ***")
    for d,rf,rt in mismatches[:25]: print(f"     {d}: full={rf}  truncated={rt}")
else:
    print("  => reg[bar_idx] é CAUSAL no bar de entrada. Nenhum label muda ao esconder o futuro.")

# quantos bear no full vs quantos seriam bear com truncamento (viabilidade do gate se causal)
print(f"  distribuição reg_full (entradas): {dict(Counter(x['reg'] for x in rows))}")

# ============================================================
# PONTO 2 — f7_cascade shift (só confirmação; leak upstream não derruba gate-total)
# ============================================================
print("\n"+"="*72);print("PONTO 2 — f7_cascade_now (D-1 shift no daily)")
print("  gerador: l2_bpt_dspa_path_features.py f7_regime -> k=bisect_left(RBdate, ed)-1 (último daily < entry date).")
print("  => casc lido do daily estritamente ANTERIOR à data de entrada (D-1). Causal no nível diário.")
print("  ressalva: cascade_score da fonte regime_B pode peekar; guarda só adiciona +4.2R (não derruba gate-total).")

# ============================================================
# PANEL util
# ============================================================
CAPthr=lambda x,thr: x["casc"] is not None and x["casc"]<=thr
def stats(kept):
    rs=[x["R"] for x in kept];n=len(rs)
    if not n: return None
    w=sum(1 for v in rs if v>0);s=sum(rs);cum=peak=dd=0;streak=mx=0;runs=[]
    for v in rs:
        cum+=v;peak=max(peak,cum);dd=min(dd,cum-peak)
        if v<=0: streak+=1;mx=max(mx,streak)
        else:
            if streak: runs.append(streak)
            streak=0
    if streak: runs.append(streak)
    r5=sum(1 for q in runs if q>=5)
    mth=defaultdict(float)
    for x in kept: mth[x["ym"]]+=x["R"]
    posm=sum(1 for v in mth.values() if v>0);tot=len(mth);worst=min(mth.values())
    return dict(n=n,wr=100*w/n,s=s,dd=dd,mx=mx,r5=r5,posm=posm,tot=tot,worst=worst)
def show(label,kept):
    d=stats(kept)
    if not d: print(f"  {label:32} N=0");return
    print(f"  {label:32} N={d['n']:3} WR={d['wr']:3.0f}% sumR={d['s']:+6.1f} DD={d['dd']:6.1f} | MAXstreak={d['mx']:2} runs>=5:{d['r5']} | meses {d['posm']}/{d['tot']}({100*d['posm']/d['tot']:.0f}%+) pior{d['worst']:+5.1f}")

base=[x for x in rows]
gtot=[x for x in rows if x["reg"]!="BEAR"]
gkeep=[x for x in rows if x["reg"]!="BEAR" or CAPthr(x,-3)]
print("\n"+"="*72);print("PAINEL (reprodução phase32)")
show("BASELINE",base);show("GATE-BEAR TOTAL",gtot);show("GATE-BEAR KEEP-CAPIT(-3)",gkeep)

# ============================================================
# PONTO 3 — concentração do ganho
# ============================================================
print("\n"+"="*72);print("PONTO 3 — concentração")
bear=[x for x in rows if x["reg"]=="BEAR"]
bear_sorted=sorted(bear,key=lambda z:z["R"])
sb=sum(x["R"] for x in bear)
print(f"  bear trades N={len(bear)} sumR={sb:+.1f}. Removê-los = +{-sb:.1f}R ao gate-total.")
print("  piores bear (arrasto que o gate remove):")
for x in bear_sorted[:6]: print(f"     {x['date']} R{x['R']:+5.1f} casc={x['casc']}")
print("  melhores bear (o que o gate-total joga fora):")
for x in sorted(bear,key=lambda z:-z['R'])[:6]: print(f"     {x['date']} R{x['R']:+5.1f} casc={x['casc']}")
# keep-capit sem 2023-10-06
big="2023-10-06"
gkeep_no=[x for x in gkeep if x["date"]!=big]
gtot_s=stats(gtot);gkeep_s=stats(gkeep);gkeep_no_s=stats(gkeep_no)
print(f"\n  keep-capit sumR={gkeep_s['s']:+.1f} vs gate-total {gtot_s['s']:+.1f}  (delta +{gkeep_s['s']-gtot_s['s']:.1f})")
print(f"  keep-capit SEM {big}: sumR={gkeep_no_s['s']:+.1f}  => keep {'AINDA bate' if gkeep_no_s['s']>gtot_s['s'] else 'NÃO bate'} gate-total")
capit_trades=[x for x in rows if x["reg"]=="BEAR" and CAPthr(x,-3)]
print(f"  trades preservados pela guarda (bear & casc<=-3): {len(capit_trades)} -> sumR {sum(x['R'] for x in capit_trades):+.1f}")
for x in sorted(capit_trades,key=lambda z:z['bi']): print(f"     {x['date']} R{x['R']:+5.1f} casc={x['casc']} {'WIN' if x['R']>0 else 'loss'}")

# ============================================================
# PONTO 4 — robustez por ano
# ============================================================
print("\n"+"="*72);print("PONTO 4 — por ano (baseline vs gate-total vs keep-capit)")
for yr in sorted(set(x["yr"] for x in rows)):
    b=[x for x in base if x["yr"]==yr];g=[x for x in gtot if x["yr"]==yr];k=[x for x in gkeep if x["yr"]==yr]
    bear_y=[x for x in b if x["reg"]=="BEAR"]
    sbb=stats(b);sgg=stats(g);skk=stats(k)
    line=f"  {yr}: base N={sbb['n']:2} sumR={sbb['s']:+6.1f} streak{sbb['mx']:2}  ->  gtot N={sgg['n']:2} sumR={sgg['s']:+6.1f} streak{sgg['mx']:2}"
    line+=f"  bear:{len(bear_y)}({sum(x['R'] for x in bear_y):+.1f})"
    print(line)

# ============================================================
# PONTO 5 — sensibilidade threshold casc
# ============================================================
print("\n"+"="*72);print("PONTO 5 — sensibilidade do threshold casc (keep-capit)")
for thr in [-2,-3,-4]:
    gk=[x for x in rows if x["reg"]!="BEAR" or CAPthr(x,thr)]
    kept_bear=[x for x in rows if x["reg"]=="BEAR" and CAPthr(x,thr)]
    d=stats(gk)
    print(f"  casc<={thr}: keep-capit N={d['n']:3} sumR={d['s']:+6.1f} streak={d['mx']:2} | bear-preservados={len(kept_bear)} (sumR {sum(x['R'] for x in kept_bear):+.1f})")
# quais bear winners cada thr captura
print("  bear WINNERS e o casc de cada (qual thr os pega):")
for x in sorted([z for z in bear if z['R']>0],key=lambda z:-z['R']):
    print(f"     {x['date']} R{x['R']:+5.1f} casc={x['casc']}")

# ============================================================
# PONTO 6 — streak honesty (composição da pior run pós-gate)
# ============================================================
print("\n"+"="*72);print("PONTO 6 — composição da pior streak (baseline e pós-gate)")
def worst_run(seq):
    best=[];cur=[]
    for x in seq:
        if x["R"]<=0: cur.append(x)
        else:
            if len(cur)>len(best): best=cur[:]
            cur=[]
    if len(cur)>len(best): best=cur[:]
    return best
for label,seq in [("baseline",base),("gate-total",gtot),("keep-capit",gkeep)]:
    wr=worst_run(seq)
    comp=dict(Counter(z['reg'] for z in wr))
    print(f"  {label:12} pior run={len(wr)} losses {wr[0]['date']}->{wr[-1]['date']} | regimes {comp}")
