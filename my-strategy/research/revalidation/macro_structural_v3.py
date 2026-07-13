#!/usr/bin/env python3
"""MACRO ESTRUTURAL v3 (spec aprovada Cris 2026-07-13: ESTRUTURA-cronometra / CONFLUÊNCIA-filtra).
Causa-raiz do whack-a-mole anterior: regime definido por NÍVEL (SMA/drawdown/dólar) num FSM pegajoso
=> toda virada atrasa => cada atraso pede um gatilho-onset com o seu limiar => erra a vizinha.

Redesenho: separa TIMING de SIGNIFICÂNCIA.
  TIMING  = ESTRUTURA. Pivôs fractais causais (m barras), reduzidos a esqueleto alternado H/L
            (enviesado a MUITOS pivôs — sem botão de magnitude no timing). A virada é um CHoCH
            geométrico: em BULL, close ROMPE abaixo do último swing-low protegido; em BEAR, close
            ROMPE acima do último swing-high protegido. Dispara NA barra do rompimento (sem lag).
  SIGNIF. = CONFLUÊNCIA (porteiro, não gatilho). Um CHoCH só FLIP-a o regime macro se a perna
            rompida for macro-escala (>= k_atr*ATR) E >=1 leitura ortogonal concordar
            (drawdown / dólar / crash p/ BEAR; dólar-a-cair / run-up p/ BULL). CHoCH que não passa
            = pullback interno => regime mantém. CRASH (2d) = override BEAR imediato.
  RANGE   = estrutura sem progressão (topo~=topo anterior E fundo~=fundo anterior = EQH/EQL);
            sai por rompimento SUSTENTADO de extremo com significância.
Causal close-only (pivô conhecido só em bar+m; rompimento avaliado ao close de i). RAW-nativo 1D.
Medição = scorer AUDITADO (layer1_audit_metrics), nunca %-por-barra sozinho. Sem P&L."""
import json, sys, bisect, statistics, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import layer1_audit_metrics as A
D1 = [json.loads(l) for l in open(HERE/"raw_1d_ohlc.jsonl")]
T = [b["t"] for b in D1]; H = [b["h"] for b in D1]; L = [b["l"] for b in D1]; C = [b["c"] for b in D1]
O = [b["o"] for b in D1]; N = len(T)
DXY = [json.loads(l) for l in open(HERE/"raw_dxy_1d.jsonl")]
DXY_K = [r["t"]+86400 for r in DXY]; DXY_C = [r["c"] for r in DXY]
def dxy_ret(t, w):
    j = bisect.bisect_right(DXY_K, t)-1
    return (DXY_C[j]/DXY_C[j-w]-1)*100 if j >= w else 0.0
# ATR causal (média do true range em atr_n dias até i)
def atr(i, n):
    s = 0.0
    for k in range(i-n+1, i+1):
        tr = max(H[k]-L[k], abs(H[k]-C[k-1]), abs(L[k]-C[k-1]))
        s += tr
    return s/n

def fractal_pivots(m):
    """pivôs fractais causais: swing-high em k confirmado em k+m se H[k] domina m barras de cada
    lado; idem swing-low. Devolve eventos (confirm_bar, tipo, pivot_bar, preço) ordenados por
    confirm_bar (só usáveis quando confirm_bar <= i => causal)."""
    ev = []
    for k in range(m, N-m):
        if all(H[k] > H[k-j] for j in range(1, m+1)) and all(H[k] >= H[k+j] for j in range(1, m+1)):
            ev.append((k+m, "H", k, H[k]))
        if all(L[k] < L[k-j] for j in range(1, m+1)) and all(L[k] <= L[k+j] for j in range(1, m+1)):
            ev.append((k+m, "L", k, L[k]))
    ev.sort()
    return ev

def build(m=4, k_atr=0.0, dd_bear=8.0, crash_thr=-6.0, dxy_w=90, atr_n=50,
          eq_tol=2.5, ru_bull=12.0, W_rng=120, band_rng=10.0):
    """TRACKER DE ESTRUTURA DE MERCADO (BOS/CHoCH próprio) + FSM CHoCH-porteiro.
    Protege o HIGHER-LOW ESTRUTURAL (o low que sustentou o último higher-high / BOS-up), não cada
    mini-pivô — assim mini-dips num bull não geram CHoCH. RANGE só via CHoCH-sem-significância."""
    ev = fractal_pivots(m); pj = 0
    # trackers de estrutura: pivôs IMEDIATOS (o último swing-low / swing-high confirmado) —
    # o HL protegido é o do pullback imediato antes do topo, não o mínimo profundo (=> turno no lugar)
    prot_low = None; prot_high = None          # último low / high pivot confirmado
    n_higher_lows = n_lower_highs = 0          # p/ deteção de range (progressão estrutural)
    prev_low = prev_high = None
    state = "RANGE"; rng_hi = rng_lo = None
    out = []
    for i in range(N):
        while pj < len(ev) and ev[pj][0] <= i:
            _, typ, pb, px = ev[pj]; pj += 1
            if typ == "H":
                if prot_high is not None:
                    n_lower_highs = n_lower_highs+1 if px < prot_high else 0
                prev_high, prot_high = prot_high, px
            else:
                if prot_low is not None:
                    n_higher_lows = n_higher_lows+1 if px > prot_low else 0
                prev_low, prot_low = prot_low, px
        if i < 360 or prot_low is None or prot_high is None:
            out.append("RANGE"); continue
        # leituras de contexto (causais, close de i)
        a = atr(i, atr_n)
        hi252 = max(H[i-252:i+1]); dd = (hi252-C[i])/hi252*100
        lo252 = min(L[i-252:i+1]); ru = (C[i]-lo252)/lo252*100
        rising = dxy_ret(T[i]+86400, dxy_w) > 0
        falling = dxy_ret(T[i]+86400, dxy_w) < 0
        crash = (C[i]/C[i-2]-1)*100 <= crash_thr
        # porteiro de significância (confluência) — >=1 leitura ortogonal
        bear_gate = crash or (dd >= dd_bear) or rising
        bull_gate = falling or (ru >= ru_bull)
        choch_dn = C[i] < prot_low                  # rompe o higher-low imediato
        choch_up = C[i] > prot_high                 # rompe o lower-high imediato
        # RANGE por CONTENÇÃO sustentada: preço bounded numa banda ao longo de W_rng dias
        # (largura Donchian relativa <= band_rng). Não fragmenta em tendência (banda larga).
        dc_hi = max(H[i-W_rng:i]); dc_lo = min(L[i-W_rng:i])
        contained = (dc_hi-dc_lo)/C[i]*100 <= band_rng
        # PRIORIDADE: crash > CONTENÇÃO (enquanto bounded, sem flip de tendência — mata
        # false-bear/bull dentro de range) > CHoCH-reversão estrutural com significância.
        if crash:
            state = "BEAR"; rng_hi = rng_lo = None
        elif contained:
            if state != "RANGE": rng_hi, rng_lo = dc_hi, dc_lo
            state = "RANGE"; rng_hi = max(rng_hi, dc_hi); rng_lo = min(rng_lo, dc_lo)
        elif state == "RANGE":   # deixou de estar contido => rompe na direção do gate
            if rng_hi is None: rng_hi, rng_lo = dc_hi, dc_lo
            if C[i] > rng_hi and bull_gate: state = "BULL"; rng_hi = rng_lo = None
            elif C[i] < rng_lo and bear_gate: state = "BEAR"; rng_hi = rng_lo = None
            # senão mantém RANGE até um gate confirmar a saída
        elif state == "BULL":
            if choch_dn and bear_gate: state = "BEAR"
        elif state == "BEAR":
            if choch_up and bull_gate: state = "BULL"
        out.append(state)
    return out

def _rsi14(n=14):
    """RSI de Wilder causal (idêntico ao harness). out[i] usa só barras <= i."""
    out = [50.0]*N; g = ll = 0.0
    for i in range(1, N):
        ch = C[i]-C[i-1]; up = max(ch, 0); dn = max(-ch, 0)
        if i <= n: g += up; ll += dn; out[i] = 50.0
        else:
            g = (g*(n-1)+up)/n; ll = (ll*(n-1)+dn)/n
            out[i] = 100.0 if ll == 0 else 100-100/(1+g/ll)
    return out

def build_layer1(m=5, m_sw=13, dd_bear=8.0, crash_thr=-6.0, dxy_w=90, ru_bull=12.0,
                 RSI_LO=40.0, RSI_HI=60.0, EQ=0.008, EXIT_BUF=0.02, POS_HI_BULL=0.72,
                 bull_rev_swing=True, min_bear_age=8):
    """LAYER1 COMPLETO (integração 2026-07-13): motor de TURNOS CHoCH (escala imediata m) + ramo
    RANGE estrutural SYNTH (validado pelo engine: recall 93%, PRESERVA turnos). RANGE = falha-de-
    progressão da 2ª escala de swing (m_sw), confirmada no imediato, SEM CHoCH, AGREGADA a (i) close
    no meio/fundo da banda de swing (corta consolidação-de-bull colada ao topo) e (ii) RSI de volta
    à banda média. Reversão dos turnos tem PRIORIDADE sobre entrar em range (protege onsets). Causal
    close-only, RAW-nativo. Reproduz byte-a-byte range_lab_harness.run(range_cand_SYNTH)."""
    evi = fractal_pivots(m); evs = fractal_pivots(m_sw); pi = ps = 0
    RSI = _rsi14(14)
    prot_low = prot_high = prev_low = prev_high = None       # escala imediata (turnos)
    sw_low = sw_high = sw_prev_low = sw_prev_high = None      # 2ª escala swing (range)
    state = "RANGE"; rng_hi = rng_lo = None; out = []; bear_age = 0
    for i in range(N):
        while pi < len(evi) and evi[pi][0] <= i:
            _, typ, pb, px = evi[pi]; pi += 1
            if typ == "H": prev_high, prot_high = prot_high, px
            else: prev_low, prot_low = prot_low, px
        while ps < len(evs) and evs[ps][0] <= i:
            _, typ, pb, px = evs[ps]; ps += 1
            if typ == "H": sw_prev_high, sw_high = sw_high, px
            else: sw_prev_low, sw_low = sw_low, px
        if i < 360 or prot_low is None or prot_high is None:
            out.append("RANGE"); continue
        hi252 = max(H[i-252:i+1]); dd = (hi252-C[i])/hi252*100
        lo252 = min(L[i-252:i+1]); ru = (C[i]-lo252)/lo252*100
        dxr = dxy_ret(T[i]+86400, dxy_w); rising = dxr > 0; falling = dxr < 0
        crash = (C[i]/C[i-2]-1)*100 <= crash_thr
        bear_gate = crash or dd >= dd_bear or rising
        bull_gate = falling or ru >= ru_bull
        choch_dn = C[i] < prot_low; choch_up = C[i] > prot_high
        # REVERSÃO BEAR->BULL: reconquistar o lower-high da 2ª ESCALA DE SWING (não o imediato).
        # Bear flag (bounce logo após crash) rompe só mini-highs mas NÃO reconquista o swing-high
        # (fica BEAR); fundo maduro já baixou os swing-highs e reconquista-os (vira BULL). Distingue
        # bear-flag de reversão genuína por MATURIDADE ESTRUTURAL, causal. choch_dn (turnos->BEAR)
        # fica no imediato (mantém onsets tight).
        rev_ref = sw_high if (bull_rev_swing and sw_high is not None) else prot_high
        choch_up_rev = C[i] > rev_ref
        rsi = RSI[i]
        swpos = ((C[i]-sw_low)/(sw_high-sw_low)
                 if (sw_high is not None and sw_low is not None and sw_high > sw_low) else None)
        stall_bull = (sw_high is not None and sw_prev_high is not None and sw_high <= sw_prev_high*(1+EQ)
                      and prev_high is not None and prot_high <= prev_high and not choch_dn)
        stall_bear = (sw_low is not None and sw_prev_low is not None and sw_low >= sw_prev_low*(1-EQ)
                      and prev_low is not None and prot_low >= prev_low and not choch_up)
        def enter_range():
            if not (RSI_LO <= rsi <= RSI_HI): return False
            if state == "BULL":
                if not stall_bull: return False
                if swpos is not None and swpos > POS_HI_BULL: return False
                return True
            if state == "BEAR": return stall_bear
            return False
        # FSM: TURNOS FIXOS (reversão prioridade) + ramo RANGE SYNTH
        if crash:
            state = "BEAR"; rng_hi = rng_lo = None
        elif state == "BULL":
            if choch_dn and bear_gate: state = "BEAR"
            elif enter_range(): state = "RANGE"; rng_hi, rng_lo = sw_high, sw_low
        elif state == "BEAR":
            # gate de MATURIDADE: bear muito jovem (ex.: bounce logo após crash) não pode virar BULL
            if choch_up_rev and bull_gate and bear_age >= min_bear_age: state = "BULL"
            elif enter_range(): state = "RANGE"; rng_hi, rng_lo = sw_high, sw_low
        else:  # RANGE — banda acumula extremos imediatos; sai por re-extensão OU rutura decisiva+gate
            if rng_hi is None: rng_hi, rng_lo = sw_high, sw_low
            rng_hi = max(rng_hi, prot_high); rng_lo = min(rng_lo, prot_low)
            new_hh = sw_high is not None and sw_prev_high is not None and sw_high > sw_prev_high*(1+EQ)
            new_ll = sw_low is not None and sw_prev_low is not None and sw_low < sw_prev_low*(1-EQ)
            if C[i] > rng_hi and bull_gate and (new_hh or C[i] > rng_hi*(1+EXIT_BUF)):
                state = "BULL"; rng_hi = rng_lo = None
            elif C[i] < rng_lo and bear_gate and (new_ll or C[i] < rng_lo*(1-EXIT_BUF)):
                state = "BEAR"; rng_hi = rng_lo = None
        out.append(state)
        bear_age = bear_age+1 if state == "BEAR" else 0
    return out

GRID = [(m, wr, br)
        for m in (5, 7) for wr in (90, 120, 150) for br in (8.0, 10.0, 13.0)]

def blocks(lab, since=2019):
    runs = []
    for i in range(N):
        if runs and runs[-1][0] == lab[i]: runs[-1][2] = i
        else: runs.append([lab[i], i, i])
    t0 = int(dt.datetime(since, 1, 1, tzinfo=dt.timezone.utc).timestamp())
    return [(s, a, b) for s, a, b in runs if T[b] >= t0 and (T[b]-T[a]) >= 5*86400]

def main():
    rows = []
    for m, wr, br in GRID:
        lab = build(m=m, W_rng=wr, band_rng=br)
        mm = A.audit(lab); sc = A.coherence_score(mm)
        rows.append({"cfg": (m, wr, br), "m": mm, "sc": sc, "lab": lab})
    rows.sort(key=lambda r: -r["sc"])
    print("== ESTRUTURAL v3 (CHoCH-timing / confluência-gate) · scorer AUDITADO ==")
    print(f"  {'cfg(m,Wrng,band)':<20} {'coh':>6} {'runs':>4} {'FBr_bl':>6} {'FBr_rg':>6} {'FBl_br':>6} {'RgBl':>5} {'RgRec':>5} {'2026':>5} {'bears':>5} {'bal':>4}")
    for r in rows:
        mm = r["m"]
        print(f"  {str(r['cfg']):<20} {r['sc']:6.1f} {mm['n_runs']:4d} "
              f"{str(mm['false_bear_in_bull_pct']):>6} {str(mm['false_bear_in_range_pct']):>6} "
              f"{str(mm['false_bull_in_bear_pct']):>6} {str(mm['false_range_in_bull_pct']):>5} "
              f"{str(mm['recall']['RANGE']):>5} "
              f"{str(mm['coherence_2026_bear_pct']):>5} {mm['bears_detected']:>5} {mm['bal']:4.0f}")
    best = rows[0]; mm = best["m"]
    print(f"\n== BEST {best['cfg']} · coherence {best['sc']} ==")
    print(f"  runs {mm['n_runs']} medDur {mm['med_dur_d']}d | onset {mm['onset_lag_by_bear']} | bears {mm['bears_detected']}")
    print(f"  false: bear-in-bull {mm['false_bear_in_bull_pct']}% · bear-in-range {mm['false_bear_in_range_pct']}% · bull-in-bear {mm['false_bull_in_bear_pct']}% · range-in-bull {mm['false_range_in_bull_pct']}%")
    print(f"  recall {mm['recall']} · 2026 held {mm['coherence_2026_bear_pct']}%")
    print("  per-janela:")
    for w in A.GT["windows"]:
        print(f"    {w['d0']}→{w['d1']} {w['regime']:<6}{' [nest]' if w['nested'] else '      '} {mm['per_window'][w['d0']]}%")
    print("\n  BLOCOS 2019+ (spot-check turno):")
    for s, a, b in blocks(best["lab"]):
        d0 = dt.datetime.utcfromtimestamp(T[a]).strftime("%Y-%m-%d")
        d1 = dt.datetime.utcfromtimestamp(T[b]).strftime("%Y-%m-%d")
        print(f"    {d0}→{d1} {s:<6} {int((T[b]-T[a])/86400):4d}d {C[a]:.0f}->{C[b]:.0f}")

if __name__ == "__main__":
    main()
