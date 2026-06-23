#!/usr/bin/env python3
"""RAW-CLEAN PACKET COM VALUE-AREA REAL — re-le Clusters 1/2 incluindo a VA de volume (POC/VAH/VAL) que estava
DISPONIVEL o tempo todo (erro corrigido em c1b24cf; ver reference_svp_value_area_provenance). NAO re-deriva: le a
VA da infra EXISTENTE e validada — F6 (results/l2_bpt_dspa_path_features_276.csv: f6_svp_state/f6_dist_poc_atr/
f6_above_value/f6_below_value) + niveis POC/VAH/VAL de repro_recovery/svp_bars.jsonl (as-of-entry). Backbone causal
(anchor as-of por timestamp real). Output _withva (NAO sobrescreve _postfix sem-VA, que vira histórico). Sem outcome
(leak-check). Saida: results/raw_rebuild_cluster{1,2}_withva/. Verified at: 2026-06-23."""
import json, os, re, sys, csv, bisect

D = "results"
BACK = {int(json.loads(l)["bar_idx"]): json.loads(l) for l in open(f"{D}/l2_bpt_raw_backbone_episodes.jsonl")}
IND = {int(json.loads(l)["bar_idx"]): json.loads(l) for l in open(f"{D}/l2_bpt_raw_indicator_events.jsonl")}
F6 = {int(r["bar_idx"]): r for r in csv.DictReader(open(f"{D}/l2_bpt_dspa_path_features_276.csv")) if r.get("bar_idx")}
FX = [json.loads(l) for l in open("repro_recovery/raw_features_2020_2026.jsonl")]
SB = {}
for _line in open("repro_recovery/svp_bars.jsonl"):
    if '"vp"' not in _line: continue
    _r = json.loads(_line); SB[int(_r["time"])] = _r["vp"]
SBT = sorted(SB)

CL1 = [("cluster 3a (superficie identica; discriminar pelo contexto causal + VALUE-AREA real)",
        [4918, 1661, 5701, 6887, 7426, 8878, 8923, 8940, 4926])]
CL2 = [("A. macro negativo + CLEAN SKY", [5826, 1623]),
       ("B. macro negativo + SUPPLY PROXIMO", [4401, 3825]),
       ("C. macro negativo + FLUSH sob supply", [1522, 1873, 5627, 1775]),
       ("D. macro negativo EXTREMO", [3949, 3929])]


def va_levels(b):
    et = int(FX[b]["ts_epoch"]); k = bisect.bisect_right(SBT, et) - 1
    if k < 0: return None
    vp = SB[SBT[k]]; exact = (SBT[k] == et)
    return {"poc": round(vp[0], 2), "vah": round(vp[1], 2), "val": round(vp[2], 2), "asof_exact": exact}


def va_summary(b):
    r = F6.get(b, {}); lv = va_levels(b)
    st = r.get("f6_svp_state"); dp = r.get("f6_dist_poc_atr")
    lvtxt = f"POC={lv['poc']} VAH={lv['vah']} VAL={lv['val']}" if lv else "niveis n/d"
    return (f"VALUE-AREA REAL (RAW, validada 7f3c852): svp_state={st} dist_poc={dp}ATR | {lvtxt} | "
            f"close {'ACIMA da VA' if st=='ACCEPTING_ABOVE_VALUE' else 'ABAIXO/rejeitado' if st=='BELOW_VALUE_REJECTED' else 'DENTRO da VA'}")


def ind_summary(b):
    e = IND.get(b, {})
    nas = [x for x in (e.get("nas_events_recent") or []) if x.get("in_current_era")]
    smc = [x for x in (e.get("smc_events_recent") or []) if x.get("in_current_era")]
    bub = e.get("bubble_cluster_summary") or {}; div = e.get("rsi_divergence_events") or {}
    return (f"NAS(RAW)={[x['text'] for x in nas][:5]} | SMC(RAW)={[x['text'] for x in smc][:5]} | "
            f"bubbles sell_mL={bub.get('sell_mL')} buy_mL={bub.get('buy_mL')} | RSI={e.get('rsi_value')} div={list(div.keys()) or 'nenhuma'}")


def emit(members_flat, title, fname):
    L = []; a = L.append
    a(f"# PACOTE DE LEITURA RAW-CLEAN COM VALUE-AREA REAL — {title}\n")
    a("> LEITURA CEGA, 100% RAW, backbone CAUSAL + **VALUE-AREA DE VOLUME REAL** (POC/VAH/VAL as-of-bar, de")
    a("> session_vp via svp_bars.jsonl/DSPA F6, validada causal commit 7f3c852). Esta e a base que ANTES rodou")
    a("> SEM a VA (pacote _postfix) por engano de fonte. svp_state = ACCEPTING_ABOVE_VALUE / IN_VALUE /")
    a("> BELOW_VALUE_REJECTED. SEM resultado/R/futuro pos-entry. NAO classifique TAKE/SKIP. Leia o EPISODIO.\n")
    a("## Contexto (regime RAW + supply/demand Custom OB causal + VALUE-AREA real)")
    a("| sub | bar | data | weekly | casc | sup_cat | distSup | svp_state | dist_poc | tpo_acc |")
    a("|---|---|---|---|---|---|---|---|---|---|")
    for sub, members in members_flat:
        for b in members:
            bk = BACK.get(b, {}); sd = bk.get("supply_demand_raw_mapped", {}); rg = bk.get("regime_raw_mapped", {})
            wk = rg.get("weekly_slope"); wk = round(wk, 2) if isinstance(wk, (int, float)) else wk
            r = F6.get(b, {})
            a(f"| {sub[0]} | {b} | {bk.get('timestamp','')[:10]} | {wk} | {rg.get('cascade_score')} | "
              f"{sd.get('sup_cat')} | {sd.get('dist_supply_atr')} | {r.get('f6_svp_state')} | {r.get('f6_dist_poc_atr')} | {bk.get('tpo_acceptance')} |")
    for sub, members in members_flat:
        a("\n" + "#" * 90); a(f"# SUB-BLOCO {sub}\n")
        for b in members:
            bk = BACK.get(b, {}); sd = bk.get("supply_demand_raw_mapped", {}); rg = bk.get("regime_raw_mapped", {})
            a("\n" + "=" * 88); a(f"## EPISODIO {b} ({bk.get('timestamp','')})")
            a(f"\n### Camada 1 backbone (RAW causal)")
            a(f"- regime: weekly_slope={rg.get('weekly_slope')} cascade={rg.get('cascade_score')} macro_broken={rg.get('macro_broken')} v3={rg.get('v3_state')}")
            a(f"- supply/demand (RAW Custom OB causal): sup_cat={sd.get('sup_cat')} clean_sky={sd.get('clean_sky')} dist_supply={sd.get('dist_supply_atr')}ATR dist_demand={sd.get('dist_demand_atr')}ATR")
            a(f"- {va_summary(b)}")
            a(f"- anchor: causal={bk.get('causal_window_ends_at_entry')} exato={bk.get('anchor_exact')} warnings={bk.get('warnings')}")
            a(f"\n### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)")
            for bar in (bk.get("ohlcv_window") or [])[-12:]:
                a(f"    O{bar.get('o')} H{bar.get('h')} L{bar.get('l')} C{bar.get('c')}")
            a(f"\n### Indicadores (RAW): {ind_summary(b)}")
    text = "\n".join(L)
    OUTD = os.path.join(D, fname); os.makedirs(OUTD, exist_ok=True)
    FORB = ["mfe", "runner", "trap", "winner", "loser", "_audit", "outcome", "monument"]
    rmult = re.findall(r"\b\d+(?:\.\d+)?\s*r\b", text.lower())
    hits = [w for w in FORB if w in text.lower()]
    if hits or rmult:
        print(f"LEAK CHECK FALHOU em {fname}: {hits} {rmult[:5]}"); sys.exit(1)
    open(os.path.join(OUTD, "reading_packet_RAW_CLEAN.md"), "w").write(text)
    allb = sorted({b for _, ms in members_flat for b in ms})
    rep = [f"SOURCE GATE REPORT — {fname} (com VALUE-AREA real)",
           f"episodios: {len(allb)} | leak-check: PASS | backbone causal",
           "VA real: f6_svp_state/f6_dist_poc_atr (DSPA F6) + POC/VAH/VAL (svp_bars.jsonl), validada 7f3c852",
           "POC/VAL/VAH = DERIVED_FROM_RAW_WITH_MAPPING (NAO mais blocked); sem outcome/R."]
    open(os.path.join(OUTD, "source_gate_report.txt"), "w").write("\n".join(rep) + "\n")
    entry = {"input_id": fname, "cluster_id": fname.replace("raw_rebuild_", "").replace("_withva", ""),
             "input_path": f"{OUTD}/reading_packet_RAW_CLEAN.md", "created_by_script": "l2_bpt_reading_packet_withva.py",
             "source_packet_type": "RAW_CLEAN_WITH_VALUE_AREA", "allowed_for_reader": "YES", "source_gate_required": "YES",
             "source_mapping_status": "RAW_CLEAN_ALLOWED", "contains_outcome": "NO", "contains_blocked_fields": "NO",
             "status": "RAW_CLEAN_ALLOWED", "episodes": allb, "notes": "VA real incluida; backbone causal; supersede _postfix (sem-VA)"}
    json.dump(entry, open(os.path.join(OUTD, "reader_input_manifest_entry.json"), "w"), indent=2, ensure_ascii=False)
    print(f"OK {fname}: {len(allb)} episodios (VA real) -> {OUTD}/ (leak-check PASS)")


emit(CL1, "Cluster 1 — RAW-clean COM VALUE-AREA real", "raw_rebuild_cluster1_withva")
emit(CL2, "Cluster 2 — RAW-clean COM VALUE-AREA real", "raw_rebuild_cluster2_withva")
print("Pacotes RAW-clean COM VA real gerados. POC/VAL/VAH real (validada 7f3c852); sem outcome.")
