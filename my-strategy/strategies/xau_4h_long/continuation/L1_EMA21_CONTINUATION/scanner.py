#!/usr/bin/env python3
"""Headless scanner — L1 · EMA21 CONTINUATION (suite XAU 4H LONG — CONTINUATION).

Production v2, peça 1 (Scanner). Transforma a regra-base APROVADA da L1 num scanner PURO:
gera candidato + flags BLOCK/REVIEW e imprime JSON no stdout. NADA além disso.

NÃO faz: Telegram, envio, MCP/chart, daemon, journal, outcome, backtest, escrita de arquivo.
Read-only sobre a fonte RAW/canonical já usada no rebuild_v3.

Regra-base = gate idêntico ao rebuild_v2/rebuild_l1_ema21_a_f5_v2.py (close-only-causal, SHIFT1).
Flags BLOCK/REVIEW = vol_entry_z>=1.993 OR rsi_vs_ma<=-9.35 (filtro aprovado, human-discretionary).

Uso:
  python3 scanner.py                 # avalia o ÚLTIMO bar do RAW canônico
  python3 scanner.py --at <unixts>   # avalia o bar daquele timestamp (dry-run/verificação)
"""
import gzip, json, bisect, statistics, sys
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
REGIME = REPO / "my-strategy/strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl"

SYMBOL, TIMEFRAME = "PEPPERSTONE:XAUUSD", "240"
# regra-base (idêntica ao rebuild_v2 — NÃO alterar sem re-aprovar)
ATR_MIN, ATR_MAX = 0.004, 0.030
BODY_MIN, F5_MAX, RET5_MIN = 0.35, 1.0, -0.04
OB_TOL, MA_TOL = 0.001, 0.002
# flags BLOCK/REVIEW aprovados (congelados)
VOL_Z_THR, RSI_VS_MA_THR = 1.993, -9.35


def _f(x):
    """Parse seguro de valor de study_value (trata sinal unicode/strings)."""
    if x is None:
        return None
    try:
        return float(str(x).replace(" ", "").replace(",", "").replace("−", "-"))
    except Exception:
        return None


def load_series():
    """Lê o RAW canônico (read-only): OHLCV + zones Custom OB + RSI/RSI-MA por bar."""
    bars, zones_at, rsi_at = {}, {}, {}
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
                if "Relative Strength Index" in s.get("name", ""):
                    vals = s.get("values") or {}
                    rsi_at[cur] = (_f(vals.get("RSI")), _f(vals.get("RSI-based MA")))
    return bars, zones_at, rsi_at


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


def main():
    at = None
    if "--at" in sys.argv:
        try: at = int(sys.argv[sys.argv.index("--at") + 1])
        except Exception: pass

    bars, zones_at, rsi_at = load_series()
    T = sorted(bars); idx = {t: i for i, t in enumerate(T)}; N = len(T)
    O = [bars[t]["o"] for t in T]; H = [bars[t]["h"] for t in T]
    L = [bars[t]["l"] for t in T]; C = [bars[t]["c"] for t in T]; V = [bars[t]["v"] for t in T]
    EMA21 = ema(C, 21); SMA50 = sma(C, 50)
    TR = [H[0] - L[0]] + [max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])) for i in range(1, N)]
    ATR14 = [None] * N
    if N >= 14:
        a = sum(TR[:14]) / 14; ATR14[13] = a
        for i in range(14, N): a = (a * 13 + TR[i]) / 14; ATR14[i] = a

    reg = []
    for l in open(REGIME):
        r = json.loads(l); ts = r.get("ts")
        try: t = int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
        except Exception: t = int(datetime.strptime(ts[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
        reg.append((t, r.get("v3_state")))
    reg.sort(); RT = [t for t, _ in reg]

    def regime_d1(et):
        i = bisect.bisect_left(RT, et) - 1
        while i > 0 and RT[i] >= et: i -= 1
        return reg[i][1] if i >= 0 else None

    def demand_zone(i):
        zs = zones_at.get(T[i - 1])
        if not zs:
            j = i - 1
            while j >= 0 and T[j] not in zones_at: j -= 1
            zs = zones_at.get(T[j]) if j >= 0 else None
        if not zs: return None
        cprev = C[i - 1]; below = [(hi, lo) for hi, lo in zs if hi < cprev]
        if not below: return None
        return max(below, key=lambda z: z[0])

    def gate_trace(i):
        """(passed, reason). Gate idêntico ao rebuild_v2 — close-only-causal."""
        if i < 60: return False, "history"
        if None in (EMA21[i - 1], SMA50[i - 1], ATR14[i - 1]) or i - 7 < 0 or SMA50[i - 7] is None:
            return False, "indicators_none"
        if regime_d1(T[i]) != "BULL": return False, "regime_d1_not_BULL"
        if not (C[i - 1] > EMA21[i - 1]): return False, "close_prev<=EMA21"
        if not (C[i - 1] > SMA50[i - 1]): return False, "close_prev<=SMA50"
        if not (EMA21[i - 1] > EMA21[i - 4]): return False, "ema21_slope3<=0"
        if not (SMA50[i - 1] > SMA50[i - 7]): return False, "sma50_slope6<=0"
        hh20 = max(H[max(0, i - 21):i - 1])
        if not (hh20 > max(C[max(0, i - 21):i - 1])): return False, "bos_fail"
        atrr = ATR14[i - 1] / C[i - 1]
        if not (ATR_MIN <= atrr <= ATR_MAX): return False, f"atr_ratio_oob({atrr:.4f})"
        dz = demand_zone(i)
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

    def flags(i):
        """Flags BLOCK/REVIEW (filtro aprovado). vol_entry_z + rsi_vs_ma no bar de entrada i."""
        vz = None
        if i - 50 >= 0:
            window = V[i - 50:i]
            mu = statistics.fmean(window); sd = statistics.pstdev(window)
            vz = (V[i] - mu) / sd if sd else 0.0
        rsi, rma = rsi_at.get(T[i], (None, None))
        rvm = (rsi - rma) if (rsi is not None and rma is not None) else None
        return vz, rvm

    # selecionar bar alvo: --at <unixts> ou o último bar do RAW
    if at is not None:
        i = idx.get(at)
        if i is None and T:
            i = min(range(N), key=lambda k: abs(T[k] - at))  # nearest
    else:
        i = N - 1

    if i is None or N == 0:
        print(json.dumps({"error": "no_bars_in_raw"})); return

    passed, reason = gate_trace(i)
    vz, rvm = flags(i)
    flag_vol = (vz is not None and vz >= VOL_Z_THR)
    flag_rsi = (rvm is not None and rvm <= RSI_VS_MA_THR)

    out = {
        "strategy": "L1 · EMA21 CONTINUATION",
        "suite": "XAU 4H LONG — CONTINUATION",
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
        "timestamp": datetime.utcfromtimestamp(T[i]).isoformat(),
        "candidate": bool(passed),
        "review_required": True,
        "block_or_review": {
            "vol_entry_z>=1.993": flag_vol,
            "rsi_vs_ma<=-9.35": flag_rsi,
            "any_flag": bool(flag_vol or flag_rsi),
            "values": {
                "vol_entry_z": round(vz, 3) if vz is not None else None,
                "rsi_vs_ma": round(rvm, 2) if rvm is not None else None,
            },
        },
        "automation_level": "SCANNER_ONLY",
        "telegram_allowed": False,
    }
    if not passed:
        out["gate_reason"] = reason
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
