#!/usr/bin/env python3
"""Headless scanner — L1 · EMA21 CONTINUATION (suite XAU 4H LONG — CONTINUATION).

Production v2, peça 1 (Scanner). Transforma a regra-base APROVADA da L1 num scanner PURO:
gera candidato + flag BLOCK/REVIEW e imprime JSON no stdout. NADA além disso.

NÃO faz: Telegram, envio, MCP/chart, daemon, journal, outcome, backtest, escrita de arquivo.
Read-only sobre a fonte RAW/canonical já usada no rebuild_v3.

Regra-base = gate idêntico ao rebuild_v2/rebuild_l1_ema21_a_f5_v2.py (close-only-causal, SHIFT1).
Gate de exaustão = RSI-only AUTOMÁTICO: rsi_vs_ma <= -9.35 -> state=blocked_exhaustion (não-operacional).
(O leg de volume vol_entry_z>=1.993 foi REMOVIDO 2026-06-15 — ver STRATEGY.md auditoria.)

Regime D-1 = **regime_l1_v4** (2026-06-16): UNIFICADO com runtime_xau.py via
`latest_state_before`. O regime_B_v3 (legado, morto como autoridade) foi REMOVIDO do caminho L1.
Funções de gate expostas a nível de módulo (build_series/gate_trace/...) para re-derivação reusar
a MESMA lógica sem duplicação.

Uso:
  python3 scanner.py                 # avalia o ÚLTIMO bar do RAW canônico
  python3 scanner.py --at <unixts>   # avalia o bar daquele timestamp (dry-run/verificação)
"""
import gzip, json, bisect, statistics, sys, hashlib
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
def _repo_root(p):
    for d in [p] + list(p.parents):
        if (d / "my-strategy").is_dir() and (d / "alert-bridge").is_dir():
            return d
    return p.parents[5]
REPO = _repo_root(HERE)
RAW = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
# Regime D-1 = regime_l1_v4 (UNIFICADO com runtime). regime_B_v3 NÃO entra no caminho L1.
REGIME = REPO / "my-strategy/core/regime_l1/regime_l1_v4_classifications.jsonl"
sys.path.insert(0, str(REPO / "my-strategy/core/regime_l1"))
from regime_l1_v4 import latest_state_before  # noqa: E402  (mesma função do runtime_xau.py)

SYMBOL, TIMEFRAME = "PEPPERSTONE:XAUUSD", "240"
# regra-base (idêntica ao rebuild_v2 — NÃO alterar sem re-aprovar)
ATR_MIN, ATR_MAX = 0.004, 0.030
BODY_MIN, F5_MAX, RET5_MIN = 0.35, 1.0, -0.04
OB_TOL, MA_TOL = 0.001, 0.002
# Gate de exaustão = RSI-only (2026-06-15). Leg de volume (vol_entry_z>=1.993) REMOVIDO
# (artefato de matriz bugada E morto sob F5). Ver STRATEGY.md (auditoria 2026-06-15).
RSI_VS_MA_THR = -9.35

# === Refinamento APROVADO 2026-06-16 (in-sample 2020-2026; ver APPROVED_REFINEMENT_2026_06_16.md) ===
# Filtros at-entry causais (stack v1 anti-extensão) + filtro NAS (SHIFT1). Thresholds CONGELADOS.
RET5_MAX = 0.0142          # ret5 (retorno 5 barras) <= 1.42%
EXT_EMA_ATR_MAX = 2.95     # (close-EMA21)/ATR <= 2.95
ZONE_W_ATR_MIN = 0.6       # largura da zona OB / ATR >= 0.6
DIST_ZONE_ATR_MAX = 1.81   # (entry-zone_high)/ATR <= 1.81
NAS_DIST_SHIFT1_MIN = 1.31 # NAS_DISTANCE_FROM_EMA_ATR no bar i-1 >= 1.31
SWING_N = 6                # swing low das últimas 6 barras (<= bar i)
SL_ATR_BUFFER = 0.1        # SL OFICIAL V1 (Cris 2026-07-03) = zone_OB_low - 0.1*ATR  (era max(zona,swing6): SUPERSEDED)
TARGET_R = 3.0             # +3R


def _f(x):
    """Parse seguro de valor de study_value (trata sinal unicode/strings)."""
    if x is None:
        return None
    try:
        return float(str(x).replace(" ", "").replace(",", "").replace("−", "-"))
    except Exception:
        return None


def load_series():
    """Lê o RAW canônico (read-only): OHLCV + zones Custom OB + RSI/RSI-MA + NAS_DISTANCE por bar."""
    bars, zones_at, rsi_at, nas_at = {}, {}, {}, {}
    with gzip.open(RAW, "rt") as f:
        for line in f:
            if '"replay_current_date"' not in line:
                continue
            r = json.loads(line)
            ov = r.get("ohlcv") or []
            if not ov:
                continue
            for b in ov:
                if b.get("time") is not None and b.get("close") is not None:
                    bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"],
                                       "c": b["close"], "v": b.get("volume") or 0}
            cur = max(b["time"] for b in ov)
            zs = []
            for s in (r.get("pine_boxes") or []):
                if "Custom OB" in s.get("name", ""):
                    for z in (s.get("zones") or []):
                        if z.get("high") is not None and z.get("low") is not None:
                            zs.append((z["high"], z["low"]))
            if zs:
                zones_at[cur] = zs
            for s in (r.get("study_values") or []):
                nm = s.get("name", "")
                if "Relative Strength Index" in nm:
                    vals = s.get("values") or {}
                    rsi_at[cur] = (_f(vals.get("RSI")), _f(vals.get("RSI-based MA")))
                if "NAS" in nm:
                    nas_at[cur] = _f((s.get("values") or {}).get("NAS_DISTANCE_FROM_EMA_ATR"))
    return bars, zones_at, rsi_at, nas_at


def ema(s, sp):
    k = 2 / (sp + 1); out = [None] * len(s); e = s[0]
    for i, x in enumerate(s):
        e = x if i == 0 else x * k + e * (1 - k); out[i] = e
    return out


def sma(s, n):
    out = [None] * len(s); q = deque(); ss = 0.0
    for i, x in enumerate(s):
        q.append(x); ss += x
        if len(q) > n: ss -= q.popleft()
        if len(q) == n: out[i] = ss / n
    return out


class Series:
    """Container das séries + features + regime (regime_l1_v4 classifications)."""
    __slots__ = ("T", "idx", "N", "O", "H", "L", "C", "V", "EMA21", "SMA50",
                 "ATR14", "zones_at", "rsi_at", "nas_at", "CLS")


def build_series():
    """Carrega RAW + computa indicadores + carrega classifications regime_l1_v4. Read-only."""
    bars, zones_at, rsi_at, nas_at = load_series()
    S = Series()
    S.T = sorted(bars); S.idx = {t: i for i, t in enumerate(S.T)}; S.N = len(S.T)
    S.O = [bars[t]["o"] for t in S.T]; S.H = [bars[t]["h"] for t in S.T]
    S.L = [bars[t]["l"] for t in S.T]; S.C = [bars[t]["c"] for t in S.T]
    S.V = [bars[t]["v"] for t in S.T]
    S.EMA21 = ema(S.C, 21); S.SMA50 = sma(S.C, 50)
    N = S.N; H = S.H; L = S.L; C = S.C
    TR = [H[0] - L[0]] + [max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])) for i in range(1, N)]
    S.ATR14 = [None] * N
    if N >= 14:
        a = sum(TR[:14]) / 14; S.ATR14[13] = a
        for i in range(14, N): a = (a * 13 + TR[i]) / 14; S.ATR14[i] = a
    S.zones_at = zones_at; S.rsi_at = rsi_at; S.nas_at = nas_at
    S.CLS = [json.loads(l) for l in open(REGIME) if l.strip()]
    return S


def regime_d1(S, et):
    """Regime D-1 causal = último regime_l1_v4 com ts < et (idêntico ao runtime_xau.py)."""
    state, _stale = latest_state_before(S.CLS, et)
    return state


def demand_zone(S, i):
    T, C, zones_at = S.T, S.C, S.zones_at
    zs = zones_at.get(T[i - 1])
    if not zs:
        j = i - 1
        while j >= 0 and T[j] not in zones_at: j -= 1
        zs = zones_at.get(T[j]) if j >= 0 else None
    if not zs: return None
    cprev = C[i - 1]; below = [(hi, lo) for hi, lo in zs if hi < cprev]
    if not below: return None
    return max(below, key=lambda z: z[0])


def gate_trace(S, i):
    """(passed, reason). Gate idêntico ao rebuild_v2 — close-only-causal. Regime via regime_l1_v4."""
    T, O, H, L, C, V = S.T, S.O, S.H, S.L, S.C, S.V
    EMA21, SMA50, ATR14 = S.EMA21, S.SMA50, S.ATR14
    if i < 60: return False, "history"
    if None in (EMA21[i - 1], SMA50[i - 1], ATR14[i - 1]) or i - 7 < 0 or SMA50[i - 7] is None:
        return False, "indicators_none"
    if regime_d1(S, T[i]) != "BULL": return False, "regime_d1_not_BULL"
    if not (C[i - 1] > EMA21[i - 1]): return False, "close_prev<=EMA21"
    if not (C[i - 1] > SMA50[i - 1]): return False, "close_prev<=SMA50"
    if not (EMA21[i - 1] > EMA21[i - 4]): return False, "ema21_slope3<=0"
    if not (SMA50[i - 1] > SMA50[i - 7]): return False, "sma50_slope6<=0"
    hh20 = max(H[max(0, i - 21):i - 1])
    if not (hh20 > max(C[max(0, i - 21):i - 1])): return False, "bos_fail"
    atrr = ATR14[i - 1] / C[i - 1]
    if not (ATR_MIN <= atrr <= ATR_MAX): return False, f"atr_ratio_oob({atrr:.4f})"
    dz = demand_zone(S, i)
    if dz is None: zhi = zlo = EMA21[i - 1]; tol = MA_TOL
    else: zhi, zlo = dz; tol = OB_TOL
    touched = (L[i] <= zhi * (1 + tol) and L[i] >= zlo * (1 - tol)) or \
              (L[i - 1] <= zhi * (1 + tol) and L[i - 1] >= zlo * (1 - tol)) or \
              (L[i] < zlo and C[i] > zhi)
    if not touched: return False, "zone_not_touched"
    if not (C[i] > zhi): return False, "close<=zone_high"
    rng = H[i] - L[i]
    if rng <= 0 or (C[i] - O[i]) / rng < BODY_MIN: return False, f"body_pct<{BODY_MIN}"
    if not (C[i] > C[i - 1]): return False, "close<=prior"
    if i - 5 < 0 or (C[i] / C[i - 5] - 1) <= RET5_MIN: return False, "ret5<=-4%"
    vmed = statistics.median(V[i - 50:i]) if i - 50 >= 0 else None
    if not vmed or vmed <= 0: return False, "vmed_none"
    if V[i] / vmed > F5_MAX: return False, "F5_vol_ratio>1.0"
    return True, "PASS"


def rsi_vs_ma(S, i):
    """rsi_vs_ma = RSI - RSI-based MA no bar de entrada i (divergência bearish no topo)."""
    rsi, rma = S.rsi_at.get(S.T[i], (None, None))
    return (rsi - rma) if (rsi is not None and rma is not None) else None


def nas_dist_shift1(S, i):
    """NAS_DISTANCE_FROM_EMA_ATR no bar i-1 (SHIFT1 causal; NAS top/bottom repinta)."""
    return S.nas_at.get(S.T[i - 1]) if i >= 1 else None


def refined_features(S, i):
    """Features at-entry causais (conhecidas no close do bar i) do refinamento aprovado."""
    C, H, L, EMA21, ATR14 = S.C, S.H, S.L, S.EMA21, S.ATR14
    atr = ATR14[i] or 0.0
    dz = demand_zone(S, i)
    zhi, zlo = (dz if dz else (EMA21[i - 1], EMA21[i - 1]))
    swing6_low = min(L[max(0, i - SWING_N + 1):i + 1])  # somente barras <= i
    f = {
        "ret5": (C[i] / C[i - 5] - 1) if i >= 5 else None,
        "ext_ema_atr": ((C[i] - EMA21[i]) / atr) if atr else None,
        "zone_w_atr": ((zhi - zlo) / atr) if (dz and atr) else 0.0,
        "dist_zone_atr": ((C[i] - zhi) / atr) if (dz and atr) else 0.0,
        "nas_dist_shift1": nas_dist_shift1(S, i),
        "swing6_low": round(swing6_low, 2),
        "zone_ob_low": round(zlo, 2) if dz else None,
        "atr": round(atr, 4),
    }
    return f, atr, (zlo if dz else None), swing6_low


def refined_filter(S, i):
    """(pass, trace) do stack v1 + NAS SHIFT1 — thresholds CONGELADOS (aprovados 2026-06-16)."""
    f, atr, zlo, sw6 = refined_features(S, i)
    nd = f["nas_dist_shift1"]
    gates = {
        "ret5<=1.42%": (f["ret5"] is not None and f["ret5"] <= RET5_MAX),
        "ext_ema<=2.95ATR": (f["ext_ema_atr"] is not None and f["ext_ema_atr"] <= EXT_EMA_ATR_MAX),
        "zone_w>=0.6ATR": (f["zone_w_atr"] >= ZONE_W_ATR_MIN),
        "dist_zone<=1.81ATR": (f["dist_zone_atr"] <= DIST_ZONE_ATR_MAX),
        "nas_dist_shift1>=1.31": (nd is not None and nd >= NAS_DIST_SHIFT1_MIN),
    }
    return all(gates.values()), {**f, "gates": gates}


def structural_sl(S, i):
    """SL estrutural OFICIAL V1 (canon Cris 2026-07-03) = zone_OB_low - 0.1*ATR.
    SUPERSEDED (revogada, NÃO usar): max(zone_OB_low, swing6_low) - 0.1*ATR.
    Reconciliação 2026-07-09: alinhado ao canon V1 (era max(zona,swing6), drift corrigido).
    Fallback swing6 só se não houver zona (a base-rule exige zona tocada → não ocorre em operacional)."""
    atr = S.ATR14[i] or 0.0
    dz = demand_zone(S, i)
    if dz is not None:
        base = dz[1]                                        # V1: zone_OB_low APENAS (não max com swing6)
    else:
        base = min(S.L[max(0, i - SWING_N + 1):i + 1])      # fallback defensivo (sem zona)
    return base - SL_ATR_BUFFER * atr


def evaluate(S, i):
    """Avalia o bar i. Gate: base-rule -> RSI exhaustion -> filtro refinado (stack v1 + NAS SHIFT1).
    Exit aprovado: SL estrutural V1 = zone_OB_low-0.1ATR + target +3R. Tudo causal (close do bar i)."""
    passed, reason = gate_trace(S, i)
    rvm = rsi_vs_ma(S, i)
    exhaustion_gate = (rvm is not None and round(rvm, 2) <= RSI_VS_MA_THR)
    ref_pass, ref_trace = refined_filter(S, i)
    operational = bool(passed and not exhaustion_gate and ref_pass)
    if operational:
        state = "operational_candidate"
    elif passed and exhaustion_gate:
        state = "blocked_exhaustion"
    elif passed and not ref_pass:
        state = "blocked_l1_refined_filter"
    else:
        state = "no_candidate"

    # exit aprovado (SL estrutural + 3R) — só faz sentido quando a base-rule passou
    entry = S.C[i]
    stop = structural_sl(S, i) if passed else None
    target = (entry + TARGET_R * (entry - stop)) if (stop is not None and entry - stop > 0) else None

    ts_iso = datetime.utcfromtimestamp(S.T[i]).isoformat()
    base_symbol = SYMBOL.split(":")[-1]
    _key = f"{ts_iso}|{base_symbol}|{TIMEFRAME}|L1_EMA21_CONTINUATION|continuation"
    signal_hash = hashlib.sha256(_key.encode("utf-8")).hexdigest()[:16]
    out = {
        "strategy": "L1 · EMA21 CONTINUATION",
        "suite": "XAU 4H LONG — CONTINUATION",
        "signal_hash": signal_hash,
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
        "timestamp": ts_iso,
        "candidate": bool(passed),
        "exhaustion_gate": exhaustion_gate,
        "refined_filter_pass": ref_pass,
        "operational": operational,
        "state": state,
        "rsi_vs_ma": round(rvm, 2) if rvm is not None else None,
        "entry_price": round(entry, 2),
        "stop_price": round(stop, 2) if stop is not None else None,
        "target_price": round(target, 2) if target is not None else None,
        "filter_trace": {**ref_trace, "regime_state": regime_d1(S, S.T[i]),
                          "rsi_vs_ma": round(rvm, 2) if rvm is not None else None},
        "review_required": True,
        "automation_level": "SCANNER_ONLY",
        "telegram_allowed": False,
    }
    if not passed:
        out["gate_reason"] = reason
    return out


def main():
    at = None
    if "--at" in sys.argv:
        try: at = int(sys.argv[sys.argv.index("--at") + 1])
        except Exception: pass

    S = build_series()
    if S.N == 0:
        print(json.dumps({"error": "no_bars_in_raw"})); return

    if at is not None:
        i = S.idx.get(at)
        if i is None:
            i = min(range(S.N), key=lambda k: abs(S.T[k] - at))  # nearest
    else:
        i = S.N - 1

    print(json.dumps(evaluate(S, i), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
