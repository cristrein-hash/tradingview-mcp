#!/usr/bin/env python3
"""Headless outcome tool — L1 · EMA21 CONTINUATION (Production v2, peça 6).

Lê um journal JSONL (--journal-path), e SÓ para linhas human_decision=KEEP e
outcome_status=PENDING, recomputa o resultado R post-hoc sobre o RAW canônico
(read-only). NÃO altera o journal. Default: imprime no stdout; só grava arquivo
separado se passar --outcome-path.

Exit policy = IDÊNTICA ao rebuild_v3 (stop estrutural largo, R_CEIL removido, V_stair,
target +20R, time_stop 60, slippage 0.1R). Read-only: nenhuma escrita em produção/logs.

NÃO faz: Telegram, envio, MCP/chart, daemon, alterar journal/scanner. Standalone.

Uso:
  python3 outcome.py --journal-path /path/journal.jsonl
  python3 outcome.py --journal-path /path/journal.jsonl --outcome-path /path/outcome.jsonl
"""
import gzip, json, sys, argparse, statistics
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

# exit policy (idêntica ao rebuild_v3)
R_FLOOR_ATR = 0.3
TARGET_R, TIME_STOP, SLIP = 20.0, 60, 0.1
STAIR = [(2.0, 0.0), (5.0, 1.0), (8.0, 3.0), (12.0, 6.0), (16.0, 10.0)]
OB_TOL, MA_TOL = 0.001, 0.002


def load_series():
    bars, zones_at = {}, {}
    with gzip.open(RAW, "rt") as f:
        for line in f:
            if '"replay_current_date"' not in line:
                continue
            r = json.loads(line); ov = r.get("ohlcv") or []
            if not ov:
                continue
            for b in ov:
                if b.get("time") is not None and b.get("close") is not None:
                    bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"],
                                       "c": b["close"], "v": b.get("volume") or 0}
            cur = max(b["time"] for b in ov); zs = []
            for s in (r.get("pine_boxes") or []):
                if "Custom OB" in s.get("name", ""):
                    for z in (s.get("zones") or []):
                        if z.get("high") is not None and z.get("low") is not None:
                            zs.append((z["high"], z["low"]))
            if zs:
                zones_at[cur] = zs
    return bars, zones_at


def ema(s, sp):
    k = 2 / (sp + 1); out = [None] * len(s); e = s[0]
    for i, x in enumerate(s):
        e = x if i == 0 else x * k + e * (1 - k); out[i] = e
    return out


def main():
    ap = argparse.ArgumentParser(description="Read-only outcome for L1 journal KEEP decisions.")
    ap.add_argument("--journal-path", required=True, help="JSONL do journal (read-only)")
    ap.add_argument("--outcome-path", default=None,
                    help="se ausente, imprime no stdout e NÃO grava arquivo")
    args = ap.parse_args()

    jp = Path(args.journal_path)
    if not jp.exists():
        print(f"error: journal not found: {jp}", file=sys.stderr); return 2
    rows = []
    for ln in jp.read_text().splitlines():
        ln = ln.strip()
        if ln:
            try: rows.append(json.loads(ln))
            except Exception: pass
    todo = [r for r in rows if r.get("human_decision") == "KEEP" and r.get("outcome_status") == "PENDING"]
    if not todo:
        print("[outcome] no KEEP+PENDING rows to measure", file=sys.stderr); return 0

    bars, zones_at = load_series()
    T = sorted(bars); idx = {t: i for i, t in enumerate(T)}; N = len(T)
    H = [bars[t]["h"] for t in T]; L = [bars[t]["l"] for t in T]; C = [bars[t]["c"] for t in T]
    EMA21 = ema(C, 21)
    TR = [H[0] - L[0]] + [max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])) for i in range(1, N)]
    ATR14 = [None] * N
    if N >= 14:
        a = sum(TR[:14]) / 14; ATR14[13] = a
        for i in range(14, N): a = (a * 13 + TR[i]) / 14; ATR14[i] = a

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

    def measure(i):
        if i < 60 or ATR14[i - 1] is None:
            return {"result_status": "INSUFFICIENT_HISTORY"}
        entry = C[i]
        dz = demand_zone(i)
        zlo = (dz[1] if dz else EMA21[i - 1])
        sl = min(L[i], min(L[max(0, i - 4):i + 1]), zlo) - 0.1 * ATR14[i - 1]
        Runit = entry - sl
        if Runit < R_FLOOR_ATR * ATR14[i - 1]:
            sl = entry - R_FLOOR_ATR * ATR14[i - 1]; Runit = entry - sl
        if Runit <= 0:
            return {"result_status": "INVALID_STOP"}
        if i + 1 >= N:
            return {"result_status": "INCOMPLETE_NO_FORWARD_BARS"}
        stop = sl; mfe = 0.0; mae = 0.0; locked = 0.0
        last = min(i + TIME_STOP, N - 1)
        exit_i, why = last, "time"
        for j in range(i + 1, last + 1):
            fav = (H[j] - entry) / Runit; adv = (L[j] - entry) / Runit
            if fav > mfe: mfe = fav
            if adv < mae: mae = adv
            for thr, lk in STAIR:
                if mfe >= thr and lk >= locked: locked = lk; stop = entry + locked * Runit
            if L[j] <= stop:
                exit_i, why = j, ("stop" if locked == 0 else "lock"); r = (stop - entry) / Runit - SLIP; break
            if H[j] >= entry + TARGET_R * Runit:
                exit_i, why = j, "target"; r = TARGET_R - SLIP; break
        else:
            r = (C[last] - entry) / Runit - SLIP
        incomplete = (why == "time" and last == N - 1 and (i + TIME_STOP) > N - 1)
        return {
            "result_status": ("INCOMPLETE_END_OF_DATA" if incomplete else ("WIN" if r > 0 else "LOSS")),
            "exit_reason": why,
            "r_result": round(r, 2),
            "mfe_r": round(mfe, 2),
            "mae_r": round(mae, 2),
            "bars_held": exit_i - i,
        }

    out_lines = []
    for r in todo:
        ts = r.get("candidate_timestamp")
        i = None
        if ts:
            try:
                et = int(datetime.fromisoformat(ts).replace(tzinfo=timezone.utc).timestamp())
                i = idx.get(et)
                if i is None and T:
                    i = min(range(N), key=lambda k: abs(T[k] - et))
            except Exception:
                i = None
        m = measure(i) if i is not None else {"result_status": "TIMESTAMP_NOT_FOUND"}
        line = {
            "event_type": "outcome_result",
            "strategy": r.get("strategy"),
            "suite": r.get("suite"),
            "symbol": r.get("symbol"),
            "timeframe": r.get("timeframe"),
            "candidate_timestamp": ts,
            "human_decision": r.get("human_decision"),
            "result_status": m.get("result_status"),
            "r_result": m.get("r_result"),
            "mfe_r": m.get("mfe_r"),
            "mae_r": m.get("mae_r"),
            "bars_held": m.get("bars_held"),
            "outcome_source": "RAW_READ_ONLY",
            "telegram_allowed": False,
        }
        if m.get("exit_reason"):
            line["exit_reason"] = m["exit_reason"]
        out_lines.append(line)

    rendered = "\n".join(json.dumps(x, ensure_ascii=False) for x in out_lines)
    if args.outcome_path:
        with open(args.outcome_path, "a") as f:
            f.write(rendered + "\n")
        print(f"[outcome] appended {len(out_lines)} line(s) -> {args.outcome_path}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
