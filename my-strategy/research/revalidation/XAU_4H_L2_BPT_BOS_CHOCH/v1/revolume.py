import json
from bisect import bisect_right
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')];TS=[r['ts_epoch'] for r in frozen]
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
svp={r['time']:r for r in (json.loads(l) for l in open('/tmp/svp_bars.jsonl'))}
def real_vc(i):
    vols=[(svp.get(TS[x]) or {}).get('vol') or 0 for x in range(max(0,i-50),i+1)]
    if len(vols)<51 or sum(vols[:-10])<=0: return None
    a=sum(vols[:-10])/(len(vols)-10); return round(max(vols[-10:])/a,2) if a else None
WIN={'E1','E13','E17','E27','E30','E40','E21','E23','E5'}
BEAR_WIN={'E1','E17'}; BEAR_TRAP={'E6','E7','E11','E36','E37'}
print("=== 1D-bear subset: REAL volume-climax ===")
for ep in ['E1','E17','E6','E7','E11','E36','E37']:
    g='WIN' if ep in BEAR_WIN else 'TRAP'
    print(f"  {ep:<4}{g:<6} real_volclmx={real_vc(geom[ep]['bar_idx'])}")
print("\n=== all winners real_volclmx ===")
for ep in sorted(WIN,key=lambda e:int(e[1:])):
    print(f"  {ep:<4} {real_vc(geom[ep]['bar_idx'])}")
