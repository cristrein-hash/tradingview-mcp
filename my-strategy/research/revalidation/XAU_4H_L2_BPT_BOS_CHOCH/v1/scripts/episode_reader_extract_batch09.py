#!/usr/bin/env python3
"""
Episode Reader extraction helper — batch_09 (0-indexed lines 160-179, 20 episodes).

Purpose: deterministic, reproducible compaction of the whole-episode context used by
the LIVING EPISODE READER for XAU 4H L2/BPT. NO scoring / NO voting / NO thresholds.
This script only renders each episode WHOLE so the reader can hold the price-sequence
shape conditioned by weekly/regime/macro context. The qualitative narrative readings
themselves are authored by the reader (model), not computed here.

Usage:
    cd /Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/
    python3 scripts/episode_reader_extract_batch09.py

Input : results/l2_bpt_episode_reading_input_276.jsonl
Range : 0-indexed lines 160..179 inclusive
Output: stdout compact whole-episode dump (context only; no outcome present in input)
"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT = os.path.join(HERE, "results", "l2_bpt_episode_reading_input_276.jsonl")
START, END = 160, 179  # inclusive, 0-indexed


def load_lines(path):
    with open(path) as f:
        return f.readlines()


def render(e):
    seq = e["price_sequence_4h"]
    closes = [b["c"] for b in seq]
    entry_bars = [b for b in seq if b.get("entry")]
    eb = entry_bars[-1] if entry_bars else seq[-1]
    lo = min(b["l"] for b in seq)
    hi = max(b["h"] for b in seq)
    w = e["weekly_1d_context"]
    r = e["regime_B"]
    m = e["macro_engine_states"]
    d = e["dspa_path"]
    di = e["dspa_intermediate"]
    sd = e["supply_demand"]
    ind = e["indicators"]
    out = []
    out.append(f"### id {e['episode_id']} | {e['timestamp']}")
    out.append(f" price: start_c {closes[0]} end_c {closes[-1]} lo {lo} hi {hi} "
               f"entry_c {eb['c']} entry_body {eb['body']}")
    out.append(f" last6_closes {[round(c,1) for c in closes[-6:]]}")
    out.append(f" last6_body {[round(b['body'],1) for b in seq[-6:]]}")
    wslope = round(w['weekly_slope_20pct'], 3) if w['weekly_slope_20pct'] is not None else None
    out.append(f" weekly: slope {wslope} state {w['weekly_state']} "
               f"dr1d {w['dealing_range_1d']} dr4h {w['dealing_range_4h']}")
    out.append(f" regimeB: v3 {r['v3_state']} stage {r['stage_dir']} {r['stage_n']} "
               f"cascade {r['cascade_score']} macro_broken {r['macro_broken']} "
               f"wbreak_bull {r['w_break_bull']} wbreak_bear {r['w_break_bear']} "
               f"dd13w {round(r['drawdown_pct_13w'],1)} distrib {r['distribution_flag']}")
    out.append(f" macro: {m['regime']} {m['macro_state']} mtf {m['mtf']} mom {m['momentum']} "
               f"supply {m['supply']} demand {m['demand']} capit {m['capit']} "
               f"vol {m['volume']} fuel {m['fuel']} risk {m['risk']}")
    out.append(f" dspa: struct {d['structure']} accept {d['acceptance']} svp {d['svp_path']} "
               f"flush {d['flush']} drop_atr {d['drop_atr']} sweep {d['sweep']} "
               f"BOS {d['BOS']} CHoCH {d['CHoCH']} traj {d['regime_trajectory']} dist_poc {d['dist_poc']}")
    out.append(f" dspa_inter: {di['primary']} / {di['secondary']}")
    out.append(f" SD: sup_cat {sd['sup_cat']} pol_cat {sd['pol_cat']} demand_cat {sd['demand_cat']} "
               f"macro_leg {sd['macro_reader_leg']} clean_sky {sd['clean_sky']} "
               f"bottom_turn {sd['bottom_turn']} dist_supply {sd['dist_supply_atr']} "
               f"dist_demand {sd['dist_demand_atr']}")
    bos = ind['smc_bos'][:40] if ind['smc_bos'] else None
    out.append(f" ind: bub_buy {ind['bub_buy']} bub_sell {ind['bub_sell']} bub_ctx {ind['bubbles_ctx']} "
               f"rsi {ind['rsi']} rsi1d {ind['rsi_1d']} rsi_min8 {ind['rsi_min8']} "
               f"nas_L {ind['nas_long']} nas_S {ind['nas_short']} smc_ctx {ind['smc_ctx']} "
               f"bos {bos} choch {ind['smc_choch']}")
    return "\n".join(out)


def main():
    lines = load_lines(INPUT)
    for i in range(START, END + 1):
        e = json.loads(lines[i])
        print(f"[IDX {i}]")
        print(render(e))
        print()


if __name__ == "__main__":
    main()
