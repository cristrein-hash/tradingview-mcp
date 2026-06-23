#!/usr/bin/env python3
"""CAUSAL INDICATOR LAYER — evidencia de leitura (NAO decisao) para pacotes cegos. FONTE = RAW ORIGINAL.

INCIDENTE corrigido (2026-06-23): versao anterior consumiu o DERIVADO repro_recovery/raw_features_2020_2026.jsonl,
cujo nas_recent/smc_recent pegava a CABECA do buffer de 500 labels (NAS/SMC de 2018-19 = stale) e concluiu erradamente
"unreliable". O RAW original (replay 4H) tem NAS/SMC/bubbles/RSI+divergencia AUTENTICOS e causais (auditoria provou).
=> Esta camada consome o artefato extraido do RAW: results/l2_bpt_raw_indicator_events.jsonl (gerado por
l2_bpt_raw_indicator_extract.py, que le /Volumes/.../raw_replay/XAUUSD/4H/*.jsonl.gz). REGRA PERMANENTE: TODO indicador
(NAS, SMC, bubbles, RSI, SVP) vem do RAW original, nunca de derivado/repro_recovery/frozen/slim/packet.

GUARD DURO: este modulo se RECUSA a importar raw_features_2020_2026 como fonte de indicador (assert no import path).
Evidencia faz PERGUNTAS (capitulacao? absorcao? exaustao? mudanca de carater? whipsaw?), nunca TAKE/SKIP/score/gate.
SEM outcome/MFE/R/runner/trap/winner/loser.
"""
import json, os, re

D = "results"
RAW_EVENTS = f"{D}/l2_bpt_raw_indicator_events.jsonl"
FORBIDDEN_INDICATOR_SOURCE = "raw_features_2020_2026"   # guard: nunca fonte de indicador
RAW_SOURCE_PATTERN = re.compile(r"XAUUSD.*replay.*\.jsonl\.gz$")  # defesa-em-profundidade: so RAW replay original

def _load_raw_events():
    if not os.path.exists(RAW_EVENTS):
        raise FileNotFoundError(f"Rode l2_bpt_raw_indicator_extract.py primeiro (gera {RAW_EVENTS} do RAW original).")
    ev = {}
    for l in open(RAW_EVENTS):
        r = json.loads(l)
        src = str(r.get("source_raw_file", ""))
        # GUARD DURO: fonte tem de ser o RAW replay original (pattern), nunca derivado, e declarar RAW_AUTHENTIC
        assert FORBIDDEN_INDICATOR_SOURCE not in src, "FONTE PROIBIDA: indicador nao pode vir de raw_features_2020_2026 (derivado)."
        assert RAW_SOURCE_PATTERN.search(src), f"FONTE INVALIDA: '{src}' nao bate XAUUSD_*replay*.jsonl.gz (RAW original)."
        assert r.get("reliability") == "RAW_AUTHENTIC", f"ep {r.get('bar_idx')} sem RAW_AUTHENTIC."
        ev[int(r["bar_idx"])] = r
    return ev

def indicator_evidence(bar_idx, raw_events=None):
    """Evidencia causal de indicador (RAW) para o episodio, framed como PERGUNTAS. SEM outcome/decisao."""
    ev = raw_events or _load_raw_events()
    r = ev.get(bar_idx)
    if r is None:
        return {"status": "EP_NAO_EXTRAIDO_DO_RAW", "_nota": f"adicione {bar_idx} a l2_bpt_raw_indicator_extract.py"}
    bub = r.get("bubble_cluster_summary") or {}
    nas = r.get("nas_events_recent") or []
    smc = r.get("smc_events_recent") or []
    nas_era = [e for e in nas if e.get("in_current_era")]
    smc_era = [e for e in smc if e.get("in_current_era")]
    nas_long = sum(1 for e in nas_era if "LONG" in str(e.get("text", "")).upper() or "BOTTOM" in str(e.get("text", "")).upper())
    nas_short = sum(1 for e in nas_era if "SHORT" in str(e.get("text", "")).upper() or "TOP" in str(e.get("text", "")).upper())
    choch = sum(1 for e in smc_era if "CHOCH" in str(e.get("text", "")).upper())
    bos = sum(1 for e in smc_era if e.get("text") == "BOS")
    div = r.get("rsi_divergence_events") or {}
    bull_div = any("Bullish" in k for k in div); bear_div = any("Bearish" in k for k in div)
    return {
        "_fonte": "RAW_ORIGINAL", "source_raw_file": r.get("source_raw_file"), "reliability": "RAW_AUTHENTIC",
        "_nota": "EVIDENCIA DE LEITURA (RAW), nao decisao. Indicador PERGUNTA, nao classifica TAKE/SKIP.",
        "nas": {"recent_era": [(e["text"], e["price"]) for e in nas_era], "long": nas_long, "short": nas_short,
                "field": "RAW pine_labels[NAS TOP BOTTOM DETECTOR] (tail as-of-entry)"},
        "smc": {"recent_era": [(e["text"], e["price"]) for e in smc_era], "CHoCH": choch, "BOS": bos,
                "field": "RAW pine_labels[Smart Money Concepts [LuxAlgo]] (tail as-of-entry)"},
        "bubbles": {"buy_total": bub.get("buy_total"), "sell_total": bub.get("sell_total"),
                    "buy_mL": bub.get("buy_mL"), "sell_mL": bub.get("sell_mL"),
                    "field": "RAW pine_shapes_bubbles[Market Order Bubbles]"},
        "rsi": {"value": r.get("rsi_value"), "divergence_raw": div, "bull_div": bull_div, "bear_div": bear_div,
                "field": "RAW study_values[Relative Strength Index]"},
        "PERGUNTAS_DE_LEITURA": [
            f"CAPITULACAO? sell-bubbles m/L={bub.get('sell_mL')} + RSI={r.get('rsi_value')} + RSI-bull-div={bull_div}?",
            f"ABSORCAO? buy-bubbles m/L={bub.get('buy_mL')} + NAS_long(era)={nas_long} (RAW)?",
            f"EXAUSTAO? RSI-bear-div={bear_div} + NAS_short(era)={nas_short} (topo/supply acima?)",
            f"MUDANCA DE CARATER? CHoCH(era)={choch} vs BOS(era)={bos} (RAW SMC LuxAlgo)?",
            "WHIPSAW? cruzar NAS-bottom recente + estrutura nao confirmada = tentativa-de-fundo vs confirmada?",
        ],
    }

if __name__ == "__main__":
    ev = _load_raw_events()
    CLUSTER2 = [5826, 1623, 4401, 3825, 1522, 1873, 5627, 1775, 3949, 3929]
    print("DEMO causal indicator layer — FONTE RAW ORIGINAL (cluster 2, evidencia sem outcome):\n")
    for b in CLUSTER2:
        e = indicator_evidence(b, ev)
        if e.get("status"):
            print(f"#{b}: {e['status']}"); continue
        print(f"#{b}: NAS(era) L{e['nas']['long']}/S{e['nas']['short']} {e['nas']['recent_era'][:2]} | "
              f"SMC CHoCH{e['smc']['CHoCH']}/BOS{e['smc']['BOS']} | bubbles sell_mL{e['bubbles']['sell_mL']}/buy_mL{e['bubbles']['buy_mL']} | "
              f"RSI {e['rsi']['value']} bull_div={e['rsi']['bull_div']} bear_div={e['rsi']['bear_div']} | src={e['source_raw_file']}")
    print("\nTODO indicador (NAS/SMC/bubbles/RSI/SVP) = RAW original. Guard recusa raw_features_2020_2026. Evidencia faz perguntas, nao decide.")
