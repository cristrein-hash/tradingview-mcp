#!/usr/bin/env python3
"""DA INDEPENDENTE — 35 trades manuais do Cris (2026-07-04).
Ataques: (2) reprodução manual letrun 5 trades (implementação NOVA, path bar-a-bar) +
tipo de saída (trail vs fim-de-janela) p/ TODOS os 35 + auditoria de fill/grade de barras ·
(3) plan_outcome (#19 SL, OPENs = truncamento de bloco? ambiguidade same-bar) ·
(4) sensibilidade do matching (6/12/24 barras) + natureza dos 7 SEM-FLUSH ·
(5) reprodução das medianas + fração exata swept=0 ·
(6) assinatura candidata EXPLORATORY (lista pré-declarada, sem otimização)."""
import json, hashlib, bisect
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
TICK = 0.01
CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0], "SEAL FAIL"
U = [json.loads(l) for l in open(CANON)]
Ubyt = sorted(U, key=lambda r: r["cj_t"])
ns = {"__name__": "e", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "e", "exec"), ns)
PRIMK, HMAX, RCAP = ns["PRIMK"], ns["HMAX"], ns["RCAP"]
regime_h = ns["regime_hourcausal"]

raw = json.load(open(HERE / "results" / "cris_manual_trades_20260704.json"))
trades = []
for sh in raw["shapes"]:
    if sh.get("name") != "long_position": continue
    p = sh["props"]; pts = p["points"]; props = p["properties"]
    entry = pts[0]["price"]; t0 = pts[0]["time"]
    trades.append({"id": sh["id"], "t": t0, "entry": entry,
                   "sl": round(entry - props["stopLevel"] * TICK, 2),
                   "tgt": round(entry + props["profitLevel"] * TICK, 2)})
trades.sort(key=lambda x: x["t"])
assert len(trades) == 35, f"esperado 35, veio {len(trades)}"

def find_block(t):
    for k, pr in PRIMK.items():
        s = pr["series"]
        if s[0]["t"] <= t <= s[-1]["t"]: return k, s
    return None, None

# ============ ATAQUE A: grade de barras + fill do entry ============
print("=" * 100)
print("A. GRADE DE BARRAS + FILL DO ENTRY (entry desenhado é preenchível na barra j0?)")
fill_issues = 0
for i, tr in enumerate(trades, 1):
    bk, s = find_block(tr["t"])
    ts = [b["t"] for b in s]
    j0 = bisect.bisect_right(ts, tr["t"]) - 1
    bar = s[j0]
    grid = tr["t"] % 900
    gap = (tr["t"] - bar["t"]) // 900
    inside = bar["l"] <= tr["entry"] <= bar["h"]
    # se fora da barra j0: quando o preço seria tocado depois?
    note = ""
    if not inside:
        fill_issues += 1
        touched = None
        for k in range(j0 + 1, len(s)):
            if s[k]["l"] <= tr["entry"] <= s[k]["h"]: touched = k - j0; break
        note = f"  ENTRY FORA da barra j0 [{bar['l']},{bar['h']}] → tocado {touched} barras depois" if touched else "  ENTRY NUNCA tocado depois"
    flag = "" if grid == 0 and gap == 0 else f"  grid%900={grid} gap_j0={gap}b"
    if flag or note: print(f"  #{i:>2} t={tr['t']}{flag}{note}")
print(f"  → todos t0 na grade (mod900==0): {all(tr['t'] % 900 == 0 for tr in trades)}")
print(f"  → entries fora do range da barra j0: {fill_issues}/35")

# ============ ATAQUE B: letrun independente (reimplementação) ============
def fractal_lows_upto(L, i, lookback=120):
    """fractais k2 confirmáveis até a barra i (janela q-2..q+2, q<=i-2), como cf_low do engine."""
    best = None
    for q in range(max(2, i - lookback), i - 1):
        if L[q] == min(L[q - 2:q + 3]): best = q
    return best

def letrun_indep(s, j0, entry, sl, atr, trace=False):
    """Reimplementação independente do let-run. Retorna (R, exit_kind, exit_bar, events)."""
    risk = entry - sl
    stop = sl; armed = False
    end = min(j0 + HMAX, len(s) - 1)
    L = [b["l"] for b in s]
    ev = []
    for k in range(j0 + 1, end + 1):
        if s[k]["l"] <= stop:
            R = max(-1.0, min(RCAP, (stop - entry) / risk))
            if trace: ev.append(f"bar+{k-j0}: low {s[k]['l']} <= stop {round(stop,2)} → EXIT R={R:+.2f}")
            return R, ("TRAIL" if stop > sl else "SL"), k, ev
        if not armed and (s[k]["h"] - entry) / risk >= 1:
            armed = True
            if trace: ev.append(f"bar+{k-j0}: high {s[k]['h']} >= +1R ({round(entry+risk,2)}) → ARMED")
        if armed:
            q = fractal_lows_upto(L, k)
            if q is not None and L[q] - 0.1 * atr > stop:
                stop = L[q] - 0.1 * atr
                if trace: ev.append(f"bar+{k-j0}: trail ↑ {round(stop,2)} (fractal@-{k-q}b low {L[q]})")
    R = max(-1.0, min(RCAP, (s[end]["c"] - entry) / risk))
    return R, "END_OF_WINDOW", end, ev

print("\n" + "=" * 100)
print("B. LETRUN — reprodução independente TODOS os 35 + tipo de saída")
stored = json.load(open(HERE / "results" / "cris_trades_analysis_20260704.json"))
kinds = {"TRAIL": 0, "SL": 0, "END_OF_WINDOW": 0}
mismatch = 0
detail5 = {1, 11, 19, 22, 35}
for i, tr in enumerate(trades, 1):
    bk, s = find_block(tr["t"])
    ts = [b["t"] for b in s]
    j0 = bisect.bisect_right(ts, tr["t"]) - 1
    atr = s[j0].get("atr") or 1.0
    R, kind, kx, ev = letrun_indep(s, j0, tr["entry"], tr["sl"], atr, trace=(i in detail5))
    kinds[kind] += 1
    st = stored[i - 1]["R_letrun_ourexit"]
    ok = abs(R - st) < 0.005
    if not ok: mismatch += 1
    if i in detail5:
        print(f"\n  --- #{i} {dt.datetime.utcfromtimestamp(tr['t']).strftime('%Y-%m-%d %H:%M')} entry {tr['entry']} sl {tr['sl']} risk {round(tr['entry']-tr['sl'],2)} atr {round(atr,2)} ---")
        for e in ev[:4] + (["  ..."] if len(ev) > 8 else []) + ev[-4:] if len(ev) > 8 else ev:
            print(f"    {e}")
        print(f"    EXIT: {kind} @bar+{kx-j0} → R_indep={R:+.2f} vs armazenado {st:+.2f}  {'OK' if ok else '*** MISMATCH ***'}")
    elif not ok:
        print(f"  #{i}: R_indep {R:+.2f} vs armazenado {st:+.2f} *** MISMATCH ***")
print(f"\n  Reprodução: {35 - mismatch}/35 batem (tolerância 0.005)")
print(f"  Tipos de saída: {kinds}")
enders = [(i + 1, round(letrun_indep(find_block(t['t'])[1], bisect.bisect_right([b['t'] for b in find_block(t['t'])[1]], t['t']) - 1, t['entry'], t['sl'], (find_block(t['t'])[1][bisect.bisect_right([b['t'] for b in find_block(t['t'])[1]], t['t']) - 1].get('atr') or 1.0))[0], 2)) for i, t in enumerate(trades)]
# WR sem os END_OF_WINDOW:
rs = []
for i, tr in enumerate(trades, 1):
    bk, s = find_block(tr["t"]); ts = [b["t"] for b in s]
    j0 = bisect.bisect_right(ts, tr["t"]) - 1
    atr = s[j0].get("atr") or 1.0
    R, kind, kx, _ = letrun_indep(s, j0, tr["entry"], tr["sl"], atr)
    rs.append((i, R, kind, kx - j0, len(s) - 1 - j0))
ew = [x for x in rs if x[2] == "END_OF_WINDOW"]
print(f"  END_OF_WINDOW: {[(i, r, f'{nb}b janela', f'{avail}b no bloco') for i, r, k, nb, avail in ew]}")
tr_only = [x for x in rs if x[2] != "END_OF_WINDOW"]
print(f"  WR só saídas por trail/SL: {sum(1 for x in tr_only if x[1] > 0)}/{len(tr_only)} · sumR {sum(x[1] for x in tr_only):+.1f}")
print(f"  sumR total indep: {sum(x[1] for x in rs):+.1f} · WR {sum(1 for x in rs if x[1] > 0)}/35")

# ============ ATAQUE C: plan_outcome ============
print("\n" + "=" * 100)
print("C. PLAN_OUTCOME — #19, OPENs, ambiguidade same-bar, truncamento de bloco")
allbars = ns["bars"]; T15 = ns["T15"]  # timeline global mesclada de todos os blocos
for i, tr in enumerate(trades, 1):
    bk, s = find_block(tr["t"])
    ts = [b["t"] for b in s]
    j0 = bisect.bisect_right(ts, tr["t"]) - 1
    oc = None; kx = None; amb_bars = 0
    for k in range(j0 + 1, len(s)):
        hs = s[k]["l"] <= tr["sl"]; ht = s[k]["h"] >= tr["tgt"]
        if hs and ht: amb_bars += 1; oc = oc or ("AMBIGUO", k)
        elif hs: oc = oc or ("SL", k)
        elif ht: oc = oc or ("TARGET", k)
        if oc: break
    oc = oc or ("OPEN", len(s) - 1)
    st = stored[i - 1]["plan_outcome"]
    match = (oc[0] == st) or (oc[0] == "AMBIGUO" and st == "AMBIGUO_same_bar")
    if oc[0] in ("SL", "OPEN", "AMBIGUO") or not match:
        blk_end = dt.datetime.utcfromtimestamp(s[-1]["t"]).strftime("%Y-%m-%d")
        extra = ""
        if oc[0] == "OPEN":
            # verifica na timeline GLOBAL (todos os blocos) o que viria primeiro depois do fim do bloco
            gi = bisect.bisect_right(T15, tr["t"])
            first = None
            for tt in T15[gi:]:
                b = allbars[tt]
                hs = b["l"] <= tr["sl"]; ht = b["h"] >= tr["tgt"]
                if hs and ht: first = ("AMBIGUO", tt); break
                if hs: first = ("SL", tt); break
                if ht: first = ("TARGET", tt); break
            if first:
                extra = f" | timeline global (cross-block): {first[0]} em {dt.datetime.utcfromtimestamp(first[1]).strftime('%Y-%m-%d')}"
            barsleft = len(s) - 1 - j0
            extra += f" | bloco {bk} termina {blk_end} ({barsleft}b após entry)"
        print(f"  #{i:>2} {st:<8} recomputado {oc[0]:<8} {'OK' if match else '*** MISMATCH ***'}{extra}")
amb_total = sum(1 for r in stored if r["plan_outcome"] == "AMBIGUO_same_bar")
print(f"  AMBIGUO_same_bar armazenados: {amb_total}")

# ============ ATAQUE D: sensibilidade do matching ============
print("\n" + "=" * 100)
print("D. MATCHING — sensibilidade da janela (6/12/24/32 barras)")
for NB in (6, 12, 24, 32):
    m = 0; ids = []
    for i, tr in enumerate(trades, 1):
        cands = [r for r in Ubyt if tr["t"] - NB * 900 <= r["cj_t"] <= tr["t"]]
        if cands: m += 1
        else: ids.append(i)
    print(f"  ≤{NB:>2} barras: {m}/35 casados · sem match: {ids}")
# distância exata do flush mais próximo (antes) p/ os 7 SEM-FLUSH da análise
print("  Distância exata ao último flush (qualquer bloco) p/ os 7 'SEM-FLUSH' (janela 12):")
for i, tr in enumerate(trades, 1):
    cands12 = [r for r in Ubyt if tr["t"] - 12 * 900 <= r["cj_t"] <= tr["t"]]
    if cands12: continue
    prev = [r for r in Ubyt if r["cj_t"] <= tr["t"]]
    d = (tr["t"] - prev[-1]["cj_t"]) // 900 if prev else None
    print(f"    #{i:>2}: último flush {d} barras antes")

# ============ ATAQUE E: medianas + swept ============
print("\n" + "=" * 100)
print("E. PERFIL CAUSAL — reprodução das medianas + fração swept=0")
NEAR = 12
matched_rows = []
for i, tr in enumerate(trades, 1):
    cands = [r for r in Ubyt if tr["t"] - NEAR * 900 <= r["cj_t"] <= tr["t"]]
    if cands: matched_rows.append((i, min(cands, key=lambda r: tr["t"] - r["cj_t"])))
def med(v):
    v = sorted(x for x in v if isinstance(x, (int, float))); return v[len(v) // 2] if v else None
B = [r for r in U if r["g_in_base435"] == 1 and r["g_v5h"] != "BEAR"]
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
print(f"  casados: {len(matched_rows)}/35 · base435 (não-BEAR): {len(B)}")
for k in ("legpos60", "h1_pos", "g_box96", "g_ema21_dist", "g_rec_speed", "swept_prior_low"):
    print(f"    {k:<16} cris={med([m.get(k) for _, m in matched_rows])}  base435={med([fv(b, k) for b in B])}")
sw1 = sum(1 for _, m in matched_rows if fv(m, "swept_prior_low") == 1)
print(f"  swept_prior_low==1 nos casados: {sw1}/{len(matched_rows)} ({100 * sw1 / len(matched_rows):.0f}%) — base435 exige swept=1 (100%)")

# ============ ATAQUE F: assinatura EXPLORATORY (lista pré-declarada) ============
print("\n" + "=" * 100)
print("F. ASSINATURA CANDIDATA (EXPLORATORY, sem otimização) — cobertura nos casados(≤24b) vs seletividade no universo")
m24 = []
for i, tr in enumerate(trades, 1):
    cands = [r for r in Ubyt if tr["t"] - 24 * 900 <= r["cj_t"] <= tr["t"]]
    if cands: m24.append((i, min(cands, key=lambda r: tr["t"] - r["cj_t"])))
Unb = [r for r in U if r["g_v5h"] != "BEAR"]
days_span = (Ubyt[-1]["cj_t"] - Ubyt[0]["cj_t"]) / 86400
LENSES = {
    "in_demand==1":            lambda r: fv(r, "in_demand") == 1,
    "htf_demand_any==1":       lambda r: fv(r, "htf_demand_any") == 1,
    "h1n_trend==1":            lambda r: fv(r, "h1n_trend") == 1,
    "h4n_trend==1":            lambda r: fv(r, "h4n_trend") == 1,
    "g_knife==0":              lambda r: fv(r, "g_knife") == 0,
    "h1_pos<=0.85":            lambda r: fv(r, "h1_pos", 1) <= 0.85,
    "ema21_dist in[-1.5,1.5]": lambda r: -1.5 <= fv(r, "g_ema21_dist", 9) <= 1.5,
    "legpos60<=0.85":          lambda r: fv(r, "legpos60", 1) <= 0.85,
    "box480>=0.15":            lambda r: fv(r, "g_box480") >= 0.15,
    "swept==1":                lambda r: fv(r, "swept_prior_low") == 1,
}
print(f"  universo: {len(U)} flush-candidates ({len(Unb)} não-BEAR) em ~{days_span:.0f} dias (~{len(U)/days_span:.1f}/dia)")
print(f"  {'lente':<26} {'cobertura 35(m24)':<20} {'universo nb':<14}")
for name, fn in LENSES.items():
    cov = sum(1 for _, m in m24 if fn(m))
    sel = sum(1 for r in Unb if fn(r))
    print(f"  {name:<26} {cov}/{len(m24):<18} {sel}/{len(Unb)} ({100*sel/len(Unb):.0f}%)")
# conjunções pré-declaradas (2 candidatas, direcionais)
CONJ = {
    "C1: in_demand & knife==0 & h4n_trend==1":
        lambda r: fv(r, "in_demand") == 1 and fv(r, "g_knife") == 0 and fv(r, "h4n_trend") == 1,
    "C2: in_demand & knife==0 & h1n_trend==1 & ema21_dist<=1.5 (pullback, SEM sweep)":
        lambda r: fv(r, "in_demand") == 1 and fv(r, "g_knife") == 0 and fv(r, "h1n_trend") == 1 and fv(r, "g_ema21_dist", 9) <= 1.5,
}
for name, fn in CONJ.items():
    cov = [i for i, m in m24 if fn(m)]
    sel = sum(1 for r in Unb if fn(r))
    print(f"  {name}")
    print(f"    cobre {len(cov)}/{len(m24)} dos trades-Cris casados · seleciona {sel}/{len(Unb)} do universo nb ({100*sel/len(Unb):.0f}%, ~{sel/days_span:.2f}/dia) · não cobre: {[i for i, _ in m24 if i not in cov]}")
print("\nDONE")
