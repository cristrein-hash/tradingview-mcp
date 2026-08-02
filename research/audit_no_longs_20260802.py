#!/usr/bin/env python3
"""AUDITORIA (Cris 2026-08-02): porque o live não emitiu NENHUM LONG numa semana com 2 longs fortes claros?
Matriz de confusão das recusas de LONG do reader: resolve cada LONG lido-e-recusado SL-first contra o preço
(WIN=recusa ERRADA/custo, LOSS=recusa CERTA/proteção) + tese de cada recusa-de-vencedor (o padrão do 'não').
Fontes: e2_verdicts.jsonl (levels+read) + bar-store 15M. Reprodutível."""
import json, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

LX = ZoneInfo("Europe/Lisbon")
R = Path("/Users/cristrein/tradingview-mcp")
E2F = R / "alert-bridge/logs/e2_verdicts.jsonl"
STORE = R / "my-strategy/core/bar_store/store/bars_15m.jsonl"
W0, W1 = "2026-07-26", "2026-07-31"


def parse_iso(x):
    try: return dt.datetime.fromisoformat(str(x).replace("Z", "+00:00")).timestamp()
    except Exception: return None


def hm(t): return dt.datetime.fromtimestamp(t, LX).strftime("%a %d %H:%M")


def main():
    e2 = [json.loads(l) for l in open(E2F) if l.strip()]
    wk = [r for r in e2 if W0 <= str(r.get("ts", ""))[:10] <= W1]
    longs = [r for r in wk if r.get("direction") == "LONG" and not r.get("surfaced")]
    bars = [json.loads(l) for l in open(STORE) if l.strip() and l[0] == "{"]
    t0 = dt.datetime(2026, 7, 26, tzinfo=LX).timestamp()
    bars = [b for b in bars if b["t"] >= t0]
    T = [b["t"] for b in bars]

    def resolve(ets, entry, sl, tgt):
        i0 = next((i for i, t in enumerate(T) if t > ets), None)
        if i0 is None or sl is None or tgt is None: return "SEM_NIVEIS", None
        for i in range(i0, len(T)):
            b = bars[i]
            if b["l"] <= sl: return "LOSS", b["t"]
            if b["h"] >= tgt: return "WIN", b["t"]
        return "OPEN", None

    rows = []
    for r in longs:
        lv = r.get("levels") or {}
        ts = parse_iso(r.get("ts"))
        out, rt = resolve(ts or 0, lv.get("entry"), lv.get("sl"), lv.get("target"))
        veto = [v["name"] for v in (r.get("vetos_all") or []) if v.get("fired")]
        rd = r.get("read") or {}
        rows.append({"ts": ts, "rule": r.get("rule"), "tf": r.get("tf"), "entry": lv.get("entry"),
                     "sl": lv.get("sl"), "tgt": lv.get("target"), "rr": lv.get("rr"), "out": out,
                     "conv": rd.get("conviction"), "veto": veto,
                     "reasoning": str(rd.get("reasoning") or "")})
    res = [x for x in rows if x["out"] in ("WIN", "LOSS")]
    wins = [x for x in res if x["out"] == "WIN"]
    losses = [x for x in res if x["out"] == "LOSS"]
    print(f"=== MATRIZ DE CONFUSÃO — LONGs lidos e RECUSADOS na semana ===")
    print(f"total recusados: {len(longs)} | com níveis resolvíveis: {len(res)} | sem níveis: {len(rows)-len(res)-len([x for x in rows if x['out']=='OPEN'])} | OPEN: {len([x for x in rows if x['out']=='OPEN'])}")
    cost = sum(float(x["rr"] or 3.0) for x in wins)
    saved = float(len(losses))
    print(f"RECUSAS ERRADAS (teriam ganho): {len(wins)}  -> custo de oportunidade −{cost:.1f}R")
    print(f"RECUSAS CERTAS (teriam perdido): {len(losses)} -> proteção +{saved:.1f}R evitados")
    print(f"SALDO da conservadoria em longs: {saved - cost:+.1f}R")
    print("\n=== OS VENCEDORES RECUSADOS (recusa errada) — quando, o quê, e o PORQUÊ do não ===")
    for x in sorted(wins, key=lambda z: z["ts"] or 0):
        vt = f" [VETO {','.join(x['veto'])}]" if x["veto"] else ""
        print(f"\n· {hm(x['ts'])} LONG {x['rule']}@{x['tf']} entry {x['entry']} SL {x['sl']} tgt {x['tgt']} (RR {x['rr']}) conv {x['conv']}{vt}")
        print(f"  tese do NÃO: {x['reasoning'][:340]}")
    print("\n=== padrões nos NÃO-aos-vencedores (contagem por keyword) ===")
    from collections import Counter
    kw = Counter()
    for x in wins:
        th = x["reasoning"].lower()
        for k, lab in (("contra a perna", "contra-a-perna/frame BEAR"), ("faca", "contra-a-perna/frame BEAR"),
                       ("sem exaust", "sem exaustão HTF"), ("auction", "auction vendedor/vazio"),
                       ("fomc", "evento iminente"), ("pullback", "1º-pullback de perna fresca"),
                       ("vácuo", "auction vendedor/vazio"), ("vacuo", "auction vendedor/vazio")):
            if k in th: kw[lab] += 1
    print(dict(kw.most_common()))


if __name__ == "__main__":
    main()
