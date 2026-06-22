#!/usr/bin/env python3
"""BEAR-LEG BLOCK GATE v3 — CORRECTIVE PULLBACK EXTENSION — DIAGNÓSTICO nos 62 (ensino).

Sobre o v2 (carve-out climax|oversold+reclaim+demanda) adiciona DUAS mudanças PRINCIPIADAS (não ID-fit):

  (1) CARVE-OUT SCOPE FIX (corrige misfire T17/T30): o carve-out bottom/turn só faz sentido FORA de
      MACRO_BULL_LEG. Dentro de uma bull-leg estabelecida não há "fundo a virar" nem bloqueio do qual
      resgatar — o carve-out lá é rótulo falso. Restringe PRESERVE_BOTTOM_TURN a leg!=MACRO_BULL_LEG.
      Efeito: T17/T30 perdem o rótulo falso e caem em ALLOW (NÃO bloqueados — micro-estrutura aberta,
      honesto). S15 (MACRO_RANGE) mantém o carve-out.

  (2) BLOCK_CORRECTIVE_PULLBACK: leg==MACRO_CORRECTIVE_PULLBACK AND NOT bottom_turn AND drop20_atr<CP_DROP_MIN.
      Mecanismo: comprar um corrective pullback só tem edge se for um FLUSH real (queda significativa testando
      demanda); comprar um dip RASO dentro da correção = perseguir força sem capitulação = padrão dos losers.
      drop20_atr (profundidade da queda em ATR nos últimos 20 bars) separa com margem larga:
        BLOCK  (raso): T12=0.12 T25=0.30 T26=0.29 S28=0.00 (+ T33=0.32 REVIEW)
        PRESERVE (flush): S3=1.69  S27=4.28  (+ S23=2.05 REVIEW)
      Qualquer threshold em (0.32, 1.69) dá as mesmas decisões nos 8 corrective -> NÃO é knife-edge fit.

Determinístico, causal (D1 shift D-1), sem outcome/realR/MFE/futuro como predicado, sem busca cega.
Engine/decisions/registry/produção/Telegram/SLIM intocados. NÃO plota. SÓ 62 (ensino), NÃO 276/OOS."""
import json, csv, sys
from collections import Counter

D = "results"
packs = {json.loads(l)['plot_id']: json.loads(l) for l in open(f"{D}/l2_bpt_leg_state_d1_evidence_packs.jsonl")}
v1 = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_macro_specialist_confluence_62.csv"))}
v2csv = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_bear_leg_block_gate_v2_62.csv"))}

CP_DROP_MIN = 1.0  # threshold declarado (mid-gap 0.32..1.69); robusto em [0.5,1.5]

def fn(v):
    try: return float(v)
    except: return None
def tb(v): return v in (True, 'true', 'True', '1', 1)

def feats(p):
    pk = packs[p]; d1 = pk['d1_evidence']; R = v1[p]; cap = pk.get('capit', {})
    return dict(
        leg=pk['d1_macro_leg'],
        mb=tb(d1.get('macro_broken')), cs=fn(d1.get('regimeB_combined')), wsl=fn(d1.get('weekly_slope')),
        climax=(R.get('capit') == 'CLIMAX_RECLAIM'),
        rmin=fn(cap.get('rsi_min8')), recl=fn(pk.get('entry_quality', {}).get('reclaim_body')),
        dem=R.get('demand'), drop=fn(cap.get('drop20_atr')),
    )

def bottom_turn(f):
    return f['climax'] or (f['rmin'] is not None and f['rmin'] <= 32 and
                           f['recl'] is not None and f['recl'] >= 0.4 and f['dem'] == 'DEMAND_DEFENDED')

def gate(p, version):
    """version='v2' (reconstrução para smoke test) ou 'v3' (com as 2 mudanças)."""
    f = feats(p); leg = f['leg']; rc = []
    bt = bottom_turn(f)
    # (1) carve-out: v2 = sempre; v3 = só FORA de bull-leg
    carve_ok = bt and (version == 'v2' or leg != 'MACRO_BULL_LEG')
    if bt and version == 'v3' and leg == 'MACRO_BULL_LEG':
        rc.append('carveout_suppressed_in_bull_leg')
    if carve_ok:
        rc.append('bottom_turn_climax' if f['climax'] else 'bottom_turn_oversold_reclaim_demand')
        return 'PRESERVE_BOTTOM_TURN', rc, f
    # BLOCK bear-markdown
    if leg == 'MACRO_BEAR_LEG' or (f['mb'] and f['cs'] is not None and f['cs'] < 0):
        rc.append(f"bear_markdown(leg={leg},mb={f['mb']},cs={f['cs']})")
        return 'BLOCK_BEAR_MARKDOWN', rc, f
    # BLOCK range-chop
    if leg in ('MACRO_RANGE', 'MACRO_TRANSITION') and not (f['cs'] is not None and f['cs'] > 0) and not (f['wsl'] is not None and f['wsl'] > 0):
        rc.append(f"range_chop(leg={leg},cs={f['cs']},wsl={f['wsl']})")
        return 'BLOCK_RANGE_CHOP', rc, f
    # (2) BLOCK corrective-pullback (NOVO no v3): corrective leg + dip raso + sem bottom-turn
    if version == 'v3' and leg == 'MACRO_CORRECTIVE_PULLBACK' and not bt and f['drop'] is not None and f['drop'] < CP_DROP_MIN:
        rc.append(f"corrective_shallow(drop20_atr={f['drop']}<{CP_DROP_MIN}, no_flush)")
        return 'BLOCK_CORRECTIVE_PULLBACK', rc, f
    if leg == 'MACRO_CORRECTIVE_PULLBACK':
        rc.append(f"corrective_with_flush(drop20_atr={f['drop']}) -> preserve")
    rc.append(f"allow(leg={leg})")
    return 'ALLOW', rc, f

# ---- SMOKE TEST: reconstrução v2 deve bater 62/62 com o CSV v2 committado ----
mism = []
for p in packs:
    dec, _, _ = gate(p, 'v2')
    if dec != v2csv[p]['gate']:
        mism.append((p, dec, v2csv[p]['gate']))
if mism:
    print("SMOKE FAIL — reconstrução v2 não bate o v2 CSV:", mism); sys.exit(1)
print(f"SMOKE PASS: reconstrução v2 == v2 CSV em {len(packs)}/62.")

def setof(p): return v2csv[p]['set']

# ---- v3 decisions ----
rows = []
for p in sorted(packs, key=lambda x: (setof(x), x[0], int(x[1:]))):
    d3, rc3, f = gate(p, 'v3')
    d2 = v2csv[p]['gate']
    rows.append(dict(
        plot_id=p, set=setof(p), datetime=packs[p]['datetime'], d1_leg=f['leg'],
        gate_v2=d2, gate_v3=d3,
        blocked_v2=('YES' if d2.startswith('BLOCK') else 'NO'),
        blocked_v3=('YES' if d3.startswith('BLOCK') else 'NO'),
        block_type=(d3 if d3.startswith('BLOCK') else ('PRESERVE_BOTTOM_TURN' if d3 == 'PRESERVE_BOTTOM_TURN' else 'ALLOW')),
        drop20_atr=f['drop'], rsi_min8=f['rmin'], reclaim_body=f['recl'], demand=f['dem'],
        climax=f['climax'], macro_broken=f['mb'], combined=f['cs'], weekly_slope=f['wsl'],
        reason_codes='|'.join(rc3), cris=v2csv[p]['cris'],
    ))
with open(f"{D}/l2_bpt_bear_leg_block_gate_v3_62.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(rows)
by = {r['plot_id']: r for r in rows}

print("\n=== v3 gate distribution ===", dict(Counter(r['gate_v3'] for r in rows)))
print("=== v3 blocked por set ===")
for s in 'ABC':
    sub = [r for r in rows if r['set'] == s]; blk = [r['plot_id'] for r in sub if r['blocked_v3'] == 'YES']
    print(f"  {s}: {len(blk)}/{len(sub)} -> {sorted(blk, key=lambda x:(x[0],int(x[1:])))}")
# deltas v2->v3
chg = [r for r in rows if r['gate_v2'] != r['gate_v3']]
print("\n=== mudanças v2 -> v3 ===")
for r in sorted(chg, key=lambda x:(x['set'],x['plot_id'][0],int(x['plot_id'][1:]))):
    print(f"  {r['plot_id']:5} set={r['set']:2} {r['gate_v2']:22} -> {r['gate_v3']:26} cris={r['cris']}")

# ---- TARGET CHECK ----
TARGETS = {'T12':'BLOCK','T25':'BLOCK','T26':'BLOCK','S28':'BLOCK',
           'S15':'PRESERVE','T17':'DIAG_MISFIRE',
           'S7':'BLOCK','S8':'BLOCK','S13':'BLOCK','T9':'BLOCK','T11':'BLOCK','T15':'BLOCK','T42':'BLOCK'}
trows = []
for p, want in TARGETS.items():
    r = by[p]
    if want == 'BLOCK': ok = (r['blocked_v3'] == 'YES')
    elif want == 'PRESERVE': ok = (r['blocked_v3'] == 'NO')
    else: ok = None  # diagnóstico
    trows.append(dict(plot_id=p, expected=want, gate_v3=r['gate_v3'], blocked_v3=r['blocked_v3'],
                      ok=('YES' if ok else ('NO' if ok is False else 'DIAG')),
                      drop20_atr=r['drop20_atr'], reason_codes=r['reason_codes'], cris=r['cris']))
with open(f"{D}/l2_bpt_bear_leg_block_gate_v3_target_check.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(trows[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(trows)
print("\n=== TARGET CHECK ===")
for r in trows:
    print(f"  {r['plot_id']:5} want={r['expected']:13} v3={r['gate_v3']:26} blk={r['blocked_v3']:3} ok={r['ok']:4} drop={r['drop20_atr']}")

# ---- ANCHOR CHECK ----
ANCHORS = ['T34','T35','T37','S20','S24','S25','S26','S27','S29','S30','S31','S32','T39','T41','S35','S36','S37','S38']
arows = []
for p in ANCHORS:
    if p not in by:
        arows.append(dict(plot_id=p, in_62='NO', gate_v2='-', gate_v3='-', blocked_v2='-', blocked_v3='-', newly_blocked_by_v3='-', cris='-')); continue
    r = by[p]
    newly = (r['blocked_v2'] == 'NO' and r['blocked_v3'] == 'YES')
    arows.append(dict(plot_id=p, in_62='YES', gate_v2=r['gate_v2'], gate_v3=r['gate_v3'],
                      blocked_v2=r['blocked_v2'], blocked_v3=r['blocked_v3'],
                      newly_blocked_by_v3=('YES' if newly else 'NO'), cris=r['cris']))
with open(f"{D}/l2_bpt_bear_leg_block_gate_v3_anchor_check.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(arows[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(arows)
newly_anchor = [r['plot_id'] for r in arows if r['newly_blocked_by_v3'] == 'YES']
preexist_blk = [r['plot_id'] for r in arows if r['in_62']=='YES' and r['blocked_v2']=='YES']
print("\n=== ANCHOR CHECK ===")
print(f"  anchors NOVO-bloqueados por v3 (deve ser []): {newly_anchor}")
print(f"  anchors já bloqueados no v2 (pré-existente, NÃO introduzido por v3): {preexist_blk}")
print(f"  anchors fora dos 62: {[r['plot_id'] for r in arows if r['in_62']=='NO']}")

# ---- robustez do threshold ----
print("\n=== robustez CP_DROP_MIN (decisões nos 8 corrective) ===")
cp8 = [p for p in packs if feats(p)['leg']=='MACRO_CORRECTIVE_PULLBACK']
for thr in (0.5,0.8,1.0,1.2,1.5):
    blk=[p for p in cp8 if (lambda f:(not bottom_turn(f) and f['drop'] is not None and f['drop']<thr))(feats(p))]
    print(f"  thr={thr}: block {sorted(blk,key=lambda x:(x[0],int(x[1:])))}")
print("\nA preservados (não bloqueados):", sum(1 for r in rows if r['set']=='A' and r['blocked_v3']=='NO'), "/26")
