#!/usr/bin/env python3
"""V-4 — RE-DERIVAÇÃO DA RÉGUA (detector+prune+episódios+context_sl do l2_engine
sobre o frozen raw_features_2020_2026.jsonl) -> deve reproduzir os 245 bar_idx.

Gates:
  G0: alinhamento índice-a-índice raw_4h_ohlc.jsonl <-> frozen (t == ts_epoch, mesmo N)
  G1: pruned base V2 do engine == set de candidate_id do CSV l2_bpt_v2_2_pruned_base_v2.csv
  G2: episódios/reps do engine == set bar_idx de l2_bpt_uncapped_or_proxy_outcomes_276.csv
  G3: traded (context_sl != no_trade) == 245 bar_idx da régua (byte-exato, ordenado)
  G4 (bónus): colunas entry/sl da régua reproduzidas (com o quirk do sl_atr round-2dp
      de l2_bpt_sl_context_policy_results.csv -> _DA_regua_structural_letrun.py setup_ctx)

CENSO: distribuição de `tipo` (A/B/B_ctx) e `variant` nos 245 e nos 17 — quantos
dependem de bolhas (B_ctx)? (decide o que o chart live precisa)

Demanda 4H passada como ARGUMENTO (dsq CSV as-of-bar), como no sl_context.py original.
"""
import json, csv, sys, time
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import l2_engine as E

V1 = REPO / "my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1"
FROZEN = V1 / "repro_recovery/raw_features_2020_2026.jsonl"
PRUNED_CSV = V1 / "results/l2_bpt_v2_2_pruned_base_v2.csv"
UNC276_CSV = V1 / "results/l2_bpt_uncapped_or_proxy_outcomes_276.csv"
DSQ_CSV = V1 / "results/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"
REGUA_CSV = V1 / "results/l2_bpt_regua_structural.csv"
CANON17_CSV = REPO / "research/results/l2_bpt_17_trades.csv"
RAW4H = REPO / "my-strategy/research/revalidation/raw_4h_ohlc.jsonl"


def main():
    t0 = time.time()
    RAW = [json.loads(l) for l in open(FROZEN)]
    RAW.sort(key=lambda b: b['ts_epoch'])  # fonte: L2_detector_v2_2.py:19-20
    print(f"frozen: {len(RAW)} bars", flush=True)

    # G0: alinhamento índice-a-índice raw_4h_ohlc <-> frozen (bar_idx da régua vive no frozen;
    # FSM/exit vivem no raw — desalinhamento silencioso = stop avaliado na barra errada em fase 2)
    b4 = [json.loads(l) for l in open(RAW4H)]
    b4.sort(key=lambda x: x['t'])
    g0 = len(b4) == len(RAW) and all(b4[i]['t'] == RAW[i]['ts_epoch'] for i in range(len(RAW)))
    print(f"G0 alinhamento raw_4h<->frozen: {'PASS' if g0 else 'FAIL'} — {len(b4)} vs {len(RAW)} bars")
    if not g0:
        for i in range(min(len(b4), len(RAW))):
            if b4[i]['t'] != RAW[i]['ts_epoch']:
                print(f"   primeiro desalinhamento i={i}: raw t={b4[i]['t']} vs frozen ts={RAW[i]['ts_epoch']}")
                break

    det = E.make_detector(RAW)
    cands = det["run_candidate_generator"]()
    print(f"candidatos v2.2: {len(cands)} (esperado 7763) [{time.time()-t0:.0f}s]", flush=True)

    # ---- G1: prune V2 ----
    kept = [c for c in cands if not det["prune_v2"](c)]
    kept_ids = sorted(c['entry_idx'] for c in kept)
    csv_kept = sorted(int(r['candidate_id'][1:]) for r in csv.DictReader(open(PRUNED_CSV)))
    g1 = kept_ids == csv_kept
    print(f"G1 pruned base V2: {'PASS' if g1 else 'FAIL'} — engine {len(kept_ids)} vs CSV {len(csv_kept)}")
    if not g1:
        plus = sorted(set(kept_ids) - set(csv_kept)); minus = sorted(set(csv_kept) - set(kept_ids))
        print(f"   diff+ (engine só) {len(plus)}: {plus[:20]}")
        print(f"   diff- (CSV só)    {len(minus)}: {minus[:20]}")

    # ---- G2: episódios/reps ----
    slc_probe = E.make_sl_context(RAW, {})   # só p/ ATR (fonte sl_context_fullbase.py:12: reps filtram ATR)
    ATRc = slc_probe["ATR"]
    eps = E.episodes_from(kept_ids)
    reps = [e[0] for e in eps if ATRc[e[0]]]  # fonte: sl_context_fullbase.py:12
    unc276 = sorted(int(r['bar_idx']) for r in csv.DictReader(open(UNC276_CSV)))
    g2 = sorted(reps) == unc276
    print(f"G2 episódios/reps: {'PASS' if g2 else 'FAIL'} — engine {len(reps)} reps vs 276-file {len(unc276)}")
    if not g2:
        plus = sorted(set(reps) - set(unc276)); minus = sorted(set(unc276) - set(reps))
        print(f"   diff+ {len(plus)}: {plus[:20]}")
        print(f"   diff- {len(minus)}: {minus[:20]}")

    # ---- G3: context_sl -> 245 ----
    dsq = {int(r['candidate_id'][1:]): r for r in csv.DictReader(open(DSQ_CSV))}  # fonte: sl_context.py:25
    slc = E.make_sl_context(RAW, dsq)
    context_sl = slc["context_sl"]
    traded = []; notrade = []
    for i in reps:
        sl, risk, typ, dist = context_sl(i)
        if sl is None: notrade.append(i); continue
        traded.append((i, sl, risk, typ))
    regua = list(csv.DictReader(open(REGUA_CSV)))
    regua_bi = [int(r['bar_idx']) for r in regua]
    eng_bi = [x[0] for x in traded]
    g3 = eng_bi == regua_bi
    print(f"G3 régua 245 bar_idx: {'PASS' if g3 else 'FAIL'} — engine {len(eng_bi)} traded ({len(notrade)} no_trade) vs régua {len(regua_bi)}")
    if not g3:
        plus = sorted(set(eng_bi) - set(regua_bi)); minus = sorted(set(regua_bi) - set(eng_bi))
        print(f"   diff+ {len(plus)}: {plus[:20]}")
        print(f"   diff- {len(minus)}: {minus[:20]}")

    # ---- G4 (bónus): entry/sl da régua ----
    # fonte do quirk: sl_context_fullbase.py:56 (sl_atr round 2dp no CSV) +
    # _DA_regua_structural_letrun.py:36-41 (risk = SLCTX_round2 * ATR; sl = p - risk) e :111-115 (round 2dp)
    C = slc["C"]; ATR = slc["ATR"]
    reg_by_bi = {int(r['bar_idx']): r for r in regua}
    n_entry_ok = n_sl_ok = n_cmp = 0
    sl_diffs = []
    for i, sl, risk, typ in traded:
        r = reg_by_bi.get(i)
        if r is None: continue
        n_cmp += 1
        if round(C[i], 2) == float(r['entry']): n_entry_ok += 1
        sl_atr_r2 = round(risk / ATR[i], 2)
        sl_regua_style = round(C[i] - sl_atr_r2 * ATR[i], 2)
        if sl_regua_style == float(r['sl']): n_sl_ok += 1
        else: sl_diffs.append((i, sl_regua_style, float(r['sl'])))
    g4 = (n_cmp > 0 and n_entry_ok == n_cmp and n_sl_ok == n_cmp)
    print(f"G4 entry/sl byte-iguais: {'PASS' if g4 else 'FAIL'} — entry {n_entry_ok}/{n_cmp}, sl {n_sl_ok}/{n_cmp}")
    for d in sl_diffs[:10]: print(f"   sl diff bar {d[0]}: engine {d[1]} vs régua {d[2]}")

    # ---- CENSO tipo/variant (245 e 17) ----
    cand_by_idx = {c['entry_idx']: c for c in cands}
    canon17 = sorted(int(r['bar_idx']) for r in csv.DictReader(open(CANON17_CSV)))
    def censo(ids, label):
        tipos = {}; variants = {}; missing = []
        for i in ids:
            c = cand_by_idx.get(i)
            if c is None: missing.append(i); continue
            tipos[c['tipo']] = tipos.get(c['tipo'], 0) + 1
            variants[c['variant']] = variants.get(c['variant'], 0) + 1
        bctx_ids = [i for i in ids if cand_by_idx.get(i) and cand_by_idx[i]['tipo'] == 'B_ctx']
        print(f"CENSO {label}: N={len(ids)} tipos={tipos} variants={variants} -> B_ctx (bolhas-dependente): {len(bctx_ids)} {bctx_ids}" + (f" · sem candidato: {missing}" if missing else ""))
        return tipos, variants
    censo(regua_bi, "245 (régua)")
    censo(canon17, "17 (SELECT)")

    ok = g0 and g1 and g2 and g3
    print(f"\nV-4 RESULT: {'PASS' if ok else 'FAIL'} (G4 bónus: {'PASS' if g4 else 'FAIL'}) [{time.time()-t0:.0f}s]")
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
