#!/usr/bin/env python3
"""DA ATAQUE 4 — determinismo + contagens: recompute independente (transcrição _DA_mtf_common)
deve reproduzir results/cris_trades_mtf_indicator_map_20260704.json: 57 células de lente,
par campeão, lista de conjunções e ctx integral de 3 trades (spot n=1, n=18, n=35)."""
import json
import _DA_mtf_common as C

PUB = json.load(open(C.HERE / "results" / "cris_trades_mtf_indicator_map_20260704.json"))
trc = C.trades_ctx("orig")
ct = C.controls_ctx("orig", 0, "g_entry")
print(f"controles recomputados: {len(ct)} | publicado: {PUB['n_controls']}")

lifts, cands, best = C.pipeline(trc, [{k: v for k, v in o.items() if k != '_cj_t'} for o in ct])
bad = 0
for key, (a, b, l) in lifts.items():
    pa, pb, pl = PUB["lifts"][f"{key[0]}|{key[1]}"]
    if abs(a - pa) > 1e-12 or abs(b - pb) > 1e-12:
        bad += 1; print(f"  MISMATCH {key}: recomputado ({a:.4f},{b:.4f}) vs publicado ({pa:.4f},{pb:.4f})")
print(f"células de lente idênticas: {57 - bad}/57")

pub_best = PUB["conjunctions"]
ok_pairs = 0
for (nm, a, b, l), (pnm, pa, pb, pl) in zip(best[:len(pub_best)], pub_best):
    if nm == pnm and abs(a - pa) < 1e-12 and abs(b - pb) < 1e-12: ok_pairs += 1
    else: print(f"  PAIR MISMATCH: {nm} ({a:.4f},{b:.4f}) vs {pnm} ({pa:.4f},{pb:.4f})")
print(f"conjunções idênticas: {ok_pairs}/{len(pub_best)}")
a, b, l = C.pair_lift(trc, ct)
print(f"par campeão recomputado: cris {100*a:.1f}% ctrl {100*b:.2f}% lift {l:.2f}x (publicado 60%/7.32%/8.20x)")

# spot 3 trades: ctx integral vs publicado
pub_tr = {t["n"]: t for t in PUB["trades"]}
for i, n in ((0, 1), (17, None), (34, None)):
    tr = C.TR[i]; n = tr["n"]
    mine = C.full_ctx(tr["t"], tr["entry"], "orig")
    ref = pub_tr[n]["ctx"]
    same = all(mine[tf] == ref[tf] for tf in ("15M", "30M", "1H"))
    print(f"trade n={n} ({tr['utc']}): ctx idêntico nos 3 TFs = {same}")
    if not same:
        for tf in ("15M", "30M", "1H"):
            for k in mine[tf]:
                if mine[tf][k] != ref[tf][k]: print(f"    {tf}.{k}: {mine[tf][k]} vs {ref[tf][k]}")

# cache p/ ataques 1 e 3
json.dump({"trc": trc, "ct": ct}, open(C.SCRATCH / "ctx_orig_shift0.json", "w"))
print(f"cache salvo: {C.SCRATCH}/ctx_orig_shift0.json")
