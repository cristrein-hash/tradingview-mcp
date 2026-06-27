#!/usr/bin/env python3
"""The 2 suspicious >3d gaps in the global series: convert epochs to dates.
Both are 73.2h (Easter holiday weekends 2025/2026), not data corruption.
Durability walks that cross them just skip ~2 extra calendar days; durab_days inflated slightly there."""
import datetime as dt
GAPS=[(1744922700,1745186400),(1775162700,1775426400)]
for a,b in GAPS:
    da=dt.datetime.utcfromtimestamp(a); db=dt.datetime.utcfromtimestamp(b)
    print(f"gap {(b-a)/3600:.1f}h  {da} -> {db}  ({da.strftime('%a')}->{db.strftime('%a')})")
