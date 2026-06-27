#!/usr/bin/env python3
"""DA follow-up: (1) bound L_zone look-ahead severity by re-running with L_zone forced 0
(does removing the possibly-contaminated lens change conclusions?); (2) S2 L_rsi n0=7 jackknife.
Run: python3 _DA_anel2_zone_rsi.py"""
import importlib.util
from pathlib import Path
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location("anel2",HERE/"anel2_reader.py")
A=importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
r=A.detect()

print("=== (1) L_zone contamination bound: conv WITH vs WITHOUT L_zone ===")
cuts={1:4,2:3,3:4,4:5}
for sid,nm in [(1,"S1"),(2,"S2"),(3,"S3"),(4,"S4")]:
    v=r[sid]; thr=cuts[sid]
    # original conv keeps L_zone; recompute conv minus L_zone, keep same thr offset (thr-1 to be fair)
    sub_orig=[x for x in v if x["conv"]>=thr]
    sub_noz=[x for x in v if (x["conv"]-x["L_zone"])>=thr-1]  # parity: zone was ~1 vote
    print(f"{nm}: orig conv>={thr} n={len(sub_orig)} avgR={A.avg(sub_orig):+.2f} sumR={sum(x['R'] for x in sub_orig):+.1f}"
          f" | drop-zone(conv-Lz>={thr-1}) n={len(sub_noz)} avgR={A.avg(sub_noz):+.2f} sumR={sum(x['R'] for x in sub_noz):+.1f}")

print("\n=== (2) S2 L_rsi=0 jackknife (n0=7) ===")
v=r[2]; z=[x for x in v if not x["L_rsi"]]
print(f"L_rsi=0 trades: R={sorted([round(x['R'],2) for x in z])} n={len(z)} avgR={A.avg(z):+.2f}")
o=[x for x in v if x["L_rsi"]]
print(f"L_rsi=1 avgR={A.avg(o):+.2f} (n={len(o)}). Raw lift +{A.avg(o)-A.avg(z):.2f}")
import statistics as st
for k in range(len(z)):
    zz=z[:k]+z[k+1:]
    print(f"  drop 1 (R={z[k]['R']:+.2f}): L_rsi=0 avgR -> {st.mean([x['R'] for x in zz]):+.2f}  | lift -> {A.avg(o)-st.mean([x['R'] for x in zz]):+.2f}")
