#!/usr/bin/env python3
"""A1A2_FUNDO_LAB · STAGE 3 — STRUCTURAL-FIRST (protocolo XAU_15M V1).
Tabela estrutural por EVENTO (swing-low fractal m=3 CONFIRMADO no RAW 15M), classificada pelo MESMO stack
causal do GT (macro_structural_v3 D-1 + leg_v3 4H). Indicadores NÃO entram aqui (Stage 4). Fail-loud.

Regime/leg avaliados na barra de CONFIRMAÇÃO do fractal (p+3) = instante em que o evento é conhecível (causal).
Universo = todos os fractais confirmados; positivos = GT subclasse A1/A2 casados por proximidade (±6h).
Cross-check obrigatório: macro reconstruído vs macro do GT (stop se >20% contradição). Cobertura: quantos
dos 32 A1/A2 caem no RAW 15M (stop se >30% fora). py3.9 stdlib.
Output: results/a1a2_bucket_table.csv + resumo stdout.
"""
import sys, json, gzip, glob, bisect, csv, datetime as dt
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REV = HERE.parent
sys.path.insert(0, str(REV))
import macro_structural_v3 as M
import leg_v3 as LV
from a1_causal_entry import load_series, _is_swinglow, M_FRAC

RAW15 = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
GT_PATH = REV / "results" / "REGIME_GT_FUNDOS_UNIFIED_20260714.json"
OUT = HERE / "results"; OUT.mkdir(exist_ok=True)
BAR4 = 14400
SNAP = 6 * 3600           # casar GT<->fractal em ±6h (mesma janela do GT unify)
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")


def raw_blocks():
    # todos os blocos 15M ativos do HD (exclui superseded/)
    fs = sorted(glob.glob(str(RAW15 / "XAUUSD_15m_replay_*.jsonl.gz")))
    fs = [f for f in fs if "superseded" not in f]
    if not fs:
        sys.exit("FALHA: 0 blocos RAW 15M no HD")
    return fs


# --- stack causal idêntico ao fundos_gt_unify (macro D-1 + leg 4H, known-at) ---
print("A construir stack macro/leg (causal)...", flush=True)
_lab1d = M.build_layer1(); _KN1 = [t + 86400 for t in M.T]
_v3 = LV.build_leg_v3(); _lc = [r["t"] + BAR4 for r in _v3]


def macro_at(t):
    j = bisect.bisect_right(_KN1, t) - 1
    return _lab1d[j] if j >= 0 else None


def leg_at(t):
    i = bisect.bisect_right(_lc, t) - 1
    return _v3[i].get("leg", "?") if i >= 0 else "?"


def bucket(macro, leg, pos):
    """macro+leg+pos -> balde canónico (protocolo §C). Fail-loud se nome não-canónico."""
    L = str(leg or "").upper()
    if macro == "BULL":
        b = "BULL_impulse" if "IMPULSO" in L else "BULL_pullback"
    elif macro == "RANGE":
        b = "RANGE_accumulation_bottom" if (pos is not None and pos < 0.34) else "RANGE_neutral"
    elif macro == "BEAR":
        b = "BEAR_deep_capitulation" if (pos is not None and pos < 0.20) else "BEAR_active"
    else:
        b = "management_do_not_filter"
    return b


CANON = {"BULL_impulse", "BULL_pullback", "BULL_excess_top", "RANGE_neutral",
         "RANGE_distribution_top_bear", "RANGE_accumulation_bottom", "BEAR_active",
         "BEAR_shallow_bounce", "BEAR_deep_capitulation", "countertrend_bounce_in_bear",
         "management_do_not_filter"}


def main():
    blocks = raw_blocks()
    print(f"RAW 15M: {len(blocks)} blocos", flush=True)
    S = load_series(blocks)
    T, L, H = S["T"], S["L"], S["H"]; N = S["N"]
    print(f"  série: N={N} barras · {ds(T[0])} -> {ds(T[-1])}", flush=True)

    # position_in_leg proxy causal = Donchian-60 (posição do low no range das últimas 60 barras)
    def pos_at(p):
        i0 = max(0, p - 60)
        lo = min(L[i0:p + 1]); hi = max(H[i0:p + 1])
        return round((L[p] - lo) / (hi - lo), 3) if hi > lo else None

    # enumerar swing-lows fractais m=3 CONFIRMADOS (confirmação em p+3)
    events = []
    for p in range(M_FRAC, N - M_FRAC):
        if not _is_swinglow(L, p, M_FRAC):
            continue
        ct = T[p + M_FRAC]                       # barra de confirmação (known-at)
        mac = macro_at(ct); leg = leg_at(ct); pos = pos_at(p)
        buck = bucket(mac, leg, pos)
        assert buck in CANON, f"balde não-canónico: {buck}"
        events.append({"t": T[p], "confirm_t": ct, "low": L[p], "macro_regime": mac,
                       "leg_state": leg, "position_in_leg": pos, "family_label": buck})
    ET = [e["t"] for e in events]
    print(f"  fractais confirmados: {len(events)}", flush=True)

    # GT: casar A1/A2 (e OTHER) ao fractal mais próximo (±6h)
    gt = json.load(open(GT_PATH))["fundos"]
    a12 = [f for f in gt if f.get("subclasse") in ("A1_pullback_fundo", "A2_pullback_raso")]
    cov0, cov1 = T[0], T[-1]
    matched = 0; out_cov = 0; contra = 0; a12_in = 0
    for f in gt:
        sub = f.get("subclasse", ""); t = int(f["t"])
        is_a12 = sub in ("A1_pullback_fundo", "A2_pullback_raso")
        if is_a12 and not (cov0 <= t <= cov1):
            out_cov += 1; continue
        if is_a12:
            a12_in += 1
        k = bisect.bisect_left(ET, t)
        best = None; bestd = SNAP + 1
        for cand in (k - 1, k, k + 1):
            if 0 <= cand < len(events) and abs(events[cand]["t"] - t) < bestd:
                bestd = abs(events[cand]["t"] - t); best = cand
        kind = "GT_A1" if sub == "A1_pullback_fundo" else ("GT_A2" if sub == "A2_pullback_raso" else "GT_OTHER")
        if best is not None and bestd <= SNAP:
            events[best]["kind"] = kind
            events[best]["gt_macro"] = f.get("macro")
            if is_a12:
                matched += 1
                if events[best]["macro_regime"] != f.get("macro"):
                    contra += 1

    for e in events:
        e.setdefault("kind", "CAND")
        e.setdefault("gt_macro", "")
        e["causal_regime_source"] = "macro_structural_v3.build_layer1(D-1)+leg_v3.build_leg_v3(4H)@confirm_bar"

    # escrever tabela
    cols = ["t", "date", "confirm_date", "kind", "macro_regime", "leg_state", "position_in_leg",
            "family_label", "causal_regime_source", "in_raw_coverage", "gt_macro"]
    fp = OUT / "a1a2_bucket_table.csv"
    with open(fp, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(cols)
        for e in events:
            w.writerow([e["t"], ds(e["t"]), ds(e["confirm_t"]), e["kind"], e["macro_regime"],
                        e["leg_state"], e["position_in_leg"], e["family_label"],
                        e["causal_regime_source"], 1, e["gt_macro"]])

    # --- relatório ---
    print("\n=== STAGE 3 — STRUCTURAL BUCKET ===")
    print(f"eventos (fractais confirmados): {len(events)}")
    print(f"GT A1/A2 total: {len(a12)} · em cobertura RAW: {a12_in} · FORA de cobertura: {out_cov}")
    print(f"GT A1/A2 casados a um fractal (±6h): {matched}/{a12_in}")
    print(f"cross-check macro (reconstruído vs GT): {contra}/{matched} contradições "
          f"({100*contra/matched:.0f}%)" if matched else "sem casamentos")
    kb = Counter(e["kind"] for e in events)
    print(f"por kind: {dict(kb)}")
    fb = Counter(e["family_label"] for e in events)
    print(f"por balde (todos): {dict(fb)}")
    ga = Counter(e["family_label"] for e in events if e["kind"] in ("GT_A1", "GT_A2"))
    print(f"BALDE dos GT A1/A2 casados: {dict(ga)}")
    gml = Counter(f"{e['macro_regime']}/{e['leg_state']}" for e in events if e["kind"] in ("GT_A1", "GT_A2"))
    print(f"macro/leg dos GT A1/A2 casados: {dict(gml)}")
    print(f"\ntabela -> {fp.relative_to(REV.parent.parent)}")

    # STOP conditions do manifest
    if a12 and out_cov / len(a12) > 0.30:
        print(f"\n🛑 STOP: {out_cov}/{len(a12)} A1/A2 FORA de cobertura (>30%)")
    if matched and contra / matched > 0.20:
        print(f"\n🛑 STOP: {contra}/{matched} contradições macro (>20%) — reconstrução diverge do GT")
    if not (a12 and out_cov / len(a12) > 0.30) and not (matched and contra / matched > 0.20):
        print("\n✅ STOP conditions: nenhuma disparada.")


if __name__ == "__main__":
    main()
