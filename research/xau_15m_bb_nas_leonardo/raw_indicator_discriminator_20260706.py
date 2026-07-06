#!/usr/bin/env python3
"""DISCRIMINADOR DE INDICADORES RAW — aprofundamento dedicado (2026-07-06, ordem Cris).
Crítica do Cris: usei agregações grosseiras do builder; os indicadores RAW (bubbles/NAS/RSI/OB-SMC/
volume-profile) DEVEM discriminar fundo-verdadeiro de sósia; falta feature cruzada pós-estrutura.
Construo ~26 features RAW DEDICADAS causais (<= cj; bubbles por known_at) e testo winner-vs-sósia
DENTRO de cada família com MANN-WHITNEY (rank, não mediana). Núcleo = ABSORÇÃO DE FLUXO (sell_bub_w
já deu p=0,0025). + CONVERGÊNCIAS cruzadas (absorção & CHoCH+ & RSI-div).
Winner = candidato matcher-v2 de círculo que faz 3R. Sósia = candidato da família sem círculo.
FASE A: ranking MWU por família. FASE B (se separar): fica p/ script de seletor+null+DA seguinte.
SANITY_PROBE: sha GT · matcher v2 · causalidade (known_at bubbles, t<=cj smc/nas, barra fechada
séries) · MWU exato via U-stat normal-approx · famílias com winner-n>=10."""
import json, glob, bisect, hashlib, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])  # U,R3,S,TS,fv,macro_leg
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N = len(S)
ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]
VOL = [float(b.get("v") or 0) for b in S]; RSI = [b.get("rsi") for b in S]
NASD = [b.get("nas_dist") for b in S]
ST = TS

# ---- carregar RAW por timestamp global ----
BUB = []
for p in sorted(glob.glob(str(HERE / "bubbles" / "*.bubbles.jsonl"))):
    for l in open(p):
        if l.strip(): BUB.append(json.loads(l))
BUB.sort(key=lambda x: (x.get("known_at") or x["t"]))
BUBK = [(x.get("known_at") or x["t"]) for x in BUB]
NAS = []
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    NAS += [e for e in d["nas_events"] if e.get("t") and e.get("dir")]
NAS.sort(key=lambda e: e["t"]); NAST = [e["t"] for e in NAS]
# SMC direcional (do módulo: events[] tem tok BOS+/-, CHoCH+/-; ET)
# zones DEMAND
ZD = []
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for z in d.get("zones", []):
        if "DEMAND" in str(z.get("text", "")).upper() and z.get("born_t") is not None:
            ZD.append(z)
ZD.sort(key=lambda z: z["born_t"]); ZDB = [z["born_t"] for z in ZD]
W = {"S": 1, "M": 2, "L": 3}

def bubs(cj, wlo, whi):
    hi = bisect.bisect_right(BUBK, cj)
    return [BUB[i] for i in range(hi) if cj - whi * 900 <= BUB[i]["t"] <= cj - wlo * 900]

def feats(u):
    cj = u["cj_t"]; ci = bisect.bisect_right(ST, cj) - 1
    if ci < 40: return None
    a = ATR[ci] or 5.0
    o = {}
    # --- ABSORÇÃO / BUBBLES ---
    r4 = bubs(cj, 0, 4); r8 = bubs(cj, 0, 8); r12 = bubs(cj, 0, 12); old = bubs(cj, 5, 12)
    buy8 = sum(W[x["size"]] for x in r8 if x["side"] == "BUY")
    sell8 = sum(W[x["size"]] for x in r8 if x["side"] == "SELL")
    o["buy_accum12"] = sum(W[x["size"]] for x in r12 if x["side"] == "BUY")
    o["buy_seq"] = sum(W[x["size"]] for x in r4 if x["side"] == "BUY") - sum(W[x["size"]] for x in old if x["side"] == "BUY")
    o["flow_ratio8"] = (buy8 - sell8) / max(1, buy8 + sell8)
    o["sell_climax4"] = sum(1 for x in r4 if x["side"] == "SELL" and x["size"] in ("M", "L"))
    o["big_buy_recency"] = min([(cj - x["t"]) // 900 for x in r12 if x["side"] == "BUY" and x["size"] == "L"] or [99])
    # absorção: SELL M/L nas 8 barras cujo preço 4 barras depois NÃO caiu abaixo do low da bubble
    absb = 0
    for x in r8:
        if x["side"] == "SELL" and x["size"] in ("M", "L"):
            bt = bisect.bisect_right(ST, x["t"]) - 1
            # CAUSAL: só conta absorção se as 4 barras de confirmação estão <= cj (bt+4 <= ci)
            if bt + 4 <= ci and LO[bt] is not None and min(LO[bt + 1:bt + 5]) >= x["l"] - 0.2 * a:
                absb += W[x["size"]]
    o["sell_absorb8"] = absb
    o["flow_divergence"] = int(sell8 >= 2 and CL[ci] > CL[max(0, ci - 4)])   # venda mas preço subiu
    # --- NAS ---
    j = bisect.bisect_right(NAST, cj) - 1
    o["nas_long_rec"] = int(j >= 0 and NAS[j]["dir"] == "LONG" and (cj - NAS[j]["t"]) // 900 <= 8)
    o["nas_flip_long"] = int(j >= 1 and NAS[j]["dir"] == "LONG" and NAS[j - 1]["dir"] == "SHORT" and (cj - NAS[j]["t"]) // 900 <= 16)
    o["nas_dist"] = NASD[ci] if NASD[ci] is not None else 0.0
    # --- RSI ---
    o["rsi_cj"] = RSI[ci] if RSI[ci] is not None else 50
    o["rsi_min8"] = min([RSI[k] for k in range(max(0, ci - 8), ci + 1) if RSI[k] is not None] or [50])
    # divergência bullish: low atual < low de ~8-24b atrás mas RSI atual > RSI de lá
    lb = range(max(0, ci - 24), max(1, ci - 6))
    prev_low_k = min(lb, key=lambda k: LO[k]) if lb else ci
    o["rsi_bull_div"] = int(LO[ci] < LO[prev_low_k] and RSI[ci] is not None and RSI[prev_low_k] is not None and RSI[ci] > RSI[prev_low_k] + 2)
    rma = [RSI[k] for k in range(max(0, ci - 13), ci + 1) if RSI[k] is not None]
    o["rsi_above_ma"] = int(RSI[ci] is not None and rma and RSI[ci] > sum(rma) / len(rma))
    # --- SMC / OB ---
    hi_e = bisect.bisect_right(ET, cj)
    choch_up = eql = bos_up = 0
    for m in range(hi_e - 1, -1, -1):
        if cj - events[m]["t"] > 24 * 900: break
        if events[m]["tok"] == "CHoCH+": choch_up = 1
        if events[m]["tok"] == "BOS+": bos_up = 1
    o["choch_up_rec24"] = choch_up
    o["bos_up_rec24"] = bos_up
    # OB demand mitigado: flush dentro de zona DEMAND nascida antes
    flo = u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0)
    hz = bisect.bisect_right(ZDB, cj)
    in_dem = 0
    for i in range(hz):
        z = ZD[i]
        if z["low"] - 0.3 * a <= flo <= z["high"] + 0.3 * a and (z.get("last_t") or cj) >= cj - 96 * 900:
            in_dem = 1; break
    o["ob_demand_mitig"] = in_dem
    # --- VOLUME / SVP aprox ---
    v48 = VOL[max(0, ci - 48):ci]
    o["vol_climax"] = VOL[ci] / (sum(v48) / len(v48)) if v48 and VOL[ci] else 1.0
    vrec = VOL[max(0, ci - 8):ci]; vpre = VOL[max(0, ci - 32):max(1, ci - 8)]
    o["vol_dryup"] = (sum(vrec) / max(1, len(vrec))) / max(1e-9, sum(vpre) / max(1, len(vpre)))
    # POC das últimas 96 barras (bin 0,25 ATR) e distância do flush ao POC
    lo96 = min(LO[max(0, ci - 96):ci + 1]); binsz = 0.25 * a
    prof = {}
    for k in range(max(0, ci - 96), ci + 1):
        b = int((( (HI[k] + LO[k]) / 2) - lo96) / binsz)
        prof[b] = prof.get(b, 0) + VOL[k]
    if prof:
        poc_b = max(prof, key=prof.get); poc_price = lo96 + (poc_b + 0.5) * binsz
        o["poc_dist"] = (flo - poc_price) / a
        o["below_poc"] = int(flo < poc_price)
    else:
        o["poc_dist"] = 0.0; o["below_poc"] = 0
    # --- CONVERGÊNCIAS cruzadas pós-estrutura ---
    o["conv_absorb_choch"] = int((absb >= 2 or o["sell_climax4"] >= 1) and choch_up)
    o["conv_flow_rsi"] = int(o["buy_seq"] >= 1 and (o["rsi_bull_div"] or o["rsi_above_ma"]))
    o["conv_full"] = int((absb >= 1 or o["sell_climax4"] >= 1) and choch_up and (o["rsi_bull_div"] or o["rsi_min8"] < 35) and in_dem)
    return o

# marca família (retr) + winner
LOWS = []
d = 0; ehi = elo = 0
for i in range(1, N):
    if HI[i] > HI[ehi]: ehi = i
    if LO[i] < LO[elo]: elo = i
    if d >= 0 and HI[ehi] - LO[i] >= 6 * ATR[i] and ehi < i:
        d = -1; elo = min(range(ehi, i + 1), key=lambda k: LO[k])
    elif d <= 0 and HI[i] - LO[elo] >= 6 * ATR[i] and elo < i:
        LOWS.append((i, elo)); d = 1; ehi = max(range(elo, i + 1), key=lambda k: HI[k])
KLOW = [x[0] for x in LOWS]
UNIV = sorted([u for u in U if u["cj_t"] in R3], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]
def retr_of(u):
    ci = bisect.bisect_right(TS, u["cj_t"]) - 1
    j = bisect.bisect_right(KLOW, ci) - 1
    if j < 0: return None
    _, l0i = LOWS[j]; L0 = LO[l0i]; H1 = max(HI[k] for k in range(l0i, ci + 1))
    if H1 - L0 < 1e-9: return None
    flo = u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0)
    return (H1 - flo) / (H1 - L0)
for u in UNIV:
    r = retr_of(u)
    u["_fam"] = "SEM" if r is None else ("RASO" if r < 0.5 else ("BANDA" if r <= 1.3 else "FUNDO"))
    u["_circ"] = set()
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"] + 8 * 3600:
        u = UNIV[j]; a = u.get("g_atr") or 5.0; dd = (u["g_sl"] + 0.1 * a) - g["flush_low"]
        if -3 * a <= dd <= 1 * a: u["_circ"].add(gi)
        j += 1
for u in UNIV:
    u["_F"] = feats(u)
WIN = [u for u in UNIV if u["_circ"] and R3[u["cj_t"]]["R3"] >= 3 and u["_F"]]

def mwu_p(a, b):
    """Mann-Whitney U normal-approx (2-sided) → p; retorna (p, mediana_a, mediana_b)."""
    na, nb = len(a), len(b)
    if na < 5 or nb < 5: return (1.0, None, None)
    allv = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    ranks = [0.0] * len(allv); i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1][0] == allv[i][0]: j += 1
        r = (i + j) / 2 + 1
        for k in range(i, j + 1): ranks[k] = r
        i = j + 1
    Ra = sum(ranks[k] for k in range(len(allv)) if allv[k][1] == 0)
    Ua = Ra - na * (na + 1) / 2; U = min(Ua, na * nb - Ua)
    mu = na * nb / 2; sd = math.sqrt(na * nb * (na + nb + 1) / 12)
    if sd == 0: return (1.0, None, None)
    z = (U - mu) / sd
    p = math.erfc(abs(z) / math.sqrt(2))
    ma = sorted(a)[na // 2]; mb = sorted(b)[nb // 2]
    return (p, ma, mb)

FEATS = list(WIN[0]["_F"].keys())
print(f"winners totais {len(WIN)} · " + " ".join(f"{f}:{sum(1 for u in WIN if u['_fam']==f)}" for f in ("BANDA","FUNDO","RASO")))
for fam in ("BANDA", "FUNDO", "RASO"):
    Wf = [u for u in WIN if u["_fam"] == fam]
    Sf = [u for u in UNIV if u["_fam"] == fam and not u["_circ"] and u["_F"]]
    if len(Wf) < 10:
        print(f"\n=== {fam}: winners {len(Wf)} <10, pulo ==="); continue
    print(f"\n=== {fam} · winners {len(Wf)} · sósias {len(Sf)} · MWU winner-vs-sósia (p<0,05) ===")
    res = []
    for k in FEATS:
        a = [u["_F"][k] for u in Wf if u["_F"][k] is not None]
        b = [u["_F"][k] for u in Sf if u["_F"][k] is not None]
        p, ma, mb = mwu_p(a, b)
        if ma is not None:
            res.append((p, k, ma, mb, sum(a) / len(a), sum(b) / len(b)))
    res.sort()
    for p, k, ma, mb, mua, mub in res:
        if p < 0.05:
            print(f"  {k:<20} p={p:.4f} · win méd {mua:>7.2f} (med {ma:>6.2f}) · sósia méd {mub:>7.2f} (med {mb:>6.2f})")
json.dump({"winners": len(WIN)}, open(HERE / "results" / "raw_indicator_discriminator_20260706.json", "w"))
# CACHE de features p/ iteração de seletores (evita recomputar bubbles)
with open(HERE / "results" / "raw_feature_cache_20260706.jsonl", "w") as fo:
    for u in UNIV:
        if u["_F"]:
            rec = {"cj_t": u["cj_t"], "yr": u["yr"], "g_week": u["g_week"], "fam": u["_fam"],
                   "circ": sorted(u["_circ"]), "R3": R3[u["cj_t"]]["R3"], "net3": R3[u["cj_t"]]["net3"],
                   **u["_F"]}
            fo.write(json.dumps(rec) + "\n")
print("cache → results/raw_feature_cache_20260706.jsonl")
print("\nOK → results/raw_indicator_discriminator_20260706.json")
