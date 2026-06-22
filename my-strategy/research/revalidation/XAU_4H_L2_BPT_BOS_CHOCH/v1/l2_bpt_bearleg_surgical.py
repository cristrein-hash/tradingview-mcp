#!/usr/bin/env python3
"""L2/BPT — INVESTIGAÇÃO CIRÚRGICA DO BEAR_LEG (Cris): por que lift 1.63 e como refinar SEM bloqueio cego,
PRESERVANDO big winners e MONUMENTAIS. DIAGNÓSTICO. Base 276. Universo = macro_reader_leg==MACRO_BEAR_LEG.
Perfila cut-runners (MFE>=5, PRESERVAR) vs cut-losers (MFE<2, BLOQUEAR) pelos estados dos 2 engines + sub-leitores,
acha a assinatura LEGITIMATE_BEAR_BUY vs BEAR_PULLBACK_TRAP, e mede regra refinada. Causal. realR uncapped. Multi-fatorial."""
import csv, json
D="results"; RR="repro_recovery"
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
frozen=[json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
C=[r['close'] for r in frozen]
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
xv2={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_indicator_engine_cross_v2.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
v1={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dynamic_reader_v1_reading.csv"))}
def fn(v):
    try:return float(v)
    except:return None
def tb(v): return v in (1,'1',True,'True')
EP=sorted(unc); MFE={b:fn(unc[b]['mfe_R']) for b in EP}
def decel(i,w=6):
    if i-2*w<0: return False
    return (C[i]-C[i-w])/w > (C[i-w]-C[i-2*w])/w

# universo bear_leg
BL=[b for b in EP if dec.get(b,{}).get('macro_reader_leg')=='MACRO_BEAR_LEG']
nR=sum(1 for b in EP if MFE[b]>=5); base=nR/len(EP)
bl_run=[b for b in BL if MFE[b]>=5]; bl_los=[b for b in BL if MFE[b]<2]; bl_mid=[b for b in BL if 2<=MFE[b]<5]
mon=[b for b in BL if MFE[b]>=10]
print("="*84);print("INVESTIGAÇÃO CIRÚRGICA BEAR_LEG (universo macro_reader_leg==MACRO_BEAR_LEG)")
print(f"Q1 — por que lift 1.63: universo n={len(BL)} | runners(MFE>=5)={len(bl_run)} ({100*len(bl_run)/len(BL):.0f}%) "
      f"losers(MFE<2)={len(bl_los)} ({100*len(bl_los)/len(BL):.0f}%) mid={len(bl_mid)} | MONUMENTAIS(MFE>=10)={len(mon)}")
print(f"  runner_rate no bear_leg {100*len(bl_run)/len(BL):.0f}% vs base {100*base:.0f}% -> bloquear o universo corta {100*len(bl_los)/len(bl_los) if bl_los else 0:.0f}% dos losers dele")
print(f"  lift = (losers_cut/loser_total)/(runners_cut/runner_total) = ({len(bl_los)}/168)/({len(bl_run)}/72) = {(len(bl_los)/168)/(len(bl_run)/72):.2f}")

# Q2/Q3 — listar cut-runners (preservar) e cut-losers (bloquear)
print(f"\nQ2 — RUNNERS cortados pelo bear_leg cego (PRESERVAR, incl monumentais):")
for b in sorted(bl_run,key=lambda x:-MFE[x]):
    e=eng[b];d=dec.get(b,{})
    print(f"  {unc[b]['datetime']} MFE={MFE[b]:>5} {'MONUMENTAL' if MFE[b]>=10 else 'runner':10} | capit={d.get('capit'):14} demand={d.get('demand'):14} sup={d.get('sup_cat'):22} mom={e.get('momentum'):20} bub={xv2.get(b,{}).get('bubbles'):24} decel={decel(b)}")
print(f"\nQ3 — LOSERS cortados pelo bear_leg cego (BLOQUEAR) — amostra (top 10 de {len(bl_los)}):")
for b in sorted(bl_los)[:10]:
    e=eng[b];d=dec.get(b,{})
    print(f"  {unc[b]['datetime']} MFE={MFE[b]:>5} | capit={d.get('capit'):14} demand={d.get('demand'):14} sup={d.get('sup_cat'):22} mom={e.get('momentum'):20} bub={xv2.get(b,{}).get('bubbles'):24} decel={decel(b)}")

# Q4/Q5 — assinatura discriminadora: estados dos engines + sub-leitores em runners vs losers do universo
print(f"\nQ4/Q5 — ASSINATURA (runner_rate de cada estado DENTRO do bear_leg; >> ou << separa):")
def feat(b):
    e=eng[b];d=dec.get(b,{});x=xv2.get(b,{})
    return {'capit_CLIMAX':d.get('capit')=='CLIMAX_RECLAIM','demand_def':d.get('demand') in('DEMAND_DEFENDED','DEMAND_SUPPORTING_RETEST','DEMAND_ORIGIN_OF_LEG'),
        'decel':decel(b),'reclaim>0.3':(fn(pk[b].get('reclaim_body_atr')) or 0)>0.3,'bull_div':(fn(pk[b].get('rsi_bull_div_20b')) or 0)>0,
        'rsi_min8<=35':(fn(pk[b].get('rsi_min8')) or 99)<=35,'drop20>=2':(fn(pk[b].get('drop20_atr')) or 0)>=2,
        'bub_sell_climax':x.get('bubbles')=='BUBBLE_SELL_CLIMAX_BULL','smc_choch_bull':x.get('smc')=='SMC_CHOCH_BULL_TRIGGER',
        'eng_capit_CLIMAX':e.get('capit')=='CLIMAX_RECLAIM','clean_sky':d.get('clean_sky_flag')=='True','bottom_turn':d.get('bottom_turn')=='True',
        's_bearbuy_LEGIT':v1[b].get('s_bearbuy')=='LEGITIMATE_BEAR_BUY'}
keys=list(feat(BL[0]).keys())
print(f"{'feature':20}{'run%(n='+str(len(bl_run))+')':>14}{'los%(n='+str(len(bl_los))+')':>14}{'lift':>7}")
sig=[]
for k in keys:
    rr=sum(1 for b in bl_run if feat(b)[k])/len(bl_run); lr=sum(1 for b in bl_los if feat(b)[k])/len(bl_los)
    lift=(rr/lr) if lr>0 else (99 if rr>0 else 0)
    sig.append((k,rr,lr,lift))
    mark=' <<RUNNER-SIG' if rr>=0.4 and rr>lr*1.5 else (' <<LOSER-SIG' if lr>=0.4 and lr>rr*1.5 else '')
    print(f"{k:20}{100*rr:>13.0f}{100*lr:>14.0f}{lift:>7.2f}{mark}")

# Q6 — regra refinada: bloquear bear_leg EXCETO se assinatura runner (legitimate bear buy) presente
runsig=[k for k,rr,lr,lf in sig if rr>=0.4 and rr>lr*1.5]
print(f"\nQ6 — REGRA REFINADA: bloquear bear_leg EXCETO se >=1 runner-sig {runsig}")
def legit(b):
    f=feat(b); return any(f[k] for k in runsig)
# preservados vs bloqueados
pres_run=[b for b in bl_run if legit(b)]; pres_los=[b for b in bl_los if legit(b)]
blk_run=[b for b in bl_run if not legit(b)]; blk_los=[b for b in bl_los if not legit(b)]
print(f"  RUNNERS preservados: {len(pres_run)}/{len(bl_run)} (cego cortava todos {len(bl_run)})")
print(f"  MONUMENTAIS preservados: {sum(1 for b in mon if legit(b))}/{len(mon)}")
print(f"  LOSERS ainda bloqueados: {len(blk_los)}/{len(bl_los)} | losers que vazam (não bloqueados): {len(pres_los)}")
print(f"  refined lift = (losers_blk/168)/(runners_blk/72) = ({len(blk_los)}/168)/({len(blk_run)}/72 if blk_run) = {((len(blk_los)/168)/(len(blk_run)/72)) if blk_run else 99:.2f}")
print(f"  RUNNERS cortados pela regra refinada (FALHA se monumental): {[(unc[b]['datetime'],MFE[b]) for b in blk_run]}")
rows=[]
for b in BL:
    rows.append(dict(bar_idx=b,datetime=unc[b]['datetime'],mfe_R=MFE[b],klass=('runner' if MFE[b]>=5 else 'loser' if MFE[b]<2 else 'mid'),
        monumental=int(MFE[b]>=10),legit_bear_buy=int(legit(b)),refined=('PRESERVE' if legit(b) else 'BLOCK'),
        capit=dec.get(b,{}).get('capit'),demand=dec.get(b,{}).get('demand'),sup_cat=dec.get(b,{}).get('sup_cat'),decel=decel(b)))
with open(f"{D}/l2_bpt_bearleg_surgical.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()),lineterminator="\n");w.writeheader();w.writerows(rows)
print("\nDONE bear_leg surgical.")
