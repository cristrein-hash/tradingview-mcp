#!/usr/bin/env python3
"""BE-após-1R PATH-ACCURATE na L2/BPT (mesma fonte frozen=RAW, mesmo SL estrutural e stop-first do sim canônico
reconstruct_l2_bpt_outcomes_uncapped.py). BE = let-run com SL movido p/ breakeven quando high atinge +1R.
Compara letrun-static / vstair / BE-após-1R: WR, streak(loss<0; BE quebra), sumR, DD. Full 276 + overlap 2024-05+.
Roda de dentro de v1/ (paths relativos)."""
import json,csv,datetime as dt
D="results"; RR="repro_recovery"
frozen=[json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
N=len(frozen); H=[r['high'] for r in frozen]; L=[r['low'] for r in frozen]; C=[r['close'] for r in frozen]
ATR=[None]*N; trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
outc={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
pk={int(json.loads(l)['bar_idx']):json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
RW=6; R_FLOOR=0.3; R_CEIL=1.5
def structural_sl(i,p,atr):
    lo=min(L[max(0,i-RW+1):i+1]); sl=lo-0.1*atr; risk=p-sl
    if risk<=0: return None,None
    if risk<R_FLOOR*atr: sl=p-R_FLOOR*atr; risk=R_FLOOR*atr
    if risk>R_CEIL*atr: sl=p-R_CEIL*atr; risk=R_CEIL*atr
    return sl,risk
def walk(i,p,sl,risk,HZ):
    """retorna letrun-static, vstair-trailing, e BE-após-1R (path-accurate, stop-first)."""
    end=min(i+HZ,N-1); stopped=None; lock=-1.0; peakR=0.0; vstair_exit=None
    be=False; be_exit=None
    for j in range(i+1,end+1):
        # --- BE-após-1R: stop efetivo = entry se armado, senão SL original (stop-first) ---
        be_stop = p if be else sl
        if be_exit is None and L[j]<=be_stop: be_exit=(be_stop-p)/risk
        # --- V-stair trailing ---
        eff_stop=max(sl, p+lock*risk)
        if vstair_exit is None and L[j]<=eff_stop: vstair_exit=(eff_stop-p)/risk
        # --- let-run static: SL original ---
        if L[j]<=sl and stopped is None:
            stopped=j
            if vstair_exit is None: vstair_exit=-1.0
            if be_exit is None: be_exit=-1.0
            break
        highR=(H[j]-p)/risk; peakR=max(peakR,highR)
        if highR>=1.0: be=True            # arma BE p/ próximas barras
        for trig,lk in [(2,0),(5,2),(8,5),(12,8),(16,12),(20,16)]:
            if peakR>=trig and lk>lock: lock=float(lk)
    letrun=-1.0 if stopped is not None else (C[end]-p)/risk
    vstair=vstair_exit if vstair_exit is not None else (C[end]-p)/risk
    bex=be_exit if be_exit is not None else (C[end]-p)/risk
    return round(letrun,2),round(vstair,2),round(bex,2)
rows=[]
for bi in sorted(outc):
    p=C[bi]; atr=ATR[bi]
    if not atr: continue
    sl,risk=structural_sl(bi,p,atr)
    if sl is None: continue
    lr,vs,be=walk(bi,p,sl,risk,120)
    rows.append((bi,pk[bi]['datetime'][:10],lr,vs,be))
def panel(R):
    n=len(R); sm=sum(R); w=sum(1 for x in R if x>0); z=sum(1 for x in R if x==0)
    eq=pk2=dd=0
    for x in R: eq+=x; pk2=max(pk2,eq); dd=min(dd,eq-pk2)
    mL=cl=0
    for x in R:
        if x<0: cl+=1
        else: cl=0
        mL=max(mL,cl)
    return n,round(100*w/n,1),round(sm,1),round(sm/n,3),round(dd,1),mL,z
def report(rs,tag):
    print(f"\n=== {tag} (N={len(rs)}) ===")
    print(f"{'régua':<16}{'WR':>6}{'sumR':>8}{'avgR':>7}{'DD':>7}{'maxLoss':>8}{'BE/scr':>7}")
    for name,idx in (("letrun120",2),("vstair120",3),("BE_apos1R",4)):
        R=[r[idx] for r in rs]; n,wr,sm,av,dd,mL,z=panel(R)
        print(f"{name:<16}{wr:>5}%{sm:>8}{av:>7}{dd:>7}{mL:>8}{z:>7}")
report(rows,"FULL 276")
OVL=dt.datetime(2024,5,24,tzinfo=dt.timezone.utc).timestamp()
ov=[r for r in rows if dt.datetime.strptime(r[1],"%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp()>=OVL]
report(ov,"OVERLAP 2024-05+")
