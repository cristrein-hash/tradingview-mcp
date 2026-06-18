#!/usr/bin/env python3
"""Builder do XAU_1D_bars.jsonl ({time,close}) — projeção do XAU_1D_ohlc.jsonl (build_1d_ohlc.py, versionado).
Determinístico. Reconstrução do builder perdido (low-risk). FIDELITY GATE vs referência preservada."""
import argparse,json
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--ohlc',required=True);ap.add_argument('--out',required=True)
    a=ap.parse_args()
    n=0
    with open(a.out,'w') as o:
        for l in open(a.ohlc):
            l=l.strip()
            if not l:continue
            d=json.loads(l);o.write(json.dumps({'time':d['time'],'close':d['close']})+'\n');n+=1
    print(f'wrote {n} -> {a.out}')
