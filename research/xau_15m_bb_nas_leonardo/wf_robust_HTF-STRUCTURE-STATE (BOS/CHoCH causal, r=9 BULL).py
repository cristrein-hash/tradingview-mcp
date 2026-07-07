#!/usr/bin/env python3
"""ROBUSTEZ NULL — HTF-STRUCTURE-STATE (BOS/CHoCH causal, r=9 BULL).
Filtro CAUSAL reproduzido byte-a-byte das strict_metrics:
  bos_state(j,r=9): caminha os swings CONFIRMADOS ate j (causal_swings_upto),
  atualiza state=+1 quando forma H acima do H anterior (BOS bull),
  state=-1 quando forma L abaixo do L anterior (BOS bear). BULL = state>=0.
  -> N_kept=43, hit3r=0.651, 28W/15L, poison 0.83, 2025 20/26, 2026 8/17.

NULL de multiplicidade/winner-curse: permuta/rotaciona os outcomes dos 96 entries e
ve com que frequencia um filtro do MESMO tamanho (N_kept=43) atinge hit3r >= observado.
Rotacoes preservam autocorrelacao temporal (mais conservador). Permutacoes = estimativa fina.
"""
import sys, random
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import ENTRIES, score, causal_swings_upto

def bos_state(j, r=9):
    sw = causal_swings_upto(j, r)
    state = 0; ph = None; pl = None
    for tp, i, pr, ci in sw:
        if tp == 'H':
            if ph is not None and pr > ph: state = 1
            ph = pr
        else:
            if pl is not None and pr < pl: state = -1
            pl = pr
    return state

# --- filtro estrito-causal ---
keep_ns = set(e['n'] for e in ENTRIES if bos_state(e['j']) >= 0)
m = score(keep_ns)
print("STRICT filter score:", m)

ENT = ENTRIES
Nsel = m['N_kept']
obs_hit = m['hit3r_kept']
obs_win = m['winners_kept']

# posicoes selecionadas (indices no array ENTRIES) — o filtro FIXO
sel_idx = [k for k, e in enumerate(ENT) if e['n'] in keep_ns]
outs = [e['out'] for e in ENT]      # vetor de outcomes na ordem temporal (ENTRIES ja ordenado por t)
n_total = len(ENT)
base_win = sum(outs)

assert len(sel_idx) == Nsel == 43
assert sum(outs[k] for k in sel_idx) == obs_win == 28

# --- NULL A: rotacoes ciclicas (preserva blocos/autocorrelacao) ---
# rotaciona o vetor de outcomes, aplica o filtro FIXO de 43 posicoes, conta winners.
rot_hits = []
for s in range(n_total):
    rot = outs[s:] + outs[:s]
    w = sum(rot[k] for k in sel_idx)
    rot_hits.append(w / Nsel)
rot_ge = sum(1 for h in rot_hits if h >= obs_hit - 1e-9)
rot_p = rot_ge / n_total

# --- NULL B: permutacoes aleatorias dos outcomes (filtro fixo de 43 posicoes) ---
# equivalente a sortear um filtro aleatorio de tamanho 43 (winner-curse por tamanho).
random.seed(1234)
NPERM = 20000
perm_hits = []
base = list(outs)
for _ in range(NPERM):
    random.shuffle(base)
    w = sum(base[k] for k in sel_idx)
    perm_hits.append(w / Nsel)
perm_ge = sum(1 for h in perm_hits if h >= obs_hit - 1e-9)
perm_p = perm_ge / NPERM

# --- NULL C: winner-curse com MULTIPLICIDADE de escala r (best-of {6,9,12}) ---
# sob outcomes permutados, escolhe o MELHOR hit entre os 3 filtros r=6/9/12 (mesmo tamanho
# de cada um) e compara com o observado do r=9. Penaliza a escolha best-of-3.
def keep_for_r(r):
    return set(e['n'] for e in ENT if bos_state(e['j'], r) >= 0)
sel_by_r = {}
for r in (6, 9, 12):
    ks = keep_for_r(r)
    sel_by_r[r] = ([k for k, e in enumerate(ENT) if e['n'] in ks])
sizes = {r: len(v) for r, v in sel_by_r.items()}
print("sizes by r:", sizes, "| real hit r=9:", obs_hit)

random.seed(99)
best_ge = 0
for _ in range(NPERM):
    random.shuffle(base)
    best = 0.0
    for r, idx in sel_by_r.items():
        if not idx: continue
        h = sum(base[k] for k in idx) / len(idx)
        if h > best: best = h
    if best >= obs_hit - 1e-9:
        best_ge += 1
multiplicity_p = best_ge / NPERM

print("\n=== NULL RESULTS ===")
print(f"observed hit3r_kept = {obs_hit} ({obs_win}/{Nsel}), base {base_win}/{n_total}")
print(f"NULL A rotacoes ciclicas (n={n_total}): P(null>=obs) = {rot_p:.4f}  [{rot_ge}/{n_total}]")
print(f"NULL B permutacoes ({NPERM}): P(null>=obs) = {perm_p:.4f}  [{perm_ge}/{NPERM}]")
print(f"NULL C best-of-r={{6,9,12}} multiplicidade ({NPERM}): P = {multiplicity_p:.4f}")

# --- gates ---
poison_ok = m['winners_cut'] < m['losers_cut']
def yr_ok(s):
    w, n = s.split('/'); w, n = int(w), int(n)
    return (w / n) > 0.542 if n else False
both_years_ok = yr_ok(m['y2025']) and yr_ok(m['y2026'])
null_p = perm_p          # p principal = permutacao (pedido literal do FAZ #1)
survives = (null_p < 0.1) and poison_ok and both_years_ok and (Nsel >= 20)

print("\n=== GATES ===")
print(f"null_p (permutacao) = {null_p:.4f}  -> <0.1 ? {null_p<0.1}")
print(f"poison_ok (winners_cut {m['winners_cut']} < losers_cut {m['losers_cut']}) = {poison_ok}")
print(f"both_years_ok (2025 {m['y2025']}, 2026 {m['y2026']} vs base 54.2%) = {both_years_ok}")
print(f"N_kept>=20 = {Nsel>=20}")
print(f"SURVIVES = {survives}")
