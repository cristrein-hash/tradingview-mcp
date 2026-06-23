#!/usr/bin/env python3
"""EPISODE READING AUDIT (Tarefa 4) — compara as LEITURAS VIVAS (já feitas pelos readers) vs outcome uncapped,
SÓ como DIAGNÓSTICO pós-leitura (canon princípio 8). A leitura NÃO foi um score; isto apenas mede como ela se saiu.
Outcome nunca foi input da leitura (input stripado). Sem promoção, sem regra, sem threshold como decisão."""
import json, csv
D="results"
rd={int(json.loads(l)['episode_id']):json.loads(l) for l in open(f"{D}/l2_bpt_episode_readings_276.jsonl")}
pkt={int(json.loads(l)['episode_id']):json.loads(l)['_AUDIT_outcome_NOT_FOR_READING'] for l in open(f"{D}/l2_bpt_episode_context_packets_276.jsonl")}
EP=sorted(rd)
def mfe(b): return pkt[b]['mfe_R']
def engpol(b): return pkt[b]['engine_policy']
nR=sum(1 for b in EP if mfe(b)>=5); nL=sum(1 for b in EP if mfe(b)<2); nM=sum(1 for b in EP if mfe(b)>=10)
baseR=nR/len(EP); baseL=nL/len(EP)
# normalizar variantes menores de episode_type
NORM={'BULL_PULLBACK_CONTINUATION':'BULL_PULLBACK','BULL_PULLBACK_TRAP':'BEAR_PULLBACK_TRAP'}
def etype(b): return NORM.get(rd[b]['episode_type'],rd[b]['episode_type'])
def dec(b): return rd[b]['provisional_decision']

from collections import Counter
print("="*88);print(f"EPISODE READING AUDIT (diagnóstico pós-leitura) | base runner={100*baseR:.0f}% loser={100*baseL:.0f}% | R{nR} L{nL} mon{nM}")
# (1) por episode_type: o tipo VIVO separa convexidade?
print(f"\n-- por EPISODE_TYPE (a leitura viva separa?) --")
print(f"{'episode_type':26}{'n':>4}{'run%':>6}{'rLift':>6}{'los%':>6}{'mon':>4}")
rows=[]
for t in sorted(set(etype(b) for b in EP)):
    bs=[b for b in EP if etype(b)==t]; n=len(bs); r=sum(1 for b in bs if mfe(b)>=5); l=sum(1 for b in bs if mfe(b)<2); m=sum(1 for b in bs if mfe(b)>=10)
    rows.append(dict(group='type:'+t,n=n,runner_pct=round(100*r/n,1),runner_lift=round((r/n)/baseR,2),loser_pct=round(100*l/n,1),monumentals=m))
    print(f"{t:26}{n:>4}{100*r/n:>6.0f}{(r/n)/baseR:>6.2f}{100*l/n:>6.0f}{m:>4}")
# (2) por DECISÃO da leitura
print(f"\n-- por DECISÃO da leitura --")
for dv in ('TAKE','REVIEW','SKIP','TRANSFORM'):
    bs=[b for b in EP if dec(b)==dv]; n=len(bs)
    if not n: continue
    r=sum(1 for b in bs if mfe(b)>=5); l=sum(1 for b in bs if mfe(b)<2); m=sum(1 for b in bs if mfe(b)>=10)
    rows.append(dict(group='decision:'+dv,n=n,runner_pct=round(100*r/n,1),runner_lift=round((r/n)/baseR,2),loser_pct=round(100*l/n,1),monumentals=m))
    print(f"  {dv:10} n={n:>3} runner%={100*r/n:>4.0f} (lift {(r/n)/baseR:.2f}) loser%={100*l/n:>4.0f} monum={m}")
# (3) par central
LBB=[b for b in EP if etype(b)=='LEGITIMATE_BEAR_BUY']; BPT=[b for b in EP if etype(b)=='BEAR_PULLBACK_TRAP']
def rr(bs): return 100*sum(1 for b in bs if mfe(b)>=5)/len(bs) if bs else 0
def lr(bs): return 100*sum(1 for b in bs if mfe(b)<2)/len(bs) if bs else 0
print(f"\n-- PAR CENTRAL (a distinção que importa) --")
print(f"  LEGITIMATE_BEAR_BUY n={len(LBB)} runner%={rr(LBB):.0f} loser%={lr(LBB):.0f} mon={sum(1 for b in LBB if mfe(b)>=10)}")
print(f"  BEAR_PULLBACK_TRAP  n={len(BPT)} runner%={rr(BPT):.0f} loser%={lr(BPT):.0f} mon={sum(1 for b in BPT if mfe(b)>=10)}")
# (4) mislabel vs engine
TAKE_DEC={'TAKE'}; SKIP_DEC={'SKIP'}
sw=[b for b in EP if mfe(b)>=5 and engpol(b) in('SKIP','REVIEW','REVIEW_RISK') and dec(b)=='TAKE']
lc=[b for b in EP if mfe(b)<2 and engpol(b)=='TAKE' and dec(b)=='SKIP']
mon_take=[b for b in EP if mfe(b)>=10 and dec(b) in('TAKE','REVIEW')]; mon_skip=[b for b in EP if mfe(b)>=10 and dec(b)=='SKIP']
print(f"\n-- MISLABEL vs ENGINE (leitura corrige?) --")
print(f"  skip-winners RECUPERADOS (runner em SKIP-engine, leitura=TAKE): {len(sw)}/{sum(1 for b in EP if mfe(b)>=5 and engpol(b) in('SKIP','REVIEW','REVIEW_RISK'))}")
print(f"  loser-takes CORTADOS (loser em TAKE-engine, leitura=SKIP): {len(lc)}/{sum(1 for b in EP if mfe(b)<2 and engpol(b)=='TAKE')}")
print(f"  MONUMENTAIS preservados (leitura TAKE/REVIEW): {len(mon_take)}/{nM} | perdidos (leitura SKIP): {len(mon_skip)}/{nM}")
if mon_skip: print(f"    monumentais SKIPADOS (erro da leitura, PRECISAM PLOTAGEM):",[(b,rd[b]['episode_type'],round(mfe(b),1)) for b in mon_skip])
# (5) erros da própria leitura (conflitos p/ plotagem)
read_take_loser=[b for b in EP if dec(b)=='TAKE' and mfe(b)<2]   # leitura TAKE mas loser
read_skip_runner=[b for b in EP if dec(b)=='SKIP' and mfe(b)>=5] # leitura SKIP mas runner
print(f"\n-- ERROS DA LEITURA (conflitos p/ PLOTAGEM, não pós-racionalização) --")
print(f"  leitura TAKE mas LOSER: {len(read_take_loser)} (falsos positivos)")
print(f"  leitura SKIP mas RUNNER: {len(read_skip_runner)} (winners ainda perdidos pela leitura)")
print(f"    SKIP-mas-runner (plotar):",[(b,rd[b]['episode_type'],round(mfe(b),1)) for b in read_skip_runner][:12])
# onde a leitura BATE o engine
read_better=[b for b in EP if (mfe(b)>=5 and engpol(b) in('SKIP','REVIEW','REVIEW_RISK') and dec(b)=='TAKE') or (mfe(b)<2 and engpol(b)=='TAKE' and dec(b)=='SKIP')]
print(f"\n  leitura SUPERA engine em {len(read_better)} episódios (recupera runner OU corta loser que o engine errou)")
# casos p/ plotagem = monumentais skipados + skip-mas-runner + take-mas-loser de alta convicção
plot=sorted(set([b for b in mon_skip]+read_skip_runner+[b for b in read_take_loser if rd[b]['qualitative_confidence'].startswith('high')]))
with open(f"{D}/l2_bpt_episode_reading_audit_276.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['group','n','runner_pct','runner_lift','loser_pct','monumentals'],extrasaction='ignore',lineterminator="\n");w.writeheader();w.writerows(rows)
with open(f"{D}/l2_bpt_episode_reading_plot_list.csv","w",newline="") as f:
    w=csv.writer(f,lineterminator="\n");w.writerow(['bar_idx','datetime','episode_type','decision','mfe_R','reason_to_plot'])
    for b in plot:
        reason='monumental_skipped' if b in mon_skip else 'skip_but_runner' if b in read_skip_runner else 'high_conf_take_but_loser'
        w.writerow([b,rd[b].get('timestamp'),rd[b]['episode_type'],dec(b),mfe(b),reason])
print(f"\n  casos p/ PLOTAGEM: {len(plot)} (lista em l2_bpt_episode_reading_plot_list.csv)")
# DA csv — leitura por episódio para o Devil's Advocate escanear (decisão vs outcome, flag de conflito)
with open(f"{D}/l2_bpt_episode_reading_da.csv","w",newline="") as f:
    w=csv.writer(f,lineterminator="\n")
    w.writerow(['episode_id','datetime','episode_type','decision','confidence','mfe_R','engine_policy','conflict'])
    for b in EP:
        conf='take_loser' if (dec(b)=='TAKE' and mfe(b)<2) else 'skip_runner' if (dec(b)=='SKIP' and mfe(b)>=5) else ''
        w.writerow([b,rd[b].get('timestamp'),etype(b),dec(b),rd[b].get('qualitative_confidence'),round(mfe(b),1),engpol(b),conf])
print(f"  DA csv: l2_bpt_episode_reading_da.csv ({len(EP)} episódios)")
print("\nDIAGNÓSTICO apenas. Leitura NÃO virou score. Outcome nunca foi input. DONE.")
