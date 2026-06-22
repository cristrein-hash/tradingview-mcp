#!/usr/bin/env python3
"""MICRO-STRUCTURE LIQUIDITY ENGINE — feature builder (DIAGNÓSTICO nos 62 ensino).

Constrói pacotes de evidência de MICROESTRUTURA por trade, juntando o stream causal de 84 features
(l2_bpt_trade_qualification_matrix.csv, as-of-bar, proveniência verificada em commit 1937d82) ao set de 62
via JOIN SEGURO por datetime preciso (62/62 verificado; episode_id==bar_idx cross-check). visual_matrix usado
SÓ para o mapa plot_id->datetime/bar_idx — NUNCA outcome/realR/exit_type como predicado.

Tese: micro-top bad entry (T17/T20) vs micro-bottom/reclaim/breakout bom (S12; T21/T22 fora dos 62) talvez se
distingam por MICROESTRUTURA DE LIQUIDEZ: entrar PERTO da demanda/reclaim de micro-fundo (bom) vs PERTO da
supply/topo de micro-range/chase (ruim). Testado com features CAUSAIS já vetadas; sem inventar série bruta.

LIMITAÇÃO DECLARADA: não há série OHLC CONTÍGUA 2020-2026 local -> micro_range_position bruto, sweep intrabar
(high/low prior) e bars_since_swing NÃO são deriváveis aqui = FEATURE_UNAVAILABLE_NO_CONTIGUOUS_SERIES.
range-position bruto já falhou antes (memória). Usamos os proxies causais que a extração já computou da série.
NÃO produção. NÃO 276/OOS (só os 62). NÃO promover."""
import csv, json

D = "results"
packs = {json.loads(l)['plot_id']: json.loads(l) for l in open(f"{D}/l2_bpt_leg_state_d1_evidence_packs.jsonl")}
vm = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_visual_matrix_v0.csv"))}
tq_by_dt = {r['datetime']: r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_matrix.csv"))}
v3 = {r['plot_id']: r for r in csv.DictReader(open(f"{D}/l2_bpt_bear_leg_block_gate_v3_62.csv"))}

def fn(v):
    try: return round(float(v), 3)
    except: return None

# ---- SAFE JOIN verify ----
assert all(p in vm for p in packs), "plot_id sem episode_id"
assert all(vm[p]['datetime'] in tq_by_dt for p in packs), "datetime join falhou"
assert all(packs[p]['datetime'] == vm[p]['datetime'][:10] for p in packs), "datetime inconsistente pack vs vm"
print(f"SAFE JOIN OK: 62/62 plot_id -> datetime preciso -> 84-feature matrix.")

CONTRAST_OUT = {'T21', 'T22', 'S11', 'S40'}  # citados pelo Cris mas FORA dos 62

def micro_pack(p):
    t = tq_by_dt[vm[p]['datetime']]; pk = packs[p]
    # --- raw causal features (do stream 84) ---
    d_dem = fn(t['dist_4h_demand_low_atr']); d_sup = fn(t['dist_4h_supply_low_atr'])
    overhead = fn(t['has_4h_supply_overhead']); dem_touch = fn(t['demand_touched_on_retest'])
    dem_origin = fn(t['demand_origin_of_leg']); sup_rej = fn(t['supply_rejected_before']); sup_brk = fn(t['supply_broken_before'])
    legpos30 = fn(t['legpos30']); legpos90 = fn(t['legpos90'])
    below_VAL = t['below_VAL']; d_POC = fn(t['dist_POC_atr']); d_VAL = fn(t['dist_VAL_atr']); va_w = fn(t['va_width_atr'])
    recl = fn(t['reclaim_body_atr']); recl_dem = fn(t['reclaim_dist_from_demand_atr']); recl_sup = fn(t['reclaim_dist_from_supply_atr'])
    drop20 = fn(t['drop20_atr']); rise20 = fn(t['rise20_atr']); rsi = fn(t['rsi']); rsi_1d = fn(t['rsi_1d'])
    rmin8 = fn(t['rsi_min8']); rmax8 = fn(t['rsi_max8']); bear_div = fn(t['rsi_bear_div_20b'])
    smc_bos = t['smc_bos']; smc_choch_ago = t['smc_choch_bars_ago']
    bratio = fn(t['bub_buy_sell_ratio']); blarge_buy = fn(t['bub_large_buy_10b']); blarge_sell = fn(t['bub_large_sell_10b'])
    sup_cat = pk.get('sup_cat'); pol_cat = pk.get('pol_cat'); dem_cat = pk.get('demand_cat')

    # --- composites INTERPRETÁVEIS causais (não outcome) ---
    # net micro-location: >0 = mais perto da demanda que da supply (micro-fundo); <0 = mais perto da supply (micro-topo)
    net_loc = round(d_sup - d_dem, 3) if (d_sup is not None and d_dem is not None) else None
    # value-area state
    if below_VAL in (True, 'True', 'true', '1', 1): va_state = 'BELOW_VAL'
    elif d_VAL is not None and d_VAL <= 0.5: va_state = 'NEAR_VAL'
    elif d_POC is not None and d_POC <= 0.5: va_state = 'NEAR_POC'
    elif d_VAL is not None and va_w is not None and d_VAL >= va_w: va_state = 'ABOVE_VAH'
    else: va_state = 'INSIDE_VA'
    # micro-bottom reclaim signal (came down + reclaimed near demand)
    micro_bottom_reclaim = (drop20 is not None and drop20 >= 0.8 and recl is not None and recl >= 0.4
                            and recl_dem is not None and recl_dem <= 2.0)
    # micro-top chase signal (came up + near supply/overhead + not at demand)
    micro_top_chase = ((rise20 is not None and rise20 >= 1.5) and
                       ((overhead == 1) or (d_sup is not None and d_sup <= 3.0)) and
                       (d_dem is not None and d_dem >= 2.5))
    return dict(
        plot_id=p, set=v3[p]['set'], datetime=vm[p]['datetime'], bar_idx=vm[p]['episode_id'],
        d1_leg=pk['d1_macro_leg'], gate_v3=v3[p]['gate_v3'], blocked_v3=v3[p]['blocked_v3'],
        # micro-location
        dist_4h_demand_atr=d_dem, dist_4h_supply_atr=d_sup, net_micro_location=net_loc,
        has_overhead=overhead, demand_touched=dem_touch, demand_origin_leg=dem_origin,
        supply_rejected_before=sup_rej, supply_broken_before=sup_brk,
        legpos30=legpos30, legpos90=legpos90,
        # value area
        va_state=va_state, below_VAL=below_VAL, dist_POC_atr=d_POC, dist_VAL_atr=d_VAL, va_width_atr=va_w,
        # reclaim / sweep proxy (close-based; intrabar sweep UNAVAILABLE)
        reclaim_body_atr=recl, reclaim_dist_from_demand_atr=recl_dem, reclaim_dist_from_supply_atr=recl_sup,
        drop20_atr=drop20, rise20_atr=rise20,
        micro_bottom_reclaim=micro_bottom_reclaim, micro_top_chase=micro_top_chase,
        # structure
        smc_bos=smc_bos, smc_choch_bars_ago=smc_choch_ago,
        # momentum/exhaustion (conditional)
        rsi=rsi, rsi_1d=rsi_1d, rsi_min8=rmin8, rsi_max8=rmax8, bear_div=bear_div,
        # order flow
        bub_buy_sell_ratio=bratio, bub_large_buy_10b=blarge_buy, bub_large_sell_10b=blarge_sell,
        # categorical structure (1a classe)
        sup_cat=sup_cat, pol_cat=pol_cat, demand_cat=dem_cat,
        # UNAVAILABLE (declarado)
        micro_range_position='UNAVAILABLE_NO_CONTIGUOUS_SERIES',
        swept_prior_high='UNAVAILABLE_NO_CONTIGUOUS_SERIES',
        bars_since_swing='UNAVAILABLE_NO_CONTIGUOUS_SERIES',
    )

rows = [micro_pack(p) for p in sorted(packs, key=lambda x: (x[0], int(x[1:])))]
with open(f"{D}/l2_bpt_microstructure_feature_values_62.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(rows)
print(f"feature pack: {len(rows)} trades, {len(rows[0])} colunas")

# ---- diagnóstico rápido: micro-top targets vs micro-bottom contrast ----
by = {r['plot_id']: r for r in rows}
print("\n=== CONTRASTE micro-top (ruim) vs micro-bottom (bom) — features-chave ===")
hdr = f"{'pid':5}{'cls':12}{'d_dem':7}{'d_sup':7}{'netloc':8}{'ovh':4}{'dtch':5}{'lp30':6}{'va_state':11}{'recl':6}{'drop20':7}{'rise20':7}{'mbr':4}{'mtc':4}"
print(hdr)
groups = [('BAD micro-top', ['T17', 'T20', 'T24', 'T40']),
          ('GOOD contrast', ['S12', 'S15', 'S3', 'S27']),
          ('late-top resid', ['T32', 'T23'])]
for label, ids in groups:
    for p in ids:
        if p not in by: print(f"  {p:5} {label:12} FORA DOS 62"); continue
        r = by[p]
        print(f"  {p:5}{label:12}{str(r['dist_4h_demand_atr']):7}{str(r['dist_4h_supply_atr']):7}{str(r['net_micro_location']):8}"
              f"{str(r['has_overhead']):4}{str(r['demand_touched']):5}{str(r['legpos30']):6}{r['va_state']:11}"
              f"{str(r['reclaim_body_atr']):6}{str(r['drop20_atr']):7}{str(r['rise20_atr']):7}"
              f"{('Y' if r['micro_bottom_reclaim'] else '.'):4}{('Y' if r['micro_top_chase'] else '.'):4}")
print("\nCONTRAST_OUT_OF_WORKING_SET (citados pelo Cris, fora dos 62):", sorted(CONTRAST_OUT))
