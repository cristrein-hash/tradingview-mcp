#!/usr/bin/env python3
"""BLOCKER — claims ledger para labs XAU 15M (XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1 §Stage8/9).
Mata o 'fiz uma analise, apareceu 61%'. BLOQUEIA (exit 1) se o relatorio tem metricas mas nao ha ledger,
ou se alguma linha do ledger nao aponta script+input+output+source_ref, ou se numeros do report nao
aparecem no ledger. Todo N/WR/R/DD/lift/null/AUC/% precisa de fonte mecanica.

Regras que bloqueiam:
  - report com metricas e ledger ausente/vazio
  - linha de ledger sem script / input_file / output_file / source_ref
  - status invalido (fora do vocabulario do protocolo)
  - numero-metrica no report ausente do ledger (WARN se >threshold; FAIL se ledger vazio)
Saida OK: 'CLAIMS_LEDGER_PASS'."""
import sys, os, re, csv, argparse

REQ_COLS = ["claim_id","number","metric","script","input_file","output_file","source_ref","raw_or_derived","status"]
VALID_STATUS = {"VERIFIED_RAW","VERIFIED_DERIVED","EXPLORATORY","REVIEW_LAYER","RISK_CONTROL","INVALID","NOT_FOR_DECISION"}
# padroes de metrica num report: capturam SO a parte NUMERICA (grupo 1) — nao os nomes de metrica.
METRIC_PATTERNS = [
    r"\bN\s*=?\s*(\d{2,})",
    r"\bWR\s*=?\s*(\d+(?:[.,]\d+)?)",
    r"(?<![\w-])([+-]\d+(?:[.,]\d+)?)\s*R\b",   # +13R / -27R (nao 'hit-3R')
    r"\bDD\s*[=:-]?\s*([-−]?\d+(?:[.,]\d+)?)",
    r"\bP\s*=\s*(0[.,]\d+)",
    r"\bAUC\s*(0[.,]\d+)",
    r"\bhit[-_ ]?3r\s*(0[.,]\d+)",
    r"(\d{1,3}[.,]\d)\s*%",
]

def read_ledger(path):
    if not path or not os.path.exists(path): return None
    with open(path, newline="", encoding="utf-8", errors="replace") as fh:
        return list(csv.DictReader(fh))

def report_metrics(path):
    if not path or not os.path.exists(path): return []
    body = open(path, encoding="utf-8", errors="replace").read()
    hits = []
    for pat in METRIC_PATTERNS:
        for m in re.finditer(pat, body, re.IGNORECASE):
            hits.append(m.group(1).strip())   # SO a parte numerica
    return hits

def norm_num(s):
    m = re.search(r"[-−]?\d+(?:[.,]\d+)?", s)
    return m.group(0).replace(",", ".").replace("−", "-") if m else None

def main():
    ap = argparse.ArgumentParser(description="BLOCKER claims-ledger para labs XAU 15M (protocolo V1).")
    ap.add_argument("--report", required=True, help="doc do relatorio com metricas")
    ap.add_argument("--ledger", required=True, help="CSV claims ledger")
    ap.add_argument("--max-unsourced", type=int, default=0, help="nº max de metricas sem ledger antes de FAIL (default 0)")
    a = ap.parse_args()

    fails, warns = [], []
    metrics = report_metrics(a.report)
    ledger = read_ledger(a.ledger)

    if not os.path.exists(a.report):
        print(f"CLAIMS_LEDGER_FAIL\n  - report inexistente: {a.report}"); return 1
    if ledger is None:
        if metrics:
            print("CLAIMS_LEDGER_FAIL")
            print(f"  - report tem {len(metrics)} metricas mas ledger ausente: {a.ledger}")
            return 1
        print("CLAIMS_LEDGER_PASS (report sem metricas, ledger nao exigido)"); return 0

    # colunas + linhas do ledger
    if ledger:
        cols = set(ledger[0].keys())
        for c in REQ_COLS:
            if c not in cols: fails.append(f"ledger sem coluna obrigatoria: '{c}'")
    real_rows = [r for r in ledger if (r.get("claim_id") or "").strip() and not (r.get("claim_id","").startswith("EXAMPLE"))]
    for r in real_rows:
        cid = r.get("claim_id","?")
        for c in ("script","input_file","output_file","source_ref"):
            if not (r.get(c) or "").strip(): fails.append(f"claim {cid}: sem {c} (claim sem fonte)")
        st = (r.get("status") or "").strip()
        if st and st not in VALID_STATUS: fails.append(f"claim {cid}: status invalido '{st}' (usar {sorted(VALID_STATUS)})")

    # metricas do report cobertas pelo ledger
    if metrics and not real_rows:
        print("CLAIMS_LEDGER_FAIL")
        print(f"  - report tem {len(metrics)} metricas mas ledger sem linhas reais (so template/EXAMPLE)")
        return 1
    ledger_nums = {norm_num(r.get("number","")) for r in real_rows if norm_num(r.get("number",""))}
    unsourced = []
    for mtxt in metrics:
        n = norm_num(mtxt)
        if n and n not in ledger_nums: unsourced.append(mtxt)
    # dedup
    unsourced = sorted(set(unsourced))
    if len(unsourced) > a.max_unsourced:
        fails.append(f"{len(unsourced)} metricas no report sem numero correspondente no ledger (max {a.max_unsourced}): {unsourced[:8]}")

    for w in warns: print(f"WARN  {w}")
    if fails:
        print("CLAIMS_LEDGER_FAIL")
        for f in fails: print(f"  - {f}")
        return 1
    print(f"CLAIMS_LEDGER_PASS ({len(real_rows)} claims, {len(metrics)} metricas)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
