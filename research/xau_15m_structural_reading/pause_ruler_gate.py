#!/usr/bin/env python3
"""PAUSE RULER — GATE DE 3 PASSOS (ordem Cris 2026-07-10; spec XAU_15M_PAUSE_RULER_SPEC.md à letra).
1) Cobertura dos 42 (foco: 10 BULL que o v2 não vê: #8,9,11,12,13,15,17,27,29,30)
2) Trava de sujeira: nº de zonas e densidade/semana de markup vs escada visual (~1/sem; convenção
   de leitura declarada: 'explode' se >3/sem de markup)
3) Qualidade causal: zona nasce SÓ em rompimento+aceitação (known_at = fecho da aceitação),
   streaming forward-only, known_at monotónico, cobertura exige known_at < t da vela.
Sem entry, sem outcome, sem backtest. Constantes = TODAS da spec (nenhuma nova aqui)."""
import json, sys, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/"research/xau_15m_structural_leg_engine"))
from f1_structural_leg_machine import Data, W_WARMUP
GT = REPO/"research/xau_15m_bb_nas_leonardo/results/catalog_manual_tags_20260707.json"
V2 = HERE/"results/a2_v2_gate42_result.json"
# constantes da spec (§7)
PAUSA_MIN = 8; R_INI = 1.5; R_TETO = 2.5
ACC_N = 2; ACC_ATR = 0.5
Z_PISO = 0.1; W_MIN, W_MAX = 0.7, 2.5
SUPER_H = 24; AUTH_H = 168; BRK = 0.5
R_CYCLE = 4
FOCO = {8, 9, 11, 12, 13, 15, 17, 27, 29, 30}
RANGE_DATES = {"2025-08-01", "2025-08-20", "2025-11-18", "2025-11-21"}

def main():
    D = Data()
    n = len(D.TS)
    zones = []          # cada zona: lo/hi/known_at/defs[]/inv_at/sup_at/kill_at
    leg_zone_ids = []   # zonas da perna UP corrente
    # estado ciclo r=4
    d = "UP"; ext_i = 0; hi_px, lo_px = D.H[0], D.L[0]
    # estado pausa
    p = None            # dict: i0, lo, hi, cmin, cmax
    brk_run = 0; brk_i = None
    macro_bull_weeks = set()
    for i in range(n):
        c, h, l, a, t = D.C[i], D.H[i], D.L[i], D.ATR[i] or 5.0, D.TS[i]
        macro = D.macro_at(t)
        in_up = (d == "UP") and macro == "BULL" and i >= W_WARMUP
        if in_up:
            macro_bull_weeks.add(dt.datetime.utcfromtimestamp(t).strftime("%G-W%V"))
        # --- manutenção de zonas vivas (defesa/invalidação, forward-only) ---
        for z in zones:
            if z["inv_at"] or z["kill_at"] or t < z["known_at"]: continue
            beyond = (z["lo"]-c)/a
            if beyond > 0:
                z["pr"] += 1
                if beyond > BRK or z["pr"] >= 2:
                    z["inv_at"] = t+900
                continue
            z["pr"] = 0
            if l <= z["hi"] and h >= z["lo"]:
                z["defs"].append(t+900)
        # --- máquina de ciclos (kill da perna) ---
        turned_down = False
        if d == "UP":
            if h > hi_px: hi_px = h; ext_i = i
            if (hi_px-c)/a >= R_CYCLE:
                d = "DOWN"; turned_down = True
                lo_px = D.L[ext_i]; ne = ext_i
                for k in range(ext_i, i+1):
                    if D.L[k] < lo_px: lo_px = D.L[k]; ne = k
                ext_i = ne
        else:
            if l < lo_px: lo_px = l; ext_i = i
            if (c-lo_px)/a >= R_CYCLE:
                d = "UP"
                hi_px = D.H[ext_i]; ne = ext_i
                for k in range(ext_i, i+1):
                    if D.H[k] > hi_px: hi_px = D.H[k]; ne = k
                ext_i = ne
                leg_zone_ids = []
        if turned_down or macro != "BULL":
            for zid in leg_zone_ids:
                if zones[zid]["kill_at"] is None and zones[zid]["inv_at"] is None:
                    zones[zid]["kill_at"] = t+900
            if turned_down: leg_zone_ids = []
            p = None; brk_i = None; brk_run = 0
        if not in_up:
            continue
        # --- régua da pausa ---
        if p is None and brk_i is None:
            if i >= PAUSA_MIN-1:
                w_lo = min(D.L[i-PAUSA_MIN+1:i+1]); w_hi = max(D.H[i-PAUSA_MIN+1:i+1])
                if (w_hi-w_lo) <= R_INI*a:
                    cs = D.C[i-PAUSA_MIN+1:i+1]
                    p = {"i0": i-PAUSA_MIN+1, "lo": w_lo, "hi": w_hi,
                         "cmin": min(cs), "cmax": max(cs)}
            continue
        if p is not None and brk_i is None:
            if c > p["hi"]:
                brk_i = i; brk_run = 1
                if (c-p["hi"])/a >= ACC_ATR:
                    _publish(zones, leg_zone_ids, p, i, t, a)
                    p = None; brk_i = None; brk_run = 0
                continue
            if c < p["lo"]:
                p = None; continue
            nlo, nhi = min(p["lo"], l), max(p["hi"], h)
            if (nhi-nlo) > R_TETO*a:
                p = None; continue
            p["lo"], p["hi"] = nlo, nhi
            p["cmin"] = min(p["cmin"], c); p["cmax"] = max(p["cmax"], c)
            continue
        if brk_i is not None:
            if c > p["hi"]:
                brk_run += 1
                if brk_run >= ACC_N or (c-p["hi"])/a >= ACC_ATR:
                    _publish(zones, leg_zone_ids, p, i, t, a)
                    p = None; brk_i = None; brk_run = 0
            else:
                p = None; brk_i = None; brk_run = 0   # rompimento rejeitado: pausa morre sem zona
    # supersessão: zona nova ACIMA → anterior expira em SUPER_H
    for k in range(1, len(zones)):
        z = zones[k]
        for zprev in zones[:k]:
            if zprev["sup_at"] is None and zprev["inv_at"] is None and zprev["kill_at"] is None \
               and z["lo"] > zprev["lo"] and z["leg"] == zprev["leg"]:
                zprev["sup_at"] = z["known_at"]+SUPER_H*3600
    # --- (3) causal: monotonicidade ---
    ks = [z["known_at"] for z in zones]
    assert all(ks[i2] >= ks[i2-1] for i2 in range(1, len(ks))), "known_at não-monotónico"
    # --- (1) cobertura dos 42 ---
    cat = json.load(open(GT))
    fundos = sorted(cat["notes"]["FUNDO"], key=lambda x: x["t"])
    v2rows = {r["n"]: r for r in json.load(open(V2))["rows"]}
    rows = []
    for nn, f in enumerate(fundos, 1):
        t, px, date = f["t"], f["price"], f["date"]
        fam = ("CAPITULACAO" if date >= "2026-03-01" else
               "RANGE_BOTTOM" if date[:10] in RANGE_DATES else "BULL_PULLBACK")
        hit = None
        for z in zones:
            if z["known_at"] >= t: continue
            end = min(x for x in (z["inv_at"], z["kill_at"], z["sup_at"], t+1) if x is not None)
            if end <= t: continue
            if not (z["lo"] <= px <= z["hi"]): continue
            defs_before = [x for x in z["defs"] if x < t]
            ref = max([z["known_at"]]+defs_before)
            if (t-ref) <= AUTH_H*3600:
                hit = {"id": z["id"], "band": [round(z["lo"], 1), round(z["hi"], 1)],
                       "known": dt.datetime.utcfromtimestamp(z["known_at"]).strftime("%m-%d %H:%M"),
                       "antes_da_vela": z["known_at"] < t}
                break
        rows.append({"n": nn, "date": date, "familia": fam,
                     "pause_zone": hit, "v2_status": v2rows[nn]["status"]})
    foco_hits = [r for r in rows if r["n"] in FOCO and r["pause_zone"]]
    cobertos_pause = [r["n"] for r in rows if r["pause_zone"]]
    combinado = sum(1 for r in rows if r["pause_zone"] or r["v2_status"].startswith("COBERTO"))
    # --- (2) trava de sujeira ---
    n_weeks = len(macro_bull_weeks)
    dens = len(zones)/n_weeks if n_weeks else 0
    explode = dens > 3.0
    out = {"spec": "XAU_15M_PAUSE_RULER_SPEC.md",
           "zonas_publicadas": len(zones),
           "semanas_markup_bull": n_weeks,
           "densidade_zonas_por_semana_markup": round(dens, 2),
           "referencia_escada_cris": "~1/semana (ago-out 10 topos)",
           "trava_sujeira": "FALHA_EXPLODE" if explode else "OK",
           "foco_10_bull": {"recuperados": sorted(r["n"] for r in foco_hits),
                            "n": f"{len(foco_hits)}/10"},
           "cobertura_pause_only_42": f"{len(cobertos_pause)}/42",
           "cobertura_combinada_v2_mais_pause": f"{combinado}/42",
           "causal": {"known_at_monotonico": True,
                      "todas_cobrancas_known_antes_da_vela": all((r["pause_zone"] or {}).get("antes_da_vela", True) for r in rows)},
           "rows": rows}
    (HERE/"results/pause_ruler_gate_result.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    for r in rows:
        if r["n"] in FOCO or r["pause_zone"]:
            pz = r["pause_zone"]
            print(f"#{r['n']:>2} {r['date']} {r['familia']:<13} v2={r['v2_status']:<20} "
                  f"pause={'HIT '+str(pz['band'])+' known '+pz['known'] if pz else '—'}")
    print(json.dumps({k: out[k] for k in ('zonas_publicadas', 'semanas_markup_bull',
          'densidade_zonas_por_semana_markup', 'trava_sujeira', 'foco_10_bull',
          'cobertura_pause_only_42', 'cobertura_combinada_v2_mais_pause', 'causal')},
          ensure_ascii=False, indent=1))
    print("PAUSE_GATE_OK")

def _publish(zones, leg_zone_ids, p, i, t, a):
    lo = p["cmin"]-Z_PISO*a
    hi = p["cmax"]
    if (hi-lo) < W_MIN*a: hi = lo+W_MIN*a
    if (hi-lo) > W_MAX*a: hi = lo+W_MAX*a
    zones.append({"id": f"P{len(zones):04d}", "lo": lo, "hi": hi, "known_at": t+900,
                  "defs": [], "inv_at": None, "sup_at": None, "kill_at": None, "pr": 0,
                  "leg": len(leg_zone_ids) and zones[leg_zone_ids[0]]["leg"] or len(zones)})
    if not leg_zone_ids:
        zones[-1]["leg"] = len(zones)
    else:
        zones[-1]["leg"] = zones[leg_zone_ids[0]]["leg"]
    leg_zone_ids.append(len(zones)-1)

if __name__ == "__main__":
    main()
