#!/usr/bin/env python3
"""N96 · FASE 1 (lista dos 13 cortados intra-BEAR) + FASE 2 (mapa corrigido dos 44 losers).
Research-only, RAW-first, reproduzivel. Reclassificacoes do Cris incorporadas (2026-07-08):
#55-60=C (distribuicao/topo range-bear, NAO range neutro) · #58=C · #80=D · #24,#32,#64,#77=gestao/nao-filtrar.
Fail-loud se N96 nao reproduz. Outputs: results/n96_intra_bear_cut_trades.csv + results/n96_loser_family_map_corrected.csv"""
import csv, json, sys, datetime as dt
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from n96_mtf_kit import HERE, FAM, famof
from agent_ctx_kit import ENTRIES
assert len(ENTRIES)==96 and sum(e["out"] for e in ENTRIES)==52, "FAIL-LOUD: N96 nao reproduz"
REG={int(k):v for k,v in json.load(open(HERE+"/results/n96_causal_regime.json")).items()}
rows=list(csv.DictReader(open(HERE+"/results/n96_exhaustive_mtf_features.csv")))
BYN={int(r["n"]):r for r in rows}; OUT={int(r["n"]):int(r["out"]) for r in rows}
TBYN={e["n"]:e["t"] for e in ENTRIES}
def g(r,k):
    try: return float(r.get(k))
    except: return None
STALE_1D=dt.datetime(2026,5,24).timestamp()

# ================= FASE 1: 13 cortados intra-BEAR =================
CUT=[n for n in sorted(BYN) if REG[n]=="BEAR" and (g(BYN[n],"1D_px_vs_ema") or -99)>=0]
f1=[]
for n in CUT:
    f1.append({
        "trade": f"#{n}", "timestamp": dt.datetime.utcfromtimestamp(TBYN[n]).strftime("%Y-%m-%d %H:%M"),
        "regime_v5_causal": REG[n],
        "1D_px_vs_ema": g(BYN[n],"1D_px_vs_ema"), "1D_ema_trend": g(BYN[n],"1D_ema_trend"), "1D_rsi": g(BYN[n],"1D_rsi"),
        "close_R": (3 if OUT[n]==1 else -1),          # 3:1 fixo (winner+3 / loser-1)
        "SB_net_R": "unavailable_N96",                 # N96 sem ledger de slippage
        "familia": famof(n),
        "motivo": "repique raso em BEAR (preco no/acima da EMA 1D = nao-capitulacao)",
        "CDR_gestao": famof(n),
        "resultado": ("WINNER" if OUT[n]==1 else "LOSER"),
        "stale_HTF": ("STALE" if TBYN[n]>=STALE_1D else "fresh"),
    })
assert sum(1 for r in f1 if r["resultado"]=="WINNER")==0, "FAIL-LOUD: filtro cortou winner"
with open(HERE+"/results/n96_intra_bear_cut_trades.csv","w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=list(f1[0])); w.writeheader(); w.writerows(f1)
print(f"FASE 1: {len(f1)} cortados | winners={sum(1 for r in f1 if r['resultado']=='WINNER')} losers={sum(1 for r in f1 if r['resultado']=='LOSER')} | stale={sum(1 for r in f1 if r['stale_HTF']=='STALE')}")
for r in f1: print(f"  {r['trade']:>4} {r['timestamp']}  reg={r['regime_v5_causal']}  1D_px_vs_ema={r['1D_px_vs_ema']:>6}  1D_rsi={r['1D_rsi']}  fam={r['familia']:<4} {r['resultado']} {r['stale_HTF']}")

# ================= FASE 2: mapa corrigido dos 44 losers =================
# reclassificacoes Cris ja refletidas em FAM (n96_mtf_kit): MGMT={24,32,64,77}; C inclui 55-60,58; D inclui 80.
NOTES={24:"BE em gestao humana (nao filtrar)",32:"entrada antecipada; certo era esperar demanda inferior (#33) = timing/gestao",
       64:"quase-winner recuperavel por gestao (nao filtrar)",77:"quase-winner recuperavel por gestao (nao filtrar)",
       55:"C distribuicao/topo range-bear",56:"C distribuicao/topo range-bear",57:"C distribuicao/topo range-bear",
       58:"C distribuicao/topo range-bear",59:"C distribuicao/topo range-bear",60:"C distribuicao/topo range-bear",
       80:"D bear ativo"}
losers=sorted(e["n"] for e in ENTRIES if e["out"]==0)
f2=[]
for n in losers:
    fam=famof(n)
    f2.append({"trade":f"#{n}","n":n,"familia":fam,"regime_v5_causal":REG[n],
               "cortado_intra_BEAR":("SIM" if n in CUT else "nao"),
               "nota_Cris":NOTES.get(n,"")})
with open(HERE+"/results/n96_loser_family_map_corrected.csv","w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=list(f2[0])); w.writeheader(); w.writerows(f2)
from collections import Counter
cnt=Counter(r["familia"] for r in f2)
print(f"\nFASE 2: mapa corrigido 44 losers -> {dict(cnt)}")
for fam in ("C","D","R","MGMT"):
    ns=[r["n"] for r in f2 if r["familia"]==fam]
    print(f"  {fam} [{len(ns)}]: {ns}")
# validacoes obrigatorias do Cris
for must,fam in [(55,"C"),(56,"C"),(57,"C"),(58,"C"),(59,"C"),(60,"C"),(80,"D"),(24,"MGMT"),(32,"MGMT"),(64,"MGMT"),(77,"MGMT")]:
    assert famof(must)==fam, f"FAIL: #{must} deveria ser {fam}, esta {famof(must)}"
print("  validacoes Cris (55-60=C,80=D,24/32/64/77=MGMT): OK")
print("\nsaved results/n96_intra_bear_cut_trades.csv + results/n96_loser_family_map_corrected.csv")
