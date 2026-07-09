#!/usr/bin/env python3
"""F1 — STRUCTURAL LEG MACHINE (spec v1.2 §2-3; leitura DINÂMICA multi-fatorial de trajetória:
eficiência net/path + slope EMA/ATR + posição + histerese + override de flush — nunca snapshot de
eixo único, nunca zigzag/pivô confirmado por rally, nunca outcome/futuro).

Camadas (C2: constantes 100% do manifest — herdadas congeladas + 6 novas em grid):
  macro_regime : porte VERBATIM do v5 hour-causal (diário estável + override 1H) sobre RAW price-agg
  leg_dir      : raw_stable() VERBATIM com barra=bucket 1H (E50/E100, slope lb5, s100 lb10,
                 pos sobre M, peak 30, R_thr 2.0, banda .15-.85, cutoffs .55/.60) + histerese
                 K_up/K_down + flush override 15M nativo (dd do running-peak do run em ATR15,
                 rec = 5*mom)
  leg_phase    : 15M nativo sobre running extremes do run corrente (PROVISÓRIO mid-grid pb_min=1.25,
                 deep_thr=5.0, base_min=48 — REPORT-ONLY nesta fase, event layer NÃO calibrada)
  retr_fam     : retração vs perna macro (L0=fundo da última perna fechada, H1=running max desde L0);
                 UNDEFINED antes da 1ª perna fechada (C8)
Estados por barra 15M FECHADA (F0), causais: leg_dir da barra t usa o último bucket 1H FECHADO < hora
de t. Extremos = running extremes. Âncoras publicadas no flip (t_known). Sem eventos, sem entry."""
import json, sys, random, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from f0_raw_loader import load_cached

# ---------- constantes herdadas CONGELADAS (manifest.grid_preregistered) ----------
EFF_THR, SLOPE_THR, R_THR = 0.30, 0.20, 2.0
TOL_ANCHOR = 0.7
CUT_POS_BULL, CUT_POS_BEAR = 0.55, 0.6
BAND_LO, BAND_HI = 0.15, 0.85
PEAK_WIN = 30
W_WARMUP = 400            # barras 15M (manifest C2)
# macro (porte verbatim v5): N=15 diário, K=Kbear=5, override 1H P48/mom24/dd0.06/rec120
MN, MK, MKB = 15, 5, 5
MP, MMOM, MDD, MREC = 48, 24, 0.06, 120
# leg_phase provisório (mid-grid, REPORT-ONLY em F1/F1.5)
PB_MIN, DEEP_THR, BASE_MIN = 1.25, 5.0, 48

SEED_CFG = {"M": 15, "K_up": 5, "K_down": 5, "D_flush": 2.0, "mom": 24}

# ---------- pré-computo (uma vez por processo) ----------
class Data:
    def __init__(self, bars=None, ts=None):
        if bars is None:
            bars, ts = load_cached()
        self.TS = ts
        self.O = [bars[t][0] for t in ts]; self.H = [bars[t][1] for t in ts]
        self.L = [bars[t][2] for t in ts]; self.C = [bars[t][3] for t in ts]
        n = len(ts)
        # ATR14 15M (SMA de TR, padrão v5)
        TR = [0.0]
        for i in range(1, n):
            TR.append(max(self.H[i]-self.L[i], abs(self.H[i]-self.C[i-1]), abs(self.L[i]-self.C[i-1])))
        self.ATR = [5.0]*n
        s = 0.0
        for i in range(1, n):
            s += TR[i]
            if i > 14: s -= TR[i-14]
            self.ATR[i] = s/min(i, 14)
        # buckets 1H (só de barras FECHADAS)
        Hh = {}
        for i, t in enumerate(ts):
            hk = t//3600
            g = Hh.setdefault(hk, {"c": self.C[i], "h": self.H[i], "l": self.L[i]})
            g["h"] = max(g["h"], self.H[i]); g["l"] = min(g["l"], self.L[i]); g["c"] = self.C[i]
        self.HK = sorted(Hh)
        self.HC = [Hh[k]["c"] for k in self.HK]
        self.HH = [Hh[k]["h"] for k in self.HK]
        self.HL = [Hh[k]["l"] for k in self.HK]
        # ATR 1H (SMA TR 14) p/ slope normalizado da camada de pernas
        nh = len(self.HK)
        TRh = [0.0]
        for j in range(1, nh):
            TRh.append(max(self.HH[j]-self.HL[j], abs(self.HH[j]-self.HC[j-1]), abs(self.HL[j]-self.HC[j-1])))
        self.HATR = [1.0]*nh
        s = 0.0
        for j in range(1, nh):
            s += TRh[j]
            if j > 14: s -= TRh[j-14]
            self.HATR[j] = s/min(j, 14) or 1.0
        # EMA 1H (padrão ema_at verbatim, janela 3n)
        self.HE50 = [self._ema(self.HC, j, 50) for j in range(nh)]
        self.HE100 = [self._ema(self.HC, j, 100) for j in range(nh)]
        # diário (macro verbatim)
        Dd = {}
        for i, t in enumerate(ts):
            k = t//86400
            g = Dd.setdefault(k, {"h": self.H[i], "l": self.L[i], "c": self.C[i]})
            g["h"] = max(g["h"], self.H[i]); g["l"] = min(g["l"], self.L[i]); g["c"] = self.C[i]
        self.DK = sorted(Dd)
        self.DC = [Dd[k]["c"] for k in self.DK]
        self.DH = [Dd[k]["h"] for k in self.DK]
        self.DL = [Dd[k]["l"] for k in self.DK]
        nd = len(self.DK)
        TRd = [0.0]
        for i in range(1, nd):
            TRd.append(max(self.DH[i]-self.DL[i], abs(self.DH[i]-self.DC[i-1]), abs(self.DL[i]-self.DC[i-1])))
        self._TRd = TRd
        self.DE50 = [self._ema(self.DC, i, 50) for i in range(nd)]
        self.DE100 = [self._ema(self.DC, i, 100) for i in range(nd)]
        self._macro()          # stable[] diário + ov_hour[]
        self._rawleg_cache = {}

    @staticmethod
    def _ema(arr, i, n):
        c = arr[max(0, i-3*n):i+1]; k = 2/(n+1); e = c[0]
        for v in c[1:]: e = v*k+e*(1-k)
        return e

    def _atrd(self, i, n=14):
        a = self._TRd[max(1, i-n+1):i+1]
        return sum(a)/len(a) if a else 1.0

    # ---- macro: porte VERBATIM raw_stable + histerese + override 1H (v5 hour-causal) ----
    def _macro(self):
        DC, DH, DL, E50, E100 = self.DC, self.DH, self.DL, self.DE50, self.DE100
        N = MN
        def raw_stable(i):
            if i < max(2*N, 40): return "RANGE"
            a = self._atrd(i) or 1.0; slope = (E50[i]-E50[i-5])/a
            seg = DC[i-N:i+1]; net = seg[-1]-seg[0]
            path = sum(abs(seg[j]-seg[j-1]) for j in range(1, len(seg))); eff = abs(net)/path if path > 0 else 0
            hh = max(DH[i-N:i]); ll = min(DL[i-N:i]); pos = (DC[i]-ll)/(hh-ll) if hh > ll else .5
            s100 = (E100[i]-E100[i-10])/a
            tu = eff >= EFF_THR and slope > SLOPE_THR; td = eff >= EFF_THR and slope < -SLOPE_THR
            sb = E50[i] > E100[i] and s100 > 0; se = E50[i] < E100[i] and s100 < 0
            cont = eff < EFF_THR and BAND_LO <= pos <= BAND_HI and abs(slope) < SLOPE_THR
            peak = max(DH[i-PEAK_WIN:i+1]); retreat = (peak-DC[i])/a
            lh = max(DH[i-N:i]) < max(DH[i-2*N:i-N]); bef = DC[i] < E50[i] and (E50[i]-E50[i-5]) < 0
            bl = DC[i] < min(DL[i-N:i-2])
            if (bl and bef) or (retreat >= R_THR and lh and bef) or td or (se and pos < CUT_POS_BEAR and not cont): return "BEAR"
            if tu or (sb and pos > CUT_POS_BULL and not cont): return "BULL"
            return "RANGE"
        rawS = [raw_stable(i) for i in range(len(self.DK))]
        stable = []; cur = "RANGE"; pend = None; pn = 0
        for v in rawS:
            if v == cur: pend = None; pn = 0
            elif v == pend: pn += 1
            else: pend = v; pn = 1
            need = MKB if pend == "BEAR" else MK
            if pn >= need: cur = pend; pend = None; pn = 0
            stable.append(cur)
        self.m_stable = stable
        ovh = []; ov = False; quiet = 0
        for j in range(len(self.HK)):
            if j < max(MP, MMOM): ovh.append(False); continue
            peak = max(self.HH[j-MP:j+1]); ddp = (peak-self.HC[j])/peak if peak > 0 else 0
            fired = ddp >= MDD and self.HC[j] < self.HC[j-MMOM]
            if fired: ov = True; quiet = 0
            elif ov:
                quiet += 1
                if quiet >= MREC: ov = False
            ovh.append(ov)
        self.m_ovh = ovh

    def macro_at(self, t):
        di = bisect.bisect_left(self.DK, t//86400)-1
        st = "RANGE" if di < 0 else self.m_stable[di]
        hi = bisect.bisect_right(self.HK, (t//3600)-1)-1
        ovr = self.m_ovh[hi] if hi >= 0 else False
        return "BEAR" if (ovr or st == "BEAR") else st

    # ---- camada de pernas: raw_stable VERBATIM com barra = bucket 1H, janela M ----
    def rawleg(self, M):
        if M in self._rawleg_cache:
            return self._rawleg_cache[M]
        HC, HH, HL, E50, E100, A = self.HC, self.HH, self.HL, self.HE50, self.HE100, self.HATR
        out = []
        for j in range(len(self.HK)):
            if j < max(2*M, 40): out.append("LEG_FLAT"); continue
            a = A[j] or 1.0; slope = (E50[j]-E50[j-5])/a
            seg = HC[j-M:j+1]; net = seg[-1]-seg[0]
            path = sum(abs(seg[k]-seg[k-1]) for k in range(1, len(seg))); eff = abs(net)/path if path > 0 else 0
            hh = max(HH[j-M:j]); ll = min(HL[j-M:j]); pos = (HC[j]-ll)/(hh-ll) if hh > ll else .5
            s100 = (E100[j]-E100[j-10])/a
            tu = eff >= EFF_THR and slope > SLOPE_THR; td = eff >= EFF_THR and slope < -SLOPE_THR
            sb = E50[j] > E100[j] and s100 > 0; se = E50[j] < E100[j] and s100 < 0
            cont = eff < EFF_THR and BAND_LO <= pos <= BAND_HI and abs(slope) < SLOPE_THR
            peak = max(HH[j-PEAK_WIN:j+1]); retreat = (peak-HC[j])/a
            lh = max(HH[j-M:j]) < max(HH[j-2*M:j-M]); bef = HC[j] < E50[j] and (E50[j]-E50[j-5]) < 0
            bl = HC[j] < min(HL[j-M:j-2])
            if (bl and bef) or (retreat >= R_THR and lh and bef) or td or (se and pos < CUT_POS_BEAR and not cont): out.append("LEG_DOWN")
            elif tu or (sb and pos > CUT_POS_BULL and not cont): out.append("LEG_UP")
            else: out.append("LEG_FLAT")
        self._rawleg_cache[M] = out
        return out

def walk(D, cfg, i_end=None):
    """Walk streaming CAUSAL sobre barras 15M fechadas [0, i_end). Devolve (states, legs, anchors).
    states[i] = dict por barra. Sem futuro: leg_dir usa último bucket 1H FECHADO < hora da barra."""
    M, K_up, K_down = cfg["M"], cfg["K_up"], cfg["K_down"]
    D_flush, mom = cfg["D_flush"], cfg["mom"]
    rec = 5*mom
    n = len(D.TS) if i_end is None else i_end
    raw = D.rawleg(M)
    # histerese sobre buckets 1H (estado do bucket j conhecido no FECHO do bucket j)
    hstate = []; cur = "LEG_FLAT"; pend = None; pn = 0
    for v in raw:
        if v == cur: pend = None; pn = 0
        elif v == pend: pn += 1
        else: pend = v; pn = 1
        need = K_down if pend == "LEG_DOWN" else K_up
        if pn >= need: cur = pend; pend = None; pn = 0
        hstate.append(cur)
    HKl = D.HK
    states = [None]*n; legs = []; anchors = []
    ov = False; quiet = 0
    run = None   # perna corrente: dict(dir, i0, max_px, max_t, min_px, min_t)
    L0 = None; L0_t = None; H1 = None   # retr_fam
    inzone_lo = 0; inzone_hi = 0
    for i in range(n):
        t = D.TS[i]; c = D.C[i]; hi_ = D.H[i]; lo_ = D.L[i]; a = D.ATR[i] or 5.0
        hj = bisect.bisect_right(HKl, (t//3600)-1)-1
        base = hstate[hj] if hj >= 0 else "LEG_FLAT"
        # flush override 15M (dd do running-peak do run corrente)
        if run is not None:
            dd_atr = (run["max_px"]-c)/a
            fired = dd_atr >= D_flush and i >= mom and c < D.C[i-mom]
            if fired: ov = True; quiet = 0
            elif ov:
                quiet += 1
                if quiet >= rec: ov = False
        dirn = "LEG_DOWN" if ov else base
        warm = i < W_WARMUP
        if run is None:
            run = {"dir": dirn, "i0": i, "max_px": hi_, "max_t": t, "min_px": lo_, "min_t": t}
            inzone_lo = inzone_hi = 0
        elif dirn != run["dir"]:
            # fecha perna: extremos running JÁ conhecidos; âncora publicada AGORA (t_known = t)
            legs.append({"dir": run["dir"], "t_start": D.TS[run["i0"]], "t_end": t,
                         "top_px": run["max_px"], "top_t": run["max_t"],
                         "bot_px": run["min_px"], "bot_t": run["min_t"],
                         "dur_bars": i-run["i0"]})
            # t_known = FECHO da barra do flip (t+900): a decisão usa o close (DA F0-F1.5 correção 5)
            anchors.append({"px": run["max_px"], "t_known": t+900, "type": "leg_top", "leg_i": len(legs)-1})
            anchors.append({"px": run["min_px"], "t_known": t+900, "type": "leg_bottom", "leg_i": len(legs)-1})
            L0 = run["min_px"]; L0_t = t; H1 = run["max_px"]     # retr_fam: L0 = fundo da perna fechada
            run = {"dir": dirn, "i0": i, "max_px": hi_, "max_t": t, "min_px": lo_, "min_t": t}
            inzone_lo = inzone_hi = 0
        else:
            if hi_ > run["max_px"]: run["max_px"] = hi_; run["max_t"] = t
            if lo_ < run["min_px"]: run["min_px"] = lo_; run["min_t"] = t
        if H1 is not None:
            H1 = max(H1, hi_)
        # leg_phase (15M nativo; PROVISÓRIO REPORT-ONLY)
        if dirn == "LEG_UP":
            phase = "PULLBACK" if (run["max_px"]-c)/a >= PB_MIN else "IMPULSE"
        elif dirn == "LEG_DOWN":
            depth = (run["max_px"]-run["min_px"])/a
            if depth >= DEEP_THR: phase = "DEEP"
            elif (c-run["min_px"])/a >= 1.0: phase = "SHALLOW_BOUNCE"
            else: phase = "ACTIVE"
        else:
            span = run["max_px"]-run["min_px"]
            if c <= run["min_px"]+TOL_ANCHOR*a: inzone_lo += 1
            else: inzone_lo = 0
            if c >= run["max_px"]-TOL_ANCHOR*a: inzone_hi += 1
            else: inzone_hi = 0
            if inzone_lo >= BASE_MIN: phase = "BASE_BOTTOM"
            elif inzone_hi >= BASE_MIN: phase = "DISTRIBUTION_TOP"
            else: phase = "NEUTRAL"
        # retr_fam (UNDEFINED antes da 1ª perna fechada — C8)
        if L0 is None or H1 is None or H1 <= L0:
            fam = "UNDEFINED"; retr = None
        else:
            retr = (H1-c)/(H1-L0)
            fam = "RASO" if retr < 0.5 else ("BANDA" if retr <= 1.3 else "FUNDO")
        d_vale = round((t-run["min_t"])/900)
        states[i] = {"t": t, "macro": D.macro_at(t), "leg_dir": dirn, "leg_phase": phase,
                     "retr_fam": fam, "d_vale": d_vale, "warmup": warm, "override": ov}
    return states, legs, anchors

def truncation_test(D, cfg, n_samples=12, seed=20260709):
    """Recompute com série truncada em i == estado do walk streaming completo em i (zero tolerância)."""
    full, _, _ = walk(D, cfg)
    rng = random.Random(seed)
    idxs = sorted(rng.sample(range(W_WARMUP+100, len(D.TS)-1), n_samples))
    fails = []
    for i in idxs:
        part, _, _ = walk(D, cfg, i_end=i+1)
        a, b = full[i], part[i]
        if a != b:
            fails.append({"i": i, "full": a, "trunc": b})
    return {"n_samples": n_samples, "indices": idxs, "fails": fails, "pass": not fails}

if __name__ == "__main__":
    D = Data()
    states, legs, anchors = walk(D, SEED_CFG)
    tr = truncation_test(D, SEED_CFG)
    assert tr["pass"], f"STOP: truncation test FAIL: {tr['fails'][:2]}"
    n = len(states)
    occ = {}
    for s in states:
        occ[s["leg_dir"]] = occ.get(s["leg_dir"], 0)+1
    ph = {}
    for s in states:
        ph[s["leg_phase"]] = ph.get(s["leg_phase"], 0)+1
    durs = sorted(l["dur_bars"] for l in legs)
    months = (D.TS[-1]-D.TS[0])/(30*86400)
    out = {"config": SEED_CFG, "n_bars": n, "n_legs": len(legs), "legs_per_month": round(len(legs)/months, 2),
           "leg_dur_median_h": round(durs[len(durs)//2]*0.25, 1) if durs else None,
           "occupancy_pct": {k: round(100*v/n, 1) for k, v in sorted(occ.items())},
           "phase_pct": {k: round(100*v/n, 1) for k, v in sorted(ph.items())},
           "n_anchors": len(anchors),
           "truncation_test": {"pass": tr["pass"], "n_samples": tr["n_samples"]},
           "provisional_note": "leg_phase/retr_fam com defaults mid-grid REPORT-ONLY; event layer NÃO calibrada"}
    (HERE/"results/f1_structural_leg_machine_result.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    print("F1_PASS")
