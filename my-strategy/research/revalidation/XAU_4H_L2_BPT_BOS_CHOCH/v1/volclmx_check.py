import json
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen);V=[r.get('volume') or 0 for r in frozen];C=[r['close'] for r in frozen];O=[r['open'] for r in frozen];Hh=[r['high'] for r in frozen];Ll=[r['low'] for r in frozen]
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
def volclmx(i):
    avg50=sum(V[i-50:i])/50 if i>=50 and sum(V[i-50:i])>0 else None
    return round(max(V[i-9:i+1])/avg50,2) if avg50 else None
# groups
WIN_REV={'E1','E17','E27','E30','E40'}  # reversal-from-bottom winners
WIN_PB={'E13','E21','E23','E5'}         # pullback winners
TRAP_BEAR={'E6','E7','E11','E36','E37','E9','E8','E33'}  # bear-cluster traps
TRAP_TOP={'E15','E24','E34','E39'}      # top traps
import statistics
def show(name,s):
    vals=[volclmx(geom[e]['bar_idx']) for e in s if volclmx(geom[e]['bar_idx']) is not None]
    print(f"  {name:<12} n={len(vals)} volClmx: {sorted(round(v,2) for v in vals)}  median={round(statistics.median(vals),2)}")
print("=== volume-climax (max vol last10 / avg50) by group ===")
show('WIN_REV',WIN_REV); show('WIN_PB',WIN_PB); show('TRAP_BEAR',TRAP_BEAR); show('TRAP_TOP',TRAP_TOP)
