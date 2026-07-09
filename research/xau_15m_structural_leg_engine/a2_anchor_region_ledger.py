#!/usr/bin/env python3
"""A2 ANCHOR-ONLY REGION LEDGER (spec XAU_15M_A2_ANCHOR_ONLY_SPEC_20260709.md v1.1 — congelada).
Leitura DINÂMICA de trajetória (ciclos pullback/reclaim 15M nativos), não snapshot de eixo único.

Máquina simétrica de ciclos (§1, §13.5): d=UP na barra 0 (H1/L1 seed barra 0); em UP flip→DOWN quando
(H1−close)/ATR15 ≥ r_cycle → publica REGIÃO-TOPO; em DOWN flip→UP quando (close−L1)/ATR15 ≥ r_cycle
→ publica REGIÃO-FUNDO. Tracking do novo ciclo começa NA BARRA DO EXTREMO anterior. known_at = FECHO
da barra de confirmação (t+900); first_valid_bar = barra seguinte; NENHUMA entry (não existe camada);
bar de confirmação NUNCA é reteste. Bandas (§2, heranças congeladas): FUNDO [L1−0,1A, L1+0,7A];
TOPO [H1−0,7A, H1+0,1A] (A = ATR15 da barra do extremo). Invalidação (§6): FUNDO por close<price_low;
TOPO por close>price_high → **converted_support** (§13.2, evento versionado, banda mantém-se, vira
suporte esperado; converted_support invalida depois por close<price_low). Mesma barra toca E fecha
através: INVALIDAÇÃO precede, não conta reteste (§13.5.4). Warmup: 400 barras do stream (fronteiras
de bloco contíguas no preço — F0). Contexto = macro v5 verbatim no known_at (§7). pos96 report-only.
GT do Cris NUNCA entra aqui (import-guard: este módulo não abre nenhum ficheiro de GT).
Fonte: EXCLUSIVAMENTE F0 (RAW HD, sha-verified). Zero fontes derivadas banidas, sem indicadores,
sem outcome."""
import json, sys, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from f1_structural_leg_machine import Data, W_WARMUP

R_GRID = [4, 6, 8]                 # manifest r_cycle_atr15_A2
BAND_IN, BAND_OUT = 0.1, 0.7       # heranças congeladas (SL V1 / tol_anchor)

def build_regions(D, r_cycle, i_end=None):
    """Streaming causal. Devolve (regions, events). Região = snapshot IMUTÁVEL no known_at;
    mudanças de status = eventos versionados append-only com known_at próprio."""
    n = len(D.TS) if i_end is None else i_end
    regions = []; events = []
    d = "UP"; ext_i = 0                      # §13.5.1-2: extremo corrente do ciclo (índice)
    hi_px, lo_px = D.H[0], D.L[0]
    active = []                              # índices de regiões vivas (status mutável em dict local)
    for i in range(n):
        c, h, l, a = D.C[i], D.H[i], D.L[i], D.ATR[i] or 5.0
        t = D.TS[i]
        # ---- 1) invalidação/conversão/reteste das regiões vivas (precedência: invalidação §13.5.4)
        still = []
        for ri in active:
            r = regions[ri]
            if i <= r["created_from_end_bar"]:      # bar de confirmação nunca conta (§3/§4)
                still.append(ri); continue
            kind = r["kind"]; st = r["status"]
            if kind == "BOTTOM" or st == "converted_support":
                broke = c < r["price_low"]
            else:                                    # TOP ainda não convertida
                broke = c > r["price_high"]
            if broke:
                if kind == "TOP" and st != "converted_support":
                    r["status"] = "converted_support"
                    events.append({"region_id": r["region_id"], "event": "converted_support",
                                   "known_at": t+900})
                    still.append(ri)
                else:
                    r["status"] = "invalidated"
                    events.append({"region_id": r["region_id"], "event": "invalidated",
                                   "known_at": t+900})
                continue
            # reteste (só regista; entry NÃO existe)
            if l <= r["price_high"] and h >= r["price_low"]:
                r["n_retests"] += 1
                if r["n_retests"] == 1:
                    r["first_retest_t"] = t
                    if r["status"] != "converted_support":
                        r["status"] = "retested"
                    events.append({"region_id": r["region_id"], "event": "retested",
                                   "known_at": t+900})
            still.append(ri)
        active = still
        # ---- 2) máquina de ciclos (flips publicam regiões)
        if d == "UP":
            if h > hi_px: hi_px = h; ext_i = i
            if (hi_px - c)/a >= r_cycle:
                # flip UP->DOWN: publica REGIÃO-TOPO (extremo = wick high da barra ext_i)
                ea = D.ATR[ext_i] or 5.0
                _publish(regions, active, events, D, kind="TOP", ext_i=ext_i, ext_px=hi_px,
                         conf_i=i, price_low=hi_px-BAND_OUT*ea, price_high=hi_px+BAND_IN*ea,
                         r_cycle=r_cycle)
                d = "DOWN"; lo_px = D.L[ext_i]; new_ext = ext_i   # §13.5.1: tracking desde o extremo
                for k in range(ext_i, i+1):
                    if D.L[k] < lo_px: lo_px = D.L[k]; new_ext = k
                ext_i = new_ext
        else:
            if l < lo_px: lo_px = l; ext_i = i
            if (c - lo_px)/a >= r_cycle:
                ea = D.ATR[ext_i] or 5.0
                _publish(regions, active, events, D, kind="BOTTOM", ext_i=ext_i, ext_px=lo_px,
                         conf_i=i, price_low=lo_px-BAND_IN*ea, price_high=lo_px+BAND_OUT*ea,
                         r_cycle=r_cycle)
                d = "UP"; hi_px = D.H[ext_i]; new_ext = ext_i
                for k in range(ext_i, i+1):
                    if D.H[k] > hi_px: hi_px = D.H[k]; new_ext = k
                ext_i = new_ext
    return regions, events

def _publish(regions, active, events, D, kind, ext_i, ext_px, conf_i, price_low, price_high, r_cycle):
    t_conf = D.TS[conf_i]
    # warmup §13.5.3: extremo E confirmação fora das primeiras 400 barras
    if ext_i < W_WARMUP or conf_i < W_WARMUP:
        return
    macro = D.macro_at(t_conf)
    ctx = ({"BULL": "BULL_PULLBACK", "RANGE": "RANGE_BOTTOM", "BEAR": "BEAR_CAPITULATION"}[macro]
           if kind == "BOTTOM" else f"TOP_{macro}")
    # pos96 §13.5.5: 96 barras estritamente anteriores ao extremo
    w0 = max(0, ext_i-96)
    seg_h = D.H[w0:ext_i]; seg_l = D.L[w0:ext_i]
    if seg_h and max(seg_h) > min(seg_l):
        pos96 = (ext_px-min(seg_l))/(max(seg_h)-min(seg_l))
    else:
        pos96 = 0.5
    depth = abs(D.C[conf_i]-ext_px)/(D.ATR[conf_i] or 5.0)
    rid = f"{kind[0]}{len(regions):05d}_r{r_cycle}"
    reg = {"region_id": rid, "kind": kind, "context": ctx,
           "price_low": round(price_low, 2), "price_high": round(price_high, 2),
           "extreme_px": round(ext_px, 2), "extreme_t": D.TS[ext_i],
           "created_from_start_bar": ext_i, "created_from_end_bar": conf_i,
           "known_at": t_conf+900, "first_valid_bar_after_known_at": conf_i+1,
           "latency_bars": conf_i-ext_i, "depth_atr": round(depth, 2), "pos96": round(pos96, 3),
           "source": "RAW_HD", "status": "active", "n_retests": 0, "first_retest_t": None,
           "no_entry_on_confirmation": (conf_i+1) > conf_i}
    regions.append(reg); active.append(len(regions)-1)
    events.append({"region_id": rid, "event": "confirmed_active", "known_at": t_conf+900})

def summarize(regions, events, D, r):
    weeks = (D.TS[-1]-D.TS[W_WARMUP])/(7*86400)
    bt = [x for x in regions if x["kind"] == "BOTTOM"]; tp = [x for x in regions if x["kind"] == "TOP"]
    def pct(xs): return round(100*xs, 1)
    conv = sum(1 for x in tp if x["status"] in ("converted_support",) or
               any(e["region_id"] == x["region_id"] and e["event"] == "converted_support" for e in events))
    ret_inv = {}
    for x in bt:
        got_ret = x["n_retests"] > 0
        inv = x["status"] == "invalidated"
        k = x["context"]
        d0 = ret_inv.setdefault(k, {"retested": 0, "ret_then_inv": 0})
        if got_ret:
            d0["retested"] += 1
            if inv: d0["ret_then_inv"] += 1
    lat = sorted(x["latency_bars"] for x in regions)
    return {"r_cycle": r, "n_regions": len(regions), "n_bottom": len(bt), "n_top": len(tp),
            "regions_per_week": round(len(regions)/weeks, 2),
            "bottoms_per_week": round(len(bt)/weeks, 2),
            "top_converted_support": conv,
            "latency_bars_p50_p90": [lat[len(lat)//2], lat[int(len(lat)*0.9)]] if lat else None,
            "bottom_status": {s: sum(1 for x in bt if x["status"] == s)
                              for s in ("active", "retested", "invalidated")},
            "retested_then_invalidated_by_context": {k: {"rate": round(v["ret_then_inv"]/v["retested"], 3)
                                                          if v["retested"] else None, **v}
                                                     for k, v in sorted(ret_inv.items())},
            "top_buy_traps_pos96": sum(1 for x in bt if x["pos96"] > 0.67),
            "no_entry_on_confirmation_all": all(x["no_entry_on_confirmation"] for x in regions)}

if __name__ == "__main__":
    D = Data()
    out = {"spec": "XAU_15M_A2_ANCHOR_ONLY_SPEC_20260709.md v1.1", "per_r": []}
    store = {}
    for r in R_GRID:
        regions, events = build_regions(D, r)
        out["per_r"].append(summarize(regions, events, D, r))
        store[r] = {"regions": regions, "events": events}
    (HERE/"results/a2_anchor_region_ledger_result.json").write_text(json.dumps(out, indent=2))
    # ledgers completos por r (append-only por construção; ficheiro por r)
    for r, s in store.items():
        with open(HERE/f"results/a2_regions_r{r}.jsonl", "w") as fh:
            for reg in s["regions"]: fh.write(json.dumps(reg)+"\n")
        with open(HERE/f"results/a2_events_r{r}.jsonl", "w") as fh:
            for e in s["events"]: fh.write(json.dumps(e)+"\n")
    print(json.dumps(out, indent=2))
    print("A2_LEDGER_BUILT")
