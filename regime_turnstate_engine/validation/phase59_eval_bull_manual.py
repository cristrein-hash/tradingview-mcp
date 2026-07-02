#!/usr/bin/env python3
"""Avalia os 10 bull-reteste com os SL/TP AJUSTADOS MANUALMENTE pelo Cris no chart (extraídos via MCP draw_get_properties).
Para cada: SL/TP novos (offsets em ticks→preço), R:R do setup, simula resultado (TP-first vs SL-first até exit_bar do Cris;
senão close), MFE (máx alcançado em R) e MAE (mín em R). Compara com o let-run original. custo 0.35 no R realizado."""
import io,contextlib,sys,bisect
from pathlib import Path
MT=0.01;COST=0.35
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def bar(t): return bisect.bisect_left(T,t)
# (id, entry_time, entry, SL_ticks, TP_ticks, exit_time, R_letrun_original)
TR=[
 ("B1",1679263200,1969.60,5853, 9483,1680501600,+0.13),
 ("B2",1681077600,1997.00,5428, 5830,1681884000,-1.35),
 ("B3",1698141600,1964.48,4706,31073,1700449200,+0.52),
 ("B4",1712570400,2327.38,2739, 9233,1713333600,-1.35),
 ("B5",1716372000,2410.54,5580, 2790,1717408800,-1.35),
 ("B6",1721340000,2426.15,14554,102690,1722492000,-1.35),
 ("B7",1730196000,2760.87,2953, 1476,1730383200,-1.35),
 ("B8",1738335600,2798.94,5460,64746,1739257200,+0.15),
 ("B9",1758520800,3723.23,5974,63629,1760940000,+8.65),
 ("B10",1768230000,4610.77,11576,94880,1769569200,-1.35),
]
print(f"{'#':4}{'entry':8}{'SL':8}{'TP':8}{'R:R':6}{'result':9}{'Rreal':7}{'MFE_R':7}{'MAE_R':7} exit")
for tag,et,entry,slt,tpt,xt,rlo in TR:
    sl=entry-slt*MT;tp=entry+tpt*MT;risk=entry-sl;rr=tpt/slt
    bi=bar(et);xe=min(bar(xt),n4-1);xe=max(xe,bi+1)
    res=None;rr_real=None
    mfe=mae=0
    for j in range(bi+1,xe+1):
        mfe=max(mfe,(H[j]-entry)/risk);mae=min(mae,(L[j]-entry)/risk)
        if L[j]<=sl: res="SL";rr_real=-1.0;break
        if H[j]>=tp: res="TP";rr_real=rr;break
    if res is None:
        res="close";rr_real=(C[xe]-entry)/risk
    open_flag=" (ABERTO/futuro)" if xt>T[n4-1] else ""
    print(f"{tag:4}{entry:8.1f}{sl:8.1f}{tp:8.1f}{rr:6.2f}{res:9}{rr_real-COST:+7.2f}{mfe:+7.2f}{mae:+7.2f} {res}{open_flag}")
print(f"\n(R:R = alvo/risco do setup do Cris; Rreal = resultado pós-custo; MFE/MAE = excursão máx favorável/adversa em R até o exit dele)")
