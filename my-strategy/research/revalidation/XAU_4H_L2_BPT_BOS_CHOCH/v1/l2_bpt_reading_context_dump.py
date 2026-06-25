#!/usr/bin/env python3
"""Dump de CONTEXTO VIVO por episódio p/ LEITURA (não análise/lift). Puxa a sequência real do path 4H (lead-in),
SVP POC/VAH/VAL, estrutura, sweep/flush, estados dos engines, regime — tudo de uma vez, por episódio, p/ ler o todo.
Casos contrastantes: runners bear (incl 2 monumentais) vs traps/losers bear de superfície parecida. Outcome só rótulo."""
import json, csv, datetime as dt
D="results"; RR="repro_recovery"
F=[json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
O=[r['open'] for r in F];H=[r['high'] for r in F];L=[r['low'] for r in F];C=[r['close'] for r in F];TS=[r['ts_epoch'] for r in F]
path={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_path_features_276.csv"))}
eng={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_engine_confluence.csv"))}
dec={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}
unc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
def d10(t): return dt.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d %H:%M')
# bar_idx por data
bydate={}
for b in path: bydate[path[b]['datetime']]=b
RUN=['2023-03-08','2023-03-09','2021-08-13','2020-12-02']  # runners bear (2023-03 = monumentais)
LOS=['2021-01-28','2021-02-22','2022-06-23','2021-03-10']  # losers/traps bear
def dump(b,tag):
    p=path[b];e=eng[b];d=dec.get(b,{});o=unc[b]
    print(f"\n{'='*92}\n{tag}  {p['datetime']}  bar_idx={b}  | MFE={o['mfe_R']}R exit={o.get('capped_exitype','')} (rótulo, não input)")
    print("  PATH 4H lead-in (12 barras até a entrada — a FORMA real):")
    for j in range(b-11,b+1):
        bar='ENTRY>' if j==b else '      '
        rng=H[j]-L[j]; body=C[j]-O[j]
        print(f"   {bar} {d10(TS[j])} O{O[j]:.1f} H{H[j]:.1f} L{L[j]:.1f} C{C[j]:.1f}  rng{rng:.1f} body{body:+.1f}")
    print(f"  PATH FEATURES: sweep_low_reclaim={p['f1_swept_low_reclaim']} depth={p['f1_sweep_depth_atr']} | flush={p['f2_flush_state']} vel={p['f2_velocity_atr_bar']} drop={p['f2_drop_atr']} consec_dn={p['f2_consec_down']}")
    print(f"     acceptance={p['f3_acceptance_state']} (above_res={p['f3_closes_above_res']} rej={p['f3_rejections_at_res']}) | structure={p['f4_structure_state']} BOS={p['f4_BOS']} CHoCH={p['f4_CHoCH']}")
    print(f"     dealing_range 4H={p['f5_range_pos_4h']}({p['f5_range_pct_4h']}) 1D={p['f5_range_pos_1d']}({p['f5_range_pct_1d']}) | SVP={p['f6_svp_state']} above_val={p['f6_above_value']} below_val={p['f6_below_value']} dist_poc={p['f6_dist_poc_atr']}")
    print(f"     regime_traj={p['f7_regime_traj']} slope={p['f7_combined_slope']} cascade={p['f7_cascade_now']}")
    print(f"  ENGINE: supply={e.get('supply')} demand={e.get('demand')} capit={e.get('capit')} momentum={e.get('momentum')} fuel={e.get('fuel')} regime={e.get('regime')} risk={e.get('risk')} macro_state={e.get('macro_state')}")
    print(f"  PRIOR: leg={d.get('macro_reader_leg')} sup_cat={d.get('sup_cat')} demand={d.get('demand')} bottom_turn={d.get('bottom_turn')} clean_sky={d.get('clean_sky_flag')} weekly_slope={d.get('weekly_slope')}")
print("RUNNERS (bear context):")
for s in RUN:
    if s in bydate: dump(bydate[s],'RUNNER')
print("\n\nLOSERS/TRAPS (bear context, superfície parecida):")
for s in LOS:
    if s in bydate: dump(bydate[s],'LOSER')
