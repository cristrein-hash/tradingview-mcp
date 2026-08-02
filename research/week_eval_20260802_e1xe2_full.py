#!/usr/bin/env python3
"""AVALIAÇÃO DA SEMANA 27-31/07 — funil autónomo E1×E2 COMPLETO (o que o live leu SOZINHO).
(1) E1: candidatos únicos gerados (dedup por rule/tf/dir/entry-bucket) por regra/direção/dia.
(2) E2: todos os verdicts (lidos) + os SURFACED com detalhe (ts, rule, entry/sl/target, convicção).
(3) OUTCOME dos surfaced: resolução SL-first contra as barras 15M da semana (WIN=target, LOSS=SL, OPEN).
Painel completo: N · WR · somaR · avgR · streak. Reprodutível."""
import json, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
from collections import Counter, defaultdict

LX = ZoneInfo("Europe/Lisbon")
R = Path("/Users/cristrein/tradingview-mcp")
E1F = R / "alert-bridge/logs/e1_candidates.jsonl"
E2F = R / "alert-bridge/logs/e2_verdicts.jsonl"
STORE = R / "my-strategy/core/bar_store/store/bars_15m.jsonl"
W0, W1 = "2026-07-26", "2026-07-31"


def parse_iso(x):
    try:
        return dt.datetime.fromisoformat(str(x).replace("Z", "+00:00")).timestamp()
    except Exception:
        try: return float(x)
        except Exception: return None


def hm(t):
    return dt.datetime.fromtimestamp(t, LX).strftime("%a %d %H:%M")


def main():
    # ---------- E1: candidatos únicos ----------
    e1 = [json.loads(l) for l in open(E1F) if l.strip()]
    wk1 = [r for r in e1 if W0 <= str(r.get("ts", ""))[:10] <= W1]
    uniq = {}
    for r in wk1:
        c = r if "direction" in r else (r.get("cand") or {})
        en = c.get("entry")
        if en is None: continue
        k = (c.get("rule"), c.get("tf"), c.get("direction"), round(float(en) / 5) * 5, str(r.get("ts", ""))[:13])
        uniq.setdefault(k, (r, c))
    by_rule = Counter(k[0] for k in uniq)
    by_dir = Counter(k[2] for k in uniq)
    by_day = Counter()
    for (rule, tf, dirn, eb, hh), _ in uniq.items():
        by_day[hh[:10]] += 1
    print("=== E1 — GERAÇÃO (candidatos únicos na semana; dedup rule/tf/dir/entry~5pts/hora) ===")
    print(f"registos crus: {len(wk1)} | únicos: {len(uniq)}")
    print(f"por regra: {dict(by_rule.most_common())}")
    print(f"por direção: {dict(by_dir)}")
    print(f"por dia: {dict(sorted(by_day.items()))}")

    # ---------- E2: verdicts ----------
    e2 = [json.loads(l) for l in open(E2F) if l.strip()]
    wk2 = [r for r in e2 if W0 <= str(r.get("ts", ""))[:10] <= W1]
    surf, refused, vetoed = [], [], []
    for r in wk2:
        rd = r.get("read") or {}
        is_surf = bool(r.get("surfaced") or rd.get("surfaced"))
        veto_fired = [v["name"] for v in (r.get("vetos_all") or []) if v.get("fired")]
        if is_surf: surf.append(r)
        elif veto_fired: vetoed.append((r, veto_fired))
        else: refused.append(r)
    print("\n=== E2 — LEITURA (verdicts na semana) ===")
    print(f"total lidos: {len(wk2)} | SURFACED: {len(surf)} | recusados pelo read: {len(refused)} | mortos por veto higiene: {len(vetoed)}")
    d2 = Counter((r.get("direction") or (r.get("cand") or {}).get("direction")) for r in wk2)
    print(f"por direção lida: {dict(d2)}")

    # ---------- surfaced: detalhe + outcome ----------
    bars = [json.loads(l) for l in open(STORE) if l.strip() and l[0] == "{"]
    t0 = dt.datetime(2026, 7, 26, tzinfo=LX).timestamp()
    bars = [b for b in bars if b["t"] >= t0]
    T = [b["t"] for b in bars]

    def resolve(dirn, ets, entry, sl, tgt):
        i0 = next((i for i, t in enumerate(T) if t > ets), None)
        if i0 is None or sl is None or tgt is None: return "OPEN", None
        for i in range(i0, len(T)):
            b = bars[i]
            if dirn == "SHORT":
                if b["h"] >= sl: return "LOSS", b["t"]
                if b["l"] <= tgt: return "WIN", b["t"]
            else:
                if b["l"] <= sl: return "LOSS", b["t"]
                if b["h"] >= tgt: return "WIN", b["t"]
        return "OPEN", None

    print("\n=== SINAIS EMITIDOS (surfaced) — detalhe + outcome SL-first ===")
    tot = 0.0; seq = []; res_rows = []
    for r in surf:
        c = r.get("candidate") or r.get("cand") or {}
        lv = r.get("levels") or {}
        rd = r.get("read") or {}
        ts = parse_iso(r.get("ts"))
        dirn = c.get("direction") or r.get("direction")
        c = {"rule": c.get("rule") or r.get("rule"), "tf": c.get("tf") or r.get("tf"), "direction": dirn}
        entry = lv.get("entry"); sl = lv.get("sl"); tgt = lv.get("target"); rr = lv.get("rr")
        conv = rd.get("conviction") or r.get("conviction")
        out, rt = resolve(dirn, ts or 0, entry, sl, tgt)
        gain = None
        if out == "WIN": gain = float(rr or 3.0)
        elif out == "LOSS": gain = -1.0
        if gain is not None:
            tot += gain; seq.append("W" if gain > 0 else "L")
        res_rows.append((ts, dirn, c.get("rule"), c.get("tf"), entry, sl, tgt, rr, conv, out, gain))
        print(f"  {hm(ts)} {dirn:5} {str(c.get('rule')):14}@{str(c.get('tf')):3} entry {entry} SL {sl} tgt {tgt} "
              f"RR {rr} conv {conv} -> {out}" + (f" {gain:+.1f}R" if gain is not None else ""))
    n_res = len([x for x in res_rows if x[10] is not None])
    w = seq.count("W")
    if n_res:
        worst = cur = 0
        for s in seq:
            cur = cur + 1 if s == "L" else 0
            worst = max(worst, cur)
        print(f"\nPAINEL surfaced: N={len(surf)} (resolvidos {n_res}) | WR {100*w/n_res:.0f}% ({w}W/{n_res-w}L) "
              f"| somaR {tot:+.1f}R | avgR {tot/n_res:+.2f}R | pior streak L {worst}")

    # ---------- recusas: razões dominantes ----------
    print("\n=== RECUSAS DO READER — amostra de teses (porquê disse não) ===")
    reasons = Counter()
    for r in refused:
        th = str((r.get("read") or {}).get("reasoning") or r.get("thesis") or "").lower()
        for kw, lab in (("faca", "apanhar faca / contra a perna"), ("contra a perna", "apanhar faca / contra a perna"),
                        ("sem reclaim", "sem reclaim/confirmação"), ("auction", "auction contra/vazio"),
                        ("fomc", "evento iminente"), ("vácuo", "auction contra/vazio"), ("vacuo", "auction contra/vazio"),
                        ("exaust", "sem exaustão HTF")):
            if kw in th:
                reasons[lab] += 1
                break
    print(f"razões dominantes (heurística por keywords): {dict(reasons.most_common())}")


if __name__ == "__main__":
    main()
