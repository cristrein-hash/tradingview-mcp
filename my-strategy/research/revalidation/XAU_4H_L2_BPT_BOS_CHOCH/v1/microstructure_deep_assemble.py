#!/usr/bin/env python3
"""DEEP ENGINE — assembla MATRIZ MESTRA completa de features (todas as fontes causais) p/ os 62.
Objetivo: achar a assinatura ESTRUTURAL que separa o grupo-alvo do Cris {T2,T3,T4,T16,T17,T23,T24}
dos demais preservados — especialmente dos outros 4 B-preservados {T18,T20,T30,T40}.
Rótulo = classe VISUAL do Cris (cego ao outcome — mistura W e L). DIAGNÓSTICO 62; sem 276/OOS; sem chart/MCP.
Join seguro plot_id->datetime->84-stream (proveniência verificada). visual_matrix só p/ join (nunca outcome predicado)."""
import csv, json

D = "results"
packs = {json.loads(l)['plot_id']: json.loads(l) for l in open(f"{D}/l2_bpt_leg_state_d1_evidence_packs.jsonl")}
vm = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0.csv"))}
tq = {r['datetime']: r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_matrix.csv"))}
v3 = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_bear_leg_block_gate_v3_62.csv"))}

def fn(v):
    try: return float(v)
    except: return None

# safe join check
assert all(vm[p]['datetime'] in tq for p in packs), "join falhou"

# features do stream 84 a puxar (todas causais)
TQ_FEATS = ['trend_30_atr','trend_90_atr','slope20_atr','dist_sma20_atr','dist_sma50_atr','price_vs_sma50',
 'rsi_1d','rsi_1d_ma','rsi_1d_sub_ma','drop20_atr','rise20_atr','rsi','rsi_min8','rsi_max8','rsi_vs_ma',
 'rsi_drop_6b','consec_down','consec_up','range_exp','atr_level','atr_pctile_proxy','sweet_spot_falling_knife',
 'legpos30','legpos60','legpos90','rsi_bear_div_20b','rsi_bull_div_20b','nas_long_new_8b','nas_short_new_8b',
 'nas_dist_ema_atr','nas_rsi','nas_1d_long_recent','bub_buy_s','bub_buy_m','bub_buy_L','bub_sell_s','bub_sell_m',
 'bub_sell_L','bub_poc_recent','bub_buy_total','bub_sell_total','bub_buy_sell_ratio','bub_large_sell_10b',
 'bub_large_buy_10b','has_4h_demand','dist_4h_demand_low_atr','demand_width_atr','demand_age_bars',
 'demand_touched_on_retest','demand_origin_of_leg','has_d1_demand','dist_d1_demand_atr','has_4h_supply_overhead',
 'dist_4h_supply_low_atr','supply_blocks_2ATR','supply_blocks_3ATR','supply_rejected_before','supply_broken_before',
 'has_d1_supply','dist_d1_supply_atr','rel_volume','below_VAL','dist_POC_atr','dist_VAL_atr','va_width_atr',
 'smc_bos','smc_choch_bars_ago','reclaim_body_atr','reclaim_dist_from_demand_atr','reclaim_dist_from_supply_atr',
 'sl_atr','sl_source','sl_type','F_STRICT_top_late','hour_utc','dead_hour']

def assemble(p):
    pk = packs[p]; t = tq[vm[p]['datetime']]; d1 = pk['d1_evidence']
    row = dict(plot_id=p, set=v3[p]['set'], datetime=vm[p]['datetime'],
               blocked_v3=v3[p]['blocked_v3'], d1_leg=pk['d1_macro_leg'])
    # stream 84
    for k in TQ_FEATS: row[k] = t.get(k, '')
    # categoricais dos evidence packs (1a classe)
    row['sup_cat'] = pk.get('sup_cat'); row['pol_cat'] = pk.get('pol_cat'); row['demand_cat'] = pk.get('demand_cat')
    for k, v in pk.get('macro_v1_specialists', {}).items(): row['spec_' + k] = v
    # D1 backbone
    for k in ('n_SH','n_SL','regimeB_state','regimeB_combined','macro_broken','weekly_slope','weekly_rsi',
              'daily_HH','daily_HL'): row['d1_' + k] = d1.get(k)
    return row

rows = [assemble(p) for p in sorted(packs, key=lambda x: (x[0], int(x[1:])))]
cols = list(rows[0].keys())
with open(f"{D}/l2_bpt_deep_master_matrix_62.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n"); w.writeheader(); w.writerows(rows)
print(f"MATRIZ MESTRA: {len(rows)} trades x {len(cols)} colunas")
print("n features numéricas+categóricas:", len(cols) - 5)

# grupos
TARGET = ['T2','T3','T4','T16','T17','T23','T24']
OTHER_B = ['T18','T20','T30','T40']
PRES = [r['plot_id'] for r in rows if r['blocked_v3'] == 'NO']
REST = [p for p in PRES if p not in TARGET]
print(f"\ngrupos: target={len(TARGET)} other_B={len(OTHER_B)} rest_preserved={len(REST)} (de {len(PRES)} preservados)")
json.dump(dict(TARGET=TARGET, OTHER_B=OTHER_B, REST=REST, PRES=PRES),
          open(f"{D}/_deep_groups.json", "w"))
print("grupos salvos -> _deep_groups.json")
