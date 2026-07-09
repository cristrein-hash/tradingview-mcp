#!/usr/bin/env python3
"""A2 STREAMING GUARD — anti-lookahead (spec A2 §10, §13.5.12). Testes obrigatórios:
(1) TRUNCATION VERDADEIRO: Data RECONSTRUÍDO na série truncada no known_at amostrado (n=60: 40 em
r=6 + 10 em r=4 + 10 em r=8; desvio de 200 declarado — custo de reconstrução total por amostra);
o prefixo do ledger truncado tem de ser IDÊNTICO nos campos imutáveis e a região amostrada tem de
existir exatamente no known_at (nunca antes; nenhuma região com known_at > corte).
(2) known_at monotónico em todo o stream de eventos. (3) imutabilidade: campos core nunca mudam
pós-publicação (comparação prefixo truncado vs full). (4) no-retro-use: first_retest_t > known_at;
nenhum evento antes do confirmed_active da própria região. (5) bar de confirmação nunca é reteste.
(6) whitelist de campos (zero futuro/outcome/membership N96-N83). (7) builder não importa GT.
SANITY: isto é verificação de causalidade, não análise de separação."""
import json, sys, random, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from f0_raw_loader import load_cached
from f1_structural_leg_machine import Data
from a2_anchor_region_ledger import build_regions

CORE = ("region_id", "kind", "context", "price_low", "price_high", "extreme_px", "extreme_t",
        "created_from_start_bar", "created_from_end_bar", "known_at",
        "first_valid_bar_after_known_at", "latency_bars", "depth_atr", "pos96", "source")
ALLOWED = set(CORE) | {"status", "n_retests", "first_retest_t", "no_entry_on_confirmation"}

def main():
    rng = random.Random(20260709)
    bars, ts = load_cached()
    D = Data(bars, ts)
    fails = []; checks = {}
    full = {r: build_regions(D, r) for r in (4, 6, 8)}
    # (2) monotonicidade
    for r, (regs, evs) in full.items():
        ks = [e["known_at"] for e in evs]
        if any(ks[i] < ks[i-1] for i in range(1, len(ks))):
            fails.append(f"r={r}: eventos known_at não-monotónicos")
    checks["monotonic_known_at"] = "PASS" if not fails else "FAIL"
    # (4)(5) retro-use e bar de confirmação
    for r, (regs, evs) in full.items():
        for x in regs:
            if x["first_retest_t"] is not None:
                if x["first_retest_t"] + 900 <= x["known_at"]:
                    fails.append(f"r={r} {x['region_id']}: reteste antes/no known_at")
                if x["first_retest_t"] == ts[x["created_from_end_bar"]]:
                    fails.append(f"r={r} {x['region_id']}: bar de confirmação contou como reteste")
            if not x["no_entry_on_confirmation"]:
                fails.append(f"r={r} {x['region_id']}: no_entry_on_confirmation FALSE")
            if x["first_valid_bar_after_known_at"] <= x["created_from_end_bar"]:
                fails.append(f"r={r} {x['region_id']}: first_valid_bar <= barra de confirmação")
    checks["no_retro_use_and_confirmation_bar"] = "PASS" if not fails else "FAIL"
    # (6) whitelist de campos
    for r, (regs, _) in full.items():
        for x in regs[:50]:
            extra = set(x) - ALLOWED
            if extra: fails.append(f"r={r}: campos fora da whitelist: {extra}")
    checks["field_whitelist"] = "PASS" if not fails else "FAIL"
    # (7) builder não importa GT
    src = (HERE/"a2_anchor_region_ledger.py").read_text().lower()
    for banned in ("catalog_manual_tags", "manual_shapes", "primitives", "raw_features", "n96", "n83"):
        if banned in src:
            fails.append(f"builder referencia fonte proibida: {banned}")
    checks["builder_gt_free"] = "PASS" if not fails else "FAIL"
    # (1)(3) TRUNCATION VERDADEIRO
    samples = []
    for r, n in ((6, 40), (4, 10), (8, 10)):
        regs = full[r][0]
        pool = [x for x in regs if x["created_from_end_bar"] < len(ts)-2]
        samples += [(r, x) for x in rng.sample(pool, min(n, len(pool)))]
    n_ok = 0
    for r, x in samples:
        cut = x["created_from_end_bar"]          # última barra incluída = barra de confirmação
        ts_cut = ts[:cut+1]
        bars_cut = {t: bars[t] for t in ts_cut}
        Dc = Data(bars_cut, ts_cut)
        regs_c, _ = build_regions(Dc, r)
        # a região amostrada existe EXATAMENTE no corte, com campos core idênticos
        m = [y for y in regs_c if y["known_at"] == x["known_at"] and y["kind"] == x["kind"]
             and y["extreme_t"] == x["extreme_t"]]
        if not m or any(m[0][k] != x[k] for k in CORE if k != "region_id"):
            fails.append(f"TRUNC r={r} {x['region_id']}: região ausente/divergente no corte")
            continue
        # nenhuma região além do corte; prefixo idêntico nos campos core
        if any(y["known_at"] > ts[cut]+900 for y in regs_c):
            fails.append(f"TRUNC r={r} {x['region_id']}: região com known_at > corte")
            continue
        prefix_full = [y for y in full[r][0] if y["created_from_end_bar"] <= cut]
        if len(prefix_full) != len(regs_c):
            fails.append(f"TRUNC r={r} {x['region_id']}: nº de regiões prefixo {len(prefix_full)} != {len(regs_c)}")
            continue
        bad = False
        for yf, yc in zip(prefix_full, regs_c):
            if any(yf[k] != yc[k] for k in CORE if k != "region_id"):
                fails.append(f"TRUNC r={r}: campo core divergente em {yf['region_id']}"); bad = True; break
        if not bad: n_ok += 1
    checks["truncation_true"] = f"{n_ok}/{len(samples)} PASS" if n_ok == len(samples) else f"FAIL {n_ok}/{len(samples)}"
    # determinismo (imutabilidade entre runs)
    regs2, _ = build_regions(D, 6)
    h1 = hashlib.sha256(json.dumps(full[6][0], sort_keys=True).encode()).hexdigest()
    h2 = hashlib.sha256(json.dumps(regs2, sort_keys=True).encode()).hexdigest()
    checks["deterministic"] = "PASS" if h1 == h2 else "FAIL"
    if h1 != h2: fails.append("runs não determinísticos")
    out = {"checks": checks, "n_truncation_samples": len(samples), "fails": fails[:20],
           "status": "PASS" if not fails else "FAIL_A2_LOOKAHEAD_OR_RETROACTIVE_USE"}
    (HERE/"results/a2_anchor_streaming_guard_result.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
