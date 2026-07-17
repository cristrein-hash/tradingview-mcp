#!/usr/bin/env python3
"""PARIDADE Cp — o motor puro (cp_engine_live.scan) alimentado com o MESMO RAW tem de reproduzir os 26
trades do baseline (cp_plot_window.run_trades) BYTE-EXATO em (fundo_t, etime, ent, sl, tgt). Gate de
go-live: sem PASS 26/26, o runtime não sobe. Disciplina L2 (parity antes de live)."""
import sys, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
RUNTIME = HERE.parent
REV = Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation")
sys.path.insert(0, str(RUNTIME)); sys.path.insert(0, str(REV / "a1a2_fundo_lab")); sys.path.insert(0, str(REV))
import cp_engine_live as ENG
import cp_plot_window as CP

ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")


def main():
    # referência: baseline (loader RAW + lógica original)
    ref = CP.run_trades()
    # motor puro alimentado com os MESMOS arrays/bubbles do RAW
    live = ENG.scan(CP.T, CP.O, CP.H, CP.L, CP.C, CP.BUYS, CP.SELLS, t_lo=CP.T_LO, t_hi=CP.T_HI)
    print(f"baseline: {len(ref)} trades · motor puro: {len(live)} trades")
    ok = len(ref) == len(live)
    for i, (a, b) in enumerate(zip(ref, live), 1):
        same = (a["etime"] == b["etime"] and abs(a["ent"] - b["ent"]) < 1e-9 and
                abs(a["sl"] - b["sl"]) < 1e-9 and abs(a["tgt"] - b["tgt"]) < 1e-9)
        ok = ok and same
        flag = "OK " if same else "DIFF"
        print(f"  #{i:2d} {flag} {ds(a['etime'])} ent {a['ent']:.2f}/{b['ent']:.2f} "
              f"sl {a['sl']:.2f}/{b['sl']:.2f} tgt {a['tgt']:.2f}/{b['tgt']:.2f}")
    print(f"\nPARITY: {'PASS' if ok else 'FAIL'} ({len(ref)}/{len(live)})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
