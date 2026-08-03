#!/usr/bin/env python3
"""CHECK ANTI-REABERTURA (Cris 2026-08-03: "antes de implementar verificar se a afinação não abre muitos
losers evitados"). Classifica as 13 recusas-CERTAS de SHORT (teriam SL) contra as condições dos blocos
propostos A (fade-em-supply-com-sequência + tensão-de-rótulo) e B (continuação-em-compressão): se a tese
guardada da recusa CASA com as condições, a afinação poderia tê-la reaberto (= risco). PASS: <=2/13 casam
(e revistas 1-a-1). FAIL >=3: NÃO implementar. Determinístico, sem LLM, pré-edit."""
import json, re, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

R = Path("/Users/cristrein/tradingview-mcp")
E2F = R / "alert-bridge/logs/e2_verdicts.jsonl"
LX = ZoneInfo("Europe/Lisbon")
W0, W1 = "2026-07-26", "2026-08-03"


def parse_iso(x):
    try: return dt.datetime.fromisoformat(str(x).replace("Z", "+00:00")).timestamp()
    except Exception: return None


def hm(t): return dt.datetime.fromtimestamp(t, LX).strftime("%a %d %H:%M")


def resolve_correct_losers():
    """Recusas de SHORT lidas (read presente) na janela, dedup por (rule,tf,entry), cujo outcome = LOSS
    (calculado como na auditoria). Para simplicidade e reprodutibilidade, re-resolve aqui."""
    e2 = [json.loads(l) for l in open(E2F) if l.strip()]
    wk = [r for r in e2 if W0 <= str(r.get("ts", ""))[:10] <= W1
          and r.get("direction") == "SHORT" and not r.get("surfaced")
          and (r.get("read") or {}).get("reasoning")]
    bars = [json.loads(l) for l in open(R / "my-strategy/core/bar_store/store/bars_15m.jsonl")
            if l.strip() and l[0] == "{"]
    t0 = dt.datetime(2026, 7, 26, tzinfo=LX).timestamp()
    bars = [b for b in bars if b["t"] >= t0]
    T = [b["t"] for b in bars]
    out, seen = [], set()
    for r in wk:
        lv = r.get("levels") or {}
        k = (r.get("rule"), r.get("tf"), lv.get("entry"))
        if k in seen: continue
        seen.add(k)
        ts = parse_iso(r.get("ts"))
        i0 = next((i for i, t in enumerate(T) if t > (ts or 0)), None)
        res = "OPEN"
        if i0 is not None and lv.get("sl") and lv.get("target"):
            for i in range(i0, len(T)):
                b = bars[i]
                if b["h"] >= lv["sl"]: res = "LOSS"; break
                if b["l"] <= lv["target"]: res = "WIN"; break
        r["_res"] = res; r["_ts"] = ts
        out.append(r)
    return [r for r in out if r["_res"] == "LOSS"]


A_TENSION = re.compile(r"r[óo]tulo.*(tens[ãa]o|desacordo|vs\s*(fita|dados))|declara BULL.*(DOWN|down)|cabe[çc]alho.*BULL.*(DOWN|down)", re.I | re.S)
A_REJECTS = re.compile(r"rejei[çc][õo]es?\s+confirmad|sweep d[oa]\s*(topo|m[áa]xima)", re.I)
A_NEG = re.compile(r"sem rejei[çc][ãa]o confirmada|sem sweep", re.I)
B_ABSENT = re.compile(r"sem agress[ãa]o vendedora|ADX\s*[\d.]*\s*(morto|baixo)|CHOP|sem absor[çc][ãa]o|baixa energia|sem combust[íi]vel", re.I)
B_CONTRARY = re.compile(r"janela.*buy|iniciativa.*(BUY|compradora)|comprador(a)?\s*(viva|vivo|ativo|forte)|buy\s*[2-9]/[2-9]|\+DI\s*\d+.*(>|maior)|buy_dens\s*0\.[3-9]|buy-?bubbles", re.I)
B_EVENT = re.compile(r"FOMC|high[- _]impact|evento (iminente|HIGH)|ISM HIGH", re.I)


def main():
    losers = resolve_correct_losers()
    print(f"recusas-CERTAS (LOSS evitado) lidas, dedup: {len(losers)}")
    a_m = b_m = 0
    for r in sorted(losers, key=lambda z: z["_ts"] or 0):
        rd = r.get("read") or {}
        txt = " ".join([str(rd.get("reasoning") or ""), str(rd.get("thesis") or ""),
                        " ".join(rd.get("conflicting_readings") or [])])
        fit = rd.get("candidate_fit"); ctx = rd.get("context_direction")
        A = bool(A_TENSION.search(txt)) and bool(A_REJECTS.search(txt)) and not A_NEG.search(txt)
        B = (fit == "aligned" and ctx == "SHORT" and bool(B_ABSENT.search(txt))
             and not B_CONTRARY.search(txt) and not B_EVENT.search(txt))
        flag = ("A" if A else "") + ("B" if B else "")
        a_m += A; b_m += B
        lv = r.get("levels") or {}
        print(f"  {hm(r['_ts'])} {r.get('rule')}@{r.get('tf')} entry {lv.get('entry')} fit={fit} ctx={ctx} "
              f"-> match={flag or '-'}")
        if flag:
            print(f"     EVIDÊNCIA (rever 1-a-1): {txt[:220]}")
    tot = a_m + b_m
    print(f"\nA-matches: {a_m} | B-matches: {b_m} | TOTAL em risco de reabertura: {tot}/13")
    print("VEREDITO:", "PASS (<=2 — prosseguir com revisão individual)" if tot <= 2 else "FAIL (>=3 — NÃO implementar)")


if __name__ == "__main__":
    main()
