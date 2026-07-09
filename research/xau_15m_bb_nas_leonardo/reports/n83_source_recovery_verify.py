#!/usr/bin/env python3
"""N83 SOURCE RECOVERY — verificação reprodutível da ponte PDF→repo.
PDF (Desktop, 2026-07-08, 'Sistema_Agentico_Trading_XAU_LONG_PT.pdf') reporta na tabela 'A SUITE
APROVADA': Markup-Demanda + Filtro Capitulação · 15M · trades '96 → 83' · acerto 62,7% · +125R.
Hipótese de recovery: N83 = N96 − 13 cortados pelo INTRA-BEAR CAPITULATION FILTER (SKIP se regime
BEAR-v5-causal E 1D_px_vs_ema >= 0). Este script prova mecanicamente a aritmética a partir das
fontes do repo (sem PDF como validação): base N96 (entry_engine_master json) + cut list (13 ids)
=> N83, W/L, WR, sumR@3R. Output: n83_source_recovery_verify_result.json."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent; RD=HERE.parent
BASE=RD/"results/entry_engine_master_20260707.json"
CUTL=RD/"results/n96_intra_bear_cut_list.json"
CUTC=RD/"results/n96_intra_bear_cut_trades.csv"
DOC=Path("/Users/cristrein/tradingview-mcp/docs/architecture/XAU_15M_N96_INTRA_BEAR_CAPITULATION_FILTER_20260708.md")
res={"pdf_claim":{"trades":"96 -> 83","wr":"62,7%","sumR":"+125"},
     "pdf_role":"provenance bridge ONLY (nao validacao)"}

# base N96 (markup)
rows=json.load(open(BASE))
mk=[r for r in rows if r.get("kind")=="MARKUP"]
res["base_N"]=len(mk)
res["base_W"]=sum(1 for r in mk if r.get("out")==1)
res["base_L"]=sum(1 for r in mk if r.get("out")==0)

# cut list (filtro intra-BEAR capitulation)
cl=json.load(open(CUTL)); cut=cl.get("cut_13") or []
res["cut_ids"]=cut; res["cut_n"]=len(cut)
# CSV: todos os 13 sao LOSER?
csv_lines=[l for l in open(CUTC).read().splitlines()[1:] if l.strip()]
res["cut_csv_rows"]=len(csv_lines)
res["cut_all_losers_csv"]=all(",LOSER," in l or l.endswith("LOSER,fresh") or ",LOSER" in l for l in csv_lines)

# HARDENING DA-1: checar os 13 ids contra o `out` da BASE (ids 1-based na ordem markup),
# nao confiar no CSV. Todos tem de ser out==0 (losers) na base.
res["cut_all_losers_base"]=all(mk[i-1].get("out")==0 for i in cut)

# HARDENING DA-2 (teste decisivo de nao-contaminacao): aplicar o PREDICADO cego aos 96
# (winners incluidos): regime BEAR-v5-causal E 1D_px_vs_ema>=0 => deve selecionar EXATAMENTE
# os 13 ids e ZERO winners. Fontes: n96_causal_regime.json + n96_exhaustive_mtf_features.csv.
REG=json.load(open(RD/"results/n96_causal_regime.json"))
import csv as _csv
px={}
with open(RD/"results/n96_exhaustive_mtf_features.csv") as f:
    for row in _csv.DictReader(f):
        try: px[int(row.get("trade") or row.get("id") or row.get("n"))]=float(row["1D_px_vs_ema"])
        except Exception: pass
def _reg(i):
    v=REG.get(str(i)) or REG.get(i)
    return v.get("regime") if isinstance(v,dict) else v
blind=[i for i in range(1,res["base_N"]+1)
       if _reg(i)=="BEAR" and (i in px) and px[i]>=0]
res["blind_predicate_selects"]=blind
res["blind_matches_cutlist"]=(sorted(blind)==sorted(cut))
res["blind_zero_winners"]=all(mk[i-1].get("out")==0 for i in blind)
# nota: gerador original usa `(g(...) or -99)>=0` -> valor 0.0 exato seria KEPT (falsy);
# nenhum trade tem 0.0 neste dataset (sem efeito), registrado como edge-case latente.
res["latent_edge_note"]="generator `or -99` trata 1D_px_vs_ema==0.0 como KEEP (falsy); 0 ocorrencias no dataset"

# aritmética N96 -> N83 (derivada da BASE, nao do doc)
N83=res["base_N"]-res["cut_n"]
W83=res["base_W"]-sum(1 for i in cut if mk[i-1].get("out")==1)   # winners cortados (esperado 0)
L83=res["base_L"]-sum(1 for i in cut if mk[i-1].get("out")==0)
res["derived"]={"N83":N83,"W":W83,"L":L83,
    "WR_pct":round(100*W83/N83,1),
    "sumR_3R":round(W83*3.0 - L83*1.0,1)}
res["match_pdf"]={
    "N_96_to_83": (res["base_N"]==96 and N83==83),
    "WR_62_7": (round(100*W83/N83,1)==62.7),
    "sumR_125": (round(W83*3.0-L83*1.0,1)==125.0)}
res["predicate"]={"name":"intra-BEAR capitulation filter",
    "rule":"SKIP se macro_regime==BEAR (v5 hour-causal) E 1D_px_vs_ema >= 0 (ultimo bar 1D FECHADO, ATR-norm); KEEP capitulacao funda; BULL/RANGE sem filtro",
    "fields":["macro_regime_v5_causal","1D_px_vs_ema"],
    "causal":"sim (regime hour-causal + 1D bar fechado; DA causalidade PASS)",
    "source_doc":str(DOC),
    "source_outputs":[str(CUTL),str(CUTC)],
    "status":"USER_APPROVED_NOT_PRODUCTION (Cris 2026-07-08) · PROFITABLE_BUT_FRAGILE (+4..+13R conforme detector; nunca citar +13 solto)",
    "nulls":"feature-search P=0.005 · within-bear P=0.001 · joint P=0.007",
    "caveats":"N pequeno; 11/13 cortes num unico bear (2026); HTF congela 2026-05-24"}
res["verdict"]=("SOURCE_RECOVERED" if (all(res["match_pdf"].values()) and res["cut_all_losers_base"]
                and res["blind_matches_cutlist"] and res["blind_zero_winners"]) else "MISMATCH")
(HERE/"n83_source_recovery_verify_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print(json.dumps(res,indent=2,ensure_ascii=False))
