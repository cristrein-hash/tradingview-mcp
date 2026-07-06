#!/usr/bin/env python3
"""FILTRO DE EVENTO-LIXO ANTES DA ENTRY (2026-07-06, ordem Cris). Inverter a ordem: usar os 60
fundos reais como REFERÊNCIA p/ jogar fora eventos falsos ANTES de qualquer lógica de entry.
Filtro de ALTO RECALL (não classificador de precisão): construir ENVELOPE das features de evento a
partir dos eventos-fundo (q_lo..q_hi) e descartar eventos que caem FORA do envelope em alguma
dimensão = definitivamente-não-fundo. Objetivo: reduzir o pool mantendo ~todos os fundos → a entry
opera num pool menor e mais limpo.
Duas versões:
  TRIAGEM (evento formado, agregado — o que o olho faz vendo o evento): todas as features.
  CAUSAL (agregado até o candidato mediano, sem retrospectivas dur/n_cand): p/ uso real.
Medir: recall (fundos mantidos), pool restante, densidade antes/depois, hit3R do pool filtrado.
NULL HONESTO: envelope de K eventos ALEATÓRIOS (não-fundos), 500×, ver se o envelope-dos-fundos
corta MAIS lixo mantendo recall que um envelope aleatório. Se P baixo → o filtro capta estrutura real.
SANITY_PROBE: sha GT · matcher v2 · envelope = calibração declarada · null permuta rótulo-fundo ·
recall por círculo distinto · versão causal separada da triagem."""
import json, bisect, hashlib, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N = len(S); ATR = [b.get("atr") or 5.0 for b in S]; HI = [b["h"] for b in S]; LO = [b["l"] for b in S]
CACHE = {r["cj_t"]: r for r in (json.loads(l) for l in open(HERE / "results" / "raw_feature_cache_20260706.jsonl"))}
UNIV = sorted([u for u in U if u["cj_t"] in R3 and u["cj_t"] in CACHE], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]
for u in UNIV:
    u["_flo"] = u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0); u["_a"] = u.get("g_atr") or 5.0
    u["_circ"] = set(); u["_F"] = CACHE[u["cj_t"]]
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"] + 8 * 3600:
        u = UNIV[j]; d = u["_flo"] - g["flush_low"]
        if -3 * u["_a"] <= d <= 1 * u["_a"]: u["_circ"].add(gi)
        j += 1
EV = []; cur = []
for u in UNIV:
    if cur and u["cj_t"] - cur[-1]["cj_t"] <= 48 * 3600 and abs(u["_flo"] - cur[-1]["_flo"]) <= 3 * u["_a"]:
        cur.append(u)
    else:
        if cur: EV.append(cur)
        cur = [u]
if cur: EV.append(cur)

def agg(ev, causal_upto=None):
    sub = ev if causal_upto is None else ev[:causal_upto]
    F = [u["_F"] for u in sub]
    st_i = bisect.bisect_right(TS, ev[0]["cj_t"]) - 1; a = ev[0]["_a"]
    pre_hi = max(HI[max(0, st_i - 96):st_i + 1])
    ei = bisect.bisect_right(TS, sub[-1]["cj_t"]) - 1
    o = {"rsi_min8": min(f["rsi_min8"] for f in F), "nas_dist": min(f["nas_dist"] for f in F),
         "sell_climax": max(f["sell_climax4"] for f in F), "below_poc": max(f["below_poc"] for f in F),
         "poc_dist": min(f["poc_dist"] for f in F), "nas_long": max(f["nas_long_rec"] for f in F),
         "vol_climax": max(f["vol_climax"] for f in F), "flow_div": max(f["flow_divergence"] for f in F),
         "pre_drop": (pre_hi - min(LO[max(0, st_i - 8):ei + 1])) / a}
    if causal_upto is None:  # triagem: inclui retrospectivas
        o["dur_h"] = (ev[-1]["cj_t"] - ev[0]["cj_t"]) / 3600; o["n_cand"] = len(ev)
    return o

for ev in EV:
    ev[0]["_isfund"] = any(u["_circ"] for u in ev)
FUND = [ev for ev in EV if ev[0]["_isfund"]]
print(f"eventos {len(EV)} · fundo {len(FUND)} · densidade {(len(EV)-len(FUND))/len(FUND):.1f}:1")

def run(causal_upto, tag, qlo, qhi):
    A = {id(ev): agg(ev, causal_upto if causal_upto is None or len(ev) >= causal_upto else len(ev)) for ev in EV}
    # p/ eventos curtos na versão causal, usa o que tem
    KEYS = list(A[id(FUND[0])].keys())
    # direção de envelope: features "quanto menor melhor" só limite superior; etc. Usamos [qlo,qhi] bilateral
    def envelope(fund_ids):
        env = {}
        for k in KEYS:
            v = sorted(A[i][k] for i in fund_ids if k in A[i])
            if not v: continue
            env[k] = (v[int(qlo * (len(v) - 1))], v[int(qhi * (len(v) - 1))])
        return env
    fund_ids = [id(ev) for ev in FUND]
    env = envelope(fund_ids)
    def passes(ev, env):
        a = A[id(ev)]
        for k, (lo, hi) in env.items():
            if k not in a: return True  # feature ausente não descarta
            if not (lo <= a[k] <= hi): return False
        return True
    kept = [ev for ev in EV if passes(ev, env)]
    kept_fund = [ev for ev in kept if ev[0]["_isfund"]]
    circ = set()
    for ev in kept_fund:
        for u in ev: circ |= u["_circ"]
    pool_cands = [u for ev in kept for u in ev]
    h = 100 * sum(1 for u in pool_cands if R3[u["cj_t"]]["R3"] >= 3) / len(pool_cands) if pool_cands else 0
    dens = (len(kept) - len(kept_fund)) / max(1, len(kept_fund))
    print(f"\n{tag} envelope q[{qlo},{qhi}]:")
    print(f"  eventos mantidos {len(kept)}/{len(EV)} · fundos {len(kept_fund)}/{len(FUND)} · círculos {len(circ)}/60 "
          f"· densidade {dens:.1f}:1 (de {(len(EV)-len(FUND))/len(FUND):.1f}:1) · pool-cands {len(pool_cands)} hit3R {h:.1f}%")
    # NULL: envelope de K eventos aleatórios (mesmo tamanho que FUND), quantos eventos mantém
    random.seed(901); obs_cut = len(EV) - len(kept)
    ge = 0; NP = 500; all_ids = [id(ev) for ev in EV]
    for _ in range(NP):
        rid = random.sample(all_ids, len(FUND))
        e2 = envelope(rid)
        kept2 = sum(1 for ev in EV if passes(ev, e2))
        cut2 = len(EV) - kept2
        # recall dos fundos sob envelope aleatório
        rf = sum(1 for ev in FUND if passes(ev, e2))
        # comparação justa: corta MAIS que aleatório mantendo recall >= observado?
        if cut2 >= obs_cut and rf >= len(kept_fund): ge += 1
    print(f"  NULL (envelope de {len(FUND)} eventos aleatórios, {NP}×): P(corta>=obs & recall>=obs) = {ge/NP:.4f}")
    return {"kept": len(kept), "fund_kept": len(kept_fund), "circ": len(circ), "dens": round(dens, 1), "hit": round(h, 1), "p_null": ge / NP}

out = {}
out["triagem_q0_100"] = run(None, "TRIAGEM (evento formado)", 0.0, 1.0)
out["triagem_q02_98"] = run(None, "TRIAGEM (evento formado)", 0.02, 0.98)
out["causal_q0_100"] = run(3, "CAUSAL (até 3º cand)", 0.0, 1.0)
out["causal_q02_98"] = run(3, "CAUSAL (até 3º cand)", 0.02, 0.98)
json.dump(out, open(HERE / "results" / "event_envelope_filter_20260706.json", "w"), indent=1, default=float)
print("\nOK → results/event_envelope_filter_20260706.json")
