#!/usr/bin/env python3
"""RAW-CLEAN BLIND PACKET BUILDER — pacote cego do Reader Vivo SO com campos RAW_ORIGINAL_OK / DERIVED_FROM_RAW.
Consome: results/l2_bpt_raw_backbone_episodes.jsonl (Camada-1 RAW) + results/l2_bpt_raw_indicator_events.jsonl (RAW).
NAO consome derivado (raw_features_2020_2026/qual_packets/dossier). Campos bloqueados (SVP/acceptance) aparecem como
BLOCKED_UNMAPPED, nunca valor derivado. SEM outcome/R/MFE/winner/loser/runner/trap (leak-check estrito, para se falhar).
Saida: results/raw_rebuild_cluster1/reading_packet_RAW_CLEAN.md + cluster2 + reader_input_manifest_entry.json."""
import json, os, re, sys

D = "results"
BACK = {int(json.loads(l)["bar_idx"]): json.loads(l) for l in open(f"{D}/l2_bpt_raw_backbone_episodes.jsonl")}
IND = {int(json.loads(l)["bar_idx"]): json.loads(l) for l in open(f"{D}/l2_bpt_raw_indicator_events.jsonl")}

CL1 = [("cluster 3a (superficie identica; discriminar pelo contexto)",
        [4918, 1661, 5701, 6887, 7426, 8878, 8923, 8940, 4926])]
CL2 = [("A. macro negativo + CLEAN SKY", [5826, 1623]),
       ("B. macro negativo + SUPPLY PROXIMO", [4401, 3825]),
       ("C. macro negativo + FLUSH sob supply", [1522, 1873, 5627, 1775]),
       ("D. macro negativo EXTREMO", [3949, 3929])]

def ind_summary(b):
    e = IND.get(b, {})
    nas = [x for x in (e.get("nas_events_recent") or []) if x.get("in_current_era")]
    smc = [x for x in (e.get("smc_events_recent") or []) if x.get("in_current_era")]
    bub = e.get("bubble_cluster_summary") or {}; div = e.get("rsi_divergence_events") or {}
    return (f"NAS(RAW)={[(x['text']) for x in nas][:5]} | SMC(RAW)={[(x['text']) for x in smc][:5]} | "
            f"bubbles sell_mL={bub.get('sell_mL')} buy_mL={bub.get('buy_mL')} | RSI={e.get('rsi_value')} div={list(div.keys()) or 'nenhuma'}")

def emit(members_flat, title, fname):
    L = []; a = L.append
    a(f"# PACOTE DE LEITURA RAW-CLEAN — {title}\n")
    a("> LEITURA CEGA, FONTE 100% RAW ORIGINAL. Camada-1 (forma/supply-demand/regime) reconstruida do RAW;")
    a("> indicadores (NAS/SMC/bubbles/RSI) do RAW; SVP/acceptance = BLOCKED_UNMAPPED (nao computado, nao inventado).")
    a("> SEM resultado/R/futuro pos-entry. NAO classifique TAKE/SKIP. Leia o EPISODIO; campos BLOCKED limitam a leitura — declare isso.\n")
    a("## Contexto (regime RAW-derived price; supply/demand RAW Custom OB)")
    a("| sub | bar | data | weekly | cascade | sup_cat(RAW) | clean_sky | distSup | distDem |")
    a("|---|---|---|---|---|---|---|---|---|")
    for sub, members in members_flat:
        for b in members:
            bk = BACK.get(b, {}); sd = bk.get("supply_demand_raw_mapped", {}); rg = bk.get("regime_raw_mapped", {})
            wk = rg.get("weekly_slope"); wk = round(wk, 2) if isinstance(wk, (int, float)) else wk
            a(f"| {sub[0]} | {b} | {bk.get('timestamp','')[:10]} | {wk} | {rg.get('cascade_score')} | "
              f"{sd.get('sup_cat')} | {sd.get('clean_sky')} | {sd.get('dist_supply_atr')} | {sd.get('dist_demand_atr')} |")
    for sub, members in members_flat:
        a("\n" + "#" * 90); a(f"# SUB-BLOCO {sub}\n")
        for b in members:
            bk = BACK.get(b, {}); sd = bk.get("supply_demand_raw_mapped", {}); rg = bk.get("regime_raw_mapped", {})
            a("\n" + "=" * 88); a(f"## EPISODIO {b} ({bk.get('timestamp','')})")
            a(f"\n### Camada 1 backbone (RAW)")
            a(f"- regime (DERIVED_FROM_RAW price): weekly_slope={rg.get('weekly_slope')} cascade={rg.get('cascade_score')} "
              f"combined={rg.get('combined_score')} macro_broken={rg.get('macro_broken')} v3={rg.get('v3_state')} (fidelity={rg.get('_fidelity_close_vs_raw')})")
            a(f"- supply/demand (RAW Custom OB boxes): sup_cat={sd.get('sup_cat')} clean_sky={sd.get('clean_sky')} "
              f"has_overhead={sd.get('has_overhead')} dist_supply={sd.get('dist_supply_atr')}ATR dist_demand={sd.get('dist_demand_atr')}ATR")
            a(f"- SVP/POC/VAL/VAH/acceptance: **BLOCKED_UNMAPPED** (RAW tem itens VP brutos; VA nao computada — leia sem isso)")
            a(f"\n### Camada 0 forma (RAW OHLC, ultimas barras ate a entry)")
            for bar in (bk.get("ohlcv_window") or [])[-12:]:
                a(f"    O{bar.get('o')} H{bar.get('h')} L{bar.get('l')} C{bar.get('c')}")
            a(f"\n### Indicadores (RAW): {ind_summary(b)}")
    text = "\n".join(L)
    OUTD = os.path.join(D, fname)
    os.makedirs(OUTD, exist_ok=True)
    # leak-check estrito
    FORB = ["mfe", "runner", "trap", "winner", "loser", "_audit", "outcome", "monument"]
    rmult = re.findall(r"\b\d+(?:\.\d+)?\s*r\b", text.lower())
    hits = [w for w in FORB if w in text.lower()]
    if hits or rmult:
        print(f"LEAK CHECK FALHOU em {fname}: {hits} {rmult[:5]}"); sys.exit(1)
    with open(os.path.join(OUTD, "reading_packet_RAW_CLEAN.md"), "w") as f:
        f.write(text)
    allb = sorted({b for _, ms in members_flat for b in ms})
    entry = {"input_id": fname, "cluster_id": fname, "input_path": f"{OUTD}/reading_packet_RAW_CLEAN.md",
             "created_by_script": "l2_bpt_reading_packet_raw_clean.py", "source_packet_type": "RAW_CLEAN_BLIND",
             "allowed_for_reader": "YES", "source_gate_required": "YES", "source_mapping_status": "RAW_CLEAN",
             "contains_outcome": "NO", "contains_blocked_fields": "NO (SVP/acceptance marcados BLOCKED_UNMAPPED, sem valor)",
             "status": "RAW_CLEAN_ALLOWED", "episodes": allb,
             "notes": "Camada-1 RAW (supply/demand Custom OB + regime price) + indicadores RAW; SVP blocked"}
    json.dump(entry, open(os.path.join(OUTD, "reader_input_manifest_entry.json"), "w"), indent=2, ensure_ascii=False)
    print(f"OK {fname}: {len(allb)} episodios -> {OUTD}/reading_packet_RAW_CLEAN.md (leak-check PASS, RAW-clean)")

emit(CL1, "Cluster 1 (sosia 3a + continuacao 3b) — RAW-clean", "raw_rebuild_cluster1")
emit(CL2, "Cluster 2 (macro negativo) — RAW-clean", "raw_rebuild_cluster2")
print("Pacotes RAW-clean gerados. Fonte 100% RAW; SVP/acceptance BLOCKED_UNMAPPED; sem outcome.")
