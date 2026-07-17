#!/usr/bin/env python3
"""V-3 — PARIDADE EXIT TREND-EXIT/REGIME-FLIP (l2_engine sobre as 245 da régua).

Espelha o gate fail-loud de research/l2_bpt_trend_exit_execution_risk_layer.py:106-109:
  SELECT-17: abs(sumR - 105.3) < 0.6 ; maxDD == -4.1 ; streak == 3
  FULL-245 : sumR ~ +399.2 — gate ADICIONADO nesta paridade (o original só imprimia o
  FULL sem assert; |diff|<0.6 é mais estrito que a fonte, na mesma tolerância do G1)

R por trade arredondado a 2dp (como sim(), fonte :39/41/43) e painel com
round(sumR,1)/round(dd,1) (fonte :49-58).
"""
import json, csv, sys
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import l2_engine as E

RAW_PATH = REPO / "my-strategy/research/revalidation/raw_4h_ohlc.jsonl"
REGUA_PATH = REPO / "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_regua_structural.csv"


# fonte: l2_bpt_trend_exit_execution_risk_layer.py:49-58 (campos essenciais do painel)
def panel(rows):
    if not rows: return dict(N=0)
    n = len(rows); s = sum(x['R'] for x in rows); w = sum(1 for x in rows if x['R'] > 0)
    cum = peak = dd = 0; stk = mx = 0
    for x in sorted(rows, key=lambda z: z['bi']):
        cum += x['R']; peak = max(peak, cum); dd = min(dd, cum - peak); stk = stk + 1 if x['R'] <= 0 else 0; mx = max(mx, stk)
    return dict(N=n, sumR=round(s, 1), WR=round(100 * w / n), maxDD=round(dd, 1), streak=mx,
                retDD=round(s / abs(dd), 1) if dd < 0 else None, worst=round(min(x['R'] for x in rows), 2))


def main():
    B4 = [json.loads(l) for l in RAW_PATH.read_text().splitlines()]
    B4.sort(key=lambda x: x["t"])
    fsm = E.make_regime_fsm(B4)
    reg = fsm["run"](0.03, 1.15, 0.88)
    segs = E.prepare_segments(fsm["build_segments"](reg))
    sel_obj = E.make_selector(segs, fsm["T"], fsm["H"], fsm["L"])
    ex = E.make_trend_exit(B4, segs)

    RG = list(csv.DictReader(open(REGUA_PATH)))
    SEL17 = {int(r['bar_idx']) for r in RG if sel_obj["keep_signal"](int(r['bar_idx']), float(r['entry']))[0]}
    print(f"régua {len(RG)} · SEL17 pelo engine: {len(SEL17)}")

    rows_full = [ex["regime_flip_detail"](int(r['bar_idx']), float(r['entry']), float(r['sl'])) for r in RG]
    rows_17 = [x for x in rows_full if x['bi'] in SEL17]

    b17 = panel(rows_17); bF = panel(rows_full)
    print(f"SELECT-17: N={b17['N']} sumR={b17['sumR']:+} WR={b17['WR']}% maxDD={b17['maxDD']} streak={b17['streak']} retDD={b17['retDD']} worst={b17['worst']}")
    print(f"FULL-245 : N={bF['N']} sumR={bF['sumR']:+} WR={bF['WR']}% maxDD={bF['maxDD']} streak={bF['streak']} retDD={bF['retDD']} worst={bF['worst']}")

    # gates fonte: l2_bpt_trend_exit_execution_risk_layer.py:106-109
    g1 = abs(b17['sumR'] - 105.3) < 0.6
    g2 = (b17['maxDD'] == -4.1 and b17['streak'] == 3)
    g3 = abs(bF['sumR'] - 399.2) < 0.6
    print(f"G1 SELECT-17 sumR≈105.3: {'PASS' if g1 else 'FAIL'} ({b17['sumR']})")
    print(f"G2 SELECT-17 maxDD==-4.1 & streak==3: {'PASS' if g2 else 'FAIL'} ({b17['maxDD']}, {b17['streak']})")
    print(f"G3 FULL-245 sumR≈399.2: {'PASS' if g3 else 'FAIL'} ({bF['sumR']})")

    ok = g1 and g2 and g3
    print(f"\nV-3 RESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
