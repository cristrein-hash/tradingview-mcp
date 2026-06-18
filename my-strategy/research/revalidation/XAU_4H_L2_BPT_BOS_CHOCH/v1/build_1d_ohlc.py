import json,sys
bars={}
for line in sys.stdin:
    try: d=json.loads(line)
    except: continue
    for b in (d.get('ohlcv') or []):
        if isinstance(b,dict) and all(k in b for k in('time','high','low','close')):
            bars[int(b['time'])]=(b['high'],b['low'],b['close'])
out=open('/tmp/XAU_1D_ohlc.jsonl','w')
for t in sorted(bars):
    h,l,c=bars[t]; out.write(json.dumps({"time":t,"high":h,"low":l,"close":c})+"\n")
out.close(); print("wrote",len(bars),"daily OHLC bars")
