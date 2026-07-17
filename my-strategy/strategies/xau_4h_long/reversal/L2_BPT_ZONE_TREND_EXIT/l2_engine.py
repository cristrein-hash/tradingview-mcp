#!/usr/bin/env python3
"""L2/BPT XAU 4H LONG trend-exit — MOTOR PURO (FASE 1 do runtime live).

Port VERBATIM do research (USER_APPROVED_NOT_PRODUCTION, OK Cris 2026-07-02).
Cada bloco leva `# fonte: <ficheiro>:<linhas>`. Os quirks fazem parte da paridade
(V-1..V-4) — NÃO "melhorar" nada aqui sem re-correr as paridades.

Estrutura (dados passados como argumento; zero I/O, zero side-effects):
  1. make_regime_fsm(B4)        — FSM híbrido de regime (phase10)
  2. prepare_segments/make_selector — zonas phase48 (BULL ztop / BEAR deep / RANGE pos)
  3. make_detector(RAW)         — detector L2 v2.2 (candidatos BOS+pullback)
  4. prune_v2 via make_detector — PRUNED BASE V2 (overext | src_redundant | bear_flag)
  5. episodes_from(idxs)        — episódios gap<=6, representante = PRIMEIRO
  6. make_sl_context(frozen,dsq)— SL_CONTEXT + TOP_EXHAUSTION (demanda como argumento)
  7. make_trend_exit(bars,segs) — exit regime-flip (stop-first, cost 0.35, cap 500)

py3.9 · stdlib only.

Nota de escopo: SMA50 / bars 1D / SMA200_D do detector original NÃO são portados —
não entram em nenhuma camada aprovada (prune V2 usa só overextended_entry,
src_redundant e bear_flag). blk_bear_macro/first_retomada etc. ficam fora.
"""
import math
import statistics as st
import bisect
import datetime as dt

EPOCH_2023 = 1672531200  # corte dos segmentos (quirk phase10:125)


# =====================================================================
# 1) FSM DE REGIME (híbrido evento+estrutura)
# fonte: regime_turnstate_engine/validation/phase10_hybrid_regime.py:12-92 (funções)
#        e :119-133 (builder de segmentos)
# =====================================================================
def make_regime_fsm(B4):
    """B4: lista de bars {'t','o','h','l','c'} JÁ ordenada por t (contrato do
    phase10 load(), fonte :10-11). Devolve dict com run/build_segments/arrays."""
    T = [b["t"] for b in B4]
    C = [b["c"] for b in B4]
    H = [b["h"] for b in B4]
    L = [b["l"] for b in B4]
    n = len(B4)

    # fonte: phase10_hybrid_regime.py:12-19
    def rsi(c, k=14):
        g = [0.] * len(c); l = [0.] * len(c)
        for i in range(1, len(c)):
            d = c[i] - c[i - 1]; g[i] = max(d, 0); l[i] = max(-d, 0)
        ag = st.mean(g[1:k + 1]); al = st.mean(l[1:k + 1]); o = [50.] * len(c)
        for i in range(k + 1, len(c)):
            ag = (ag * (k - 1) + g[i]) / k; al = (al * (k - 1) + l[i]) / k
            o[i] = 100 - 100 / (1 + ag / al) if al else 100.
        return o

    # fonte: phase10_hybrid_regime.py:20-26
    def cusum(c, dr):
        r = [0.] + [math.log(c[i] / c[i - 1]) for i in range(1, len(c))]; a = set(); s = 0.
        for i in range(1, len(c)):
            w = r[max(1, i - 100):i]; mu = st.mean(w) if len(w) > 2 else 0
            sg = (st.pstdev(w) if len(w) > 2 else 1) or 1
            z = (r[i] - mu) / sg; s = max(0, s + (dr * z - 0.5))
            if s > 5: a.add(i); s = 0.
        return a

    # fonte: phase10_hybrid_regime.py:27
    def rng(b): return b["h"] - b["l"]

    # fonte: phase10_hybrid_regime.py:28-34 (usa C do escopo, quirk original)
    def bear_exp(B):
        o = []
        for i in range(25, len(B)):
            if C[i - 5] <= C[i - 14]: continue
            lv = st.mean([rng(b) for b in B[i - 14:i - 4]]) or 1e-9; w = B[i - 4:i + 1]
            if sum(1 for b in w if b["c"] < b["o"]) >= 4 and sum(1 for b in w if rng(b) > 1.5 * lv) >= 2 and C[i] < C[i - 5]: o.append(i)
        return o

    # fonte: phase10_hybrid_regime.py:35-38
    def ema(c, k):
        a = 2 / (k + 1); o = [c[0]]
        for x in c[1:]: o.append(a * x + (1 - a) * o[-1])
        return o

    # fonte: phase10_hybrid_regime.py:39-45
    EMAL = ema(C, 300)                   # macro (≈50 dias 4H) p/ sobre-extensão
    R4 = rsi(C)
    cd4 = cusum(C, -1); cu4 = cusum(C, 1)
    expdiv4 = [i for i in bear_exp(B4) if H[max(range(i - 8, i - 3), key=lambda k: H[k])] > H[max(range(i - 22, i - 9), key=lambda k: H[k])] and R4[max(range(i - 8, i - 3), key=lambda k: H[k])] < R4[max(range(i - 22, i - 9), key=lambda k: H[k])]]
    STRONG_TOP = set(cd4)               # topo FORTE (CUSUM-down/blow-off) -> caracteriza BEAR direto
    MILD_TOP = set(expdiv4) - set(cd4)  # topo suave -> RANGE (acumulação, pode re-expandir)
    BOT_EV = set(cu4)                   # evento de fundo (onset BULL rápido)

    # fonte: phase10_hybrid_regime.py:46-53
    def zigzag(p):
        piv = []; dirn = 0; hi_p = C[0]; hi_i = 0; lo_p = C[0]; lo_i = 0
        for i in range(1, n):
            if C[i] > hi_p: hi_p = C[i]; hi_i = i
            if C[i] < lo_p: lo_p = C[i]; lo_i = i
            if dirn >= 0 and C[i] <= hi_p * (1 - p): piv.append((i, hi_p, 'H')); dirn = -1; lo_p = C[i]; lo_i = i
            elif dirn <= 0 and C[i] >= lo_p * (1 + p): piv.append((i, lo_p, 'L')); dirn = 1; hi_p = C[i]; hi_i = i
        return piv

    # fonte: phase10_hybrid_regime.py:61-92
    def run(p_f, EXT=1.15, LO=0.88):
        piv = zigzag(p_f); pi = 0; SH = None; SL = None
        pivc = zigzag(0.08); pc = 0; SHc = None; SLc = None         # zigzag GROSSO p/ saída macro (ambos lados)
        state = 'BULL'; reg = [None] * n; r_hi = r_lo = None
        for i in range(n):
            while pi < len(piv) and piv[pi][0] <= i:
                if piv[pi][2] == 'H': SH = piv[pi][1]
                else: SL = piv[pi][1]
                pi += 1
            while pc < len(pivc) and pivc[pc][0] <= i:
                if pivc[pc][2] == 'H': SHc = pivc[pc][1]
                else: SLc = pivc[pc][1]
                pc += 1
            overext_hi = C[i] > EMAL[i] * EXT       # blow-off (topo de exaustão)
            overext_lo = C[i] < EMAL[i] * LO        # capitulação (fundo de exaustão)
            if state == 'BULL':
                if i in STRONG_TOP and overext_hi:
                    state = 'BEAR'                                   # blow-off SOBRE-ESTENDIDO: BEAR na mosca
                elif (i in MILD_TOP) or (i in STRONG_TOP):
                    state = 'RANGE'; r_hi = max(C[max(0, i - 8):i + 1]); r_lo = (SL if SL is not None else min(L[max(0, i - 8):i + 1]))
            elif state == 'BEAR':
                if i in BOT_EV and overext_lo:
                    state = 'BULL'                                   # capitulação SOBRE-ESTENDIDA: BULL na mosca (simétrico ao topo)
                elif i in BOT_EV:
                    state = 'RANGE'; r_lo = min(C[max(0, i - 8):i + 1]); r_hi = (SH if SH is not None else max(H[max(0, i - 8):i + 1]))
                elif SHc is not None and C[i] > SHc:                 # rompeu topo MACRO grosso: sai do BEAR
                    state = 'RANGE'; r_lo = min(C[max(0, i - 8):i + 1]); r_hi = SHc
            elif state == 'RANGE':
                if r_lo is not None and C[i] < r_lo: state = 'BEAR'
                elif r_hi is not None and C[i] > r_hi: state = 'BULL'
            reg[i] = state
        return reg

    # fonte: phase10_hybrid_regime.py:119-133 — builder de segmentos.
    # QUIRKS preservados: corte e<1672531200; hi/lo com bisect [i_s,i_e);
    # a barra de flip (T[i]) pertence ao intervalo do segmento ANTERIOR
    # (end=T[i] e bisect_right inclui a barra de flip no hi/lo do anterior).
    def build_segments(reg):
        segs = []; i0 = 0
        for i in range(1, n):
            if reg[i] != reg[i - 1]: segs.append((T[i0], T[i], reg[i - 1])); i0 = i
        segs.append((T[i0], T[-1], reg[-1]))
        out = []
        for s, e, f in segs:
            if e < 1672531200 or f is None: continue
            i_s = bisect.bisect_left(T, s); i_e = bisect.bisect_right(T, e)
            if i_e <= i_s: continue
            out.append({"start": int(s), "end": int(e), "regime": f, "hi": round(max(H[i_s:i_e]), 2), "lo": round(min(L[i_s:i_e]), 2),
                        "d0": dt.datetime.utcfromtimestamp(s).strftime("%Y-%m-%d"), "d1": dt.datetime.utcfromtimestamp(e).strftime("%Y-%m-%d")})
        return out

    return {"T": T, "C": C, "H": H, "L": L, "n": n, "run": run,
            "build_segments": build_segments, "zigzag": zigzag,
            "rsi": rsi, "cusum": cusum, "bear_exp": bear_exp, "ema": ema,
            "STRONG_TOP": STRONG_TOP, "MILD_TOP": MILD_TOP, "BOT_EV": BOT_EV}


# =====================================================================
# 2) ZONAS / SELEÇÃO phase48 (BULL zona-top, BEAR capitulação profunda, RANGE fundo)
# fonte: regime_turnstate_engine/validation/phase48_bear_deep_zone.py:14-46
# (mesmo contrato de research/l2_bpt_causal_selector.py:38-56)
# =====================================================================
def prepare_segments(segs):
    # fonte: phase48_bear_deep_zone.py:14-15
    segs = sorted(segs, key=lambda s: s['start'])
    for s in segs: s['bars'] = (s['end'] - s['start']) / 14400
    return segs


def make_selector(segs, T, H, L):
    """segs: saída de prepare_segments (hi/lo arredondados 2dp — quirk do JSON).
    T/H/L: arrays RAW 4H (mesmos do FSM). Devolve keep_signal(bar_idx, entry)."""

    # fonte: phase48_bear_deep_zone.py:16-19
    def seg_idx(t):
        for i in range(len(segs)):
            if segs[i]['start'] <= t <= segs[i]['end']: return i
        return None

    # fonte: phase48_bear_deep_zone.py:20-29
    # QUIRK: bars=(end-start)/14400 é tempo-CALENDÁRIO (inclui fins-de-semana), não nº de barras.
    def bear_deep(idx):
        """fundo da ACUMULAÇÃO de onde partiu a subida que o bear corrige = lo MÍNIMO dos regimes significativos
        (>=15 barras) nos ~180 dias antes do bear começar. zona = [lo_min, lo_min + banda]."""
        bear_start = segs[idx]['start']; win = 180 * 86400
        cand = [segs[j] for j in range(idx) if segs[j]['bars'] >= 15 and segs[j]['start'] >= bear_start - win]
        if not cand: cand = [segs[j] for j in range(idx) if segs[j]['bars'] >= 15]
        if not cand: return None
        lo_min = min(s['lo'] for s in cand)
        amp = max(s['hi'] - s['lo'] for s in cand)
        return (lo_min, lo_min + amp / 3)

    # fonte: phase48_bear_deep_zone.py:32-41 (construção por sinal) + :43-46 (keep)
    # RANGE: rmin/rmax do início do segmento ATÉ A BARRA DO ENTRY INCLUSIVE (linha 38).
    def signal_context(bar_idx, entry):
        bi = bar_idx; t = T[bi]; idx = seg_idx(t)
        if idx is None or idx == 0: return None
        s = segs[idx]; prev = segs[idx - 1]; amp = prev['hi'] - prev['lo']
        ztop = (prev['hi'] - amp / 3, prev['hi'])
        zdeep = bear_deep(idx)
        i0 = bisect.bisect_left(T, s['start']); rmin = min(L[i0:bi + 1]); rmax = max(H[i0:bi + 1])
        pos = (entry - rmin) / (rmax - rmin) if rmax > rmin else .5
        return {"bi": bi, "reg": s['regime'], "entry": entry, "ztop": ztop, "zdeep": zdeep, "pos": pos}

    # fonte: phase48_bear_deep_zone.py:43-46
    def keep(x):
        if x['reg'] == 'BULL': return x['ztop'][0] <= x['entry'] <= x['ztop'][1]
        if x['reg'] == 'BEAR': return x['zdeep'] and x['zdeep'][0] <= x['entry'] <= x['zdeep'][1]
        return x['pos'] < 0.34

    def keep_signal(bar_idx, entry):
        x = signal_context(bar_idx, entry)
        if x is None: return False, None
        return bool(keep(x)), x

    return {"seg_idx": seg_idx, "bear_deep": bear_deep,
            "signal_context": signal_context, "keep": keep, "keep_signal": keep_signal}


# =====================================================================
# 3) DETECTOR v2.2 + 4) PRUNE V2 blockers
# fonte: my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/pipeline/detectors/L2_detector_v2_2.py
#        my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/l2_layer23_diag.py:35-47,80-83
#        my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/build_pruned_base_v2.py:13,33-37
# =====================================================================
# fonte: L2_detector_v2_2.py:69-71
LARGE_BUY = 'plot_4'
LARGE_SELL = 'plot_8'
SELL_PLOTS = {'plot_6', 'plot_8', 'plot_10'}

# fonte: build_pruned_base_v2.py:13
REDUNDANT = {'fractal_2_2', 'nivel_interno', 'topo_duplo'}


def make_detector(RAW):
    """RAW: lista de bars frozen {'ts_epoch','open','high','low','close','volume',
    'rsi','bubbles_recent','nas_recent','smc_recent'} JÁ ordenada por ts_epoch
    (contrato do detector, fonte :19-20)."""
    N = len(RAW)

    # fonte: L2_detector_v2_2.py:28-39
    def build_atr(p=14):
        a = [None] * N
        for i in range(p, N):
            trs = []
            for j in range(i - p + 1, i + 1):
                if j == 0: continue
                trs.append(max(RAW[j]['high'] - RAW[j]['low'],
                               abs(RAW[j]['high'] - RAW[j - 1]['close']),
                               abs(RAW[j]['low'] - RAW[j - 1]['close'])))
            a[i] = sum(trs) / len(trs) if trs else None
        return a
    ATR = build_atr(14)

    # ---------- fontes de polaridade ----------
    # fonte: L2_detector_v2_2.py:78-86
    def find_fractal_3_3(i, lookback):
        out = []
        for p in range(max(3, i - lookback), i - 2):
            if p < 6: continue
            h = RAW[p]['high']
            if any(RAW[j]['high'] >= h for j in range(p - 3, p)): continue
            if any(RAW[j]['high'] >= h for j in range(p + 1, min(p + 4, i + 1))): continue
            out.append({'source': 'fractal_3_3', 'p': p, 'level': h})
        return out

    # fonte: L2_detector_v2_2.py:89-97
    def find_fractal_2_2(i, lookback):
        out = []
        for p in range(max(2, i - lookback), i - 1):
            if p < 4: continue
            h = RAW[p]['high']
            if any(RAW[j]['high'] >= h for j in range(p - 2, p)): continue
            if any(RAW[j]['high'] >= h for j in range(p + 1, min(p + 3, i + 1))): continue
            out.append({'source': 'fractal_2_2', 'p': p, 'level': h})
        return out

    # fonte: L2_detector_v2_2.py:100-115
    def find_topo_duplo(i, lookback, window=15, band_atr=0.5):
        out = []
        seen = set()
        for p1 in range(max(3, i - lookback), i - window - 2):
            h1 = RAW[p1]['high']
            atr1 = ATR[p1]
            if not atr1: continue
            for p2 in range(p1 + 3, min(p1 + window + 1, i - 2)):
                h2 = RAW[p2]['high']
                if abs(h2 - h1) > band_atr * atr1: continue
                level = max(h1, h2)
                key = (p2, round(level, 0))
                if key in seen: continue
                seen.add(key)
                out.append({'source': 'topo_duplo', 'p': p2, 'level': level})
        return out

    # fonte: L2_detector_v2_2.py:118-129
    def find_range_top(i, lookback):
        out = []
        for p in range(max(20, i - lookback), i - 2):
            h = RAW[p]['high']
            atr_v = ATR[p]
            if not atr_v: continue
            toques = sum(1 for j in range(p - 20, p) if abs(RAW[j]['high'] - h) <= 0.5 * atr_v)
            if toques < 1: continue
            if any(RAW[j]['high'] > h for j in range(p - 3, p)): continue
            if any(RAW[j]['high'] > h for j in range(p + 1, min(p + 4, i + 1))): continue
            out.append({'source': 'range_top', 'p': p, 'level': h})
        return out

    # fonte: L2_detector_v2_2.py:132-140
    def find_swing_high_simples(i, lookback):
        """Causal: high máximo dos últimos 10 bars ANTES de p (sem usar futuro além de p)."""
        out = []
        for p in range(max(10, i - lookback), i - 1):
            h = RAW[p]['high']
            # h é maior que todos os 10 bars anteriores
            if any(RAW[j]['high'] > h for j in range(p - 10, p)): continue
            out.append({'source': 'swing_high_simples', 'p': p, 'level': h})
        return out

    # fonte: L2_detector_v2_2.py:143-152
    def find_nivel_interno(i, lookback):
        """High recente dentro de 1.5 ATR do close[i] (proximidade operacional)."""
        atr_e = ATR[i]
        if not atr_e: return []
        out = []
        for p in range(max(0, i - lookback), i - 1):
            h = RAW[p]['high']
            if abs(h - RAW[i]['close']) > 1.5 * atr_e: continue
            out.append({'source': 'nivel_interno', 'p': p, 'level': h})
        return out

    # fonte: L2_detector_v2_2.py:155-173
    def gather_polarities_v2_2(i, lookback=100):
        """Retorna TODAS polaridades de todas fontes, com dedup mínimo (só níveis idênticos)."""
        all_pol = []
        all_pol.extend(find_fractal_3_3(i, lookback))
        all_pol.extend(find_fractal_2_2(i, lookback))
        all_pol.extend(find_topo_duplo(i, lookback))
        all_pol.extend(find_range_top(i, lookback))
        all_pol.extend(find_swing_high_simples(i, lookback))
        all_pol.extend(find_nivel_interno(i, lookback))

        # Dedup mínimo: por (level rounded to 0.1, p exato) — preserva sources distintas
        seen = set()
        unique = []
        for pol in all_pol:
            key = (round(pol['level'], 1), pol['p'])
            if key in seen: continue
            seen.add(key)
            unique.append(pol)
        return unique

    # ---------- gates da camada 1 ----------
    # fonte: L2_detector_v2_2.py:180-184
    def find_break_permissive(p, level, max_k):
        for k in range(p + 1, max_k + 1):
            if RAW[k]['close'] > level:
                return k
        return None

    # fonte: L2_detector_v2_2.py:187-190
    def has_acceptance_minimal(k, level, max_horizon=6, min_closes=1):
        end = min(k + max_horizon, N - 1)
        closes_above = sum(1 for j in range(k, end + 1) if RAW[j]['close'] > level)
        return closes_above >= min_closes

    # fonte: L2_detector_v2_2.py:193-195
    def is_tipo_A(i, level):
        b = RAW[i]
        return b['close'] > b['open'] and b['close'] >= level

    # fonte: L2_detector_v2_2.py:198-206
    def is_tipo_B_absorption(i, level, atr_e):
        b = RAW[i]
        if b['close'] >= b['open']: return False
        rng = b['high'] - b['low']
        if rng == 0: return False
        lw = min(b['open'], b['close']) - b['low']
        if lw / rng < 0.20: return False
        if b['close'] < level - 0.7 * atr_e: return False
        return True

    # fonte: L2_detector_v2_2.py:209-216
    def is_tipo_B_contextual(i, level, atr_e, min_sell=5):
        b = RAW[i]
        if b['close'] >= b['open']: return False
        if b['close'] < level - 0.7 * atr_e: return False
        bubs = b.get('bubbles_recent') or []
        sell_count = sum(1 for bb in bubs if bb.get('plot_id') in SELL_PLOTS
                         and bb.get('bars_ago') is not None and 0 <= bb['bars_ago'] <= 10)
        return sell_count >= min_sell

    # fonte: L2_detector_v2_2.py:219-228 — veto falso-Tipo-B (único veto duro Camada 1)
    def is_falso_tipo_B_dump_direto(i):
        """Único veto duro Camada 1."""
        b = RAW[i]
        if b['close'] >= b['open']: return False
        rng = b['high'] - b['low']
        if rng == 0: return False
        body = abs(b['close'] - b['open'])
        lw = min(b['open'], b['close']) - b['low']
        uw = b['high'] - max(b['open'], b['close'])
        return (body / rng > 0.5) and (lw / rng < 0.20) and (uw / rng < 0.10)

    # fonte: L2_detector_v2_2.py:231-319
    def candidate_l2_v2_2(i):
        """Camada 1 v2.2 — itera TODAS as polaridades sem prematuramente parar."""
        if ATR[i] is None: return None
        atr_e = ATR[i]

        if is_falso_tipo_B_dump_direto(i):
            return {'reject': 'falso_tipo_B_dump_direto'}

        polarities = gather_polarities_v2_2(i, lookback=100)
        if not polarities:
            return {'reject': 'sem_polaridade'}

        best = None
        best_score = -1
        rejection_reasons = []

        # Variant 1: BOS clássico (itera todas)
        for topo in polarities:
            p, level = topo['p'], topo['level']

            k = find_break_permissive(p, level, max_k=i - 1)
            if k is None:
                rejection_reasons.append(f'{topo["source"]} p={p}: sem break')
                continue

            if not has_acceptance_minimal(k, level, max_horizon=6, min_closes=1):
                rejection_reasons.append(f'{topo["source"]} p={p}: aceitação nula')
                continue

            if i - k > 100 or i <= k:
                rejection_reasons.append(f'{topo["source"]} p={p}: timing >100 bars')
                continue

            band_top = level + 0.8 * atr_e
            if RAW[i]['low'] > band_top:
                rejection_reasons.append(f'{topo["source"]} p={p}: low entry > banda')
                continue

            if RAW[i]['close'] < level - 0.7 * atr_e:
                rejection_reasons.append(f'{topo["source"]} p={p}: close perdeu polaridade')
                continue

            if min(RAW[j]['low'] for j in range(k + 1, i + 1)) > band_top:
                rejection_reasons.append(f'{topo["source"]} p={p}: pullback não tocou banda')
                continue

            is_a = is_tipo_A(i, level)
            is_b = is_tipo_B_absorption(i, level, atr_e)
            is_b_ctx = is_tipo_B_contextual(i, level, atr_e)
            if not (is_a or is_b or is_b_ctx):
                rejection_reasons.append(f'{topo["source"]} p={p}: tipo candle não A/B/B_ctx')
                continue

            tipo = 'A' if is_a else ('B' if is_b else 'B_ctx')
            atr_k = ATR[k]
            bos_mag_atr = (RAW[k]['close'] - level) / atr_k if atr_k else None
            score = (1.0 if topo['source'] in ('fractal_3_3', 'topo_duplo') else 0.5)
            score += (1 if RAW[i]['close'] >= level else 0)

            if score > best_score:
                best_score = score
                best = {
                    'pivot_idx': p, 'pivot_ts': RAW[p]['ts_epoch'], 'level': level,
                    'break_idx': k, 'entry_idx': i, 'entry_close': RAW[i]['close'],
                    'source': topo['source'], 'tipo': tipo, 'variant': 'classic_BOS',
                    'bos_mag_atr': bos_mag_atr, 'score': score
                }

        # Variant 2: Tipo B contextual sem BOS clássico (GT27)
        if best is None:
            for topo in polarities:
                p, level = topo['p'], topo['level']
                if abs(RAW[i]['close'] - level) > 1.0 * atr_e: continue
                if RAW[i]['close'] < level - 0.7 * atr_e: continue
                if not is_tipo_B_contextual(i, level, atr_e, min_sell=5): continue
                score = 0.3
                if score > best_score:
                    best_score = score
                    best = {
                        'pivot_idx': p, 'pivot_ts': RAW[p]['ts_epoch'], 'level': level,
                        'break_idx': None, 'entry_idx': i, 'entry_close': RAW[i]['close'],
                        'source': topo['source'], 'tipo': 'B_ctx', 'variant': 'contextual_no_BOS',
                        'bos_mag_atr': None, 'score': score
                    }

        if best:
            return best
        return {'reject': rejection_reasons[0] if rejection_reasons else 'no_match',
                'all_rejections': rejection_reasons[:5]}

    # fonte: L2_detector_v2_2.py:322-333 — 1 candidato/barra (dedup por entry_idx, melhor score)
    def run_candidate_generator():
        raw = []
        for i in range(50, N):
            r = candidate_l2_v2_2(i)
            if r and 'pivot_idx' in r:
                raw.append(r)
        # Dedup por entry_idx (cada bar produz no máximo 1 trigger)
        by_entry = {}
        for t in raw:
            if t['entry_idx'] not in by_entry or t['score'] > by_entry[t['entry_idx']]['score']:
                by_entry[t['entry_idx']] = t
        return sorted(by_entry.values(), key=lambda x: x['entry_idx'])

    # ---------- blockers do PRUNE V2 ----------
    # fonte: l2_layer23_diag.py:35-47
    def blk_bear_flag(c, lookback=15):
        p = c['pivot_idx']
        if p < lookback: return False
        for j in range(p - lookback, p):
            aj = ATR[j]
            if not aj: continue
            rng = RAW[j]['high'] - RAW[j]['low']
            if rng < 1.0 * aj: continue
            uw = RAW[j]['high'] - max(RAW[j]['open'], RAW[j]['close'])
            if rng == 0 or uw / rng < 0.6: continue
            if RAW[j]['close'] >= RAW[j]['open']: continue
            return True
        return False

    # fonte: l2_layer23_diag.py:80-83
    def blk_overextended_entry(c):
        ae = ATR[c['entry_idx']]
        if not ae: return False
        return RAW[c['entry_idx']]['close'] > c['level'] + 1.0 * ae

    # fonte: build_pruned_base_v2.py:33-37 (predicados sobre o candidato em vez da matrix CSV;
    # blk_* == '1' na matrix equivale a blocker True no candidato — l2_layer23_diag aplica-os direto)
    def prune_v2(c):
        return blk_overextended_entry(c) or (c['source'] in REDUNDANT) or blk_bear_flag(c)

    return {"N": N, "ATR": ATR, "build_atr": build_atr,
            "gather_polarities_v2_2": gather_polarities_v2_2,
            "candidate_l2_v2_2": candidate_l2_v2_2,
            "run_candidate_generator": run_candidate_generator,
            "is_falso_tipo_B_dump_direto": is_falso_tipo_B_dump_direto,
            "blk_bear_flag": blk_bear_flag, "blk_overextended_entry": blk_overextended_entry,
            "prune_v2": prune_v2}


# =====================================================================
# 5) EPISÓDIOS — candidatos consecutivos gap<=6 barras = 1 episódio; representante = PRIMEIRO
# fonte: my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/sl_context_fullbase.py:6-12
# =====================================================================
def episodes_from(idxs):
    """idxs: lista ORDENADA de entry_idx da pruned base V2."""
    idxs = sorted(idxs); eps = []; cur = [idxs[0]]
    for a, b in zip(idxs, idxs[1:]):
        if b - a <= 6: cur.append(b)
        else: eps.append(cur); cur = [b]
    eps.append(cur)
    return eps


# =====================================================================
# 6) SL_CONTEXT + TOP_EXHAUSTION (demanda 4H passada como ARGUMENTO — dsq)
# fonte: my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/sl_context.py:8-45
# =====================================================================
def make_sl_context(frozen, dsq):
    """frozen: bars frozen (mesmo contrato do detector). dsq: dict entry_idx -> row
    com campos 'nearest_4h_demand_low', 'dist_4h_demand_low_atr',
    'demand_4h_touched_on_retest' (strings, como no CSV demand_supply_quality)."""
    fr = frozen
    # fonte: sl_context.py:9-13
    H = [r['high'] for r in fr]; L = [r['low'] for r in fr]; C = [r['close'] for r in fr]
    O = [r['open'] for r in fr]; TS = [r['ts_epoch'] for r in fr]; RS = [r.get('rsi') for r in fr]; N = len(fr)
    ATR = [None] * N; trs = []
    for i in range(1, N):
        trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
        if i >= 14: ATR[i] = sum(trs[i - 14:i]) / 14

    # fonte: sl_context.py:14-16
    # QUIRK preservado: PL5 usa 5 barras de FUTURO (fallback mecânico antigo do swing_origin).
    PL5 = [False] * N
    for j in range(5, N - 5):
        if L[j] < min(L[j - 5:j]) and L[j] < min(L[j + 1:j + 6]): PL5[j] = True

    # fonte: sl_context.py:17-22
    def swing_origin(i):  # mecânico antigo (p/ comparar)
        p = C[i]; a = ATR[i]; lo = None
        for j in range(i - 5, 4, -1):
            if PL5[j] and L[j] < p: lo = L[j]; break
        if lo is None: lo = min(L[max(0, i - 6):i + 1])
        return max(p - (lo - 0.1 * a), 0.3 * a)

    # fonte: sl_context.py:23-24
    def legpos(i):
        p = C[i]; hi = max(H[max(0, i - 90):i + 1]); lo = min(L[max(0, i - 90):i + 1])
        return 100 * (p - lo) / (hi - lo) if hi > lo else 50

    # fonte: sl_context.py:26-29
    def dnum(r, k):
        try: return float(r[k])
        except: return None
    BUF = 0.1; FLOOR = 0.3

    # fonte: sl_context.py:31-45
    def context_sl(i):
        p = C[i]; a = ATR[i]; r = dsq.get(i, {})
        lp = legpos(i); rsi = RS[i] or 0
        # TOP_EXHAUSTION -> no_trade
        if lp >= 85 and rsi >= 70: return None, None, 'TOP_EXHAUSTION_NO_LONG', None
        dem_low = dnum(r, 'nearest_4h_demand_low'); dist = dnum(r, 'dist_4h_demand_low_atr')
        touched = r.get('demand_4h_touched_on_retest') == '1'
        # demanda defendida e razoável -> SL ancorado nela (tight quando perto, largo quando funda)
        if dem_low is not None and dist is not None and dist <= 5.0:
            sl = dem_low - BUF * a; risk = max(p - sl, FLOOR * a)
            typ = 'V_REVERSAL_DEMAND' if dist <= 2.0 else 'NORMAL_DEMAND_BASE'
            return sl, risk, typ, dist
        # demanda longe/ausente -> estrutura funda (swing origin) com flag review (entrada provavelmente tardia)
        risk = swing_origin(i)
        return p - risk, risk, 'LATE_WIDE_REVIEW', (dist if dist else 99)

    return {"N": N, "ATR": ATR, "H": H, "L": L, "C": C, "O": O, "TS": TS, "RS": RS,
            "PL5": PL5, "swing_origin": swing_origin, "legpos": legpos,
            "context_sl": context_sl}


# =====================================================================
# 7) EXIT trend-exit / regime-flip (stop-first por barra; cost 0.35; cap 500)
# fonte: research/l2_bpt_trailing_exit_test.py:15-35
#        (regime_at idêntico em research/l2_bpt_trend_exit_execution_risk_layer.py:20-22)
# =====================================================================
COST = 0.35
CAP = 500


# fonte: l2_bpt_trailing_exit_test.py:15-17
def g(b, *k):
    for kk in k:
        if kk in b: return b[kk]


def make_trend_exit(bars, segs):
    """bars: RAW 4H jsonl (chaves o/h/l/c/t ou open/...). segs: prepare_segments(...)."""
    # fonte: l2_bpt_trailing_exit_test.py:18
    O = [float(g(b, 'o', 'open')) for b in bars]; H = [float(g(b, 'h', 'high')) for b in bars]
    L = [float(g(b, 'l', 'low')) for b in bars]; C = [float(g(b, 'c', 'close')) for b in bars]
    T = [int(g(b, 't', 'time', 'ts')) for b in bars]; N = len(bars)

    # fonte: l2_bpt_trailing_exit_test.py:19-22
    SEG_START = [s['start'] for s in segs]
    def regime_at(j):
        i = bisect.bisect_right(SEG_START, T[j]) - 1
        return segs[i]['regime'] if 0 <= i < len(segs) else 'RANGE'

    # fonte: l2_bpt_trailing_exit_test.py:25
    def R_of(entry, sl, exitpx): return (exitpx - entry) / (entry - sl) - COST

    # fonte: l2_bpt_trailing_exit_test.py:31-35 — stop-first por barra; flip->BEAR sai no C[j]
    def regime_flip(bi, entry, sl):
        for j in range(bi + 1, min(bi + CAP, N - 1) + 1):
            if L[j] <= sl: return -1.0 - COST
            if regime_at(j) == 'BEAR': return R_of(entry, sl, C[j])
        return R_of(entry, sl, C[min(bi + CAP, N - 1)])

    # variante instrumentada (mesma matemática; devolve tb barra/motivo de saída)
    # espelha o sim() baseline de l2_bpt_trend_exit_execution_risk_layer.py:26-44 (sem partial/gap)
    def regime_flip_detail(bi, entry, sl):
        risk = entry - sl
        for j in range(bi + 1, min(bi + CAP, N - 1) + 1):
            if L[j] <= sl:
                return dict(bi=bi, R=round(-1.0 - COST, 2), exit_bar=j, mot="STOP", hold=j - bi)
            if regime_at(j) == 'BEAR':
                return dict(bi=bi, R=round((C[j] - entry) / risk - COST, 2), exit_bar=j, mot="BEAR", hold=j - bi)
        ej = min(bi + CAP, N - 1)
        return dict(bi=bi, R=round((C[ej] - entry) / risk - COST, 2), exit_bar=ej, mot="CAP", hold=ej - bi)

    return {"regime_at": regime_at, "regime_flip": regime_flip,
            "regime_flip_detail": regime_flip_detail, "R_of": R_of,
            "T": T, "H": H, "L": L, "C": C, "O": O, "N": N}
