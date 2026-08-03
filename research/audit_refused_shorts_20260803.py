#!/usr/bin/env python3
"""AUDITORIA (Cris 2026-08-03): matriz de confusão dos SHORTs LIDOS-e-RECUSADOS pelo reader (semana 27/07 +
hoje 03/08). Resolve cada um SL-first contra o preço (WIN=recusa ERRADA/perda, LOSS=recusa CERTA/proteção,
OPEN c/ MFE>=1R = provável recusa errada). Para os erros: MFE/MAE + a razão do 'não' (padrão da recusa).
Objetivo: quantificar se a conservadoria do reader nos SHORTs custa mais do que protege. Reprodutível."""
import json, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
from collections import Counter

LX = ZoneInfo("Europe/Lisbon")
R = Path("/Users/cristrein/tradingview-mcp")
E2F = R / "alert-bridge/logs/e2_verdicts.jsonl"
STORE = R / "my-strategy/core/bar_store/store/bars_15m.jsonl"
W0, W1 = "2026-07-26", "2026-08-03"


def parse_iso(x):
    try: return dt.datetime.fromisoformat(str(x).replace("Z", "+00:00")).timestamp()
    except Exception: return None


def hm(t): return dt.datetime.fromtimestamp(t, LX).strftime("%a %d %H:%M")


def main():
    e2 = [json.loads(l) for l in open(E2F) if l.strip()]
    wk = [r for r in e2 if W0 <= str(r.get("ts", ""))[:10] <= W1]
    shorts = [r for r in wk if r.get("direction") == "SHORT" and not r.get("surfaced")
              and not (r.get("read") or {}).get("surfaced")]
    bars = [json.loads(l) for l in open(STORE) if l.strip() and l[0] == "{"]
    t0 = dt.datetime(2026, 7, 26, tzinfo=LX).timestamp()
    bars = [b for b in bars if b["t"] >= t0]
    T = [b["t"] for b in bars]

    def resolve(ets, entry, sl, tgt):
        i0 = next((i for i, t in enumerate(T) if t > ets), None)
        if i0 is None or sl is None or tgt is None or entry is None:
            return "SEM_NIVEIS", None, 0.0, 0.0
        r = abs(entry - sl)
        mfe = mae = 0.0
        for i in range(i0, len(T)):
            b = bars[i]
            mfe = max(mfe, entry - b["l"])   # a favor do SHORT
            mae = max(mae, b["h"] - entry)   # contra
            if b["h"] >= sl: return "LOSS", b["t"], mfe / r if r else 0, mae / r if r else 0
            if b["l"] <= tgt: return "WIN", b["t"], mfe / r if r else 0, mae / r if r else 0
        return "OPEN", None, mfe / r if r else 0, mae / r if r else 0

    rows = []
    for r in shorts:
        lv = r.get("levels") or {}
        ts = parse_iso(r.get("ts"))
        out, rt, mfe_r, mae_r = resolve(ts or 0, lv.get("entry"), lv.get("sl"), lv.get("target"))
        rd = r.get("read") or {}
        rows.append({"ts": ts, "rule": r.get("rule"), "tf": r.get("tf"), "entry": lv.get("entry"),
                     "sl": lv.get("sl"), "tgt": lv.get("target"), "rr": lv.get("rr"), "out": out,
                     "mfe_r": round(mfe_r, 2), "mae_r": round(mae_r, 2), "conv": rd.get("conviction"),
                     "reasoning": str(rd.get("reasoning") or "")})
    res = [x for x in rows if x["out"] in ("WIN", "LOSS")]
    wins = [x for x in res if x["out"] == "WIN"]
    losses = [x for x in res if x["out"] == "LOSS"]
    # OPEN que já correram >=1.5R a favor sem tocar stop = "provável vencedor perdido"
    open_favor = [x for x in rows if x["out"] == "OPEN" and x["mfe_r"] >= 1.5 and x["mae_r"] < 1.0]

    print("=== MATRIZ DE CONFUSÃO — SHORTs lidos e RECUSADOS (semana + hoje) ===")
    print(f"total recusados: {len(shorts)} | resolvidos: {len(res)} | OPEN: {len([x for x in rows if x['out']=='OPEN'])}")
    cost = sum(float(x["rr"] or 3.0) for x in wins)
    print(f"RECUSAS ERRADAS resolvidas (teriam TP): {len(wins)} -> custo -{cost:.1f}R")
    print(f"RECUSAS CERTAS (teriam SL): {len(losses)} -> proteção +{len(losses):.1f}R")
    print(f"OPEN c/ MFE>=1.5R sem risco (provável winner perdido): {len(open_favor)}")
    net = len(losses) - cost - sum(min(x['mfe_r'], float(x['rr'] or 3.0)) for x in open_favor)
    print(f"SALDO estimado (proteção - erros resolvidos - MFE dos OPEN-a-favor): {net:+.1f}R")

    print("\n=== RECUSAS ERRADAS + OPEN-a-favor (as perdas) — detalhe + razão do NÃO ===")
    for x in sorted(wins + open_favor, key=lambda z: z["ts"] or 0):
        print(f"\n· {hm(x['ts'])} SHORT {x['rule']}@{x['tf']} entry {x['entry']} SL {x['sl']} tgt {x['tgt']} "
              f"conv {x['conv']} -> {x['out']} | MFE {x['mfe_r']}R MAE {x['mae_r']}R")
        print(f"  razão do NÃO: {x['reasoning'][:300]}")

    print("\n=== padrões nas RECUSAS ERRADAS (keyword) ===")
    kw = Counter()
    for x in wins + open_favor:
        th = x["reasoning"].lower()
        for k, lab in (("adx", "ADX morto/CHOP"), ("chop", "ADX morto/CHOP"),
                       ("sem agress", "auction sem agressão"), ("absor", "auction sem agressão"),
                       ("compress", "entrada em compressão/EMAs"), ("vácuo", "vácuo pré-evento"),
                       ("vacuo", "vácuo pré-evento"), ("dead", "vácuo pré-evento"),
                       ("pullback #3", "pullback maduro"), ("brent", "Brent→ouro bullish")):
            if k in th: kw[lab] += 1
    print(dict(kw.most_common()))


if __name__ == "__main__":
    main()
