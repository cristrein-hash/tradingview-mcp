#!/usr/bin/env python3
"""BANCO DE ENSAIO — ramo RANGE estrutural do Layer1 (sessão 2026-07-13, engine multi-agente).

OBJETIVO: encontrar uma deteção de RANGE ESTRUTURAL ("entre-tendências") agregada a CONFLUÊNCIA
DE INDICADORES, causal SEM LOOKAHEAD, que ADICIONE range recall SEM PARTIR os turnos já selados
(motor v3: bears 5/5, onsets tight). Não é caça a métrica mágica: confluência + estrutura.

O motor de TURNOS é FIXO (idêntico ao macro_structural_v3): crash>BEAR; em BULL, CHoCH-dn+bear_gate
=>BEAR; em BEAR, CHoCH-up+bull_gate=>BULL. A REVERSÃO tem PRIORIDADE sobre entrar em range (protege
onsets). O ramo RANGE é PLUGÁVEL: um módulo-candidato decide, com features causais (2 escalas de
pivô + indicadores), quando uma tendência VIRA range e quando o range ROMPE.

CAUSALIDADE POR CONSTRUÇÃO: o harness só passa ao candidato o ctx da barra i com dados <= i
(arrays pré-computados com janelas que terminam em i; pivôs confirmados só em bar+m). O candidato
NÃO deve tocar em arrays globais de futuro — a fase DA verifica isso.

INTERFACE do módulo-candidato (ficheiro range_cand_<id>.py):
    NAME = "..."; LENS = "descrição da lente estrutural + indicadores usados"
    def enter_range(c) -> bool          # de BULL/BEAR: demover para RANGE agora?
    def exit_range(c, rng_hi, rng_lo) -> "BULL"|"BEAR"|None   # de RANGE: rompeu? p/ que lado?
    (opcional) def band(c) -> (hi, lo)  # banda inicial do range; default = swing-scale
`c` é um dict (ver CTX_KEYS). Correr:  python3 range_lab_harness.py range_cand_<id>
Imprime VETOR AUDITADO + PRESERVAÇÃO-DOS-TURNOS (rejeitar se bears<5/5 ou onsets degradam)."""
import json, sys, importlib, statistics, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import macro_structural_v3 as V3
import layer1_audit_metrics as A
T, H, L, C, N = V3.T, V3.H, V3.L, V3.C, V3.N

# baseline dos turnos (v3 puro, band apertada => 0 range)
# TRAVA DE PRESERVAÇÃO (Cris 2026-07-13): o que é FIÁVEL = os 5 bears DETETADOS + 2026 segura
# macro-BEAR. Onsets são RUIDOSOS => informativos, NÃO gate: podem mover; se MELHORAM é bónus; só
# não pode PERDER um bear nem 2026 desabar. (Antes exigia onset ±10d = objetivo errado.)
BASELINE_ONSET = {"2020-09-21": 2.0, "2022-04-27": -1.0, "2023-05-17": 8.0,
                  "2024-11-11": 2.0, "2026-02-02": -2.0}
BEARS_2026_MIN = 90.0    # 2026 tem de segurar macro-BEAR (baseline 100)

# ---------------------------------------------------------------------------
# FEATURES CAUSAIS pré-computadas (indicator[i] usa só barras <= i)
# ---------------------------------------------------------------------------
def _rsi(n=14):
    out = [50.0]*N; g = ll = 0.0
    for i in range(1, N):
        ch = C[i]-C[i-1]; up = max(ch, 0); dn = max(-ch, 0)
        if i <= n: g += up; ll += dn; out[i] = 50.0
        else:
            g = (g*(n-1)+up)/n; ll = (ll*(n-1)+dn)/n
            out[i] = 100.0 if ll == 0 else 100-100/(1+g/ll)
    return out
def _dx(n=14):
    out = [0.0]*N
    for i in range(n+1, N):
        s_tr = s_p = s_m = 0.0
        for k in range(i-n+1, i+1):
            up = H[k]-H[k-1]; dn = L[k-1]-L[k]
            s_p += up if (up > dn and up > 0) else 0.0
            s_m += dn if (dn > up and dn > 0) else 0.0
            s_tr += max(H[k]-L[k], abs(H[k]-C[k-1]), abs(L[k]-C[k-1]))
        if s_tr <= 0: continue
        pdi = 100*s_p/s_tr; ndi = 100*s_m/s_tr
        out[i] = 100*abs(pdi-ndi)/(pdi+ndi) if (pdi+ndi) > 0 else 0.0
    return out
def _bbw(n=20):
    out = [0.0]*N
    for i in range(n, N):
        seg = C[i-n+1:i+1]; mu = sum(seg)/n
        sd = (sum((x-mu)**2 for x in seg)/n)**0.5
        out[i] = 100*4*sd/mu if mu else 0.0     # largura BB (4σ) relativa ao preço
    return out
def _atr(n=50):
    return [V3.atr(i, n) if i >= n else 0.0 for i in range(N)]
def _dd_ru():
    dd = [0.0]*N; ru = [0.0]*N
    for i in range(N):
        if i < 252: continue
        hi = max(H[i-252:i+1]); lo = min(L[i-252:i+1])
        dd[i] = (hi-C[i])/hi*100; ru[i] = (C[i]-lo)/lo*100
    return dd, ru

def _pivot_tracker(m):
    """arrays causais: prot_low/high (pivô imediato), prev_low/high, e swing-BOS bookkeeping."""
    ev = V3.fractal_pivots(m); pj = 0
    plow = [None]*N; phigh = [None]*N; pplow = [None]*N; pphigh = [None]*N
    since_bos = [0]*N; bos_dir = [0]*N
    prot_low = prot_high = prev_low = prev_high = None
    last_bos = None; cur_dir = 0; sh = None; sl = None
    for i in range(N):
        while pj < len(ev) and ev[pj][0] <= i:
            _, typ, pb, px = ev[pj]; pj += 1
            if typ == "H":
                prev_high, prot_high = prot_high, px
                if sh is None or px > sh: sh = px; last_bos = i; cur_dir = 1   # BOS up
            else:
                prev_low, prot_low = prot_low, px
                if sl is None or px < sl: sl = px; last_bos = i; cur_dir = -1  # BOS down
        plow[i], phigh[i] = prot_low, prot_high
        pplow[i], pphigh[i] = prev_low, prev_high
        since_bos[i] = (i-last_bos) if last_bos is not None else 9999
        bos_dir[i] = cur_dir
    return dict(plow=plow, phigh=phigh, pplow=pplow, pphigh=pphigh,
                since_bos=since_bos, bos_dir=bos_dir)

print("… pré-computando features causais", file=sys.stderr)
RSI = _rsi(14); DX = _dx(14); BBW = _bbw(20); ATR = _atr(50); DD, RU = _dd_ru()
PM = _pivot_tracker(5)     # escala IMEDIATA (turnos)
PS = _pivot_tracker(13)    # 2ª escala SWING (estrutura de range "entre-tendências")

CTX_KEYS = """i t close high low  prot_low prot_high prev_low prev_high  (imediato, m=5)
 sw_low sw_high sw_prev_low sw_prev_high sw_since_bos sw_bos_dir  (swing, m=13)
 dd ru atr atr_pct  rsi dx bbw  dxy_ret dxy_slope  rising falling crash
 choch_dn choch_up bear_gate bull_gate  state  don_w60 don_w120"""

def ctx(i, state):
    c = C[i]
    dxr = V3.dxy_ret(T[i]+86400, 90)
    dxr_s = dxr - V3.dxy_ret(T[i-20]+86400, 90) if i >= 20 else 0.0
    pl, ph = PM["plow"][i], PM["phigh"][i]
    d60 = (max(H[i-60:i])-min(L[i-60:i]))/c*100 if i >= 60 else 0.0
    d120 = (max(H[i-120:i])-min(L[i-120:i]))/c*100 if i >= 120 else 0.0
    return {
        "i": i, "t": T[i], "close": c, "high": H[i], "low": L[i],
        "prot_low": pl, "prot_high": ph, "prev_low": PM["pplow"][i], "prev_high": PM["pphigh"][i],
        "sw_low": PS["plow"][i], "sw_high": PS["phigh"][i],
        "sw_prev_low": PS["pplow"][i], "sw_prev_high": PS["pphigh"][i],
        "sw_since_bos": PS["since_bos"][i], "sw_bos_dir": PS["bos_dir"][i],
        "dd": DD[i], "ru": RU[i], "atr": ATR[i], "atr_pct": ATR[i]/c*100 if c else 0.0,
        "rsi": RSI[i], "dx": DX[i], "bbw": BBW[i],
        "dxy_ret": dxr, "dxy_slope": dxr_s,
        "rising": dxr > 0, "falling": dxr < 0,
        "crash": (C[i]/C[i-2]-1)*100 <= -6.0,
        "choch_dn": (pl is not None and c < pl), "choch_up": (ph is not None and c > ph),
        "bear_gate": ((C[i]/C[i-2]-1)*100 <= -6.0) or DD[i] >= 8.0 or dxr > 0,
        "bull_gate": (dxr < 0) or RU[i] >= 12.0,
        "state": state, "don_w60": d60, "don_w120": d120,
    }

def run(cand):
    """FSM: turnos FIXOS (reversão tem prioridade) + ramo RANGE plugável do candidato."""
    band = getattr(cand, "band", None)
    state = "RANGE"; rng_hi = rng_lo = None; out = []
    for i in range(N):
        if i < 360 or PM["plow"][i] is None or PM["phigh"][i] is None:
            out.append("RANGE"); continue
        c = ctx(i, state)
        if c["crash"]:
            state = "BEAR"; rng_hi = rng_lo = None
        elif state == "BULL":
            if c["choch_dn"] and c["bear_gate"]: state = "BEAR"
            elif cand.enter_range(c):
                state = "RANGE"
                rng_hi, rng_lo = (band(c) if band else (c["sw_high"], c["sw_low"]))
        elif state == "BEAR":
            if c["choch_up"] and c["bull_gate"]: state = "BULL"
            elif cand.enter_range(c):
                state = "RANGE"
                rng_hi, rng_lo = (band(c) if band else (c["sw_high"], c["sw_low"]))
        else:  # RANGE
            if rng_hi is None: rng_hi, rng_lo = c["sw_high"], c["sw_low"]
            rng_hi = max(rng_hi, c["prot_high"]); rng_lo = min(rng_lo, c["prot_low"])
            d = cand.exit_range(c, rng_hi, rng_lo)
            if d in ("BULL", "BEAR"): state = d; rng_hi = rng_lo = None
        out.append(state)
    return out

def report(lab, name):
    m = A.audit(lab)
    onset = m["onset_lag_by_bear"]; bears = m["bears_detected"]
    b2026 = m["coherence_2026_bear_pct"] or 0
    # TRAVA = 5 bears detetados + 2026 segura. Onset = informativo (melhor/pior/~igual), NÃO gate.
    lost = [k for k, base in BASELINE_ONSET.items() if onset.get(k) is None]
    turns_ok = (bears == "5/5") and (b2026 >= BEARS_2026_MIN)
    otag = []
    for k, base in BASELINE_ONSET.items():
        o = onset.get(k)
        if o is None: otag.append(f"{k}:PERDIDO")
        else:
            d = o-base; mark = "↓melhor" if d < -3 else ("↑pior" if d > 3 else "~igual")
            otag.append(f"{k}:{o}({mark})")
    why = "" if turns_ok else (" bears<5/5" if bears != "5/5" else "") + ("" if b2026 >= BEARS_2026_MIN else f" 2026={b2026}<{BEARS_2026_MIN}")
    print(f"== {name} · scorer AUDITADO ==")
    print(f"  TURNOS: bears {bears} · 2026 {b2026}% · PRESERVA={'SIM' if turns_ok else 'NAO'+why}")
    print(f"          onset(informativo, nao-gate): {' '.join(otag)}")
    print(f"  RANGE:  recall {m['recall']['RANGE']}% · false-bear-in-range {m['false_bear_in_range_pct']}% "
          f"· range-in-bull {m['false_range_in_bull_pct']}% · false-range-in-bear {m['false_range_in_bear_pct']}%")
    print(f"  GERAL:  runs {m['n_runs']} · recall {m['recall']} · bal {m['bal']} "
          f"· FB_bull {m['false_bear_in_bull_pct']}% · FBull_bear {m['false_bull_in_bear_pct']}%")
    print("  per-janela RANGE (GT):")
    for w in A.GT["windows"]:
        if w["regime"] == "RANGE":
            print(f"    {w['d0']}→{w['d1']}{' [nest]' if w['nested'] else ''} {m['per_window'][w['d0']]}%")
    return m, turns_ok

if __name__ == "__main__":
    modname = sys.argv[1].replace(".py", "")
    cand = importlib.import_module(modname)
    lab = run(cand)
    report(lab, getattr(cand, "NAME", modname))
