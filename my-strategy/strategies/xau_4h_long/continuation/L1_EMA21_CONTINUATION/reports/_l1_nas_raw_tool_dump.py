#!/usr/bin/env python3
"""SANITY_PROBE read-only: dump cru de data_get_study_values_at_bar p/ NAS e RSI (controlo).
Só leitura; sem draw/screenshot/symbol-change/Telegram. Diagnostica porque a série NAS veio incompleta."""
import sys, json
from pathlib import Path
HERE=Path(__file__).resolve().parent; L1=HERE.parent
sys.path.insert(0,str(L1.parents[4]/"my-strategy/core"))
from tv_read_adapter import _MCP
c=_MCP(); c.start()
try:
    st=c.call("chart_get_state")
    print("chart:",(st or {}).get("symbol"),(st or {}).get("resolution"))
    for filt in ["NAS","Relative Strength"]:
        print(f"\n===== data_get_study_values_at_bar filter={filt!r} count=8 =====")
        r=c.call("data_get_study_values_at_bar",{"study_filter":filt,"count":8})
        studies=(r or {}).get("studies") or []
        print(f"n_studies_match={len(studies)}")
        for s in studies:
            print(f"  study name={s.get('name')!r} last_index={s.get('last_index')} n_bars={len(s.get('bars') or [])}")
            for b in (s.get('bars') or [])[-4:]:
                print(f"    bar_index={b.get('bar_index')} time={b.get('time')} values={b.get('values')}")
    # controlo: current study values (data-window)
    print("\n===== data_get_study_values (current/forming) — NAS presente? =====")
    sv=c.call("data_get_study_values")
    txt=json.dumps(sv)[:1500]
    print("NAS_in_current:", "NAS" in txt, "| DISTANCE_in_current:", "DISTANCE" in txt.upper())
finally:
    try: c.stop()
    except Exception: pass
