#!/usr/bin/env python3
"""
Reentry Agent A — Target/Stop/Sizing variant grid over Caminho B 78 losers.

INPUTS (READ-ONLY):
- /tmp/caminho_b_78_losers_with_reentry.jsonl     78 losers w/ baseline reentry fields
- /Volumes/GUTS_ LACIE/TradingData/slim_features/XAUUSD/4H/*.jsonl

OUTPUT:
- /tmp/reentry_agent_A_summary.json  structured variant results
- stdout: top variants, asymmetric eval, honest commentary

Baseline being beaten:
  Demand-low + 4 ATR stop + fix_5R target → 18 wins × 5R + 41 losses × -1R = +49R nominal
  At 0.5x sizing (because new stop is 2x original): +24.5R adjusted.

The re-simulation walks forward from new_bar_idx with full OHLC. We replicate
the entry trigger logic for variants that change entry policy (demand_low / mid
/ high, confirmation, multi-level), then simulate exit per variant.
"""

import json
import glob
import math
import sys
from collections import Counter, defaultdict
from statistics import mean, median

LOSERS_PATH = '/tmp/caminho_b_78_losers_with_reentry.jsonl'
FEAT_GLOB = '/Volumes/GUTS_ LACIE/TradingData/slim_features/XAUUSD/4H/*.jsonl'
OUT_PATH = '/tmp/reentry_agent_A_summary.json'

# How far forward we let any variant run after re-entry. Set generous so fat-tail
# variants (fix_20R) get a fair chance, but capped to keep things bounded.
MAX_BARS_AFTER_ENTRY = 400  # ~67 trading days of 4H bars (baseline uses ~similar)


# ---------------------------------------------------------------------------- #
# Load
# ---------------------------------------------------------------------------- #

def load_losers():
    return [json.loads(l) for l in open(LOSERS_PATH)]


def load_bars():
    bars = []
    for f in sorted(glob.glob(FEAT_GLOB)):
        with open(f) as fp:
            for line in fp:
                bars.append(json.loads(line))
    return bars


# ---------------------------------------------------------------------------- #
# Entry triggers
# ---------------------------------------------------------------------------- #

def find_entry(bars, start_idx, loser, entry_policy, max_wait=400):
    """Return (entry_bar_idx, entry_price, wait_bars, demand_low, demand_high)
    or (None,...) on NO_TOUCH.

    entry_policy:
      'demand_low'        baseline-equivalent (touch demand low)
      'demand_mid'        wait for touch of (low + high) / 2
      'demand_high'       touch demand high (most conservative)
      'confirmation'      after demand low touch, wait next bullish close > open
      'multi_level'       same as demand_low but also accept second-nearest demand
                          (no direct way to know "second" — we just take first valid).
                          Implemented as demand_low for honesty; flagged in commentary.
    """
    for i in range(start_idx, min(start_idx + max_wait, len(bars))):
        b = bars[i]
        dlow = b.get('nearest_demand_low')
        dhigh = b.get('nearest_demand_high')
        demand_active = b.get('custom_ob_demand_active', False) or b.get('inside_demand', False)
        if dlow is None or dhigh is None:
            continue
        # pick target trigger price
        if entry_policy == 'demand_low':
            tprice = dlow
        elif entry_policy == 'demand_mid':
            tprice = (dlow + dhigh) / 2.0
        elif entry_policy == 'demand_high':
            tprice = dhigh
        elif entry_policy == 'confirmation':
            tprice = dlow
        elif entry_policy == 'multi_level':
            tprice = dlow
        else:
            tprice = dlow
        # Only enter if the bar actually traded down through tprice
        if b['low'] <= tprice <= b['high'] or b['low'] <= tprice:
            entry_price = min(tprice, b['open'])  # adverse fill if open below
            # Confirmation variant: enter on NEXT bar only if it closes bullish
            if entry_policy == 'confirmation':
                # find next bar bullish close > open
                for j in range(i + 1, min(i + 6, len(bars))):
                    nb = bars[j]
                    if nb['close'] > nb['open']:
                        return j, nb['open'], j - start_idx, dlow, dhigh
                continue
            return i, entry_price, i - start_idx, dlow, dhigh
    return None, None, None, None, None


# ---------------------------------------------------------------------------- #
# Simulate forward — capture per-bar high/low path
# ---------------------------------------------------------------------------- #

def walk(bars, entry_idx, entry_price, stop_price,
         max_bars=MAX_BARS_AFTER_ENTRY):
    """Yield (offset_bar, high, low, close) for entry_idx+1 .. up to max_bars."""
    end = min(entry_idx + max_bars + 1, len(bars))
    for j in range(entry_idx + 1, end):
        b = bars[j]
        yield j - entry_idx, b['high'], b['low'], b['close']


# ---------------------------------------------------------------------------- #
# Exit policies
# ---------------------------------------------------------------------------- #

def exit_fixR(bars, entry_idx, entry_price, stop_price, target_R):
    """Fixed target at target_R. Returns dict."""
    risk = entry_price - stop_price
    if risk <= 0:
        return dict(outcome='INVALID')
    target_price = entry_price + target_R * risk
    mfe = 0.0
    bars_in_trade = 0
    for off, h, l, c in walk(bars, entry_idx, entry_price, stop_price):
        bars_in_trade = off
        rr_high = (h - entry_price) / risk
        if rr_high > mfe:
            mfe = rr_high
        if l <= stop_price:
            return dict(outcome='LOSER', exit_R=-1.0, bars=off, mfe=mfe)
        if h >= target_price:
            return dict(outcome='WINNER', exit_R=target_R, bars=off, mfe=mfe)
    return dict(outcome='TIMEOUT', exit_R=0.0, bars=bars_in_trade, mfe=mfe)


def exit_BE_then_dyn(bars, entry_idx, entry_price, stop_price, be_at_R,
                     final_target_R=20.0):
    """When price hits be_at_R, move stop to entry. Then carry until final_target_R or BE stop hit."""
    risk = entry_price - stop_price
    if risk <= 0:
        return dict(outcome='INVALID')
    be_price = entry_price + be_at_R * risk
    target_price = entry_price + final_target_R * risk
    moved_to_be = False
    cur_stop = stop_price
    mfe = 0.0
    bars_in_trade = 0
    for off, h, l, c in walk(bars, entry_idx, entry_price, stop_price):
        bars_in_trade = off
        rr_high = (h - entry_price) / risk
        if rr_high > mfe:
            mfe = rr_high
        # Check stop first (conservative: assume worst-case intrabar order)
        if l <= cur_stop:
            r_exit = (cur_stop - entry_price) / risk
            return dict(outcome=('LOSER' if r_exit < 0 else 'BE'),
                        exit_R=r_exit, bars=off, mfe=mfe)
        if h >= target_price:
            return dict(outcome='WINNER', exit_R=final_target_R, bars=off, mfe=mfe)
        if not moved_to_be and h >= be_price:
            moved_to_be = True
            cur_stop = entry_price
    # Timeout exit at close of last bar
    last_close = bars[entry_idx + bars_in_trade]['close'] if bars_in_trade else bars[entry_idx]['close']
    r_close = (last_close - entry_price) / risk
    return dict(outcome='TIMEOUT', exit_R=r_close, bars=bars_in_trade, mfe=mfe)


def exit_trail_lock(bars, entry_idx, entry_price, stop_price,
                    arm_at_R, lock_pct=0.5, max_bars=MAX_BARS_AFTER_ENTRY):
    """When MFE hits arm_at_R, lock lock_pct of current MFE as the new stop.
    Continue trailing: stop = entry + lock_pct * mfe_so_far * risk."""
    risk = entry_price - stop_price
    if risk <= 0:
        return dict(outcome='INVALID')
    cur_stop = stop_price
    mfe = 0.0
    armed = False
    bars_in_trade = 0
    for off, h, l, c in walk(bars, entry_idx, entry_price, stop_price, max_bars):
        bars_in_trade = off
        rr_high = (h - entry_price) / risk
        if rr_high > mfe:
            mfe = rr_high
            if mfe >= arm_at_R:
                armed = True
            if armed:
                new_stop = entry_price + lock_pct * mfe * risk
                if new_stop > cur_stop:
                    cur_stop = new_stop
        if l <= cur_stop:
            r_exit = (cur_stop - entry_price) / risk
            return dict(outcome=('LOSER' if r_exit < 0 else
                                 'BE' if abs(r_exit) < 0.01 else 'TRAIL_WIN'),
                        exit_R=r_exit, bars=off, mfe=mfe)
    # Timeout
    last_close = bars[entry_idx + bars_in_trade]['close'] if bars_in_trade else bars[entry_idx]['close']
    r_close = (last_close - entry_price) / risk
    return dict(outcome='TIMEOUT', exit_R=r_close, bars=bars_in_trade, mfe=mfe)


def exit_asymmetric(bars, entry_idx, entry_price, stop_price,
                    first_target_R, runner_BE_at_R, runner_cap_R=20.0):
    """Take 50% at first_target_R; remaining 50% gets BE stop at runner_BE_at_R
    and runs to runner_cap_R or BE stop. Returns dict with exit_R averaged."""
    risk = entry_price - stop_price
    if risk <= 0:
        return dict(outcome='INVALID')
    t1_price = entry_price + first_target_R * risk
    be_arm_price = entry_price + runner_BE_at_R * risk
    runner_cap_price = entry_price + runner_cap_R * risk
    half_taken = False
    cur_stop = stop_price
    mfe = 0.0
    bars_in_trade = 0
    for off, h, l, c in walk(bars, entry_idx, entry_price, stop_price):
        bars_in_trade = off
        rr_high = (h - entry_price) / risk
        if rr_high > mfe:
            mfe = rr_high
        # Stop check
        if l <= cur_stop:
            r_stop = (cur_stop - entry_price) / risk
            if not half_taken:
                return dict(outcome='LOSER', exit_R=r_stop, bars=off, mfe=mfe)
            # half already taken at first_target_R, runner stops at cur_stop
            combined = 0.5 * first_target_R + 0.5 * r_stop
            return dict(outcome='PARTIAL', exit_R=combined, bars=off, mfe=mfe)
        # First target
        if not half_taken and h >= t1_price:
            half_taken = True
            # Stop stays at original until runner arms BE
        # Arm BE for runner
        if half_taken and h >= be_arm_price and cur_stop < entry_price:
            cur_stop = entry_price
        # Cap
        if h >= runner_cap_price:
            combined = 0.5 * first_target_R + 0.5 * runner_cap_R
            return dict(outcome='RUNNER_CAP', exit_R=combined, bars=off, mfe=mfe)
    # Timeout
    last_close = bars[entry_idx + bars_in_trade]['close'] if bars_in_trade else bars[entry_idx]['close']
    r_close = (last_close - entry_price) / risk
    if half_taken:
        combined = 0.5 * first_target_R + 0.5 * r_close
        return dict(outcome='TIMEOUT_PARTIAL', exit_R=combined, bars=bars_in_trade, mfe=mfe)
    return dict(outcome='TIMEOUT', exit_R=r_close, bars=bars_in_trade, mfe=mfe)


# ---------------------------------------------------------------------------- #
# Stop policies
# ---------------------------------------------------------------------------- #

def compute_stop(bars, entry_idx, entry_price, atr_at_loss, stop_policy,
                 orig_risk=None):
    """Return stop_price (price below entry) and the chosen risk in $."""
    # ATR at entry bar (re-entry bar) — fall back to loser atr if missing
    entry_bar = bars[entry_idx]
    atr_now = entry_bar.get('atr') or atr_at_loss
    # orig_risk-based families: baseline equivalent
    if stop_policy.startswith('orig_'):
        mult = float(stop_policy.split('_')[1])
        if orig_risk is None or orig_risk <= 0:
            return entry_price - mult * atr_now
        return entry_price - mult * orig_risk
    if stop_policy.startswith('atr_'):
        mult = float(stop_policy.split('_')[1])
        return entry_price - mult * atr_now
    if stop_policy == 'swing_5':
        # low of last 5 bars minus 0.2 ATR
        lows = [bars[entry_idx - k]['low'] for k in range(0, 5) if entry_idx - k >= 0]
        return min(lows) - 0.2 * atr_now
    if stop_policy == 'swing_10':
        lows = [bars[entry_idx - k]['low'] for k in range(0, 10) if entry_idx - k >= 0]
        return min(lows) - 0.3 * atr_now
    if stop_policy == 'vol_blend':
        # 2 * (ATR_short + ATR_long)/2 ; ATR_short from last 5 bars true range, long is ATR_now
        # approximate ATR_5 with simple high-low mean over 5 bars
        tr = []
        for k in range(0, 5):
            if entry_idx - k < 1:
                continue
            b = bars[entry_idx - k]
            pb = bars[entry_idx - k - 1]
            tr.append(max(b['high'] - b['low'], abs(b['high'] - pb['close']), abs(b['low'] - pb['close'])))
        atr5 = mean(tr) if tr else atr_now
        return entry_price - 2.0 * (atr5 + atr_now) / 2.0
    # fallback
    return entry_price - 4.0 * atr_now


# ---------------------------------------------------------------------------- #
# Run one variant across all 78 losers
# ---------------------------------------------------------------------------- #

def run_variant(losers, bars, *,
                entry_policy='demand_low',
                stop_policy='atr_4.0',
                exit_policy='fixR_5',
                size_policy='half',          # half | equal | time_decay
                max_wait=400,
                use_baseline_entry=False):
    """Returns aggregate stats.
    use_baseline_entry: if True, use the recorded reentry_baseline.new_bar_idx and
    new_entry. This isolates target/stop/sizing optimization from entry-policy noise.
    """
    results = []
    for L in losers:
        # Find loser bar in bars
        ts = L['ts']
        loser_idx = TS_TO_IDX.get(ts)
        if loser_idx is None:
            results.append(dict(ts=ts, skip='no_loser_idx'))
            continue
        # Either reuse baseline entry, or search per policy
        if use_baseline_entry:
            rb = L.get('reentry_baseline', {})
            if rb.get('outcome') != 'DONE':
                results.append(dict(ts=ts, outcome='NO_TOUCH'))
                continue
            ent_idx = rb['new_bar_idx']
            ent_price = rb['new_entry']
            wait_bars = rb.get('wait_bars', ent_idx - loser_idx)
        else:
            # Start searching for re-entry from loser_idx+1
            ent_idx, ent_price, wait_bars, dlow, dhigh = find_entry(
                bars, loser_idx + 1, L, entry_policy, max_wait=max_wait)
            if ent_idx is None:
                results.append(dict(ts=ts, outcome='NO_TOUCH'))
                continue
        stop_price = compute_stop(bars, ent_idx, ent_price, L.get('atr', 1.0), stop_policy,
                                  orig_risk=L.get('risk'))
        risk = ent_price - stop_price
        if risk <= 0:
            results.append(dict(ts=ts, outcome='INVALID_STOP'))
            continue
        # Exit policy
        if exit_policy.startswith('fixR_'):
            tgt = float(exit_policy.split('_')[1])
            res = exit_fixR(bars, ent_idx, ent_price, stop_price, tgt)
        elif exit_policy.startswith('BE'):
            # BE_at_1_dyn → BE at 1R, run to 20R
            parts = exit_policy.split('_')
            be_at = float(parts[1])
            tgt = float(parts[3]) if len(parts) > 3 else 20.0
            res = exit_BE_then_dyn(bars, ent_idx, ent_price, stop_price, be_at, final_target_R=tgt)
        elif exit_policy.startswith('trail_'):
            parts = exit_policy.split('_')
            arm = float(parts[1])
            lock = float(parts[2]) if len(parts) > 2 else 0.5
            res = exit_trail_lock(bars, ent_idx, ent_price, stop_price, arm, lock_pct=lock)
        elif exit_policy.startswith('asym_'):
            parts = exit_policy.split('_')
            t1 = float(parts[1])
            be = float(parts[2])
            cap = float(parts[3]) if len(parts) > 3 else 20.0
            res = exit_asymmetric(bars, ent_idx, ent_price, stop_price, t1, be, runner_cap_R=cap)
        else:
            res = exit_fixR(bars, ent_idx, ent_price, stop_price, 5.0)

        # Sizing
        if size_policy == 'half':
            size = 0.5
        elif size_policy == 'equal':
            size = 1.0
        elif size_policy == 'time_decay':
            if wait_bars < 30:
                size = 1.0
            elif wait_bars < 80:
                size = 0.75
            elif wait_bars < 150:
                size = 0.5
            else:
                size = 0.25
        elif size_policy == 'atr_normalized':
            # Inverse to stop distance vs original risk so $ risk is constant
            orig_risk = L['risk']
            size = orig_risk / risk if risk > 0 else 0.5
            size = max(0.1, min(2.0, size))  # cap
        else:
            size = 0.5

        record = dict(
            ts=ts,
            entry=ent_price,
            stop=stop_price,
            risk=risk,
            wait_bars=wait_bars,
            size=size,
            **res,
        )
        record['contribution_R'] = record.get('exit_R', 0.0) * size
        results.append(record)
    return results


def summarize(results, label):
    n = len(results)
    no_touch = sum(1 for r in results if r.get('outcome') == 'NO_TOUCH')
    invalid = sum(1 for r in results if r.get('outcome') in ('INVALID_STOP', 'INVALID'))
    valid = [r for r in results if r.get('exit_R') is not None]
    n_winners = sum(1 for r in valid if r.get('outcome') in ('WINNER', 'RUNNER_CAP'))
    n_losers = sum(1 for r in valid if r.get('outcome') == 'LOSER')
    n_partial = sum(1 for r in valid if r.get('outcome') in ('PARTIAL', 'TIMEOUT_PARTIAL'))
    n_trail = sum(1 for r in valid if r.get('outcome') == 'TRAIL_WIN')
    n_be = sum(1 for r in valid if r.get('outcome') == 'BE')
    n_timeout = sum(1 for r in valid if r.get('outcome') == 'TIMEOUT')
    sumR_nominal = sum(r.get('exit_R', 0.0) for r in valid)
    sumR_adjusted = sum(r.get('contribution_R', 0.0) for r in valid)
    mfes = [r.get('mfe', 0.0) for r in valid]
    waits = [r.get('wait_bars', 0) for r in valid]
    return dict(
        label=label,
        n=n,
        n_no_touch=no_touch,
        n_invalid=invalid,
        n_traded=len(valid),
        n_winners=n_winners,
        n_losers=n_losers,
        n_partial=n_partial,
        n_trail_win=n_trail,
        n_be=n_be,
        n_timeout=n_timeout,
        sumR_nominal=round(sumR_nominal, 2),
        sumR_adjusted=round(sumR_adjusted, 2),
        win_rate=round(n_winners / max(1, len(valid)), 3),
        mfe_mean=round(mean(mfes), 2) if mfes else 0.0,
        mfe_median=round(median(mfes), 2) if mfes else 0.0,
        wait_mean=round(mean(waits), 1) if waits else 0.0,
        wait_median=int(median(waits)) if waits else 0,
    )


# ---------------------------------------------------------------------------- #
# Build variant grid
# ---------------------------------------------------------------------------- #

def build_variants():
    V = []

    # All variants below use baseline-recorded entry bar/price unless tagged
    # entry_policy=... explicitly. This isolates target/stop/sizing edge.

    # ---- Section: target variants on baseline stop (orig_risk * 2) ----
    for tgt in [3, 5, 7, 10, 15, 20]:
        V.append(dict(
            label=f'tgt_fix{tgt}R | BASELINE_ENTRY | orig_2x | half',
            entry_policy='demand_low', stop_policy='orig_2.0',
            exit_policy=f'fixR_{tgt}', size_policy='half',
            use_baseline_entry=True))

    # ---- Same target variants on tighter stops ----
    for stop in ['orig_1.0', 'orig_1.5', 'orig_2.5', 'orig_3.0']:
        V.append(dict(
            label=f'tgt_fix5R | BASELINE_ENTRY | {stop} | half',
            entry_policy='demand_low', stop_policy=stop,
            exit_policy='fixR_5', size_policy='half',
            use_baseline_entry=True))

    # ---- Also test on ATR-based stops ----
    for stop in ['atr_2.0', 'atr_3.0', 'atr_4.0']:
        for tgt in [3, 5]:
            V.append(dict(
                label=f'tgt_fix{tgt}R | BASELINE_ENTRY | {stop} | half',
                entry_policy='demand_low', stop_policy=stop,
                exit_policy=f'fixR_{tgt}', size_policy='half',
                use_baseline_entry=True))

    # ---- BE @ N R then dyn target N R (on baseline stop family) ----
    for be, final in [(1, 5), (1, 10), (1, 15), (1, 20),
                      (2, 10), (2, 15), (2, 20),
                      (3, 10), (3, 20)]:
        V.append(dict(
            label=f'BE@{be}R_runner{final}R | BASELINE_ENTRY | orig_2x | half',
            entry_policy='demand_low', stop_policy='orig_2.0',
            exit_policy=f'BE_{be}_dyn_{final}', size_policy='half',
            use_baseline_entry=True))

    # ---- Trail variants on baseline stop family ----
    for arm in [2, 3, 5, 8]:
        for lock in [0.3, 0.5, 0.7]:
            V.append(dict(
                label=f'trail_arm{arm}R_lock{int(lock*100)}% | BASELINE_ENTRY | orig_2x | half',
                entry_policy='demand_low', stop_policy='orig_2.0',
                exit_policy=f'trail_{arm}_{lock}', size_policy='half',
                use_baseline_entry=True))

    # ---- Asymmetric on baseline stop family ----
    for t1, be, cap in [(2, 1, 10), (2, 1, 15), (2, 1, 20),
                        (3, 1, 10), (3, 1, 15), (3, 1, 20),
                        (3, 2, 20), (3, 0, 15),
                        (5, 2, 20), (5, 3, 30)]:
        V.append(dict(
            label=f'asym_t{t1}_be{be}_cap{cap} | BASELINE_ENTRY | orig_2x | half',
            entry_policy='demand_low', stop_policy='orig_2.0',
            exit_policy=f'asym_{t1}_{be}_{cap}', size_policy='half',
            use_baseline_entry=True))

    # ---- Stop variants on fixR_5 (baseline entry) ----
    for stop in ['orig_1.0', 'orig_1.5', 'orig_2.0', 'orig_2.5', 'orig_3.0',
                 'atr_1.5', 'atr_2.0', 'atr_2.5', 'atr_3.0', 'atr_4.0',
                 'swing_5', 'swing_10', 'vol_blend']:
        V.append(dict(
            label=f'stop_{stop} | BASELINE_ENTRY | fixR5 | half',
            entry_policy='demand_low', stop_policy=stop,
            exit_policy='fixR_5', size_policy='half',
            use_baseline_entry=True))

    # ---- Entry timing on fixR_5 / baseline stop family (alt-entry policies) ----
    for ent in ['demand_low', 'demand_mid', 'demand_high', 'confirmation']:
        V.append(dict(
            label=f'ALT-ENTRY_{ent} | fixR5 | orig_2x | half',
            entry_policy=ent, stop_policy='orig_2.0',
            exit_policy='fixR_5', size_policy='half',
            use_baseline_entry=False))

    # ---- Wait window variants (ALT-ENTRY only, since baseline uses recorded idx) ----
    for w in [50, 100, 200, 400]:
        V.append(dict(
            label=f'ALT-ENTRY maxwait{w} | demand_low fixR5 orig_2x half',
            entry_policy='demand_low', stop_policy='orig_2.0',
            exit_policy='fixR_5', size_policy='half', max_wait=w,
            use_baseline_entry=False))

    # ---- Sizing variants on baseline ----
    for sz in ['half', 'equal', 'time_decay', 'atr_normalized']:
        V.append(dict(
            label=f'size_{sz} | BASELINE_ENTRY fixR5 orig_2x',
            entry_policy='demand_low', stop_policy='orig_2.0',
            exit_policy='fixR_5', size_policy=sz,
            use_baseline_entry=True))

    # ---- Combos: best-of intuition (baseline entry) ----
    for stop in ['orig_2.0', 'orig_1.5', 'orig_1.0']:
        for exit_p in ['asym_3_1_20', 'asym_3_2_20', 'asym_5_2_20',
                       'BE_1_dyn_20', 'BE_2_dyn_20',
                       'trail_3_0.5', 'trail_5_0.5']:
            for sz in ['half', 'equal', 'atr_normalized']:
                V.append(dict(
                    label=f'COMBO {stop} + {exit_p} + {sz}',
                    entry_policy='demand_low', stop_policy=stop,
                    exit_policy=exit_p, size_policy=sz,
                    use_baseline_entry=True))

    return V


# ---------------------------------------------------------------------------- #
# Main
# ---------------------------------------------------------------------------- #

if __name__ == '__main__':
    print('[load] losers...', flush=True)
    losers = load_losers()
    print(f'[load] {len(losers)} losers', flush=True)

    print('[load] 4H bars...', flush=True)
    bars = load_bars()
    print(f'[load] {len(bars)} bars', flush=True)

    # ts -> idx cache (global so run_variant can reuse)
    TS_TO_IDX = {b['ts']: i for i, b in enumerate(bars)}
    globals()['TS_TO_IDX'] = TS_TO_IDX

    # ---- Baseline reference (recompute baseline through our pipeline for fairness) ----
    # Per reverse-engineering: baseline uses orig_risk * 2 as new stop distance.
    print('[baseline] sanity check via our pipeline (use_baseline_entry + orig_2.0 + fixR5 + half)...', flush=True)
    baseline_results = run_variant(losers, bars,
                                   entry_policy='demand_low',
                                   stop_policy='orig_2.0',
                                   exit_policy='fixR_5',
                                   size_policy='half',
                                   max_wait=400,
                                   use_baseline_entry=True)
    base_summary = summarize(baseline_results, 'BASELINE_RECOMPUTED use_baseline_entry orig_2x fixR5 half')
    print('[baseline] our recompute:', base_summary, flush=True)

    # ---- Original baseline as reported in input file ----
    orig_done = [l for l in losers if l['reentry_baseline']['outcome'] == 'DONE']
    orig_winR = sum(l['reentry_baseline'].get('exit_R', 0) for l in orig_done)
    print(f'[baseline] original reported sumR nominal: {orig_winR} (×0.5 sizing = {orig_winR*0.5})')

    # ---- Run variants ----
    variants = build_variants()
    print(f'[run] {len(variants)} variants', flush=True)
    all_summaries = []
    for i, v in enumerate(variants, 1):
        max_wait = v.pop('max_wait', 400)
        use_baseline = v.pop('use_baseline_entry', False)
        label = v['label']
        try:
            r = run_variant(losers, bars, max_wait=max_wait,
                            use_baseline_entry=use_baseline,
                            **{k: v[k] for k in
                ['entry_policy', 'stop_policy', 'exit_policy', 'size_policy']})
            s = summarize(r, label)
        except Exception as e:
            s = dict(label=label, error=str(e))
        s['config'] = v
        s['use_baseline_entry'] = use_baseline
        all_summaries.append(s)
        print(f'  [{i}/{len(variants)}] {label} → sumR_adj={s.get("sumR_adjusted")}  '
              f'W:{s.get("n_winners")} L:{s.get("n_losers")} NT:{s.get("n_no_touch")} '
              f'mfe_med={s.get("mfe_median")}', flush=True)

    # ---- Rank ----
    ranked = sorted(all_summaries, key=lambda s: s.get('sumR_adjusted', -9999), reverse=True)
    print('\n========== TOP 10 by sumR_adjusted ==========')
    for s in ranked[:10]:
        print(f'  sumR_adj={s.get("sumR_adjusted"):>7}  nom={s.get("sumR_nominal"):>7}  '
              f'W:{s.get("n_winners")}/{s.get("n_traded")}  '
              f'NT:{s.get("n_no_touch"):>2}  | {s.get("label")}')

    print('\n========== ASYMMETRIC variants ==========')
    asym = [s for s in all_summaries if 'asym' in s.get('label', '')]
    for s in sorted(asym, key=lambda s: s.get('sumR_adjusted', -9999), reverse=True):
        print(f'  sumR_adj={s.get("sumR_adjusted"):>7}  nom={s.get("sumR_nominal"):>7}  '
              f'W:{s.get("n_winners")}  P:{s.get("n_partial")}  L:{s.get("n_losers")}  '
              f'TO:{s.get("n_timeout")}  | {s.get("label")}')

    # ---- Write output ----
    out = dict(
        meta=dict(
            agent='A_targetstop',
            n_losers=len(losers),
            n_bars=len(bars),
            baseline_recomputed=base_summary,
            baseline_reported_sumR_nominal=orig_winR,
            baseline_reported_sumR_adjusted=orig_winR * 0.5,
        ),
        variants=all_summaries,
        ranked_top10=[s.get('label') for s in ranked[:10]],
    )
    with open(OUT_PATH, 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print(f'\n[done] wrote {OUT_PATH}')
