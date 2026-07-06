#!/usr/bin/env python3
"""ESTÁGIO-2 no POOL FILTRADO (2026-07-06, ordem Cris: leitura na ordem que funcionou).
Estágio-1 = filtro por-família (densidade 5,6:1, recall 100%). Aqui, DENTRO do pool limpo, a
LEITURA SEQUENCIAL na ordem que deu certo (CASCEX/entry-bar): estrutura de reversão → confirmação
→ entry. NULL CORRETO (lição DA7): comparar a entry escolhida vs candidato ALEATÓRIO do MESMO
evento (não universo) — só assim mede edge de ENTRY, não de seleção-de-evento.
LEITURA (por candidato, dentro do evento filtrado, causal):
  pós-low (preço não faz novo mínimo) → reversão estrutural (CHoCH+ desde o low OU higher-low) →
  confirmação (reclaim close>high[-1] & body_up) → entry
Políticas (1/evento, no pool filtrado):
  E1 1º pós-low com CHoCH+
  E2 1º pós-low com higher-low & reclaim
  E3 1º pós-low com CHoCH+ & reclaim (estrutura+confirmação)
  E4 E3 & oversold-acumulado (rsi_min8<=35 até ali)
Painel + recall-círculo + NULL-POR-EPISÓDIO (aleatório no mesmo evento, 2000×) + streak + sub-ano.
SANITY_PROBE: pool família causal; construção causal (CHoCH+/HL/reclaim só barras<=cj);
null=aleatório-dentro-do-evento-do-pool; recall círculo; exit 3R fixo."""
import json, bisect, hashlib, random
import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N = len(S); ATR = [b.get("atr") or 5.0 for b in S]; HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]; OP = [b.get("o", b["c"]) for b in S]
CACHE = {r["cj_t"]: r for r in (json.loads(l) for l in open(HERE / "results" / "raw_feature_cache_20260706.jsonl"))}
UNIV = sorted([u for u in U if u["cj_t"] in R3 and u["cj_t"] in CACHE], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]; WK = len({u["g_week"] for u in U})
LOWS = []; d0 = 0; ehi = elo = 0
for i in range(1, N):
    if HI[i] > HI[ehi]: ehi = i
    if LO[i] < LO[elo]: elo = i
    if d0 >= 0 and HI[ehi]-LO[i] >= 6*ATR[i] and ehi < i: d0 = -1; elo = min(range(ehi,i+1), key=lambda k: LO[k])
    elif d0 <= 0 and HI[i]-LO[elo] >= 6*ATR[i] and elo < i: LOWS.append((i,elo)); d0 = 1; ehi = max(range(elo,i+1), key=lambda k: HI[k])
KLOW = [x[0] for x in LOWS]
for u in UNIV:
    u["_flo"] = u["g_sl"] + 0.1*(u.get("g_atr") or 5.0); u["_a"] = u.get("g_atr") or 5.0; u["_circ"] = set(); u["_F"] = CACHE[u["cj_t"]]
    ci = bisect.bisect_right(TS, u["cj_t"]) - 1; j = bisect.bisect_right(KLOW, ci) - 1; u["_fam"] = "SEM"
    if j >= 0:
        _, l0i = LOWS[j]; L0 = LO[l0i]; H1 = max(HI[k] for k in range(l0i, ci+1))
        if H1-L0 > 1e-9:
            r = (H1-u["_flo"])/(H1-L0); u["_fam"] = "RASO" if r<0.5 else ("BANDA" if r<=1.3 else "FUNDO")
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"]-8*3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"]+8*3600:
        u = UNIV[j]; dd = u["_flo"]-g["flush_low"]
        if -3*u["_a"] <= dd <= 1*u["_a"]: u["_circ"].add(gi)
        j += 1
EV = []; cur = []
for u in UNIV:
    if cur and u["cj_t"]-cur[-1]["cj_t"] <= 48*3600 and abs(u["_flo"]-cur[-1]["_flo"]) <= 3*u["_a"]:
        cur.append(u)
    else:
        if cur: EV.append(cur)
        cur = [u]
if cur: EV.append(cur)
# estágio-1: filtro por-família (envelope q0-q100 da própria família, feat causais até 3º cand)
FEATS = ["rsi_min8","nas_dist","sell_climax4","below_poc","poc_dist","nas_long_rec","vol_climax","flow_divergence"]
def vec(ev):
    sub = ev[:3]; F = [u["_F"] for u in sub]
    st_i = bisect.bisect_right(TS, ev[0]["cj_t"])-1; a = ev[0]["_a"]; pre_hi = max(HI[max(0,st_i-96):st_i+1]); ei = bisect.bisect_right(TS, sub[-1]["cj_t"])-1
    return [min(f["rsi_min8"] for f in F), min(f["nas_dist"] for f in F), max(f["sell_climax4"] for f in F), max(f["below_poc"] for f in F),
            min(f["poc_dist"] for f in F), max(f["nas_long_rec"] for f in F), max(f["vol_climax"] for f in F), max(f["flow_divergence"] for f in F),
            (pre_hi - min(LO[max(0,st_i-8):ei+1]))/a]
for ev in EV:
    ev[0]["_vec"] = vec(ev); ev[0]["_isf"] = any(u["_circ"] for u in ev); ev[0]["_efam"] = ev[0]["_fam"]
X = np.array([ev[0]["_vec"] for ev in EV]); isf = np.array([ev[0]["_isf"] for ev in EV]); efam = np.array([ev[0]["_efam"] for ev in EV])
keep = np.zeros(len(EV), bool)
for fam in ("RASO","BANDA","FUNDO","SEM"):
    idx = np.where(efam==fam)[0]; fidx = np.where((efam==fam)&isf)[0]
    if len(fidx) < 3: keep[idx] = True; continue
    lo = X[fidx].min(0); hi = X[fidx].max(0)
    for i in idx:
        if np.all((X[i]>=lo)&(X[i]<=hi)): keep[i] = True
POOL = [ev for k, ev in zip(keep, EV) if k]
print(f"pool filtrado (família): {len(POOL)} eventos · fundos {sum(1 for ev in POOL if ev[0]['_isf'])}/50")

# construção causal por candidato dentro do evento do pool
for ev in POOL:
    min_flo = 1e18
    for pos, u in enumerate(ev, 1):
        ci = bisect.bisect_right(TS, u["cj_t"])-1
        prevmin = min_flo
        u["_post_low"] = int(pos > 1 and u["_flo"] > prevmin + 0.05*u["_a"])
        u["_hl"] = int(u["_flo"] > prevmin + 0.05*u["_a"]) if pos > 1 else 0
        min_flo = min(min_flo, u["_flo"])
        u["_reclaim"] = int(ci >= 1 and CL[ci] > HI[ci-1] and CL[ci] > OP[ci])
        hi_e = bisect.bisect_right(ET, u["cj_t"]); ch = 0
        for m in range(hi_e-1, -1, -1):
            if u["cj_t"]-events[m]["t"] > 16*900: break
            if events[m]["tok"] == "CHoCH+": ch = 1; break
        u["_choch"] = ch
        u["_acc_rsi"] = min(u["_F"]["rsi_min8"], ev[0]["_F"]["rsi_min8"])

def first(ev, cond):
    for u in ev:
        if cond(u): return u
    return None
def panel(rows, tag):
    n = len(rows)
    if not n: print(f"  {tag:<20} vazio"); return None
    rs = sorted(rows, key=lambda r: r["cj_t"]); nets = [R3[r["cj_t"]]["net3"] for r in rs]
    h = sum(1 for r in rs if R3[r["cj_t"]]["R3"]>=3); w = sum(1 for x in nets if x>0)
    eq=pk=dd=0.0; mL=cl=0
    for x in nets:
        eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
        if x<=0: cl+=1; mL=max(mL,cl)
        else: cl=0
    yr={}
    for r,x in zip(rs,nets): yr[r["yr"]]=round(yr.get(r["yr"],0)+x,1)
    circ=set()
    for r in rs: circ|=r["_circ"]
    print(f"  {tag:<20} N{n:>3} hit3R {100*h/n:>5.1f}% WR {100*w/n:>5.1f}% NET {sum(nets):>+7.1f} DD {dd:>6.1f} stk-{mL} | {n/WK:.2f}/sem | círc {len(circ)}/60 | {yr}")
    return {"n":n,"hit":round(h/n,3),"wr":round(w/n,3),"net":round(sum(nets),1),"dd":round(dd,1),"stk":mL,"circ":len(circ)}
def null_episode(rows_sel, pol_events, seed):
    # null: em cada evento onde entrou, trocar por candidato ALEATÓRIO do mesmo evento
    obs = sum(1 for r in rows_sel if R3[r["cj_t"]]["R3"]>=3)/len(rows_sel)
    random.seed(seed); ge = 0
    for _ in range(4000):
        hh = 0
        for ev in pol_events:
            u = random.choice(ev)
            hh += R3[u["cj_t"]]["R3"] >= 3
        if hh/len(pol_events) >= obs: ge += 1
    return ge/4000
def streak_dist(rows, seed):
    nets=[R3[r["cj_t"]]["net3"] for r in sorted(rows,key=lambda x:x["cj_t"])]; random.seed(seed); q=[]
    for _ in range(2000):
        sq=random.choices(nets,k=len(nets)); c2=m2=0
        for x in sq:
            c2=c2+1 if x<=0 else 0; m2=max(m2,c2)
        q.append(m2)
    q.sort(); return q[1000], q[int(0.95*2000)], sum(1 for x in q if x>5)/2000

# ===== ANÁLISE CORRETA (ordem Cris): entry SÓ DENTRO dos eventos-fundo VERDADEIROS =====
# cascata SMC por candidato (todos eventos-fundo, não só pool)
FUNDEV = [ev for ev in EV if any(u["_circ"] for u in ev)]
for ev in FUNDEV:
    min_flo = 1e18
    for pos, u in enumerate(ev, 1):
        ci = bisect.bisect_right(TS, u["cj_t"]) - 1; prevmin = min_flo
        u["_post_low"] = int(pos > 1 and u["_flo"] > prevmin + 0.05*u["_a"])
        u["_hl"] = int(u["_flo"] > prevmin + 0.05*u["_a"]) if pos > 1 else 0
        min_flo = min(min_flo, u["_flo"])
        u["_reclaim"] = int(ci >= 1 and CL[ci] > HI[ci-1] and CL[ci] > OP[ci])
        u["_casc"] = cascade(u["cj_t"])
        u["_acc_rsi"] = min(u["_F"]["rsi_min8"], ev[0]["_F"]["rsi_min8"])
print(f"\n===== DENTRO DOS {len(FUNDEV)} EVENTOS-FUNDO VERDADEIROS (aprender a entry) =====")
def within_fund(cond, seed):
    picks = []; nev = 0
    for ev in FUNDEV:
        u = None
        for c in ev:
            if cond(c): u = c; break
        if u is not None:
            picks.append(u); nev += 1
    if not picks: print("  vazio"); return
    h = sum(1 for u in picks if R3[u["cj_t"]]["R3"] >= 3)
    nets = [R3[u["cj_t"]]["net3"] for u in picks]
    # null: entrar ALEATÓRIO dentro de cada evento-fundo onde a política entrou
    fired = [ev for ev in FUNDEV if any(cond(c) for c in ev)]
    random.seed(seed); ge = 0
    obs = h / len(picks)
    for _ in range(4000):
        hh = sum(1 for ev in fired if R3[random.choice(ev)["cj_t"]]["R3"] >= 3)
        if hh / len(fired) >= obs: ge += 1
    return h, len(picks), sum(nets), ge / 4000
print(f"  {'política':<22} {'entrou':>7} {'hit3R':>7} {'NET':>8} {'P(null-dentro-fundo)':>20}")
POLS = {
    "1º-cand (baseline)": (lambda u: True, 2001),
    "1º pós-low": (lambda u: u["_post_low"] == 1, 2002),
    "reclaim": (lambda u: u["_post_low"] == 1 and u["_reclaim"] == 1, 2003),
    "hl&reclaim": (lambda u: u["_hl"] == 1 and u["_reclaim"] == 1, 2004),
    "cascade>=4&reclaim": (lambda u: u["_casc"] >= 4 and u["_reclaim"] == 1, 2005),
    "cascade>=3&reclaim": (lambda u: u["_casc"] >= 3 and u["_reclaim"] == 1, 2006),
    "reclaim&oversold42": (lambda u: u["_post_low"] == 1 and u["_reclaim"] == 1 and u["_acc_rsi"] <= 42, 2007),
}
for nm, (cond, seed) in POLS.items():
    r = within_fund(cond, seed)
    if r:
        h, n, net, pn = r
        print(f"  {nm:<22} {n:>3}/{len(FUNDEV)} {100*h/n:>6.1f}% {net:>+8.1f} {pn:>18.4f}"
              + ("  <<< bate null" if pn < 0.05 else ""))
print("\n===== pipeline no pool filtrado (contraste) =====")
# base pool: 1º candidato de cada evento do pool
panel([ev[0] for ev in POOL], "pool 1º-cand")
# cascata SMC (a lógica CASCEX que deu WR 55,9%) por candidato do pool
for ev in POOL:
    for u in ev:
        u["_casc"] = cascade(u["cj_t"])
LOOKS = {
    "E2 hl&reclaim": (lambda u: u["_post_low"]==1 and u["_hl"]==1 and u["_reclaim"]==1, 1002),
    "E5 casc4&reclaim": (lambda u: u["_casc"]>=4 and u["_reclaim"]==1, 1005),
    "E6 casc3&hl&reclaim": (lambda u: u["_casc"]>=3 and u["_hl"]==1 and u["_reclaim"]==1, 1006),
    "E7 casc4&reclaim&os": (lambda u: u["_casc"]>=4 and u["_reclaim"]==1 and u["_acc_rsi"]<=42, 1007),
}
out = {}
for nm, (cond, seed) in LOOKS.items():
    pe = [ev for ev in POOL if first(ev, cond)]
    rows = [first(ev, cond) for ev in pe]
    p = panel(rows, nm)
    if rows and p and len(rows) >= 8:
        pn = null_episode(rows, pe, seed); q50,q95,pg5 = streak_dist(rows, seed+20)
        print(f"      P(null-episódio)={pn:.4f} · streak q50 {q50} q95 {q95} P(>5) {pg5:.2f}"
              + ("  <<< bate null-episódio" if pn < 0.05 else ""))
        out[nm] = {**p, "p_ep": pn, "stk_q95": q95}
        if pn < 0.05:
            for yy in (2024,2025,2026):
                ry=[r for r in rows if r["yr"]==yy]
                if ry: print(f"        {yy}: hit {100*sum(1 for r in ry if R3[r['cj_t']]['R3']>=3)/len(ry):.0f}% N{len(ry)} NET {sum(R3[r['cj_t']]['net3'] for r in ry):+.1f}")
json.dump(out, open(HERE/"results"/"event_stage2_entry_20260706.json","w"), indent=1, default=float)
print("OK → results/event_stage2_entry_20260706.json")
