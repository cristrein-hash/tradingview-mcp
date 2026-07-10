#!/usr/bin/env python3
"""AUTÓPSIA DOS 42 (ordem Cris 2026-07-10, conforme XAU_15M_DEMAND_REGION_SPEC.md).
Vela a vela: família estrutural · veredicto A2 · região relevante (facto: banda/estado na marca) ·
CAUSA classificada por leitura. SEM métricas/estatísticas — só factos (datas/preços) e contagens
de tabela. Convenções de LEITURA declaradas (não são thresholds de regra):
  'zona velha' = idade >168h (7 dias) na marca · 'região próxima' = banda a ≤1,5·ATR do preço da
  marca · 'furo mínimo' = invalidação com fecho ≤0,2·ATR através da banda.
Causas: COVERED_OK · COVERED_ZONA_VELHA · GEOMETRIA (banda viva perto mas não alcança/estreita) ·
INVALIDACAO_ERRADA (zona certa morta por furo mínimo antes da marca) · LATE_POR_NATUREZA
(capitulação: demanda nasce do flush — NÃO é falha, spec §2) · LATE_ESTRUTURA_NAO_MAPEADA ·
AUSENCIA_REAL. Sem entry, sem backtest, sem tuning."""
import json, csv, sys, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/"research/xau_15m_structural_leg_engine"))
from f1_structural_leg_machine import Data
GT = REPO/"research/xau_15m_bb_nas_leonardo/results/catalog_manual_tags_20260707.json"
GATE = REPO/"research/xau_15m_structural_leg_engine/results/a2_anchor_gt_gate_result.json"
REG = REPO/"research/xau_15m_structural_leg_engine/results/a2_regions_r4.jsonl"
EVT = REPO/"research/xau_15m_structural_leg_engine/results/a2_events_r4.jsonl"
RANGE_DATES = {"2025-08-01", "2025-08-20", "2025-11-18", "2025-11-21"}
VELHA_H, PROX_ATR, FURO_ATR = 168, 1.5, 0.2

def familia(date):
    if date >= "2026-03-01": return "CAPITULACAO"
    if date[:10] in RANGE_DATES: return "RANGE_BOTTOM"
    return "BULL_PULLBACK"

def main():
    D = Data()
    cat = json.load(open(GT))
    fundos = sorted(cat["notes"]["FUNDO"], key=lambda x: x["t"])
    gate = {r["date"]: r for r in json.load(open(GATE))["fundos_42"]["rows"]}
    regions = [json.loads(l) for l in open(REG)]
    ev = {}
    for l in open(EVT):
        e = json.loads(l)
        ev.setdefault(e["region_id"], {})[e["event"]] = e["known_at"]
    def close_at(t):
        i = bisect.bisect_right(D.TS, t)-1
        return D.C[i], (D.ATR[i] or 5.0)
    rows = []
    for n, f in enumerate(fundos, 1):
        t, px, date = f["t"], f["price"], f["date"]
        g = gate.get(date, {})
        verdict = g.get("verdict", "?")
        _, atr = close_at(t)
        fam = familia(date)
        # regiões relevantes na marca: banda a <=PROX_ATR do px (bottoms; tops convertidas)
        cand = []
        for r in regions:
            gap = max(r["price_low"]-px, px-r["price_high"], 0)/atr
            if gap > PROX_ATR: continue
            e = ev.get(r["region_id"], {})
            conv = e.get("converted_support"); inv = e.get("invalidated")
            if r["kind"] == "TOP" and not (conv and conv < t): continue   # top só interessa convertida antes
            if r["known_at"] >= t:
                continue  # nasceu depois (late tratada pelo verdict)
            estado = ("INVALIDADA_" + dt.datetime.utcfromtimestamp(inv).strftime("%m-%d %H:%M")
                      if (inv and inv < t) else "VIVA")
            furo = None
            if inv and inv < t:
                ci, a2 = close_at(inv-900)
                furo = round((r["price_low"]-ci)/a2, 2) if r["kind"] == "BOTTOM" or conv else None
            cand.append({"id": r["region_id"], "kind": r["kind"], "band": [r["price_low"], r["price_high"]],
                         "gap_atr": round(gap, 2), "estado": estado, "furo_atr": furo,
                         "idade_h": round((t-r["known_at"])/3600, 1)})
        cand.sort(key=lambda c: c["gap_atr"])
        best = cand[0] if cand else None
        # classificação por leitura
        if verdict.startswith("COVERED"):
            age = g.get("bottom_age_h")
            causa = "COVERED_ZONA_VELHA" if (age is not None and age > VELHA_H) else "COVERED_OK"
        elif verdict == "NEAR_MISS":
            morta_furo = next((c for c in cand if c["estado"].startswith("INVALIDADA") and c["furo_atr"] is not None
                               and abs(c["furo_atr"]) <= FURO_ATR and c["gap_atr"] == 0), None)
            causa = "INVALIDACAO_ERRADA" if morta_furo else "GEOMETRIA"
            if morta_furo: best = morta_furo
        elif verdict == "LATE_ONLY":
            if fam == "CAPITULACAO":
                causa = "LATE_POR_NATUREZA"
            else:
                viva_ou_morta = best
                if viva_ou_morta and viva_ou_morta["estado"].startswith("INVALIDADA") and \
                   viva_ou_morta["furo_atr"] is not None and abs(viva_ou_morta["furo_atr"]) <= FURO_ATR:
                    causa = "INVALIDACAO_ERRADA"
                elif viva_ou_morta:
                    causa = "GEOMETRIA"
                else:
                    causa = "LATE_ESTRUTURA_NAO_MAPEADA"
        else:  # MISS
            morta = next((c for c in cand if c["estado"].startswith("INVALIDADA")), None)
            viva = next((c for c in cand if c["estado"] == "VIVA"), None)
            if morta and morta["furo_atr"] is not None and abs(morta["furo_atr"]) <= FURO_ATR:
                causa = "INVALIDACAO_ERRADA"; best = morta
            elif viva:
                causa = "GEOMETRIA"; best = viva
            else:
                causa = "AUSENCIA_REAL"
        rows.append({"n": n, "date": date, "px": round(px, 1), "familia": fam, "verdict": verdict,
                     "regiao": best, "causa": causa})
    counts = {}
    for r in rows:
        k = f"{r['familia']}|{r['causa']}"
        counts[k] = counts.get(k, 0)+1
    out = {"spec": "XAU_15M_DEMAND_REGION_SPEC.md", "convencoes_leitura":
           {"zona_velha_h": VELHA_H, "proximidade_atr": PROX_ATR, "furo_minimo_atr": FURO_ATR},
           "rows": rows, "contagens_tabela": dict(sorted(counts.items()))}
    (HERE/"results/autopsy_42_result.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    for r in rows:
        b = r["regiao"]
        breg = (f"{b['id']} [{b['band'][0]:.0f}-{b['band'][1]:.0f}] {b['estado']} gap{b['gap_atr']}"
                + (f" furo{b['furo_atr']}" if b and b.get("furo_atr") is not None else "")) if b else "—"
        print(f"#{r['n']:>2} {r['date']} {r['familia']:<13} {r['verdict']:<17} {r['causa']:<26} {breg}")
    print(json.dumps(out["contagens_tabela"], indent=1, ensure_ascii=False))
    print("AUTOPSY_OK")

if __name__ == "__main__":
    main()
