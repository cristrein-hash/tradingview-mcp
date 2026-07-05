#!/usr/bin/env python3
"""DISCRIMINAÇÃO DENTRO DA BANDA PROFUNDA — exaustão sequencial da queda (2026-07-05).
Ordem Cris: "a discriminação fundo-genuíno vs sósia dentro do pullback profundo É o que precisa
ser descoberto — lucro e streak baixo real". Lógica de camadas: sósias na banda = perna de queda
ainda VIVA (entrar no meio da pernada); fundos genuínos = queda EXAUSTA. Exaustão = SEQUÊNCIA
(família nunca coberta: micro-forma bar-a-bar / velocidade do turno), não snapshot.

FASE A (MAPA, GT vs sósia dentro da banda, SEM outcome): 10 features sequenciais de exaustão,
todas causais (<= cj), medidas no trecho [barra do flush, cj]:
  E1 t_since_low     barras desde o último new-low do pullback (queda morta há quanto tempo)
  E2 probes_failed   nº de barras pós-flush que penetram <=0,3ATR do low SEM fechar abaixo
  E3 decel           progresso de queda últimas 8 barras / 24 anteriores (ATR-norm; vivo ~ alto)
  E4 basing_bars     barras com centro <=0,75ATR do low entre flush e cj (tempo de base)
  E5 second_test     retest do low que segura >=0,1ATR acima (higher-low micro pós-flush)
  E6 dleg_vel        velocidade da perna H1→flush (ATR/barra; capitulação = rápida)
  E7 dleg_age_h      idade da perna de queda no flush (h)
  E8 final_spike     range da barra do flush / média 8 anteriores
  E9 reclaim_speed   barras do flush até cj (turno rápido vs lento)
  E10 chplus         CHoCH+ conhecido em <=24 barras antes de cj (têm: _ch via lenses? recomputa)
FASE B (TESTE, máx 4 looks declarados): bandas q25-75 dos GT in-band nas 2-3 features com maior
separação da Fase A → conjunção sobre a banda; painel + null vs banda + streak + GT-precisão.
SANITY_PROBE: P1 barra do flush localizada por preço (|low−flush_low|<=0,2ATR) em [cj−96,cj],
falha→exclui (report contagem) · P2 features só usam barras <= cj (asserts de índice) · P3 GT
nunca é feature; bandas Fase B = calibração declarada · P4 null = candidatos da própria banda."""
import json, bisect, random, hashlib
import statistics as st
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])          # U, R3, S, TS, fv, cascade
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT_60 = json.load(open(GTF))
N = len(S)
ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]
OP = [b.get("o", b["c"]) for b in S]

def zigzag_low_pivots(r=6):
    lows = []; d = 0; ehi = elo = 0
    for i in range(1, N):
        atr = ATR[i]
        if HI[i] > HI[ehi]: ehi = i
        if LO[i] < LO[elo]: elo = i
        if d >= 0 and HI[ehi] - LO[i] >= r * atr and ehi < i:
            d = -1; elo = min(range(ehi, i + 1), key=lambda k: LO[k])
        elif d <= 0 and HI[i] - LO[elo] >= r * atr and elo < i:
            lows.append((i, elo)); d = 1
            ehi = max(range(elo, i + 1), key=lambda k: HI[k])
    return lows
LOWS = zigzag_low_pivots(6); KLOW = [x[0] for x in LOWS]

UNIV = [u for u in U if u["cj_t"] in R3]
US = sorted(UNIV, key=lambda u: u["cj_t"]); UT = [u["cj_t"] for u in US]
for u in UNIV: u["_gt"] = 0
for g in GT_60:
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UT) and UT[j] <= g["flush_t"] + 8 * 3600:
        v = US[j]
        if abs((v["g_sl"] + 0.1 * (v.get("g_atr") or 5.0)) - g["flush_low"]) <= (v.get("g_atr") or 5.0):
            v["_gt"] = 1
        j += 1

skipped = 0
for u in UNIV:
    ci = bisect.bisect_right(TS, u["cj_t"]) - 1
    a = u.get("g_atr") or 5.0
    flo = u["g_sl"] + 0.1 * a
    u["_m"] = None
    # retração macro
    j = bisect.bisect_right(KLOW, ci) - 1
    if j < 0: continue
    ki, l0i = LOWS[j]
    assert ki <= ci
    L0 = LO[l0i]
    h1i = max(range(l0i, ci + 1), key=lambda k: HI[k])
    H1 = HI[h1i]
    if H1 - L0 < 1e-9: continue
    retr = (H1 - flo) / (H1 - L0)
    if not (0.5 <= retr <= 1.3):
        continue
    # P1: barra do flush por preço
    fi = None
    for k in range(ci, max(ci - 96, h1i) - 1, -1):
        if abs(LO[k] - flo) <= 0.2 * a:
            fi = k; break
    if fi is None:
        skipped += 1; continue
    assert fi <= ci  # P2
    # E-features (trecho fi..ci e perna h1i..fi)
    low_run = flo
    t_since = 0
    for k in range(fi + 1, ci + 1):
        if LO[k] < low_run - 0.05 * a:
            low_run = LO[k]; t_since = 0
        else:
            t_since += 1
    probes = sum(1 for k in range(fi + 1, ci + 1) if LO[k] <= flo + 0.3 * a and CL[k] > flo)
    dn8 = max(0.0, (CL[max(0, ci - 8)] - CL[ci]) / a)
    dn24 = max(0.01, (CL[max(0, ci - 32)] - CL[max(0, ci - 8)]) / a)
    decel = dn8 / dn24
    basing = sum(1 for k in range(fi, ci + 1) if abs((HI[k] + LO[k]) / 2 - flo) <= 0.75 * a)
    second = 0
    rl = flo
    for k in range(fi + 2, ci + 1):
        if LO[k] <= flo + 0.5 * a and LO[k] >= flo + 0.1 * a and CL[k] > OP[k]:
            second = 1; break
    dleg_bars = max(1, fi - h1i)
    dleg_vel = (H1 - flo) / a / dleg_bars
    dleg_age = dleg_bars * 0.25
    rng = HI[fi] - LO[fi]
    prev8 = [HI[k] - LO[k] for k in range(max(0, fi - 8), fi)]
    fspike = rng / max(0.01, sum(prev8) / len(prev8)) if prev8 else None
    rspeed = ci - fi
    hi_e = bisect.bisect_right(ET, u["cj_t"])
    chplus = 0
    for m in range(hi_e - 1, -1, -1):
        if u["cj_t"] - events[m]["t"] > 24 * 900: break
        if events[m]["tok"] == "CHoCH+": chplus = 1; break
    u["_m"] = {"E1_t_since_low": t_since, "E2_probes": probes, "E3_decel": decel,
               "E4_basing": basing, "E5_second_test": second, "E6_dleg_vel": dleg_vel,
               "E7_dleg_age_h": dleg_age, "E8_final_spike": fspike, "E9_reclaim_speed": rspeed,
               "E10_chplus": chplus, "retr": retr}

BAND = [u for u in UNIV if u.get("_m")]
Bgt = [u for u in BAND if u["_gt"]]; Bng = [u for u in BAND if not u["_gt"]]
print(f"banda profunda: N{len(BAND)} · GT {len(Bgt)} · sósias {len(Bng)} · sem-flush-bar {skipped}")
print(f"\nFASE A — medianas GT vs sósia (+ q25/q75 GT):")
FEATS = ["E1_t_since_low", "E2_probes", "E3_decel", "E4_basing", "E5_second_test",
         "E6_dleg_vel", "E7_dleg_age_h", "E8_final_spike", "E9_reclaim_speed", "E10_chplus"]
sep = {}
for f in FEATS:
    A = sorted(u["_m"][f] for u in Bgt if u["_m"][f] is not None)
    B = sorted(u["_m"][f] for u in Bng if u["_m"][f] is not None)
    if not A or not B: continue
    ma, mb = st.median(A), st.median(B)
    # separação robusta: |dif mediana| / IQR combinado
    iqr = max(0.01, (sorted(A + B)[3 * len(A + B) // 4] - sorted(A + B)[len(A + B) // 4]))
    sep[f] = abs(ma - mb) / iqr
    print(f"  {f:<18} GT {ma:>7.2f} [{A[len(A)//4]:.2f},{A[3*len(A)//4]:.2f}] · sósia {mb:>7.2f} · sep {sep[f]:.2f}")
top = sorted(sep, key=lambda f: -sep[f])[:3]
print(f"\ntop-3 separação: {top}")

# FASE B — 4 looks declarados: conjunções q25-75 GT nas top features
def qgt(f, p):
    v = sorted(u["_m"][f] for u in Bgt if u["_m"][f] is not None)
    return v[int(p * (len(v) - 1))]
def null_p(rows, ref, seed):
    H0 = [1 if R3[u["cj_t"]]["R3"] >= 3 else 0 for u in ref]
    obs = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3) / len(rows)
    random.seed(seed)
    return sum(1 for _ in range(4000) if sum(random.sample(H0, len(rows))) / len(rows) >= obs) / 4000
def panel3(rows, tag):
    n = len(rows)
    if not n: print(f"  {tag:<30} vazio"); return None
    rs = sorted(rows, key=lambda u: u["cj_t"]); nets = [R3[u["cj_t"]]["net3"] for u in rs]
    h = sum(1 for u in rs if R3[u["cj_t"]]["R3"] >= 3); w = sum(1 for x in nets if x > 0)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {}
    for u2, x in zip(rs, nets): yr[u2["yr"]] = round(yr.get(u2["yr"], 0) + x, 1)
    gtp = sum(u2["_gt"] for u2 in rs)
    wk = len({u2["g_week"] for u2 in U})
    print(f"  {tag:<30} N{n:>4} hit3R {100*h/n:>5.1f}% WR {100*w/n:>5.1f}% NET {sum(nets):>+7.1f} DD {dd:>6.1f} "
          f"stk-{mL} | {n/wk:.2f}/sem | GTprec {gtp}/{n}={100*gtp/n:.0f}% | {yr}")
    return {"n": n, "hit": round(h/n, 3), "net": round(sum(nets), 1), "stk": mL, "gtp": gtp}
def inb(u, f, lo, hi):
    v = u["_m"][f]
    return v is not None and lo <= v <= hi
panel3(BAND, "BANDA (base)")
bands = {f: (qgt(f, 0.25), qgt(f, 0.75)) for f in FEATS}
looks = {
    "B1 top1": lambda u: inb(u, top[0], *bands[top[0]]),
    "B2 top1&top2": lambda u: inb(u, top[0], *bands[top[0]]) and inb(u, top[1], *bands[top[1]]),
    "B3 top1&2&3": lambda u: all(inb(u, f, *bands[f]) for f in top),
    "B4 exaustão-canônica": lambda u: u["_m"]["E1_t_since_low"] >= qgt("E1_t_since_low", 0.25)
        and u["_m"]["E3_decel"] <= qgt("E3_decel", 0.75) and u["_m"]["E2_probes"] >= qgt("E2_probes", 0.25),
}
out = {}
print(f"\nFASE B — 4 looks (bandas q25-75 GT):")
for nm, fn in looks.items():
    rows = [u for u in BAND if fn(u)]
    p = panel3(rows, nm)
    if rows and p:
        pn = null_p(rows, BAND, hash(nm) % 1000)
        print(f"      P(null vs banda)={pn:.4f}")
        out[nm] = {**p, "p": pn}
json.dump({"bands_gt": {f: bands[f] for f in FEATS}, "sep": sep, "top": top, "looks": out},
          open(HERE / "results" / "inband_exhaustion_discriminator_20260705.json", "w"), indent=1, default=float)
print("OK → results/inband_exhaustion_discriminator_20260705.json")
