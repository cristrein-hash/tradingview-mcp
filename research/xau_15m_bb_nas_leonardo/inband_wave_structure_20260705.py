#!/usr/bin/env python3
"""DISCRIMINAÇÃO NA BANDA v2 — ESTRUTURA DE ONDAS DO PULLBACK (2026-07-05).
Iteração da v1 (exaustão 3-barras = degenerada: cj vem ~3 barras após flush; sequência não cabe
ali). A exaustão mora na estrutura do PULLBACK inteiro (12-25h): quantas ondas de queda já
caíram, quantas tentativas nesta zona, sweep da liquidez local, textura de volume.
FASE A2 (MAPA GT vs sósia, sem outcome) — features causais no trecho perna [h1i..fi] e cj:
  W1 n_waves      nº de ondas de queda (zigzag micro r=2ATR dentro do pullback)
  W2 last_wave_fr travel da onda final / maior onda (capitulação vs meio-de-perna)
  W3 prior_probes nº de lows locais anteriores a <=1,0ATR do flush_low nos últimos 96b (tentativas)
  W4 swept_local  flush_low fura o low mínimo das 32-96b anteriores em >=0,1ATR (varre liquidez)
  W5 bottom_time  fração das últimas 48b com close no quartil inferior do range do pullback
  W6 vol_climax   volume da barra do flush / média 48b
  W7 vol_dryup    vol médio últimas 16b / primeiras 16b do pullback
  W8 wave_decel   velocidade da onda final / velocidade da primeira onda
FASE B2 (TESTE, máx 4 looks declarados): conjunções q25-75 GT nas top-3 + 1 canônica
(W1>=2 & W3>=1 & W4==1 = "última varredura após tentativas com perna madura").
SANITY_PROBE: P1 tudo <= cj (asserts) · P2 null = candidatos da banda · P3 GT só métrica/calibração
· P4 zigzag micro causal por construção retrospectiva DENTRO de [h1i..fi] (janela toda <= cj)."""
import json, bisect, random, hashlib
import statistics as st
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "inband_exhaustion_discriminator_20260705.py").read_text().split("skipped = 0")[0])
VOL = [float(b.get("v") or 0) for b in S]

def micro_waves(h1i, fi):
    """zigzag r=2ATR dentro de [h1i..fi] (tudo <= cj): ondas de queda (H->L)."""
    waves = []
    d = 0; ehi = elo = h1i
    for i in range(h1i + 1, fi + 1):
        atr = ATR[i]
        if HI[i] > HI[ehi]: ehi = i
        if LO[i] < LO[elo]: elo = i
        if d >= 0 and HI[ehi] - LO[i] >= 2 * atr and ehi < i:
            d = -1; elo = min(range(ehi, i + 1), key=lambda k: LO[k]); start_hi = ehi
        elif d <= 0 and HI[i] - LO[elo] >= 2 * atr and elo < i:
            # onda de queda fechou: do último high ao low
            src = max(range(max(h1i, elo - 96), elo + 1), key=lambda k: HI[k])
            waves.append({"hi_i": src, "lo_i": elo, "travel": HI[src] - LO[elo],
                          "bars": max(1, elo - src)})
            d = 1; ehi = max(range(elo, i + 1), key=lambda k: HI[k])
    # onda final até fi (aberta)
    if d <= 0 or not waves or waves[-1]["lo_i"] < fi - 4:
        src = max(range(max(h1i, fi - 96), fi + 1), key=lambda k: HI[k])
        if HI[src] - LO[fi] > 1.0 * ATR[fi] and src < fi:
            waves.append({"hi_i": src, "lo_i": fi, "travel": HI[src] - LO[fi], "bars": max(1, fi - src)})
    return waves

skipped = 0
for u in UNIV:
    ci = bisect.bisect_right(TS, u["cj_t"]) - 1
    a = u.get("g_atr") or 5.0
    flo = u["g_sl"] + 0.1 * a
    u["_w"] = None
    j = bisect.bisect_right(KLOW, ci) - 1
    if j < 0: continue
    ki, l0i = LOWS[j]
    L0 = LO[l0i]
    h1i = max(range(l0i, ci + 1), key=lambda k: HI[k])
    H1 = HI[h1i]
    if H1 - L0 < 1e-9: continue
    retr = (H1 - flo) / (H1 - L0)
    if not (0.5 <= retr <= 1.3): continue
    fi = None
    for k in range(ci, max(ci - 96, h1i) - 1, -1):
        if abs(LO[k] - flo) <= 0.2 * a:
            fi = k; break
    if fi is None or fi <= h1i:
        skipped += 1; continue
    assert fi <= ci and h1i <= fi  # P1
    wv = micro_waves(h1i, fi)
    n_waves = len(wv)
    if wv:
        mx = max(w2["travel"] for w2 in wv)
        last_fr = wv[-1]["travel"] / max(0.01, mx)
        v_first = wv[0]["travel"] / a / wv[0]["bars"]
        v_last = wv[-1]["travel"] / a / wv[-1]["bars"]
        wdecel = v_last / max(0.01, v_first)
    else:
        last_fr = None; wdecel = None
    lows_prior = []
    for k in range(max(0, fi - 96), fi - 2):
        if LO[k] == min(LO[max(0, k - 4):k + 5]) and abs(LO[k] - flo) <= 1.0 * a:
            lows_prior.append(k)
    prior_probes = len(lows_prior)
    prev_min = min(LO[max(0, fi - 96):fi]) if fi > 0 else flo
    swept = int(flo <= prev_min - 0.1 * a)
    rng_lo, rng_hi = flo, H1
    q1 = rng_lo + 0.25 * (rng_hi - rng_lo)
    win48 = range(max(h1i, fi - 48), fi + 1)
    bottom_time = sum(1 for k in win48 if CL[k] <= q1) / max(1, len(list(win48)))
    v48 = [VOL[k] for k in range(max(0, fi - 48), fi)]
    vclimax = VOL[fi] / max(1e-9, sum(v48) / len(v48)) if v48 and VOL[fi] else None
    pb_len = fi - h1i
    if pb_len >= 32:
        vfirst = sum(VOL[k] for k in range(h1i, h1i + 16)) / 16
        vlast = sum(VOL[k] for k in range(fi - 16, fi)) / 16
        vdry = vlast / max(1e-9, vfirst)
    else:
        vdry = None
    u["_w"] = {"W1_n_waves": n_waves, "W2_last_wave_fr": last_fr, "W3_prior_probes": prior_probes,
               "W4_swept_local": swept, "W5_bottom_time": bottom_time, "W6_vol_climax": vclimax,
               "W7_vol_dryup": vdry, "W8_wave_decel": wdecel}

BAND = [u for u in UNIV if u.get("_w")]
Bgt = [u for u in BAND if u["_gt"]]; Bng = [u for u in BAND if not u["_gt"]]
print(f"banda: N{len(BAND)} · GT {len(Bgt)} · sósias {len(Bng)} · skip {skipped}")
FEATS = ["W1_n_waves", "W2_last_wave_fr", "W3_prior_probes", "W4_swept_local",
         "W5_bottom_time", "W6_vol_climax", "W7_vol_dryup", "W8_wave_decel"]
print(f"\nFASE A2 — medianas GT [q25,q75] vs sósia:")
sep = {}
for f in FEATS:
    A = sorted(u["_w"][f] for u in Bgt if u["_w"][f] is not None)
    B = sorted(u["_w"][f] for u in Bng if u["_w"][f] is not None)
    if not A or not B: continue
    ma, mb = st.median(A), st.median(B)
    iqr = max(0.01, (sorted(A + B)[3 * len(A + B) // 4] - sorted(A + B)[len(A + B) // 4]))
    sep[f] = abs(ma - mb) / iqr
    print(f"  {f:<17} GT {ma:>6.2f} [{A[len(A)//4]:.2f},{A[3*len(A)//4]:.2f}] · sósia {mb:>6.2f} · sep {sep[f]:.2f}")
top = sorted(sep, key=lambda f: -sep[f])[:3]
print(f"top-3: {top}")

def qgt(f, p):
    v = sorted(u["_w"][f] for u in Bgt if u["_w"][f] is not None)
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
    v = u["_w"][f]
    return v is not None and lo <= v <= hi
panel3(BAND, "BANDA (base)")
bands = {f: (qgt(f, 0.25), qgt(f, 0.75)) for f in FEATS}
looks = {
    "C1 top1": lambda u: inb(u, top[0], *bands[top[0]]),
    "C2 top1&2": lambda u: inb(u, top[0], *bands[top[0]]) and inb(u, top[1], *bands[top[1]]),
    "C3 top1&2&3": lambda u: all(inb(u, f, *bands[f]) for f in top),
    "C4 varredura-madura": lambda u: (u["_w"]["W1_n_waves"] >= 2 and u["_w"]["W3_prior_probes"] >= 1
                                       and u["_w"]["W4_swept_local"] == 1),
}
out = {}
print(f"\nFASE B2 — 4 looks:")
for nm, fn in looks.items():
    rows = [u for u in BAND if fn(u)]
    p = panel3(rows, nm)
    if rows and p:
        pn = null_p(rows, BAND, abs(hash(nm)) % 1000)
        print(f"      P(null vs banda)={pn:.4f}")
        out[nm] = {**p, "p": pn}
json.dump({"sep": sep, "top": top, "bands": {f: list(bands[f]) for f in FEATS}, "looks": out},
          open(HERE / "results" / "inband_wave_structure_20260705.json", "w"), indent=1, default=float)
print("OK → results/inband_wave_structure_20260705.json")
