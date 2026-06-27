"""Concentration / tail-dependence audit for rule: rsi>=48.01 AND disp4_atr<-0.898.
Companion to _verify_rsi_disp4.py (which does per-year/per-block/ex-top2)."""
import json, statistics

rows = [json.loads(l) for l in open('entry_dataset.jsonl')]
def R(r): return r.get('R_reclaim') or 0.0
def rule(r): return r['rsi'] >= 48.01 and r['disp4_atr'] < -0.898
sel = [r for r in rows if rule(r)]
Rs = [R(r) for r in sel]

big = [r for r in sel if R(r) >= 10]
print('n=', len(sel), 'avgR=', round(sum(Rs)/len(sel), 3))
print('runners R>=10:', len(big), [(r['block'], round(R(r), 1)) for r in big])
print('avgR capped@+5:', round(sum(min(R(r), 5) for r in sel)/len(sel), 3))
print('avgR capped@+3:', round(sum(min(R(r), 3) for r in sel)/len(sel), 3))
srt = sorted(Rs, reverse=True)
print('top5 R:', [round(x, 1) for x in srt[:5]])
print('sum top10:', round(sum(srt[:10]), 1), 'of', round(sum(Rs), 1),
      '=', round(sum(srt[:10])/sum(Rs)*100), '%')
bl = {}
for r in sel: bl.setdefault(r['block'], []).append(R(r))
ba = [sum(v)/len(v) for v in bl.values()]
print('block avgR: min', round(min(ba), 2), 'max', round(max(ba), 2),
      'std', round(statistics.pstdev(ba), 2), 'all positive:', all(x > 0 for x in ba))
