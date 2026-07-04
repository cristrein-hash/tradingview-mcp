#!/usr/bin/env python3
"""DA ATAQUE 1 — vantagem de maturidade dos controles.
Trades t0 = pullback maduro (cand_dt_bars 0-11 após cj do candidato matched; cj = flush+3);
controles medidos no cj_t. supply_far/demand_near dependem da posição micro → o par campeão
sobrevive medindo os controles +4/+12/+20 barras APÓS o cj deles? (preço = close 15M na barra
deslocada; variante shift=0/close15 isola o efeito da definição de preço)."""
import json
import _DA_mtf_common as C

an = json.load(open(C.HERE / "results" / "cris_trades_analysis_20260704.json"))
dts = sorted(r["cand_dt_bars"] for r in an if r.get("cand_dt_bars") is not None)
print(f"lateness dos 35 (cand_dt_bars, {len(dts)} matched): min={dts[0]} mediana={dts[len(dts)//2]} max={dts[-1]} | não-matched={35-len(dts)}")

# g_entry vs close15 no cj_t (sanity da definição de preço)
diffs = []
for r in C.CTRL[:200]:
    c, tb = C.close15_at(r["cj_t"])
    if c is not None: diffs.append(abs(c - r["g_entry"]))
print(f"|g_entry − close15(cj_t)| (200 primeiros controles): mediana={sorted(diffs)[len(diffs)//2]:.2f}$ max={max(diffs):.2f}$")

cache = json.load(open(C.SCRATCH / "ctx_orig_shift0.json"))
trc = cache["trc"]

print(f"\n{'VARIANTE CONTROLES':<28}{'n_ctrl':>7}{'par: cris':>10}{'ctrl':>8}{'lift':>7}   {'sf3@15M ctrl':>13}{'dn1@1H ctrl':>12}")
variants = [("shift0 g_entry (PUBLICADO)", cache["ct"]),
            ("shift0 close15", C.controls_ctx("orig", 0, "close15")),
            ("shift+4 close15", C.controls_ctx("orig", 4, "close15")),
            ("shift+12 close15", C.controls_ctx("orig", 12, "close15")),
            ("shift+20 close15", C.controls_ctx("orig", 20, "close15"))]
out = {}
for name, ct in variants:
    a, b, l = C.pair_lift(trc, ct)
    sf = C.cov(ct, "15M", "supply_far3atr"); dn = C.cov(ct, "1H", "demand_near1atr")
    out[name] = (len(ct), a, b, l, sf, dn)
    print(f"{name:<28}{len(ct):>7}{100*a:>9.1f}%{100*b:>7.2f}%{l:>6.2f}x   {100*sf:>12.1f}%{100*dn:>11.1f}%")
json.dump({k: v for k, v in out.items()}, open(C.SCRATCH / "attack1_shift_results.json", "w"), indent=1)
