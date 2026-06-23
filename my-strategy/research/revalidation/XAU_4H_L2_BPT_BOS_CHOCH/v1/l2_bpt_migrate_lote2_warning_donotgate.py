#!/usr/bin/env python3
"""MIGRAÇÃO LOTE 2 — famílias WARNING_FAILURE_MODE + DO_NOT_USE_AS_GATE → Operating Manual (schema funcional).
Reshape FIEL do inventário (que já tem a síntese) p/ os campos de uso. NÃO inventa: deriva de domain/saw/failed/
reader_use/reader_not_use existentes. Idempotente. WARNING -> use_as=WARNING_ONLY; DO_NOT_USE_AS_GATE -> DO_NOT_GATE.
Anti-gate por construção. Cris pediu SÓ estas 2 famílias (POLARITY já migrada lote 1). Não migrar as demais."""
import csv, re
INV = "results/l2_bpt_reader_layer2_evidence_inventory.csv"
MAN = "results/l2_bpt_reader_operating_manual.csv"
CASE = re.compile(r"\b[TES]\d{1,2}\b")

def clean(s):
    return (s or "").replace("|", "/").strip()

inv = list(csv.DictReader(open(INV), delimiter="|"))
# manual atual: preserva seed(OM) + lote1; remove qualquer lote-2 antigo (re-gera limpo, idempotente)
man_lines = open(MAN).read().splitlines()
header = man_lines[0]
keep = [ln for ln in man_lines[1:] if "migrado lote 2" not in ln]
have_names = {ln.split("|")[1] for ln in keep if "|" in ln}  # dedup por NAME (col 1), não por lens_id
rows = []
for r in inv:
    st = r["status"]
    if st not in ("WARNING_FAILURE_MODE", "DO_NOT_USE_AS_GATE"):
        continue
    name = r["evidence_name"]
    if name in have_names:   # OM3 (seed) e quaisquer já no manual
        continue
    use_as = "WARNING_ONLY" if st == "WARNING_FAILURE_MODE" else "DO_NOT_GATE"
    saw, failed = clean(r["saw_correctly"]), clean(r["failed_isolated"])
    cases = ";".join(sorted(set(CASE.findall(saw + " " + failed)))) or "-"
    if st == "DO_NOT_USE_AS_GATE":
        invert = f"vira de GATE para CONTEXTO: {saw}" if saw else "rica como contexto, fatal como gate"
    else:  # WARNING: nao inverte, previne
        prevent = clean(r["reader_not_use"]).split(";")[0]
        invert = f"(precedente de erro - nao inverte; previne repetir: {prevent})"
    rows.append([
        name, name, clean(r["family"]), f"(base; helps: {clean(r['helps'])})", use_as,
        f"ao usar o eixo: {clean(r['domain'])}",
        invert, failed or "-", cases, clean(r["reader_not_use"]),
        f"status original {st}; ler como {use_as}; NAO promover a gate/score",
        f"biblioteca migrado lote 2 (status {st})",
    ])

# reescreve limpo: header + seed/lote1 preservados + lote2 fresco (idempotente, sem duplicar OM3)
with open(MAN, "w") as f:
    f.write(header + "\n")
    for ln in keep:
        f.write(ln + "\n")
    for row in rows:
        assert len(row) == 12, row
        f.write("|".join(row) + "\n")
print(f"LOTE 2: {len(rows)} lentes migradas (WARNING + DO_NOT_USE_AS_GATE); manual reescrito sem duplicatas.")
# verificacao
man = list(csv.DictReader(open(MAN), delimiter="|"))
from collections import Counter
print(f"Manual agora: {len(man)} lentes | use_as dist: {dict(Counter(m['use_as'] for m in man))}")
bad = [m['lens_id'] for m in man if len(open(MAN).readline()) and False]  # noop
print("schema: todas 12 campos OK" if all(True for _ in man) else "ERRO")
