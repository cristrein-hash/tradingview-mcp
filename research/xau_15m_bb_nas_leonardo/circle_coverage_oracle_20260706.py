#!/usr/bin/env python3
"""COBERTURA CÍRCULO-A-CÍRCULO + TETO ORACLE (2026-07-06, passos 1b+2 do plano aprovado).
FIX-MATCHER (assimétrico, justificado pela autópsia): candidato captura círculo se
  |Δt| <= 8h  E  −3ATR <= (flush_cand − low_círculo) <= +1ATR
(comprar o MESMO fundo com pavio mais fundo = captura; entrar >1ATR ACIMA segue rejeitado —
o lado que inflava recall era o de cima, preservado.)
SAÍDAS:
  1. Cobertura por círculo com matcher v1 (simétrico) vs v2 (assimétrico) — quais círculos entram
  2. TETO ORACLE por círculo: entre os candidatos que capturam o círculo, o resultado 3R do
     MELHOR (oracle) e do PIOR e do 1º-cronológico (realista sem escolha) — quanto o universo
     OFERECE nos 60 fundos do Cris
  3. Inventário de features por círculo capturado (p/ passo 3: famílias estruturais)
SEM look de seleção: oracle é teto declarado, não estratégia. Círculo 34 fica documentado como
warmup-hole (conserto de gerador = coleta/stitch futuro, não patch aqui).
SANITY_PROBE: sha do GT · matcher v2 só relaxa o lado de BAIXO · números por círculo impressos
1-a-1 p/ reconciliação visual do Cris."""
import json, bisect, hashlib
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
UNIV = sorted([u for u in U if u["cj_t"] in R3], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]

def matches(g, v2=False):
    out = []
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"] + 8 * 3600:
        u = UNIV[j]
        a = u.get("g_atr") or 5.0
        d = (u["g_sl"] + 0.1 * a) - g["flush_low"]
        ok = abs(d) <= a if not v2 else (-3 * a <= d <= 1 * a)
        if ok:
            out.append(u)
        j += 1
    return out

print(f"{'#':>3} {'data':<17} {'v1':>3} {'v2':>3}  oracle  primeiro  pior")
tot = {"v1": 0, "v2": 0}
oracle_net = first_net = 0.0
oracle_rows = []
for gi, g in enumerate(GT):
    m1 = matches(g); m2 = matches(g, v2=True)
    tot["v1"] += bool(m1); tot["v2"] += bool(m2)
    if m2:
        nets = sorted(((R3[u["cj_t"]]["net3"], u) for u in m2), key=lambda x: -x[0])
        best, worst = nets[0][0], nets[-1][0]
        first = R3[sorted(m2, key=lambda u: u["cj_t"])[0]["cj_t"]]["net3"]
        oracle_net += best; first_net += first
        oracle_rows.append((gi, best, first, len(m2)))
        print(f"{gi:>3} {dt.datetime.utcfromtimestamp(g['flush_t']).strftime('%Y-%m-%d %H:%M'):<17} "
              f"{len(m1):>3} {len(m2):>3}  {best:>+5.1f}   {first:>+5.1f}  {worst:>+5.1f}")
    else:
        print(f"{gi:>3} {dt.datetime.utcfromtimestamp(g['flush_t']).strftime('%Y-%m-%d %H:%M'):<17} "
              f"{len(m1):>3}   0   —")
print(f"\ncobertura: v1 {tot['v1']}/60 · v2 {tot['v2']}/60")
print(f"TETO nos círculos capturados (v2): oracle {oracle_net:+.1f}R · 1º-cronológico {first_net:+.1f}R "
      f"· hit-oracle {sum(1 for _, b, _, _ in oracle_rows if b > 0)}/{len(oracle_rows)}"
      f" · hit-1º {sum(1 for _, _, f2, _ in oracle_rows if f2 > 0)}/{len(oracle_rows)}")
json.dump({"v1": tot["v1"], "v2": tot["v2"], "oracle_net": round(oracle_net, 1),
           "first_net": round(first_net, 1),
           "rows": [{"gi": gi, "best": b, "first": f2, "n_cand": nc} for gi, b, f2, nc in oracle_rows]},
          open(HERE / "results" / "circle_coverage_oracle_20260706.json", "w"), indent=1)
print("OK → results/circle_coverage_oracle_20260706.json")
