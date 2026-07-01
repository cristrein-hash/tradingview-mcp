#!/usr/bin/env python3
"""_DA_phase35_causal_zones.py  (orphan-guard: prefixo _DA_, script SALVO, reprodutível)

DEVIL'S ADVOCATE sobre a tese estrutural do Cris (2026-07-01):
  "As zonas TOP/BOTTOM de cada regime tornam-se níveis que o PRÓXIMO regime RETESTA.
   BEAR capitula perto do BOTTOM (demanda) do regime anterior; entries no RANGE seguinte
   funcionam quando reteem o bottom do regime anterior."

phase35_structural_zones.py encontrou: trades com entry DENTRO de zona hand-drawn
'BOTTOM regime anterior' = N6 WR100% +17.1R  vs  'TOP regime anterior' = N21 WR29% +2.6R.

PROBLEMA: as 10 zonas foram DESENHADAS À MÃO com o chart INTEIRO visível. Se a zona foi
colocada onde o preço reverteu (hindsight), "trade dentro da zona ganha" é CIRCULAR.

ESTE SCRIPT constrói a versão 100% CAUSAL (zonas derivadas do hi/lo do segmento-fonte,
conhecidos no fim do segmento anterior — sem desenho à mão) e testa se o edge sobrevive.

Pontos: 1) zonas causais [lo, lo+k*ATR] / [hi-k*ATR, hi]; prior=imediato E prior=último RANGE/BULL-pre-BEAR.
        2) re-teste dos trades vs base rate.
        3) circularity check: gap zona-hand-drawn vs seg.lo do segmento-fonte.
        4) capitulation: bear-low vs prior-regime lo (ATR).
        5) n / multiple testing / permutação.
Só análise, nenhuma escrita em produção, nenhum toque no chart."""
import json, csv, io, contextlib, sys, bisect, datetime as dt, random
from pathlib import Path

VAL = Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation")
sys.path.insert(0, str(VAL))
with contextlib.redirect_stdout(io.StringIO()):
    import phase10_hybrid_regime as P
T, H, L, C = P.T, P.H, P.L, P.C


def dds(t):
    return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")


# --- ATR(14) 4H, causal (usa só barras fechadas até i) ---
def atr_series(period=14):
    tr = [0.0] * len(C)
    for i in range(1, len(C)):
        tr[i] = max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1]))
    atr = [0.0] * len(C)
    if len(C) > period:
        atr[period] = sum(tr[1:period + 1]) / period
        for i in range(period + 1, len(C)):
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


ATR = atr_series()


def atr_at(t):
    i = bisect.bisect_right(T, t) - 1
    i = max(0, min(i, len(ATR) - 1))
    # usar ATR da barra ANTERIOR ao evento (causal)
    return ATR[max(0, i - 1)] or ATR[i] or 1.0


segs = json.load(open("/tmp/causal_segments_v10.json"))
segs = sorted(segs, key=lambda s: s["start"])

# --- trades ---
D = Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/"
         "XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
trades = []
for r in csv.DictReader(open(D / "l2_bpt_regua_structural.csv")):
    bi = int(r["bar_idx"])
    trades.append({"bi": bi, "t": T[bi], "entry": float(r["entry"]),
                   "R": round(float(r["letrun_struct"]) - 0.35, 2)})


def stats(rows):
    if not rows:
        return "EMPTY"
    n = len(rows)
    wr = 100 * sum(1 for x in rows if x["R"] > 0) / n
    sr = sum(x["R"] for x in rows)
    return f"N={n} WR={wr:.0f}% sumR={sr:+.1f} avgR={sr / n:+.3f}"


# base rate reference book (all + >=2023, o subconjunto onde as zonas vivem)
ALL = trades
Y23 = [x for x in trades if dt.datetime.utcfromtimestamp(x["t"]).year >= 2023]
print("=" * 100)
print("BASE RATE (livro completo, sem seleção)")
print("=" * 100)
print("  ALL     :", stats(ALL))
print("  >=2023  :", stats(Y23))
BASE_WR = 100 * sum(1 for x in Y23 if x["R"] > 0) / len(Y23)
BASE_AVG = sum(x["R"] for x in Y23) / len(Y23)

# ============================================================================
# helper: para cada segmento, definir o "prior" de dois jeitos
#   (A) prior = segmento imediatamente anterior (chained)
#   (B) prior = último RANGE ou BULL antes do BEAR/RANGE atual (reach-back)
# ============================================================================
def prior_immediate(idx):
    return segs[idx - 1] if idx > 0 else None


def prior_last_range_or_bull(idx):
    for j in range(idx - 1, -1, -1):
        if segs[j]["regime"] in ("RANGE", "BULL"):
            return segs[j]
    return None


# ============================================================================
# PONTO 1+2 — ZONAS CAUSAIS: para cada trade, olhar o segmento ATUAL do trade,
# pegar o segmento PRIOR (imediato ou reach-back), e definir zona bottom/top a
# partir do prior.lo/prior.hi conhecidos ANTES do segmento atual começar.
# Testar se entry cai dentro da prior-bottom-zone e se ganha.
# ============================================================================
def seg_index_at(t):
    for i, s in enumerate(segs):
        if s["start"] <= t <= s["end"]:
            return i
    # trades antes do 1o segmento (2019-2022): sem segmento -> None
    return None


def test_causal(prior_fn, k, band_mode, label):
    """band_mode='atr' -> [lo, lo+k*ATR]; 'pct' -> [lo, lo + k*(hi-lo)]"""
    bottom_hits, top_hits, no_seg = [], [], 0
    for x in trades:
        idx = seg_index_at(x["t"])
        if idx is None:
            no_seg += 1
            continue
        pr = prior_fn(idx)
        if pr is None:
            continue
        a = atr_at(pr["end"])  # ATR conhecido no fim do prior (causal)
        if band_mode == "atr":
            b_lo, b_hi = pr["lo"], pr["lo"] + k * a
            t_lo, t_hi = pr["hi"] - k * a, pr["hi"]
        else:  # pct of prior range
            rng = pr["hi"] - pr["lo"]
            b_lo, b_hi = pr["lo"], pr["lo"] + k * rng
            t_lo, t_hi = pr["hi"] - k * rng, pr["hi"]
        e = x["entry"]
        if b_lo <= e <= b_hi:
            bottom_hits.append(x)
        if t_lo <= e <= t_hi:
            top_hits.append(x)
    print(f"\n--- {label} ---")
    print(f"   prior-BOTTOM zone: {stats(bottom_hits)}   (base>=2023 WR{BASE_WR:.0f}% avgR{BASE_AVG:+.3f})")
    print(f"   prior-TOP    zone: {stats(top_hits)}")
    return bottom_hits, top_hits


print("\n" + "=" * 100)
print("PONTO 1+2 — ZONAS 100% CAUSAIS (derivadas de prior seg hi/lo, sem hand-drawing)")
print("=" * 100)
res = {}
for pname, pfn in [("PRIOR=imediato", prior_immediate),
                   ("PRIOR=ultimo RANGE/BULL", prior_last_range_or_bull)]:
    for k in (0.5, 1.0, 1.5):
        res[(pname, "atr", k)] = test_causal(pfn, k, "atr", f"{pname} | ATR band k={k}")
    for kp in (0.20, 0.33):
        res[(pname, "pct", kp)] = test_causal(pfn, kp, "pct", f"{pname} | %-range band k={kp}")

# ============================================================================
# PONTO 3 — CIRCULARITY CHECK sobre as 10 zonas hand-drawn.
# Para cada zona 'BOTTOM regime anterior', quanto a zona desenhada difere do
# seg.lo do segmento-fonte (causal)? E fica perto do LOW subsequente (hindsight)?
# ============================================================================
BOX = [
    ("atlF8P", 1991.26, 1926.71, 1684980000, 1719352800, "TOP regime BEAR/RANGE anteriores"),
    ("ROZB2X", 2144.73, 2058.70, 1697551200, 1720504800, "TOP regimes BULL/RANGE anteriores"),
    ("MoAPGk", 2305.92, 2229.45, 1709521200, 1721613600, "TOP regime anterior"),
    ("eKxgPH", 2542.55, 2429.92, 1723456800, 1738551600, "BOTTOM regime anterior"),
    ("AmKxn8", 2798.81, 2710.98, 1730426400, 1752069600, "TOP regime anterior"),
    ("rCNv4C", 3168.74, 3036.48, 1738206000, 1759485600, "TOP regime anterior"),
    ("B9wh1W", 3510.73, 3377.64, 1745373600, 1762513200, "TOP regime anterior"),
    ("klGwY0", 4007.03, 3819.12, 1759284000, 1770202800, "BOTTOM regime anterior"),
    ("Oid3MH", 4389.71, 4221.37, 1760925600, 1770015600, "TOP regime anterior"),
    ("NCWct7", 4601.27, 4494.00, 1766977200, 1772607600, "TOP regime anterior"),
]
print("\n" + "=" * 100)
print("PONTO 3 — CIRCULARITY: zona hand-drawn vs seg.lo causal do segmento-fonte")
print("=" * 100)
for bid, hi, lo, t0, t1, lab in BOX:
    if "BOTTOM" not in lab:
        continue
    # segmento-fonte = ultimo segmento que termina <= inicio da zona
    src = None
    for s in segs:
        if s["end"] <= t0 + 4 * 3600:
            src = s
    a = atr_at(t0)
    # low subsequente realizado dentro da janela projetada [t0,t1] (hindsight ref)
    i0 = bisect.bisect_left(T, t0); i1 = bisect.bisect_right(T, t1)
    fut_low = min(L[i0:i1]) if i1 > i0 else None
    print(f"\n[{bid}] zona hand-drawn {lo:.0f}-{hi:.0f}  ({dds(t0)}->{dds(t1)})")
    if src:
        gap_lo = (lo - src["lo"]) / a
        gap_hi = (hi - src["lo"]) / a
        print(f"   segmento-fonte {src['regime']}[{dds(src['start'])}->{dds(src['end'])}] "
              f"hi{src['hi']:.0f}/lo{src['lo']:.0f}  ATR~{a:.0f}")
        print(f"   GAP zona.lo vs src.lo = {lo - src['lo']:+.0f} ({gap_lo:+.1f} ATR) | "
              f"zona.hi vs src.lo = {hi - src['lo']:+.0f} ({gap_hi:+.1f} ATR)")
        print(f"   src.hi vs zona: zona.lo-src.hi={lo - src['hi']:+.0f} ({(lo - src['hi']) / a:+.1f} ATR)")
    if fut_low is not None:
        gap_fl = (min(lo, hi) - fut_low) / a
        inside = lo <= fut_low <= hi
        print(f"   LOW subsequente realizado na janela = {fut_low:.0f}  | "
              f"dentro da zona? {inside} | zona.lo - fut_low = {lo - fut_low:+.0f} ({gap_fl:+.1f} ATR)")


# ============================================================================
# PONTO 4 — CAPITULATION: para cada BEAR, distancia do bear-low ao prior-lo.
# ============================================================================
print("\n" + "=" * 100)
print("PONTO 4 — CAPITULATION: bear-low vs prior-regime lo (ATR)")
print("=" * 100)
bear_gaps_imm, bear_gaps_rb = [], []
for i, s in enumerate(segs):
    if s["regime"] != "BEAR":
        continue
    a = atr_at(s["start"])
    pim = prior_immediate(i)
    prb = prior_last_range_or_bull(i)
    d_im = (s["lo"] - pim["lo"]) / a if pim else None
    d_rb = (s["lo"] - prb["lo"]) / a if prb else None
    if d_im is not None:
        bear_gaps_imm.append(d_im)
    if d_rb is not None:
        bear_gaps_rb.append(d_rb)
    dur_h = (s["end"] - s["start"]) / 3600
    print(f"  BEAR[{dds(s['start'])}->{dds(s['end'])}] dur~{dur_h:.0f}h lo{s['lo']:.0f}  ATR~{a:.0f}")
    if pim:
        print(f"     prior imediato {pim['regime']} lo{pim['lo']:.0f} -> bear_lo-prior_lo = "
              f"{s['lo'] - pim['lo']:+.0f} ({d_im:+.1f} ATR)")
    if prb:
        print(f"     prior RANGE/BULL {prb['regime']} lo{prb['lo']:.0f} -> bear_lo-prior_lo = "
              f"{s['lo'] - prb['lo']:+.0f} ({d_rb:+.1f} ATR)")


def summ(vals, lbl):
    if not vals:
        print(f"  {lbl}: n=0")
        return
    vals = sorted(vals)
    n = len(vals)
    med = vals[n // 2]
    within1 = sum(1 for v in vals if abs(v) <= 1.0)
    within2 = sum(1 for v in vals if abs(v) <= 2.0)
    print(f"  {lbl}: n={n} median={med:+.1f}ATR  |gap|<=1ATR: {within1}/{n}  |gap|<=2ATR: {within2}/{n}"
          f"  range[{vals[0]:+.1f},{vals[-1]:+.1f}]")


print("\n  RESUMO capitulation (quanto o bear-low fica ACIMA(+)/ABAIXO(-) do prior-lo):")
summ(bear_gaps_imm, "prior=imediato")
summ(bear_gaps_rb, "prior=ultimo RANGE/BULL")


# ============================================================================
# PONTO 5 — n / MULTIPLE TESTING: permutação sobre a melhor zona causal bottom.
# H0: entrar em zona bottom causal nao muda o avgR vs sortear o mesmo N do livro.
# ============================================================================
print("\n" + "=" * 100)
print("PONTO 5 — n / PERMUTACAO (base-rate framing)")
print("=" * 100)
# escolher a config causal bottom com maior N util (>=5) e reportar p-value permutacional
random.seed(42)
for key, (bh, th) in res.items():
    if len(bh) < 5:
        continue
    pname, mode, k = key
    obs_avg = sum(x["R"] for x in bh) / len(bh)
    obs_wr = 100 * sum(1 for x in bh if x["R"] > 0) / len(bh)
    n = len(bh)
    pool = trades  # livro completo como base
    ge = 0
    NPERM = 20000
    for _ in range(NPERM):
        samp = random.sample(pool, n)
        if sum(x["R"] for x in samp) / n >= obs_avg:
            ge += 1
    p = (ge + 1) / (NPERM + 1)
    print(f"  [{pname}|{mode}|k={k}] BOTTOM causal: N={n} WR={obs_wr:.0f}% avgR={obs_avg:+.3f} "
          f"| p(perm avgR>=obs)={p:.3f}")

# ============================================================================
# PONTO 6 — confirmar os 6 vencedores hand-drawn + checar SIMETRIA direcional
# (se TOP tambem paga na mesma config, o efeito NAO e' bottom-especifico = ruido)
# ============================================================================
print("\n" + "=" * 100)
print("PONTO 6 — hand-drawn 6/6 confirm + simetria direcional da melhor cell causal")
print("=" * 100)
HAND_BOT = [(2542.55, 2429.92, 1723456800, 1738551600),
            (4007.03, 3819.12, 1759284000, 1770202800)]
hits = [x for x in trades for hi, lo, t0, t1 in HAND_BOT
        if t0 <= x["t"] <= t1 and lo <= x["entry"] <= hi]
print(f"  hand-drawn BOTTOM: N={len(hits)} Rs={[x['R'] for x in hits]} "
      f"WR={100 * sum(1 for x in hits if x['R'] > 0) / len(hits):.0f}% "
      f"sumR={sum(x['R'] for x in hits):+.1f}")
bh, th = res[("PRIOR=imediato", "pct", 0.20)]
print(f"  causal pct-k0.2 BOTTOM: {stats(bh)}  vs  TOP: {stats(th)}")
print("  -> se TOP.avgR >= BOTTOM.avgR o 'edge' e' inespecifico de direcao (ruido de band larga)")

print("\n(fim — reprodução salva; ver verdict no relatório)")
