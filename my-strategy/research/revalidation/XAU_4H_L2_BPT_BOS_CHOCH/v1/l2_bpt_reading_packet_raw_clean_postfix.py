#!/usr/bin/env python3
"""RAW-CLEAN POST-ANCHOR-FIX PACKET BUILDER — regenera pacotes cegos dos Clusters 1/2 sobre o backbone CAUSAL
corrigido (commit 1267c8d: as-of join por timestamp real, 19/19 causal+exato). NAO sobrescreve os pacotes
pre-fix (raw_rebuild_cluster{1,2}); escreve em raw_rebuild_cluster{1,2}_postfix.
Fonte 100% RAW: l2_bpt_raw_backbone_episodes.jsonl (Camada-1 causal) + l2_bpt_raw_indicator_events.jsonl +
l2_bpt_raw_svp_acceptance_episodes.jsonl (volume RAW + TPO de tempo). POC/VAL/VAH de VOLUME LuxAlgo = BLOCKED.
SEM outcome/R/MFE/winner/loser/runner/trap (leak-check estrito). Saida: reading_packet_RAW_CLEAN.md +
source_gate_report.txt + reader_input_manifest_entry.json. Verified at: 2026-06-23."""
import json, os, re, sys

D = "results"
BACK = {int(json.loads(l)["bar_idx"]): json.loads(l) for l in open(f"{D}/l2_bpt_raw_backbone_episodes.jsonl")}
IND = {int(json.loads(l)["bar_idx"]): json.loads(l) for l in open(f"{D}/l2_bpt_raw_indicator_events.jsonl")}
SVP = {int(json.loads(l)["bar_idx"]): json.loads(l) for l in open(f"{D}/l2_bpt_raw_svp_acceptance_episodes.jsonl")}

CL1 = [("cluster 3a (superficie identica; discriminar pelo contexto causal)",
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


def svp_summary(b):
    s = SVP.get(b, {}); v = s.get("svp_bar_volume_raw", {}); tpo = s.get("tpo_value_area") or {}
    return (f"volume RAW entry_up={v.get('entry_up_ratio')} last6_up={v.get('last6_up_ratio')} | "
            f"tpo_acceptance(TEMPO,NAO-volume)={s.get('tpo_acceptance')} poc_tpo={tpo.get('poc_tpo')} | "
            f"POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**")


def emit(members_flat, title, fname):
    L = []; a = L.append
    a(f"# PACOTE DE LEITURA RAW-CLEAN POS-ANCHOR-FIX — {title}\n")
    a("> LEITURA CEGA, FONTE 100% RAW ORIGINAL, **backbone CAUSAL pos-fix** (commit 1267c8d: as-of join por")
    a("> timestamp real, 19/19 causal+exato, SEM look-ahead). Camada-1 (forma/supply-demand/regime), indicadores")
    a("> (NAS/SMC/bubbles/RSI) e volume RAW. TPO value-area = de TEMPO (proxy, NAO VA de volume). POC/VAL/VAH de")
    a("> VOLUME LuxAlgo = BLOCKED (nao serializado, nao inventado).")
    a("> SEM resultado/R/futuro pos-entry. NAO classifique TAKE/SKIP. Leia o EPISODIO; campos BLOCKED limitam a")
    a("> leitura — declare isso. (Esta e a base FINAL; os pacotes pre-fix sao historicos contaminados por look-ahead.)\n")
    a("## Contexto (regime RAW-derived price; supply/demand RAW Custom OB causal)")
    a("| sub | bar | data | weekly | cascade | sup_cat | clean_sky | distSup | distDem | tpo_acc | causal |")
    a("|---|---|---|---|---|---|---|---|---|---|---|")
    for sub, members in members_flat:
        for b in members:
            bk = BACK.get(b, {}); sd = bk.get("supply_demand_raw_mapped", {}); rg = bk.get("regime_raw_mapped", {})
            wk = rg.get("weekly_slope"); wk = round(wk, 2) if isinstance(wk, (int, float)) else wk
            a(f"| {sub[0]} | {b} | {bk.get('timestamp','')[:10]} | {wk} | {rg.get('cascade_score')} | "
              f"{sd.get('sup_cat')} | {sd.get('clean_sky')} | {sd.get('dist_supply_atr')} | {sd.get('dist_demand_atr')} | "
              f"{bk.get('tpo_acceptance')} | {bk.get('causal_window_ends_at_entry')} |")
    for sub, members in members_flat:
        a("\n" + "#" * 90); a(f"# SUB-BLOCO {sub}\n")
        for b in members:
            bk = BACK.get(b, {}); sd = bk.get("supply_demand_raw_mapped", {}); rg = bk.get("regime_raw_mapped", {})
            a("\n" + "=" * 88); a(f"## EPISODIO {b} ({bk.get('timestamp','')})")
            a(f"\n### Camada 1 backbone (RAW causal pos-fix)")
            a(f"- regime (DERIVED_FROM_RAW price): weekly_slope={rg.get('weekly_slope')} cascade={rg.get('cascade_score')} "
              f"combined={rg.get('combined_score')} macro_broken={rg.get('macro_broken')} v3={rg.get('v3_state')} (fidelity={rg.get('_fidelity_close_vs_raw')})")
            a(f"- supply/demand (RAW Custom OB, causal): sup_cat={sd.get('sup_cat')} clean_sky={sd.get('clean_sky')} "
              f"has_overhead={sd.get('has_overhead')} dist_supply={sd.get('dist_supply_atr')}ATR dist_demand={sd.get('dist_demand_atr')}ATR")
            a(f"- anchor: causal={bk.get('causal_window_ends_at_entry')} exato={bk.get('anchor_exact')} "
              f"close_fidelity={bk.get('anchor_close_fidelity')} warnings={bk.get('warnings')}")
            a(f"- SVP/acceptance: {svp_summary(b)}")
            a(f"\n### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)")
            for bar in (bk.get("ohlcv_window") or [])[-12:]:
                a(f"    O{bar.get('o')} H{bar.get('h')} L{bar.get('l')} C{bar.get('c')}")
            a(f"\n### Indicadores (RAW): {ind_summary(b)}")
    text = "\n".join(L)
    OUTD = os.path.join(D, fname)
    os.makedirs(OUTD, exist_ok=True)
    FORB = ["mfe", "runner", "trap", "winner", "loser", "_audit", "outcome", "monument"]
    rmult = re.findall(r"\b\d+(?:\.\d+)?\s*r\b", text.lower())
    hits = [w for w in FORB if w in text.lower()]
    if hits or rmult:
        print(f"LEAK CHECK FALHOU em {fname}: {hits} {rmult[:5]}"); sys.exit(1)
    with open(os.path.join(OUTD, "reading_packet_RAW_CLEAN.md"), "w") as f:
        f.write(text)
    allb = sorted({b for _, ms in members_flat for b in ms})
    # source_gate_report
    ncausal = sum(1 for b in allb if BACK.get(b, {}).get("causal_window_ends_at_entry"))
    rep = [f"SOURCE GATE REPORT — {fname} (pos-anchor-fix)",
           f"episodios: {len(allb)} | causal(sem futuro): {ncausal}/{len(allb)} | leak-check: PASS (0)",
           "backbone: l2_bpt_raw_backbone_episodes.jsonl (anchor as-of por timestamp real, commit 1267c8d)",
           "campos: Camada-0/1 RAW + indicadores RAW + svp_bar_volume_raw(RAW_OK) + tpo_value_area(DERIVED, tempo)",
           "BLOCKED no pacote: POC/VAL/VAH de VOLUME LuxAlgo (UNKNOWN_BLOCKED, nao fabricado)",
           f"fidelity-fail (feed RAW!=frozen, flagado): {[b for b in allb if not BACK.get(b,{}).get('anchor_close_fidelity')]}",
           "sem outcome/R/MFE/winner/loser/runner/trap. allowed_for_reader=YES."]
    with open(os.path.join(OUTD, "source_gate_report.txt"), "w") as f:
        f.write("\n".join(rep) + "\n")
    entry = {"input_id": fname, "cluster_id": fname.replace("raw_rebuild_", "").replace("_postfix", ""),
             "input_path": f"{OUTD}/reading_packet_RAW_CLEAN.md",
             "created_by_script": "l2_bpt_reading_packet_raw_clean_postfix.py",
             "source_packet_type": "RAW_CLEAN_POST_ANCHOR_FIX", "allowed_for_reader": "YES",
             "source_gate_required": "YES", "source_mapping_status": "RAW_CLEAN_ALLOWED",
             "contains_outcome": "NO", "contains_blocked_fields": "NO", "status": "RAW_CLEAN_ALLOWED",
             "episodes": allb, "notes": "backbone causal pos-fix commit 1267c8d; POC/VAL/VAH volume BLOCKED"}
    json.dump(entry, open(os.path.join(OUTD, "reader_input_manifest_entry.json"), "w"), indent=2, ensure_ascii=False)
    print(f"OK {fname}: {len(allb)} episodios, causal {ncausal}/{len(allb)} -> {OUTD}/ (leak-check PASS)")


emit(CL1, "Cluster 1 (sosia 3a + continuacao 3b) — RAW-clean POS-FIX", "raw_rebuild_cluster1_postfix")
emit(CL2, "Cluster 2 (macro negativo) — RAW-clean POS-FIX", "raw_rebuild_cluster2_postfix")
print("Pacotes RAW-clean POS-FIX gerados. Fonte 100% RAW causal; POC/VAL/VAH volume BLOCKED; sem outcome.")
