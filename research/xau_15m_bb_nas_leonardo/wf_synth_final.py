import sys; sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import ENTRIES, score

# ---------------------------------------------------------------------------
# SINTESE FINAL — filtro macro-contextual causal-clean para XAU 15M LONG.
# Desenho pedido: (c) contexto macro (BULL-markup u bull-in-bear u range-demand)
#                 + (a) maturidade da perna (cortar exaustao-topo)
#                 + (b) direcao HTF (cortar perna-bear-ativa).
# Todos CAUSAIS, estruturais, sem lookahead.
#
# ESTADO DA AUDITORIA: de 7 hipoteses estruturais, exatamente 1 sobreviveu
# aos 4 gates (null_p<0.1 por 2 nulls + poison<0.9 + ambos anos+ + N>=20):
#   impulse_efficiency_prior_leg (Kaufman ER causal >= 0.26).
# As features que MATERIALIZAM o desenho (a)+(b)+(c) — HTF-direction,
# range-demand, bull-in-bear, leg-maturity — TODAS reprovaram
# (2026<base OU null_p>0.1 OU poison>=0.9). Logo NAO existe conjunto de
# multiplos sobreviventes para intersectar: a "combinacao" colapsa no unico
# sobrevivente.
# ---------------------------------------------------------------------------

BASE = [e["n"] for e in ENTRIES]

# keep_ns causal-clean do UNICO sobrevivente (ER>=0.26), tal como devolvido
# pela auditoria (reproduz strict_metrics byte-a-byte).
ER_KEEP = [1,2,3,6,7,8,12,13,14,18,20,22,24,28,30,31,37,38,40,41,42,43,52,53,54,
           61,63,64,65,66,68,69,70,71,72,73,74,75,76,77,78,80,81,85,86,87,88,90,
           91,92,95,96]

print("=== BASE (sem filtro) ===")
print(score(BASE))
print()
print("=== SOBREVIVENTE UNICO: impulse_efficiency ER>=0.26 ===")
s = score(ER_KEEP)
print(s)
print()

# Sanidade: os 4 gates aplicados ao proprio kit (numeros REAIS, nao estimados)
baseW = sum(e["out"] for e in ENTRIES); baseN = len(ENTRIES)
base_hit = baseW/baseN
poison = s["poison_ratio"]
y25 = [int(x) for x in s["y2025"].split("/")]; y26 = [int(x) for x in s["y2026"].split("/")]
y25r = y25[0]/y25[1]; y26r = y26[0]/y26[1]
print("=== GATES (verificados no kit) ===")
print(f"base hit-3R        : {base_hit:.4f}  ({baseW}/{baseN})")
print(f"hit3r_kept         : {s['hit3r_kept']:.4f}  (lift {s['hit3r_kept']-base_hit:+.4f})")
print(f"poison_ratio<0.9   : {poison}  -> {'PASS' if poison<0.9 else 'FAIL'}")
print(f"y2025 vs base      : {y25r:.3f} vs {base_hit:.3f} -> {'PASS' if y25r>base_hit else 'FAIL'}")
print(f"y2026 vs base      : {y26r:.3f} vs {base_hit:.3f} -> {'PASS' if y26r>base_hit else 'FAIL'}")
print(f"N_kept>=20         : {s['N_kept']} -> {'PASS' if s['N_kept']>=20 else 'FAIL'}")
print()
print("keep_ns final (N=%d):" % s["N_kept"], ER_KEEP)
