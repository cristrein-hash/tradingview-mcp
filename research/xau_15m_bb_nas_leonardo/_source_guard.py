#!/usr/bin/env python3
"""SOURCE GUARD — XAU 15M BB+NAS (mínimo, específico desta frente; não existia guard 15M).
Constrição mecânica: o Stage-B só pode ler do RAW gz 15M (fonte canônica) ou das primitivas geradas DELE
(build_causal_primitives.py → primitives/*.json). FALHA (exit 1) se um script referenciar QUALQUER fonte
derivada/secundária proibida (raw_features, slim, packets, regime files, repro_recovery, eval_tmp, artefatos 4H).
Verifica também a cadeia: build_causal_primitives.py lê só o RAW gz. Roda standalone com os scripts como args.
Verified 2026-06-25."""
import sys, re, json
from pathlib import Path
HERE = Path(__file__).parent
RAW_DIR = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M"
ALLOWED_DATA = [RAW_DIR, str(HERE / "primitives")]              # únicas raízes de dados permitidas
FORBIDDEN = [  # tokens que, se aparecerem como FONTE de dados, provam uso de derivado/secundário
    "raw_features", "slim_features", "slim/", "repro_recovery", "regime_B", "regime_classifier",
    "regime_v3", "macro_bear", "_packet", "candidate_pool", "eval_tmp", "l2_bpt_", "dataset_registry",
    "_DA_L1_", "raw_features_2020_2026",
]
# tokens que provam leitura de fonte permitida (pelo menos um deve existir num script que lê dados)
# calibração 2026-07-04: exec do engine sancionado = cadeia permitida (o engine lê primitives e passa o guard)
ALLOWED_TOKENS = ["raw_replay/XAUUSD/15M", "primitives", "build_causal_primitives",
                  "engine_substrate4_v5_hourcausal",
                  # intermediário sancionado (determinístico, gerado por lab_g_context_inventory.py guard-PASS
                  # a partir de engine+primitives; regenerável; NUNCA fonte de verdade — RAW segue autoridade)
                  "lab_g_candidates.jsonl"]

def scan(script: Path):
    txt = script.read_text(errors="ignore")
    viol = []
    for tok in FORBIDDEN:
        for m in re.finditer(re.escape(tok), txt):
            ln = txt[: m.start()].count("\n") + 1
            # ignora se o token aparece só em comentário de NEGAÇÃO explícita ("não usar", "NÃO", "proibido")
            line = txt.splitlines()[ln - 1] if ln - 1 < len(txt.splitlines()) else ""
            if re.search(r"(não|nao|never|proib|forbidden|NÃO|guard|FORBIDDEN)", line, re.I):
                continue
            # calibração 2026-07-04 (classe GUARDRAIL_CARD): token como NOME DE CAMPO sendo ESCRITO
            # (f["macro_bear"]=...) não é leitura de fonte proibida — só flagra uso como FONTE de dados.
            if re.search(r'\[["\']' + re.escape(tok) + r'["\']\]\s*=[^=]', line):
                continue
            viol.append((tok, ln, line.strip()[:90]))
    reads_data = any(t in txt for t in (["gzip.open", "json.load", "open("]))
    has_allowed = any(t in txt for t in ALLOWED_TOKENS)
    return viol, (reads_data and not has_allowed)

def main(scripts):
    ok = True
    print("=== SOURCE GUARD 15M ===")
    print(f"  fontes permitidas: RAW gz 15M + primitives/ (geradas do RAW)")
    for s in scripts:
        p = Path(s)
        if not p.exists():
            print(f"  [SKIP] {p} (inexistente)"); continue
        viol, missing_src = scan(p)
        if viol:
            ok = False
            print(f"  [FAIL] {p.name}: referência a fonte PROIBIDA:")
            for tok, ln, line in viol: print(f"         L{ln} «{tok}» :: {line}")
        elif missing_src:
            ok = False
            print(f"  [FAIL] {p.name}: lê dados mas não referencia fonte permitida (RAW/primitives).")
        else:
            print(f"  [PASS] {p.name}")
    # proveniência registrada?
    man = HERE / "MANIFEST_PROVENANCE.json"
    if man.exists():
        m = json.loads(man.read_text())
        print(f"  [PROV] Custom OB v11 = {m.get('bigbeluga_proxy', {}).get('status', '?')}")
    else:
        print("  [WARN] MANIFEST_PROVENANCE.json ausente — registrar linhagem antes de prosseguir.")
    print("=== GUARD", "PASS ===" if ok else "FAIL ===")
    return 0 if ok else 1

if __name__ == "__main__":
    args = sys.argv[1:] or [str(HERE / "build_causal_primitives.py"), str(HERE / "detect_candidates.py")]
    sys.exit(main(args))
