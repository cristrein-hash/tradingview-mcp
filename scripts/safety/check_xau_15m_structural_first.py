#!/usr/bin/env python3
"""BLOCKER — structural-first para labs XAU 15M (XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1 §C).
A TRAVA MAIS IMPORTANTE: sem macro_regime + leg_state + family, nenhum indicador vira evidencia.
BLOQUEIA (exit 1) se o(s) output(s) do lab cruzam indicadores SEM colunas de balde estrutural,
ou se usam baldes fora da lista canonica. Le manifest (buckets declarados) + outputs (CSV).

Regras que bloqueiam:
  - output CSV sem coluna de regime estrutural (macro_regime|regime|causal_regime)
  - output CSV sem coluna de familia (family|fam|family_label)
  - (aviso) sem leg_state/position_in_leg/regime_phase
  - structural_buckets do manifest fora da lista canonica
  - relatorio que declara 'global scan' como DECISAO sem qualificador (esteril/nao-gate/review)
Saida OK: 'STRUCTURAL_FIRST_PASS'."""
import sys, os, re, json, argparse, csv

CANON_BUCKETS = {
    "BULL_impulse","BULL_pullback","BULL_excess_top",
    "RANGE_neutral","RANGE_distribution_top_bear","RANGE_accumulation_bottom",
    "BEAR_active","BEAR_shallow_bounce","BEAR_deep_capitulation",
    "countertrend_bounce_in_bear","management_do_not_filter",
}
REGIME_COLS = ("macro_regime","regime","causal_regime","regime_v5_causal")
FAMILY_COLS = ("family","fam","family_label","subfam")
NICE_COLS   = ("leg_state","position_in_leg","regime_phase","frac_leg")

def load_manifest(path):
    if not os.path.exists(path): return None
    txt = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r"```json\s*(\{.*?\})\s*```", txt, re.DOTALL)
    try: return json.loads(m.group(1)) if m else None
    except Exception: return None

def csv_headers(path):
    try:
        with open(path, newline="", encoding="utf-8", errors="replace") as fh:
            return next(csv.reader(fh))
    except Exception:
        return None

def main():
    ap = argparse.ArgumentParser(description="BLOCKER structural-first para labs XAU 15M (protocolo V1).")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--results", nargs="*", default=[], help="CSV(s) de output do lab (se vazio, usa manifest.outputs)")
    ap.add_argument("--report", help="doc do relatorio (checa 'global scan' como decisao)")
    a = ap.parse_args()

    fails, warns = [], []
    man = load_manifest(a.manifest)
    if man is None:
        print("STRUCTURAL_FIRST_FAIL\n  - manifest ausente/invalido"); return 1

    # baldes canonicos
    for b in man.get("structural_buckets", []):
        if b not in CANON_BUCKETS:
            fails.append(f"balde fora da lista canonica: '{b}' (ver protocolo §C)")
    if not man.get("structural_buckets"):
        fails.append("manifest sem structural_buckets declarados")

    results = a.results or man.get("outputs", [])
    if not results:
        fails.append("nenhum output/CSV para verificar structural-first")
    csv_results = [r for r in results if str(r).endswith(".csv")]
    if results and not csv_results:
        warns.append("outputs nao contem CSV — structural-first verifica colunas em CSV")

    for r in csv_results:
        if not os.path.exists(r):
            warns.append(f"output ainda inexistente (correr o lab): {r}"); continue
        hdr = csv_headers(r)
        if not hdr:
            fails.append(f"CSV ilegivel/vazio: {r}"); continue
        hset = {h.strip().lower() for h in hdr}
        if not any(c in hset for c in REGIME_COLS):
            fails.append(f"{r}: sem coluna de regime estrutural {REGIME_COLS} — indicador sem contexto = PROIBIDO")
        if not any(c in hset for c in FAMILY_COLS):
            fails.append(f"{r}: sem coluna de familia {FAMILY_COLS}")
        if not any(c in hset for c in NICE_COLS):
            warns.append(f"{r}: sem leg_state/position_in_leg/regime_phase (recomendado)")

    if a.report and os.path.exists(a.report):
        body = open(a.report, encoding="utf-8", errors="replace").read().lower()
        for m in re.finditer(r"[^.\n]*global\s+(scan|cross|cruzamento)[^.\n]*", body):
            seg = m.group(0)
            if not re.search(r"esteril|est[eé]ril|nao[- ]gate|n[aã]o[- ]gate|review|refut|sem edge|nao decid|n[aã]o decid", seg):
                fails.append(f"report usa 'global scan' como decisao sem qualificador: '...{seg.strip()[:90]}...'")
                break

    for w in warns: print(f"WARN  {w}")
    if fails:
        print("STRUCTURAL_FIRST_FAIL")
        for f in fails: print(f"  - {f}")
        return 1
    print("STRUCTURAL_FIRST_PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
