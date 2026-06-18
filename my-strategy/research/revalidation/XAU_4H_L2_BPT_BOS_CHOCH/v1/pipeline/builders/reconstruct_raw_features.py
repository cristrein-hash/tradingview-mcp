#!/usr/bin/env python3
"""RECONSTRUÇÃO do frozen builder (extract_raw_features.py perdido) sob FIDELITY GATE.
Regras deduzidas empiricamente do artefato de referência (SHA 9fac96b9, 9880 bars):
  - bar set = bars FECHADOS vistos no buffer ohlcv (primeira ocorrência com high>low).
  - open/high/low/close/volume = do bar FECHADO no buffer.
  - rsi = RSI do snapshot onde o bar é CORRENTE (study_values 'Relative Strength Index'.RSI).
  - bubbles_recent = acúmulo de pine_shapes_bubbles[].activations (plots 0/2/4/6/8/10; POC plot_12 excluído),
    bars_ago = índice-global(bar) - índice-global(activation), janela 0..60, ordenado por time.
  - nas_recent/smc_recent = labels do snapshot-corrente (text,x,price) do detector NAS / Smart Money.
Determinístico. Não-SLIM (campos brutos). Parametrizado por --gz (1+ arquivos) e --out.
USO p/ FIDELITY GATE: rodar nos gz 2020-2026 e comparar contra raw_features_2020_2026.jsonl.
"""
import argparse, gzip, json, sys
from pathlib import Path

def load_snapshots(gz_paths):
    """Itera snapshots em ordem; yield dict por snapshot."""
    for gz in gz_paths:
        op = gzip.open if str(gz).endswith('.gz') else open
        with op(gz, 'rt') as f:
            for line in f:
                line=line.strip()
                if not line: continue
                try: d=json.loads(line)
                except: continue
                yield d

def build(gz_paths):
    ohlc={}           # time -> (o,h,l,c,vol)  (primeira ocorrência fechada h>l)
    rsi_by_cur={}     # current_time -> (forming_range, rsi)  -> mantém o snapshot mais formado
    nas_by_cur={}     # current_time -> [{text,x,price}]  (x<=30, recente)
    smc_by_cur={}     # current_time -> [{text,x,price}]  (x<=30)
    acts={}           # (time,plot_id) -> True  (activation deduped)
    BUB_PLOTS={'plot_0','plot_2','plot_4','plot_6','plot_8','plot_10'}
    NAS_X_WINDOW=30   # nas_recent/smc_recent = labels com x<=30 (deduzido do ref)
    for d in load_snapshots(gz_paths):
        ov=d.get('ohlcv') or []
        if not ov: continue
        cur=ov[-1]['time']
        fb=ov[-1]; frange=(fb.get('high') or 0)-(fb.get('low') or 0)  # quão formado está o bar corrente
        # OHLC: bars fechados no buffer (todos menos o forming ov[-1])
        for b in ov[:-1]:
            t=b['time']
            if t not in ohlc and b.get('high') is not None and b.get('low') is not None and b['high']>b['low']:
                ohlc[t]=(b['open'],b['high'],b['low'],b['close'],b.get('volume'))
        # RSI do snapshot corrente — manter o do snapshot mais formado (maior range do forming bar)
        for s in (d.get('study_values') or []):
            if 'Relative Strength' in (s.get('name') or ''):
                try:
                    rv=round(float(str(s['values'].get('RSI')).replace(',','')),2)
                    prev=rsi_by_cur.get(cur)
                    if prev is None or frange>=prev[0]: rsi_by_cur[cur]=(frange,rv)
                except: pass
                break
        # NAS / SMC labels do snapshot corrente (x<=30, recente)
        for lab in (d.get('pine_labels') or []):
            nm=(lab.get('name') or '')
            arr=lab.get('all_labels') or lab.get('labels') or []
            rec=[{'text':x.get('text'),'x':x.get('x'),'price':x.get('price')} for x in arr if (x.get('x') is not None and x.get('x')<=NAS_X_WINDOW)]
            if 'NAS' in nm.upper(): nas_by_cur[cur]=rec
            elif 'Smart Money' in nm: smc_by_cur[cur]=rec
        # activations (bubbles)
        for sb in (d.get('pine_shapes_bubbles') or []):
            for a in (sb.get('activations') or []):
                t=a.get('time')
                for pid,cnt in (a.get('shapes') or {}).items():
                    if pid in BUB_PLOTS and cnt and t is not None:
                        acts[(t,pid)]=True
    # ordenação global de barras (todos os times com OHLC)
    bars=sorted(ohlc)
    gidx={t:i for i,t in enumerate(bars)}
    # activations -> por bar emitir bubbles dentro da janela
    acts_by_gidx={}  # gidx do activation -> list de (plot_id,time)
    for (t,pid) in acts:
        if t in gidx: acts_by_gidx.setdefault(gidx[t],[]).append((pid,t))
    out=[]
    for t in bars:
        gi=gidx[t]; o,h,l,c,v=ohlc[t]
        bub=[]
        lo=gi-60
        for ai in range(lo, gi+1):
            for (pid,at) in acts_by_gidx.get(ai,[]):
                bub.append({'plot_id':pid,'bars_ago':gi-ai,'time':at})
        bub.sort(key=lambda x:(x['time'],x['plot_id']))
        _rsi=rsi_by_cur.get(t)
        out.append({'ts_epoch':t,'open':o,'high':h,'low':l,'close':c,'volume':v,
                    'rsi':(_rsi[1] if _rsi is not None else None),
                    'bubbles_recent':bub,
                    'nas_recent':nas_by_cur.get(t,[]),
                    'smc_recent':smc_by_cur.get(t,[])})
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--gz',nargs='+',required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    rows=build(a.gz)
    with open(a.out,'w') as f:
        for r in rows: f.write(json.dumps(r)+'\n')
    print(f"wrote {len(rows)} bars -> {a.out}")
