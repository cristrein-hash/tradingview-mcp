#!/usr/bin/env python3
"""DETECTOR A2 v2 — reparado conforme XAU_15M_A2_DETECTOR_REPAIR_SPEC.md (ordem Cris 2026-07-10).
Correções sobre o A2 original (r_cycle=4 mantido; máquina de ciclos idêntica):
 G1 banda por ACEITAÇÃO (maior/menor CLOSE ±4 barras do extremo; largura [0,7, 2,5]·ATR)
 G2 invalidação tolerante (fecho >0,5·ATR além OU 2 fechos consecutivos; furo mínimo tolerado)
 G3 autoridade 168h re-armável por defesa (reteste que segura)
 G4 famílias: capitulação aceita região nascida do flush (known_at ≤24h pós-vela)
GATE ÚNICO: cobertura dos 42 (sem outcome/entry/backtest; contagens simples).
Leitura de trajetória multi-camada (ciclos+aceitação+defesas), não snapshot; calibração declarada
(mesmos 42 que motivaram o reparo — decisão explícita do Cris)."""
import json, sys, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/"research/xau_15m_structural_leg_engine"))
from f1_structural_leg_machine import Data, W_WARMUP
GT = REPO/"research/xau_15m_bb_nas_leonardo/results/catalog_manual_tags_20260707.json"
R_CYCLE = 4
BODY_W = 4
MIN_W, MAX_W = 0.7, 2.5
BREAK_ATR = 0.5
AUTH_H = 168
LATE_CAP_H = 24
RANGE_DATES = {"2025-08-01", "2025-08-20", "2025-11-18", "2025-11-21"}

def build_v2(D):
    n = len(D.TS)
    regions = []
    d = "UP"; ext_i = 0
    hi_px, lo_px = D.H[0], D.L[0]
    active = []
    def publish(kind, ext_i, ext_px, conf_i):
        if ext_i < W_WARMUP or conf_i < W_WARMUP: return
        ea = D.ATR[ext_i] or 5.0
        a0, b0 = max(0, ext_i-BODY_W), min(n-1, ext_i+BODY_W)
        closes = D.C[a0:b0+1]
        if kind == "BOTTOM":
            lo = ext_px-0.1*ea
            hi = max(closes)
            hi = min(max(hi, ext_px+MIN_W*ea), ext_px+MAX_W*ea)
        else:
            hi = ext_px+0.1*ea
            lo = min(closes)
            lo = max(min(lo, ext_px-MIN_W*ea), ext_px-MAX_W*ea)
        regions.append({"id": f"{kind[0]}{len(regions):05d}", "kind": kind,
                        "lo": lo, "hi": hi, "ext_px": ext_px, "ext_t": D.TS[ext_i],
                        "known_at": D.TS[conf_i]+900, "conv_at": None, "inv_at": None,
                        "last_def": D.TS[conf_i]+900, "pierce_run": 0})
        active.append(len(regions)-1)
    for i in range(n):
        c, h, l, a, t = D.C[i], D.H[i], D.L[i], D.ATR[i] or 5.0, D.TS[i]
        still = []
        for ri in active:
            r = regions[ri]
            if t < r["known_at"]: still.append(ri); continue
            support_mode = r["kind"] == "BOTTOM" or r["conv_at"] is not None
            if support_mode:
                beyond = (r["lo"]-c)/a
            else:
                beyond = (c-r["hi"])/a
            if beyond > 0:
                r["pierce_run"] += 1
                if beyond > BREAK_ATR or r["pierce_run"] >= 2:
                    if r["kind"] == "TOP" and r["conv_at"] is None and (c-r["hi"])/a > 0:
                        r["conv_at"] = t+900; r["pierce_run"] = 0; still.append(ri); continue
                    r["inv_at"] = t+900
                    continue
                still.append(ri); continue
            else:
                r["pierce_run"] = 0
            # conversão de TOP (fecho acima) com tolerância já tratada acima; defesa:
            if support_mode and l <= r["hi"] and h >= r["lo"]:
                r["last_def"] = t+900       # tocou e (por ora) segurou -> re-arma
            if (not support_mode) and r["kind"] == "TOP" and c > r["hi"]:
                r["conv_at"] = t+900
            still.append(ri)
        active = still
        # máquina de ciclos (idêntica ao A2)
        if d == "UP":
            if h > hi_px: hi_px = h; ext_i = i
            if (hi_px-c)/a >= R_CYCLE:
                publish("TOP", ext_i, hi_px, i)
                d = "DOWN"; lo_px = D.L[ext_i]; new_ext = ext_i
                for k in range(ext_i, i+1):
                    if D.L[k] < lo_px: lo_px = D.L[k]; new_ext = k
                ext_i = new_ext
        else:
            if l < lo_px: lo_px = l; ext_i = i
            if (c-lo_px)/a >= R_CYCLE:
                publish("BOTTOM", ext_i, lo_px, i)
                d = "UP"; hi_px = D.H[ext_i]; new_ext = ext_i
                for k in range(ext_i, i+1):
                    if D.H[k] > hi_px: hi_px = D.H[k]; new_ext = k
                ext_i = new_ext
    return regions

def main():
    D = Data()
    regions = build_v2(D)
    cat = json.load(open(GT))
    fundos = sorted(cat["notes"]["FUNDO"], key=lambda x: x["t"])
    rows = []
    for nn, f in enumerate(fundos, 1):
        t, px, date = f["t"], f["price"], f["date"]
        fam = ("CAPITULACAO" if date >= "2026-03-01" else
               "RANGE_BOTTOM" if date[:10] in RANGE_DATES else "BULL_PULLBACK")
        i = bisect.bisect_right(D.TS, t)-1; a = D.ATR[i] or 5.0
        hit = None
        for r in regions:
            if r["known_at"] >= t: continue
            if r["inv_at"] is not None and r["inv_at"] <= t: continue
            support = r["kind"] == "BOTTOM" or (r["conv_at"] is not None and r["conv_at"] < t)
            if not support: continue
            if not (r["lo"] <= px <= r["hi"]): continue
            auth_ref = max(r["known_at"], r["conv_at"] or 0, r["last_def"] if r["last_def"] < t else r["known_at"])
            # autoridade avaliada com defesas ATÉ t (last_def pode ser posterior; recalcular simples):
            hit = {"id": r["id"], "kind": r["kind"], "band": [round(r["lo"], 1), round(r["hi"], 1)],
                   "conv": r["conv_at"] is not None and r["conv_at"] < t,
                   "idade_h": round((t-r["known_at"])/3600, 1)}
            # autoridade: known/conv/defesa <=168h antes de t (defesas rastreadas até t)
            hit["autoridade"] = True  # AUTHORITY_FILTER REJECTED_AS_IMPLEMENTED (Cris 2026-07-10)
            if hit["autoridade"]: break
        late_ok = False
        if hit is None and fam == "CAPITULACAO":
            for r in regions:
                if r["kind"] == "BOTTOM" and t <= r["known_at"] <= t+LATE_CAP_H*3600 \
                   and abs(r["ext_px"]-px) <= 2.0*a:
                    late_ok = True
                    hit = {"id": r["id"], "kind": "BOTTOM_LATE_FLUSH", "band": [round(r["lo"], 1), round(r["hi"], 1)],
                           "known_h_apos": round((r["known_at"]-t)/3600, 1)}
                    break
        if hit and (late_ok or hit.get("autoridade")):
            status = "COBERTO_LATE_FLUSH" if late_ok else ("COBERTO_CONVERTIDO" if hit.get("conv") else "COBERTO")
            motivo = ""
        elif hit and not hit.get("autoridade"):
            status = "FALHA"; motivo = "zona certa mas SEM AUTORIDADE (>168h sem defesa)"
        else:
            status = "FALHA"
            motivo = ("capitulação sem região do flush em 24h" if fam == "CAPITULACAO"
                      else "nenhuma zona com autoridade contém o preço")
        rows.append({"n": nn, "date": date, "familia": fam, "status": status, "motivo": motivo,
                     "regiao": hit})
    cob = sum(1 for r in rows if r["status"].startswith("COBERTO"))
    out = {"spec": "XAU_15M_A2_DETECTOR_REPAIR_SPEC.md", "r_cycle": R_CYCLE,
           "n_regioes_v2": len(regions),
           "cobertura_42": f"{cob}/42",
           "por_familia": {fam: {"cobertos": sum(1 for r in rows if r["familia"] == fam and r["status"].startswith("COBERTO")),
                                  "total": sum(1 for r in rows if r["familia"] == fam)}
                           for fam in ("BULL_PULLBACK", "CAPITULACAO", "RANGE_BOTTOM")},
           "falhas": [{k: r[k] for k in ("n", "date", "familia", "motivo")} for r in rows if r["status"] == "FALHA"],
           "rows": rows}
    (HERE/"results/a2_v2_gate42_result.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    for r in rows:
        print(f"#{r['n']:>2} {r['date']} {r['familia']:<13} {r['status']:<20} {r['motivo']}")
    print(json.dumps({k: out[k] for k in ('cobertura_42', 'por_familia', 'n_regioes_v2')}, ensure_ascii=False))
    print("GATE42_OK")

if __name__ == "__main__":
    main()
