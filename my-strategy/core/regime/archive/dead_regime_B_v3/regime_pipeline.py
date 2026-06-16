#!/usr/bin/env python3
"""Regime pipeline repo-local — port fiel de regime_classifier_B_v2.py + _v3.py.

Reproduz a cadeia canônica v2→v3 a partir de paths do REPO (não /tmp):
  entradas: v1 "B" classifications (ts, state, combined_score) + daily features (com high/atr_14)
  v2: STALL + SHARP_DROP + DIST_ALARM(none) + score modifier + histerese 2d -> v2_state_final
  v3: MACRO_BROKEN state machine + drawdown_pct_13w -> v3_state

⚠️ O classificador v1 "B" (cascade/stage/breaks que gera combined_score/state) está AUSENTE
do repo. Este pipeline SOURCEIA a saída do v1 B do registro canônico (offline, até 2026-05-25)
— NÃO reconstrói a lógica do v1 B. Estender p/ dias novos (live) exige o v1 B (BLOCO 2).

dist_alarm: eventos de distribuição ausentes; confirmado 100% False no canônico -> sem efeito.
Read-only, headless, sem MCP, sem rede, sem side effects no import.
"""
import json, sys, argparse


def _hysteresis(states, k=2):
    if not states:
        return []
    out = list(states); cur = out[0]; pending = None; pc = 0
    for i in range(1, len(out)):
        if out[i] == cur:
            pending = None; pc = 0
        else:
            if pending == out[i]:
                pc += 1
                if pc >= k:
                    cur = out[i]; pending = None; pc = 0
            else:
                pending = out[i]; pc = 1
            out[i] = cur
    return out


def run_v2(bars_b, daily):
    """Port fiel do regime_classifier_B_v2 (sem DIST_ALARM — eventos ausentes)."""
    ds = sorted(daily, key=lambda b: b["ts"]); N = len(ds)
    didx = {b["ts"]: i for i, b in enumerate(ds)}
    rh182 = [max(ds[j]["high"] for j in range(max(0, i - 181), i + 1)) for i in range(N)]
    # days since new 26w high
    dsnh = [None] * N; last = 0
    for i in range(N):
        if ds[i]["high"] >= rh182[i] - 0.001:
            last = i
        dsnh[i] = i - last
    stall_sig = [dsnh[i] >= 30 for i in range(N)]
    rh28 = [max(ds[j]["high"] for j in range(max(0, i - 27), i + 1)) for i in range(N)]
    sd_sig = [False] * N
    for i in range(N):
        if i < 10:
            continue
        atr = ds[i].get("atr_14")
        if not atr:
            continue
        dd = rh28[i] - ds[i]["close"]; days4 = 0
        for j in range(i, max(0, i - 28), -1):
            if ds[j]["high"] >= rh28[i] - 0.001:
                days4 = i - j; break
        if dd > 2.5 * atr and 0 < days4 <= 10:
            sd_sig[i] = True
    out = []
    for b in bars_b:
        ts = b["ts"]; i = didx.get(ts)
        if i is None:
            b = {**b, "v2_state": b.get("state"), "stall": False, "sharp_drop": False,
                 "dist_alarm": False, "v2_score_modifier": 0}
            out.append(b); continue
        stall = stall_sig[i]; sd = sd_sig[i]; da = False  # dist_alarm: eventos ausentes
        mod = (-1 if stall else 0) + (-2 if sd else 0) + (-1 if da else 0)
        ns = b.get("combined_score", 0) + mod
        v2 = "BULL" if ns >= 2 else "BEAR" if ns <= -2 else "TRANSITION"
        out.append({**b, "v2_state": v2, "stall": stall, "sharp_drop": sd,
                    "dist_alarm": da, "v2_score_modifier": mod})
    v2f = _hysteresis([b["v2_state"] for b in out], k=2)
    for b, s in zip(out, v2f):
        b["v2_state_final"] = s
    return out


def run_v3(bars_v2, daily):
    """Port fiel do regime_classifier_B_v3 (MACRO_BROKEN overlay)."""
    ds = sorted(daily, key=lambda b: b["ts"]); N = len(ds)
    didx = {b["ts"]: i for i, b in enumerate(ds)}
    rh91 = [max(ds[j]["high"] for j in range(max(0, i - 90), i + 1)) for i in range(N)]
    dd13 = [((rh91[i] - ds[i]["close"]) / rh91[i] * 100 if rh91[i] else 0) for i in range(N)]
    bars = sorted(bars_v2, key=lambda b: b["ts"])
    mb = False; cbear = 0; cbull = 0
    for b in bars:
        ts = b["ts"]; v2 = b.get("v2_state_final", b.get("state")); i = didx.get(ts)
        if i is None:
            b["v3_state"] = v2; b["macro_broken"] = mb; continue
        if v2 == "BEAR":
            cbear += 1; cbull = 0
        elif v2 == "BULL":
            cbull += 1; cbear = 0
        dd = dd13[i] or 0
        if not mb and (dd > 10.0 or cbear >= 3):
            mb = True
        if mb:
            c = ds[i]["close"]; h = rh91[i]
            if (h and c >= h * 0.97) or (h and c >= h - 0.001):
                mb = False
        b["v3_state"] = "TRANSITION" if (mb and v2 == "BULL") else v2
        b["macro_broken"] = mb; b["drawdown_pct_13w"] = dd
    return bars


def main():
    ap = argparse.ArgumentParser(description="Repo-local regime v2->v3 pipeline.")
    ap.add_argument("--v1b", required=True, help="jsonl v1 B (ts, state, combined_score)")
    ap.add_argument("--daily", required=True, help="jsonl daily features (ts, high, atr_14, close)")
    ap.add_argument("--out", default=None, help="escreve v3 classifications")
    ap.add_argument("--validate-against", default=None, help="canônico p/ validar v3_state por ts")
    args = ap.parse_args()
    v1b = [json.loads(l) for l in open(args.v1b) if l.strip()]
    daily = [json.loads(l) for l in open(args.daily) if l.strip()]
    v2 = run_v2(v1b, daily)
    v3 = run_v3(v2, daily)
    if args.validate_against:
        ref = {b["ts"]: b.get("v3_state") for b in (json.loads(l) for l in open(args.validate_against) if l.strip())}
        match = tot = 0; diffs = []
        for b in v3:
            if b["ts"] in ref:
                tot += 1
                if b["v3_state"] == ref[b["ts"]]:
                    match += 1
                else:
                    diffs.append((b["ts"], ref[b["ts"]], b["v3_state"]))
        print(f"  v3_state match: {match}/{tot}")
        if diffs:
            print(f"  divergências ({len(diffs)}), primeiras 8:", diffs[:8])
        ok = (match == tot and tot > 0)
        print("VALIDATE:", "PASS" if ok else "FAIL")
        if not ok:
            return 1
    if args.out:
        with open(args.out, "w") as f:
            for b in v3:
                f.write(json.dumps(b) + "\n")
        print(f"[pipeline] wrote {len(v3)} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
