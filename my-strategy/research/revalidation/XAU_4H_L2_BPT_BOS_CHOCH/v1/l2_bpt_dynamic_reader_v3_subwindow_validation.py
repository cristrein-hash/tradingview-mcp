#!/usr/bin/env python3
"""L2/BPT — v3: VALIDAÇÃO SUB-JANELA dos sinais de voto DENTRO da 276 (decide real vs in-sample). DIAGNÓSTICO.
DA flagou que S2 (lift 1.30) é parcialmente in-sample (2 sinais escolhidos olhando a 276). Teste decisivo, SEM OOS:
deriva o SINAL (runner-context vs loser-context) de cada estado numa METADE temporal e TESTA na outra (out-of-slice
dentro da 276). Se os sinais reproduzem nas duas direções -> estrutural; se não -> artefato in-sample.
realR uncapped. Causal. Sem promoção. Multi-fatorial."""
import csv, json, random
D="results"; RR="repro_recovery"
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
xv2={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_indicator_engine_cross_v2.csv"))}
def fn(v):
    try:return float(v)
    except:return None
EP=sorted(unc); MFE={b:fn(unc[b]['mfe_R']) for b in EP}
def period(b): return 'P1' if pk[b]['datetime'][:10]<'2023-01-01' else 'P2'
P1=[b for b in EP if period(b)=='P1']; P2=[b for b in EP if period(b)=='P2']

# estados candidatos (dos 2 engines) cujo SINAL queremos validar out-of-slice
def states(b):
    e=eng[b]; x=xv2.get(b,{})
    return {'macro_state':e.get('macro_state'),'supply':e.get('supply'),'momentum':e.get('momentum'),
            'capit':e.get('capit'),'fuel':e.get('fuel'),'ind_conf':x.get('indicator_confluence'),
            'bubbles':x.get('bubbles'),'smc':x.get('smc'),'nas':x.get('nas')}

def base_rate(bs): return sum(1 for b in bs if MFE[b]>=5)/len(bs) if bs else 0
def derive_signs(train, minn=6, margin=0.05):
    """deriva sinal de cada (dim,valor): +1 se runner_rate>base+margin, -1 se <base-margin, senão 0."""
    br=base_rate(train); from collections import defaultdict
    g=defaultdict(list)
    for b in train:
        for dim,val in states(b).items():
            if val: g[(dim,val)].append(b)
    signs={}
    for (dim,val),bs in g.items():
        if len(bs)<minn: continue
        rr=base_rate(bs)
        signs[(dim,val)] = 1 if rr>br+margin else (-1 if rr<br-margin else 0)
    return signs
def apply_vote(b, signs):
    return sum(signs.get((dim,val),0) for dim,val in states(b).items() if val)
def evaluate(test, signs, thr=2):
    br=base_rate(test)
    TAKE=[b for b in test if apply_vote(b,signs)>=thr]
    n=len(TAKE); rr=base_rate(TAKE)
    # null
    rng=random.Random(9); k=n; ge=0; mv=[MFE[b] for b in test]
    if k:
        for _ in range(3000):
            idx=list(range(len(test)));rng.shuffle(idx);s=idx[:k]
            if sum(1 for j in s if mv[j]>=5)/k>=rr: ge+=1
    return dict(n_test=len(test),n_take=n,runner_rate=round(100*rr,1),base_rate=round(100*br,1),
        lift=round(rr/br,2) if br else 0,null_p=round(ge/3000 if k else 1,3))

print("="*80);print("v3 — VALIDAÇÃO SUB-JANELA dos sinais de voto (out-of-slice DENTRO da 276)")
print("Deriva sinais numa metade, testa na outra. thr=net>=2 (convergência).\n")
rows=[]
for train,test,nm in [(P1,P2,'derive_P1_test_P2'),(P2,P1,'derive_P2_test_P1')]:
    signs=derive_signs(train)
    r=evaluate(test,signs); r['split']=nm; rows.append(r)
    print(f"{nm}: train n={len(train)} -> test n={r['n_test']} | TAKE n={r['n_take']} runner_rate={r['runner_rate']}% (base {r['base_rate']}%) lift={r['lift']} null_p={r['null_p']}")
# checar se os 2 sinais suspeitos reproduzem direção nas duas metades
print("\n--- reprodução dos 2 sinais suspeitos (direção em cada metade) ---")
for dim,val in [('macro_state','BULL_PULLBACK_CONTINUATION'),('ind_conf','STRONG_BEAR_CONFIRM')]:
    for half,bs in [('P1',P1),('P2',P2)]:
        sub=[b for b in bs if states(b).get(dim)==val]
        if sub:
            rr=base_rate(sub); br=base_rate(bs)
            print(f"  {val:30} {half}: n={len(sub):>3} runner_rate={100*rr:.1f}% vs base {100*br:.1f}% lift={rr/br:.2f}")
with open(f"{D}/l2_bpt_dynamic_reader_v3_subwindow_validation.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=['split','n_test','n_take','runner_rate','base_rate','lift','null_p'],lineterminator="\n");w.writeheader();w.writerows(rows)
print("\nVEREDITO: se ambos splits dão lift>1 e null_p<0.05 E os 2 sinais reproduzem direção nas 2 metades = ESTRUTURAL.")
print("Se algum split lava (lift~1 / p>0.05) ou um sinal inverte entre metades = IN-SAMPLE (só estrutural-only 1.17 é real, < bear_leg 1.63).")
print("DONE v3 subwindow.")
