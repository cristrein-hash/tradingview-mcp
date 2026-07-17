#!/usr/bin/env python3
"""V-2 — PARIDADE SELEÇÃO-17 (l2_engine FSM+segmentos+zonas sobre a régua vs canon).

Mesmo contrato de research/l2_bpt_causal_selector.py:54-56 (fail-loud, byte-a-byte):
  sorted(selecionados) == sorted(bar_idx de research/results/l2_bpt_17_trades.csv)

Pipeline engine-only: FSM(raw 4H) -> build_segments -> prepare_segments -> keep_signal
sobre l2_bpt_regua_structural.csv (245 sinais).
"""
import json, csv, sys
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import l2_engine as E

RAW_PATH = REPO / "my-strategy/research/revalidation/raw_4h_ohlc.jsonl"
REGUA_PATH = REPO / "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_regua_structural.csv"
CANON_PATH = REPO / "research/results/l2_bpt_17_trades.csv"


def main():
    B4 = [json.loads(l) for l in RAW_PATH.read_text().splitlines()]
    B4.sort(key=lambda x: x["t"])
    fsm = E.make_regime_fsm(B4)
    reg = fsm["run"](0.03, 1.15, 0.88)
    segs = E.prepare_segments(fsm["build_segments"](reg))
    sel_obj = E.make_selector(segs, fsm["T"], fsm["H"], fsm["L"])

    REGUA = list(csv.DictReader(open(REGUA_PATH)))
    print(f"régua: {len(REGUA)} sinais · segmentos: {len(segs)}")

    sel = []
    by_reg = {'BULL': 0, 'RANGE': 0, 'BEAR': 0}
    for r in REGUA:
        bi = int(r["bar_idx"]); entry = float(r["entry"])
        kept, x = sel_obj["keep_signal"](bi, entry)
        if kept:
            sel.append(bi); by_reg[x['reg']] += 1
    sel = sorted(sel)

    CANON17 = sorted(int(r["bar_idx"]) for r in csv.DictReader(open(CANON_PATH)))
    assert len(CANON17) == 17

    # contrato fonte: research/l2_bpt_causal_selector.py:54-56
    if sel != CANON17:
        print(f"V-2 RESULT: FAIL — selector não reproduz os 17.")
        print(f"  selecionado={sel}")
        print(f"  canonico   ={CANON17}")
        print(f"  diff+={sorted(set(sel) - set(CANON17))} diff-={sorted(set(CANON17) - set(sel))}")
        return 1
    print(f"V-2 RESULT: PASS — engine reproduz os 17 byte-a-byte ({len(REGUA)} -> {len(sel)})")
    print(f"  por regime: " + ", ".join(f"{rg}={by_reg[rg]}" for rg in ('BULL', 'RANGE', 'BEAR')))
    print(f"  bar_idx: {sel}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
