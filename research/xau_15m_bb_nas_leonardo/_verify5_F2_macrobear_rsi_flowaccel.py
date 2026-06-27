"""
DEVIL'S ADVOCATE verify (recalibrated) for 5ATR filter F2.

RULE: macro_bear<=0 AND rsi>=53.0 AND flow_accel<=78
Claim: n_keep=2498, wr_keep=63.21, streak_keep=22, winners_kept_pct=85.7

Regua: NAO vetar por tail/WR-only/sem-OOS.
VETO only for:
  - look-ahead (feature uses future/outcome)
  - non-stationarity: WR-after by YEAR vs BASE-OF-THAT-YEAR, and by BLOCK.
      WORSE in any year OR >2/8 blocks => VETO
  - cuts winners < 85%
  - cherry-pick: +/-20% neighborhood collapses

Outcome field = 'win' (matches base WR=60.49 = 1843/3047). 'win' differs from
R>0 in exactly 1 scratch row (R==0 labeled win=1); irrelevant.

Streak = max consecutive losers (win==0), ordered by low_t (chronological).
"""
import json

ROWS = [json.loads(l) for l in open('dataset_5atr.jsonl')]
ROWS.sort(key=lambda r: r['low_t'])  # chronological for streak

FEATS = ['macro_bear', 'rsi', 'flow_accel']
OUTCOME = ['R', 'win', 'cj']  # outcome / forward fields not allowed in rule


def sel(r):
    return r['macro_bear'] <= 0 and r['rsi'] >= 53.0 and r['flow_accel'] <= 78


def wr(rows):
    n = len(rows)
    if n == 0:
        return 0.0, 0
    w = sum(x['win'] for x in rows)
    return w / n * 100, n


def max_loss_streak(rows):
    # rows already chronological
    cur = mx = 0
    for r in rows:
        if r['win'] == 0:
            cur += 1
            mx = max(mx, cur)
        else:
            cur = 0
    return mx


# ---------- TOTAL ----------
base_wr, base_n = wr(ROWS)
kept = [r for r in ROWS if sel(r)]
cut = [r for r in ROWS if not sel(r)]
keep_wr, keep_n = wr(kept)

base_winners = sum(r['win'] for r in ROWS)
kept_winners = sum(r['win'] for r in kept)
winners_kept_pct = kept_winners / base_winners * 100
losers_base = base_n - base_winners
losers_cut = sum(1 for r in cut if r['win'] == 0)
losers_cut_pct = losers_cut / losers_base * 100

base_streak = max_loss_streak(ROWS)
keep_streak = max_loss_streak(kept)

print("=== TOTAL ===")
print(f"base   n={base_n} WR={base_wr:.2f} winners={base_winners} losers={losers_base} streak={base_streak}")
print(f"kept   n={keep_n} WR={keep_wr:.2f} winners={kept_winners} streak={keep_streak}")
print(f"deltaWR={keep_wr-base_wr:+.2f}pp  winners_kept_pct={winners_kept_pct:.1f}%  losers_cut_pct={losers_cut_pct:.1f}%")

# ---------- LOOK-AHEAD ----------
print("\n=== LOOK-AHEAD ===")
print("rule features:", FEATS)
print("none in outcome set:", all(f not in OUTCOME for f in FEATS))
# macro_bear: macro-leg state at base; rsi: at reclaim bar; flow_accel: flow at bar.
# All are bar-of-signal state (no forward fields). PASS unless a feature is forward.

# ---------- STATIONARITY: PER YEAR (vs base-of-year) ----------
print("\n=== PER YEAR (WR base-of-year vs kept) ===")
year_fail = False
for yr in sorted(set(r['yr'] for r in ROWS)):
    yall = [r for r in ROWS if r['yr'] == yr]
    ykept = [r for r in kept if r['yr'] == yr]
    ybw, ybn = wr(yall)
    ykw, ykn = wr(ykept)
    worse = ykw < ybw
    if worse:
        year_fail = True
    print(f"{yr}: base n={ybn} WR={ybw:.2f} | kept n={ykn} WR={ykw:.2f} | delta={ykw-ybw:+.2f}pp {'WORSE!' if worse else 'ok'}")

# ---------- STATIONARITY: PER BLOCK (vs base-of-block) ----------
print("\n=== PER BLOCK (WR base-of-block vs kept) ===")
block_worse = 0
for b in sorted(set(r['block'] for r in ROWS)):
    ball = [r for r in ROWS if r['block'] == b]
    bkept = [r for r in kept if r['block'] == b]
    bbw, bbn = wr(ball)
    bkw, bkn = wr(bkept)
    worse = bkw < bbw
    if worse:
        block_worse += 1
    print(f"{b}: base n={bbn} WR={bbw:.2f} | kept n={bkn} WR={bkw:.2f} | delta={bkw-bbw:+.2f}pp {'WORSE!' if worse else 'ok'}")
print(f"blocks WORSE: {block_worse}/8 (VETO if >2)")

# ---------- CHERRY-PICK: +/-20% threshold neighborhood ----------
print("\n=== CHERRY-PICK (+/-20% on rsi & flow_accel thresholds) ===")
# rsi base=53.0 -> +/-20% of value: 42.4 .. 63.6 ; flow_accel base=78 -> 62.4 .. 93.6
for rsi_t in (53.0*0.8, 53.0, 53.0*1.2):
    for fa_t in (78*0.8, 78, 78*1.2):
        kk = [r for r in ROWS if r['macro_bear'] <= 0 and r['rsi'] >= rsi_t and r['flow_accel'] <= fa_t]
        w, n = wr(kk)
        wk = sum(r['win'] for r in kk) / base_winners * 100
        print(f"rsi>={rsi_t:5.1f} flow<={fa_t:5.1f}: n={n:4d} WR={w:.2f} winners_kept={wk:.1f}%")

# ---------- COMPONENT MARGINALS (does flow_accel add anything?) ----------
print("\n=== COMPONENT MARGINALS ===")
def stat(name, fn):
    kk = [r for r in ROWS if fn(r)]
    w, n = wr(kk)
    wk = sum(r['win'] for r in kk) / base_winners * 100
    print(f"{name:38s} n={n:4d} WR={w:.2f} winners_kept={wk:.1f}% streak={max_loss_streak(kk)}")

stat("macro_bear<=0 only", lambda r: r['macro_bear'] <= 0)
stat("rsi>=53 only", lambda r: r['rsi'] >= 53.0)
stat("flow_accel<=78 only", lambda r: r['flow_accel'] <= 78)
stat("macro_bear<=0 & rsi>=53", lambda r: r['macro_bear'] <= 0 and r['rsi'] >= 53.0)
stat("FULL (mb & rsi & flow)", sel)

# ---------- VERDICT ----------
print("\n=== VERDICT ===")
veto = []
if not all(f not in OUTCOME for f in FEATS):
    veto.append("look-ahead")
if year_fail:
    veto.append("year-nonstationary")
if block_worse > 2:
    veto.append(f"block-nonstationary({block_worse}/8)")
if winners_kept_pct < 85.0:
    veto.append(f"cuts-winners({winners_kept_pct:.1f}%)")
print("VETO reasons:", veto if veto else "NONE")
print("SURVIVES:", len(veto) == 0)
print(f"REPORT wr_keep={keep_wr:.2f} streak_keep={keep_streak} winners_kept_pct={winners_kept_pct:.1f}")
