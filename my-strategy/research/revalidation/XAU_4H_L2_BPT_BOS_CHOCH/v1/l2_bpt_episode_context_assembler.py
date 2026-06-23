#!/usr/bin/env python3
"""EPISODE CONTEXT ASSEMBLER (Tarefa 2) — monta pacote de LEITURA VIVO por episódio (276), legível por LLM/agent.
CÓDIGO QUE MONTA CONTEXTO, NÃO JULGA (canon princípio 2). Outcome SÓ como campo _AUDIT separado, NUNCA input da leitura.
Contém: sequência 4H real (a FORMA) + path DSPA + 1D/weekly + regime_B + Macro Engine states + DSPA states + SVP +
supply/demand/sup_cat/pol_cat + NAS/bubbles/SMC/RSI. Causal."""
import json, csv, bisect, datetime as dt
D="results"; RR="repro_recovery"
F=[json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
O=[r['open'] for r in F];H=[r['high'] for r in F];L=[r['low'] for r in F];Cl=[r['close'] for r in F];TS=[r['ts_epoch'] for r in F]
ATR=[None]*len(F);trs=[]
for i in range(1,len(F)):
    trs.append(max(H[i]-L[i],abs(H[i]-Cl[i-1]),abs(L[i]-Cl[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
path={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_path_features_276.csv"))}
states={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_intermediate_states_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
ind={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_indicator_engine_cross_v2.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
dsq={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
RB=[json.loads(l) for l in open("../../../../strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl") if json.loads(l).get('ts')]
RB.sort(key=lambda r:r['ts']);RBdate=[r['ts'][:10] for r in RB]
WK=[json.loads(l) for l in open("../../../../strategies/candidates/regime_classifier_v3/xau_weekly_with_features.jsonl") if json.loads(l).get('ts')]
WK.sort(key=lambda r:r['ts']);WKts=[r['ts'] for r in WK]
def fn(v):
    try:return float(v)
    except:return None
def d10(t): return dt.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d %H:%M')
EP=sorted(path)
def regime_b_asof(ed):
    k=bisect.bisect_left(RBdate,ed)-1
    if k<0: return {}
    r=RB[k]; return {k2:r.get(k2) for k2 in ('combined_score','cascade_score','macro_broken','distribution_flag','d_break_bull','d_break_bear','w_break_bull','w_break_bear','drawdown_pct_13w','v3_state','stage_dir','stage_n','ma200_bull','ma200_bear')}
def weekly_asof(ed):
    k=bisect.bisect_left(WKts,ed)-1
    if k<0: return {}
    r=WK[k]; return {'weekly_slope_20pct':r.get('slope_20_pct'),'weekly_state':r.get('state',r.get('v3_state'))}

out=open(f"{D}/l2_bpt_episode_context_packets_276.jsonl","w")
n=0
for b in EP:
    ed=path[b]['datetime']; e=eng[b];p=path[b];x=ind.get(b,{});d=dec.get(b,{});q=dsq.get(b,{});P=pk.get(b,{})
    # sequência 4H real (14 barras até a entrada) — a FORMA
    seq=[]
    for j in range(max(0,b-13),b+1):
        seq.append(dict(t=d10(TS[j]),o=round(O[j],1),h=round(H[j],1),l=round(L[j],1),c=round(Cl[j],1),
            rng=round(H[j]-L[j],1),body=round(Cl[j]-O[j],1),entry=(j==b)))
    pkt=dict(episode_id=b,bar_idx=b,timestamp=ed,
        price_sequence_4h=seq,
        weekly_1d_context=dict(**weekly_asof(ed), weekly_slope_decisions=d.get('weekly_slope'),
            dealing_range_4h=p.get('f5_range_pos_4h'),dealing_range_1d=p.get('f5_range_pos_1d')),
        regime_B=regime_b_asof(ed),
        macro_engine_states=dict(supply=e.get('supply'),demand=e.get('demand'),volume=e.get('volume'),mtf=e.get('mtf'),
            regime=e.get('regime'),momentum=e.get('momentum'),capit=e.get('capit'),fuel=e.get('fuel'),risk=e.get('risk'),macro_state=e.get('macro_state')),
        dspa_path=dict(sweep=p.get('f1_swept_low_reclaim'),sweep_depth=p.get('f1_sweep_depth_atr'),swept_high=p.get('f1_swept_high_reject'),
            flush=p.get('f2_flush_state'),flush_velocity=p.get('f2_velocity_atr_bar'),drop_atr=p.get('f2_drop_atr'),
            acceptance=p.get('f3_acceptance_state'),closes_above_res=p.get('f3_closes_above_res'),rejections=p.get('f3_rejections_at_res'),
            structure=p.get('f4_structure_state'),BOS=p.get('f4_BOS'),CHoCH=p.get('f4_CHoCH'),
            svp_path=p.get('f6_svp_state'),above_value=p.get('f6_above_value'),below_value=p.get('f6_below_value'),dist_poc=p.get('f6_dist_poc_atr'),
            regime_trajectory=p.get('f7_regime_traj'),combined_slope=p.get('f7_combined_slope'),cascade_now=p.get('f7_cascade_now')),
        dspa_intermediate=dict(primary=states[b]['dspa_primary_state'],secondary=states[b]['dspa_secondary_state']),
        supply_demand=dict(macro_reader_leg=d.get('macro_reader_leg'),sup_cat=d.get('sup_cat'),pol_cat=q.get('polarity_category'),
            demand_cat=q.get('demand_category'),demand=d.get('demand'),clean_sky=d.get('clean_sky_flag'),bottom_turn=d.get('bottom_turn'),
            dist_supply_atr=P.get('dist_4h_supply_low_atr'),dist_demand_atr=P.get('dist_4h_demand_low_atr')),
        indicators=dict(nas_long=P.get('nas_long_new_8b'),nas_short=P.get('nas_short_new_8b'),
            bub_buy=f"s{P.get('bub_buy_s')}/m{P.get('bub_buy_m')}/L{P.get('bub_buy_L')}",bub_sell=f"s{P.get('bub_sell_s')}/m{P.get('bub_sell_m')}/L{P.get('bub_sell_L')}",
            smc_bos=str(P.get('smc_bos'))[:40],smc_choch=str(P.get('smc_choch'))[:40],rsi=P.get('rsi'),rsi_1d=P.get('rsi_1d'),rsi_min8=P.get('rsi_min8'),
            bubbles_ctx=x.get('bubbles'),smc_ctx=x.get('smc')),
        _AUDIT_outcome_NOT_FOR_READING=dict(mfe_R=fn(unc[b]['mfe_R']),capped_exitype=unc[b].get('capped_exitype'),
            engine_policy=e.get('policy'),is_runner=int(fn(unc[b]['mfe_R'])>=5),is_loser=int(fn(unc[b]['mfe_R'])<2),is_monumental=int(fn(unc[b]['mfe_R'])>=10)))
    out.write(json.dumps(pkt)+"\n"); n+=1
out.close()
print(f"Context Assembler: {n}/276 pacotes vivos escritos em l2_bpt_episode_context_packets_276.jsonl")
print("Cada pacote = sequência 4H real + path DSPA + 1D/weekly + regime_B + engine states + SVP + supply/demand + indicadores.")
print("Outcome SÓ em _AUDIT_outcome_NOT_FOR_READING (separado, nunca input da leitura). Código montou, NÃO julgou.")
