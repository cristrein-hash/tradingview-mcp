#!/usr/bin/env python3
"""PACOTES CEGOS FOCADOS (2a rodada direcionada) — Cluster 1 continuation/fuel reread + Cluster 2 error-only review.
NAO reescreve nada anterior (output em dirs novos). VA REAL da infra existente (F6 + svp_bars, validada 7f3c852),
backbone causal. Inclui perguntas vivas da rodada. Sem outcome (leak-check estrito). NAO re-deriva.
Saidas: results/cluster1_continuation_fuel_reread/ + results/cluster2_error_only_review/. Verified at: 2026-06-23."""
import json, os, re, sys, csv, bisect

D = "results"
BACK = {int(json.loads(l)["bar_idx"]): json.loads(l) for l in open(f"{D}/l2_bpt_raw_backbone_episodes.jsonl")}
IND = {int(json.loads(l)["bar_idx"]): json.loads(l) for l in open(f"{D}/l2_bpt_raw_indicator_events.jsonl")}
F6 = {int(r["bar_idx"]): r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_path_features_276.csv")) if r.get("bar_idx")}
FX = [json.loads(l) for l in open("repro_recovery/raw_features_2020_2026.jsonl")]
SB = {}
for _l in open("repro_recovery/svp_bars.jsonl"):
    if '"vp"' in _l:
        _r = json.loads(_l); SB[int(_r["time"])] = _r["vp"]
SBT = sorted(SB)

# FASE 2 — escopos
C1_PRIM = [4918, 4926, 8878, 8940, 6887]
C1_CTX = [1661, 5701, 7426, 8923]
C2 = [5627, 1522, 3825, 3929, 3949, 4401]

C1_Q = [
    "PERGUNTA VIVA (Cluster 1 continuation/fuel): quando dois trades sao irmaos estruturais / continuacao de",
    "movimento legitimo e ha VA/acceptance construtiva, o que faz o SEGUNDO parecer perigoso? Como distinguir",
    "supply-as-WALL de supply-BEING-CONSUMED sem criar regra de gate?",
    "Subperguntas: 4926 e erro real, exception de continuacao, ou HONEST_RESIDUAL? dist_poc grande em bull/markup =",
    "expansao saudavel ou exaustao? ACCEPTING_ABOVE_VALUE muda a leitura de supply proxima? Supply proxima e parede",
    "ou alvo/combustivel? O Reader trata o 2o impulso como trade isolado? Continuacao estrutural deveria ter",
    "prioridade interpretativa sobre supply-wall?",
]
C2_Q = [
    "PERGUNTA VIVA (Cluster 2 error-only): os erros restantes sao residuo honesto, falta de variavel, ou a MESMA",
    "fraqueza de continuation/fuel do Cluster 1? Subperguntas: IN_VALUE e ambiguo ou ha subestrutura que separa?",
    "below/in-POC pode ser BASE em vez de armadilha-bear? entry-red-bar warning sobrevive com VA real?",
    "compressao-que-DESENVOLVE vs washout-que-DESENVOLVE precisam ser separados? O que diferencia wall REAL de",
    "combustivel ACUMULADO dentro do value? As refutacoes restantes tem variavel comum?",
]


def va_block(b):
    r = F6.get(b, {}); et = int(FX[b]["ts_epoch"]); k = bisect.bisect_right(SBT, et) - 1
    vp = SB[SBT[k]] if k >= 0 else None
    lv = f"POC={round(vp[0],2)} VAH={round(vp[1],2)} VAL={round(vp[2],2)}" if vp else "n/d"
    return (f"VALUE-AREA REAL (RAW, validada 7f3c852): svp_state={r.get('f6_svp_state')} dist_poc={r.get('f6_dist_poc_atr')}ATR "
            f"above_value={r.get('f6_above_value')} below_value={r.get('f6_below_value')} | {lv}")


def ind_summary(b):
    e = IND.get(b, {})
    nas = [x for x in (e.get("nas_events_recent") or []) if x.get("in_current_era")]
    smc = [x for x in (e.get("smc_events_recent") or []) if x.get("in_current_era")]
    bub = e.get("bubble_cluster_summary") or {}; div = e.get("rsi_divergence_events") or {}
    return (f"NAS(RAW)={[x['text'] for x in nas][:5]} | SMC(RAW)={[x['text'] for x in smc][:5]} | "
            f"bubbles sell_mL={bub.get('sell_mL')} buy_mL={bub.get('buy_mL')} | RSI={e.get('rsi_value')} div={list(div.keys()) or 'nenhuma'}")


def episode_md(b, a):
    bk = BACK.get(b, {}); sd = bk.get("supply_demand_raw_mapped", {}); rg = bk.get("regime_raw_mapped", {})
    a("\n" + "=" * 88); a(f"## EPISODIO {b} ({bk.get('timestamp','')})")
    a(f"- regime (RAW causal): weekly_slope={rg.get('weekly_slope')} cascade={rg.get('cascade_score')} macro_broken={rg.get('macro_broken')} v3={rg.get('v3_state')}")
    a(f"- supply/demand (RAW Custom OB causal): sup_cat={sd.get('sup_cat')} clean_sky={sd.get('clean_sky')} dist_supply={sd.get('dist_supply_atr')}ATR dist_demand={sd.get('dist_demand_atr')}ATR")
    a(f"- {va_block(b)}")
    a(f"- anchor causal={bk.get('causal_window_ends_at_entry')} exato={bk.get('anchor_exact')} warnings={bk.get('warnings')}")
    a(f"- forma (RAW OHLC, ultimas 12 barras ate entry):")
    for bar in (bk.get("ohlcv_window") or [])[-12:]:
        a(f"    O{bar.get('o')} H{bar.get('h')} L{bar.get('l')} C{bar.get('c')}")
    a(f"- indicadores (RAW): {ind_summary(b)}")


def emit(title, fname, prim, ctx, questions, blocked_note):
    L = []; a = L.append
    a(f"# PACOTE CEGO FOCADO — {title}\n")
    a("> LEITURA CEGA, 100% RAW (DERIVED_FROM_RAW_WITH_MAPPING onde aplicavel), backbone CAUSAL, VALUE-AREA REAL.")
    a("> VA = EVIDENCIA de leitura, NAO decisao. TPO != VA. SEM resultado/R/futuro pos-entry. NAO classifique")
    a("> TAKE/SKIP, score, gate. Responda as PERGUNTAS VIVAS abaixo lendo cada episodio multi-fatorialmente.\n")
    a("### " + " ".join(questions) + "\n")
    a(f"### Campos ainda bloqueados/limitados: {blocked_note}\n")
    a("## Source mapping: regime/supply-demand/VA = DERIVED_FROM_RAW_WITH_MAPPING (validados); OHLC/indicadores = RAW_ORIGINAL_OK.\n")
    a("## EPISODIOS PRIMARIOS")
    for b in prim: episode_md(b, a)
    if ctx:
        a("\n" + "#" * 90); a("# CONTEXTO SECUNDARIO (apoio, mesma rodada)")
        for b in ctx: episode_md(b, a)
    text = "\n".join(L)
    OUTD = os.path.join(D, fname); os.makedirs(OUTD, exist_ok=True)
    FORB = ["mfe", "runner", "trap", "winner", "loser", "_audit", "outcome", "monument"]
    rmult = re.findall(r"\b\d+(?:\.\d+)?\s*r\b", text.lower())
    hits = [w for w in FORB if w in text.lower()]
    if hits or rmult:
        print(f"LEAK CHECK FALHOU em {fname}: {hits} {rmult[:5]}"); sys.exit(1)
    open(os.path.join(OUTD, "reading_packet_BLIND.md"), "w").write(text)
    allb = prim + ctx
    rep = [f"SOURCE GATE REPORT — {fname}", f"episodios: {len(allb)} (prim {len(prim)} + ctx {len(ctx)}) | leak-check PASS",
           "VA real (f6_svp_state/dist_poc + POC/VAH/VAL svp_bars, validada 7f3c852); backbone causal; sem outcome/R."]
    open(os.path.join(OUTD, "source_gate_report.txt"), "w").write("\n".join(rep) + "\n")
    entry = {"input_id": fname, "cluster_id": fname, "input_path": f"{OUTD}/reading_packet_BLIND.md",
             "created_by_script": "l2_bpt_reading_packet_focused.py", "source_packet_type": "RAW_CLEAN_FOCUSED_REREAD",
             "allowed_for_reader": "YES", "source_gate_required": "YES", "source_mapping_status": "RAW_CLEAN_ALLOWED",
             "contains_outcome": "NO", "contains_blocked_fields": "NO", "status": "RAW_CLEAN_ALLOWED",
             "episodes": allb, "notes": "2a rodada direcionada com VA real; sem outcome"}
    json.dump(entry, open(os.path.join(OUTD, "reader_input_manifest_entry.json"), "w"), indent=2, ensure_ascii=False)
    print(f"OK {fname}: {len(allb)} episodios -> {OUTD}/ (leak-check PASS)")


emit("Cluster 1 Continuation/Fuel Reread", "cluster1_continuation_fuel_reread", C1_PRIM, C1_CTX, C1_Q,
     "compressao-sob-supply nos IN_VALUE (eixo aberto); segunda-perna estrutural nao instrumentada explicitamente")
emit("Cluster 2 Error-Only Review", "cluster2_error_only_review", C2, [], C2_Q,
     "subestrutura intra-IN_VALUE; demanda-floor distante em alguns casos")
print("Pacotes cegos focados gerados. VA real; sem outcome; perguntas vivas embutidas.")
