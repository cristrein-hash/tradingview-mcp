#!/usr/bin/env python3
"""EPISODE READING PERFORMANCE (diagnóstico pós-leitura) — WR/DD/streak do conjunto de decisões da leitura,
sob R REALIZADO (não MFE). Exit é EIXO PRÓPRIO (canon): reporto sob 3 políticas realizadas que o projeto já tem
(capped_realR, V_stair 120, let-run 120). realR capado = CALIBRAÇÃO não árbitro — aqui é só avaliação, nunca decide.
Outcome nunca foi input da leitura. Trades ordenados cronologicamente p/ DD e streak corretos."""
import json, csv
D="results"
rd={int(json.loads(l)['episode_id']):json.loads(l)['provisional_decision'] for l in open(f"{D}/l2_bpt_episode_readings_276.jsonl")}
O={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
def fn(v):
    try: return float(v)
    except: return None
POL={'capped_realR':'capped_realR','vstair_120':'realized_vstair_120','letrun_120':'realized_letrun_120'}
order=sorted(O, key=lambda b:O[b]['datetime'])  # cronológico

def metrics(bars, col):
    rs=[fn(O[b][col]) for b in bars if fn(O[b][col]) is not None]
    n=len(rs)
    if not n: return None
    wins=sum(1 for r in rs if r>0); sumR=sum(rs)
    # equity curve cronológica -> max drawdown em R
    eq=0; peak=0; dd=0
    for r in rs:
        eq+=r; peak=max(peak,eq); dd=min(dd,eq-peak)
    # streaks (loser e winner consecutivos)
    mls=cur=0
    for r in rs:
        if r<=0: cur+=1; mls=max(mls,cur)
        else: cur=0
    mws=cur=0
    for r in rs:
        if r>0: cur+=1; mws=max(mws,cur)
        else: cur=0
    return dict(n=n,WR=round(100*wins/n,1),sumR=round(sumR,1),avgR=round(sumR/n,2),
                maxDD_R=round(dd,1),loser_streak=mls,winner_streak=mws)

SETS={'TAKE':[b for b in order if rd[b]=='TAKE'],
      'TAKE+REVIEW':[b for b in order if rd[b] in('TAKE','REVIEW')],
      'REVIEW':[b for b in order if rd[b]=='REVIEW'],
      'SKIP':[b for b in order if rd[b]=='SKIP'],
      'ALL_276':[b for b in order]}
print("="*100)
print("EPISODE READING PERFORMANCE | R REALIZADO | exit=eixo próprio | diagnóstico, não árbitro")
rows=[]
for col_label,col in POL.items():
    print(f"\n#### EXIT POLICY = {col_label} ####")
    print(f"{'set':14}{'n':>4}{'WR%':>7}{'sumR':>8}{'avgR':>7}{'maxDD_R':>9}{'Lstreak':>8}{'Wstreak':>8}")
    for s,bars in SETS.items():
        m=metrics(bars,col)
        if not m: continue
        print(f"{s:14}{m['n']:>4}{m['WR']:>7}{m['sumR']:>8}{m['avgR']:>7}{m['maxDD_R']:>9}{m['loser_streak']:>8}{m['winner_streak']:>8}")
        rows.append(dict(exit_policy=col_label,decision_set=s,**m))
with open(f"{D}/l2_bpt_episode_reading_performance.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['exit_policy','decision_set','n','WR','sumR','avgR','maxDD_R','loser_streak','winner_streak'],lineterminator="\n")
    w.writeheader(); w.writerows(rows)
print(f"\nCSV: {D}/l2_bpt_episode_reading_performance.csv")
print("NOTA: a leitura NÃO especifica exit; estes são 3 cenários de saída sobre o MESMO conjunto de TAKE.")
print("WR/sumR/DD/streak = avaliação do conjunto, NUNCA usado p/ redefinir a leitura. realR capado = calibração.")
