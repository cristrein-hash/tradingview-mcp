#!/usr/bin/env python3
"""AUDIT da LEITURA CONVERGENTE — testa se a CONVICCAO (julgamento convergente do episodio, NAO um fator isolado)
separa RUNNER de STOPPER. Le a conviccao do dossie congelado + labels guardados (l2_bpt_confluence_dataset, fora do
pacote cego) + mfe_R (outcomes). SANITY_PROBE: calibracao em 31 contrastivos, NAO validacao. Read-only. Verified 2026-06-24."""
import json, re, csv, collections

DOS = "results/confluence_reading/reader_dossier_FROZEN.md"
conv = {}
for line in open(DOS):
    m = re.search(r"EPISODE\s+(\d+).*CONVICTION:\s*(HIGH|MED|LOW)\b", line)
    if m: conv[int(m.group(1))] = m.group(2)
lab = {int(json.loads(l)["bar_idx"]): json.loads(l)["_label_AUDIT_ONLY"] for l in open("results/l2_bpt_confluence_dataset.jsonl")}
mfe = {int(r["bar_idx"]): float(r["mfe_R"]) for r in csv.DictReader(open("results/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}

eps = sorted(conv)
print(f"AUDIT LEITURA CONVERGENTE — {len(eps)} episodios; conviccao parseada do dossie congelado.\n")
order = {"HIGH": 3, "MED": 2, "LOW": 1}
# contingencia conviccao x label
ct = collections.defaultdict(lambda: collections.Counter())
for b in eps: ct[conv[b]][lab.get(b, "?")] += 1
print(f"{'conviccao':>8} | {'n':>3} | {'RUNNER':>6} | {'STOPPER':>7} | {'mean mfe_R':>10} | {'runner-rate':>11}")
for cv in ("HIGH", "MED", "LOW"):
    bs = [b for b in eps if conv[b] == cv]
    if not bs: continue
    nr = sum(1 for b in bs if lab.get(b) == "RUNNER"); ns = sum(1 for b in bs if lab.get(b) == "STOPPER")
    mm = sum(mfe.get(b, 0) for b in bs) / len(bs)
    print(f"{cv:>8} | {len(bs):>3} | {nr:>6} | {ns:>7} | {mm:>10.2f} | {nr/len(bs):>10.0%}")

# separacao: conviccao alta deveria correr; baixa deveria parar
hi = [b for b in eps if order[conv[b]] >= 2]  # HIGH+MED
lo = [b for b in eps if conv[b] == "LOW"]
rr_hi = sum(1 for b in hi if lab.get(b) == "RUNNER") / max(1, len(hi))
rr_lo = sum(1 for b in lo if lab.get(b) == "RUNNER") / max(1, len(lo))
print(f"\nRunner-rate HIGH+MED={rr_hi:.0%} ({len(hi)} ep) vs LOW={rr_lo:.0%} ({len(lo)} ep) | lift={rr_hi/max(0.01,rr_lo):.2f}x")
# correlacao de ranking conviccao x mfe
print(f"\nmean mfe_R: HIGH={sum(mfe[b] for b in eps if conv[b]=='HIGH')/max(1,sum(1 for b in eps if conv[b]=='HIGH')):.2f} "
      f"MED={sum(mfe[b] for b in eps if conv[b]=='MED')/max(1,sum(1 for b in eps if conv[b]=='MED')):.2f} "
      f"LOW={sum(mfe[b] for b in eps if conv[b]=='LOW')/max(1,sum(1 for b in eps if conv[b]=='LOW')):.2f}")
# MISSES (onde a confluencia errou)
print("\nMISSES (conviccao vs realidade):")
for b in eps:
    if conv[b] == "LOW" and lab.get(b) == "RUNNER":
        print(f"  LOW->RUNNER (perdeu runner): #{b} mfe={mfe.get(b)}")
    if conv[b] == "HIGH" and lab.get(b) == "STOPPER":
        print(f"  HIGH->STOPPER (falso fuel): #{b} mfe={mfe.get(b)}")
print("\nNOTA: calibracao em 31 contrastivos (nao validacao). Mede a CONFLUENCIA (julgamento), nao um fator.")
