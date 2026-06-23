#!/usr/bin/env python3
"""SELEÇÃO do CLUSTER 2 — macro quebrado + cascade profundo: RUNNER vs TRAP no MESMO contexto bear.
Pergunta viva: o que diferencia runner legitimo em macro negativo de bear-pullback-trap?
A SELEÇÃO usa outcome SO para montar o set contrastivo (igual ao hard-cluster) — a LEITURA depois e cega.
Coorte: weekly_slope < 0 E cascade <= -2 (profundo). Split runner (mfe>=5) vs trap (mfe<2). NAO plota, NAO le."""
import json
D = "results"
DOSS = {}
for l in open(f"{D}/l2_bpt_reader_dossier_276.jsonl"):
    r = json.loads(l); DOSS[int(r["bar_idx"])] = r
def fn(v):
    try: return float(v)
    except (TypeError, ValueError): return None
rows = []
for b, d in DOSS.items():
    c1 = d["camada_1_backbone"]; wk = c1.get("weekly_1d_context", {}); rb = c1.get("regime_B", {})
    pf = d["camada_0_form"].get("path_form_276", {})
    au = d.get("_AUDIT_outcome_NOT_FOR_READING", {})
    weekly = fn(wk.get("weekly_slope_decisions")); weekly = weekly if weekly is not None else fn(wk.get("weekly_slope_20pct"))
    casc = fn(rb.get("cascade_score"))
    mfe = fn(au.get("mfe_R"))
    if weekly is None or casc is None or mfe is None:
        continue
    if weekly < 0 and casc <= -2:                       # coorte: macro negativo + cascade profundo
        rows.append(dict(b=b, date=d["timestamp"][:10], weekly=round(weekly, 2), casc=casc,
                         broken=rb.get("macro_broken"), leg=c1.get("macro_reader_leg"),
                         flush=pf.get("flush"), sup=c1.get("sup_cat"), accept=pf.get("acceptance"),
                         demand=c1.get("bottom_turn"), mfe=round(mfe, 1),
                         kind="RUNNER" if mfe >= 5 else ("trap" if mfe < 2 else "mid")))
runners = sorted([r for r in rows if r["kind"] == "RUNNER"], key=lambda r: -r["mfe"])
traps = sorted([r for r in rows if r["kind"] == "trap"], key=lambda r: r["b"])
mids = [r for r in rows if r["kind"] == "mid"]
print(f"COORTE bear-macro (weekly<0 E cascade<=-2): {len(rows)} episodios | RUNNERS={len(runners)} traps={len(traps)} mid={len(mids)}")
print("\n=== RUNNERS legitimos em macro NEGATIVO (mfe>=5) — o lado que quebra a regra falsa ===")
print(f"{'bar':>5} {'date':10} {'wk':>6} {'casc':>5} {'flush':>14} {'accept':>18} {'sup_cat':>22} mfe")
for r in runners:
    print(f"{r['b']:>5} {r['date']:10} {r['weekly']:>6} {r['casc']:>5} {str(r['flush']):>14} {str(r['accept']):>18} {str(r['sup']):>22} {r['mfe']:>5}")
print("\n=== TRAPS no MESMO contexto (mfe<2) ===")
print(f"{'bar':>5} {'date':10} {'wk':>6} {'casc':>5} {'flush':>14} {'accept':>18} {'sup_cat':>22} mfe")
for r in traps:
    print(f"{r['b']:>5} {r['date']:10} {r['weekly']:>6} {r['casc']:>5} {str(r['flush']):>14} {str(r['accept']):>18} {str(r['sup']):>22} {r['mfe']:>5}")
print(f"\n(mid {len(mids)}: " + ", ".join(f"{r['b']}({r['mfe']})" for r in mids) + ")")
print("\nSELECAO so define o set contrastivo (outcome usado como no hard-cluster); leitura sera CEGA. NAO plota/le.")
