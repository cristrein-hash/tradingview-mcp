#!/usr/bin/env python3
"""AUDITORIA DOS SINAIS REJEITADOS PELO READER/E2 — semana 24-28/08 (ordem Cris 28/08).
Fontes: e2_verdicts.jsonl (veredito+veto por candidato) × e1_candidates (entry/sl/target) × bars_15m
(resolução SL-first 3R, LONG e SHORT). Um a um: quando, regra, direção, veto/razão, surfaced?, e o que
teria dado. Também o funil 963→42 (por que a maioria nem chegou a veredito). Read-only. py3 stdlib."""
import json
import datetime as dt
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
LOGS = REPO / "alert-bridge/logs"
LX = dt.timezone(dt.timedelta(hours=1))
W0 = dt.datetime(2026, 8, 24, tzinfo=dt.timezone.utc).timestamp()


def jl(p):
    try:
        return [json.loads(l) for l in open(p).read().splitlines() if l.strip()]
    except Exception:
        return []


def ts_of(r):
    for k in ("ts", "cycle_ts", "bar_time"):
        v = r.get(k)
        if isinstance(v, (int, float)):
            return v
        if isinstance(v, str):
            try:
                return dt.datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp()
            except Exception:
                pass
    return 0


def hm(t):
    return dt.datetime.fromtimestamp(int(t), LX).strftime("%a %d/%m %H:%M")


bars = jl(REPO / "my-strategy/core/bar_store/store/bars_15m.jsonl")
T = [b["t"] for b in bars]; H = [b["h"] for b in bars]; L = [b["l"] for b in bars]


def resolve(t0, e, sl, is_long):
    if not (e and sl):
        return "SEM-NUM", None, None
    risk = (e - sl) if is_long else (sl - e)
    if risk <= 0:
        return "RISK<=0", None, None
    tgt = e + 3 * risk if is_long else e - 3 * risk
    i0 = next((i for i, t in enumerate(T) if t > t0), None)
    if i0 is None:
        return "SEM-BARRAS", None, None
    mfe = 0.0
    for i in range(i0, len(T)):
        fav = (H[i] - e) / risk if is_long else (e - L[i]) / risk
        mfe = max(mfe, fav)
        if is_long:
            if L[i] <= sl: return "LOSS", -1.0, round(mfe, 2)
            if H[i] >= tgt: return "WIN", 3.0, round(mfe, 2)
        else:
            if H[i] >= sl: return "LOSS", -1.0, round(mfe, 2)
            if L[i] <= tgt: return "WIN", 3.0, round(mfe, 2)
    return "OPEN", 0.0, round(mfe, 2)


verd = [r for r in jl(LOGS / "e2_verdicts.jsonl") if ts_of(r) >= W0]
cands = jl(LOGS / "e1_candidates.jsonl")

print(f"=== E2 VEREDITOS DA SEMANA: {len(verd)} ===")
print(f"{'quando':<17}{'dir':<6}{'regra':<18}{'grade':<7}{'surf':<6}{'veto/razão':<34}{'res':>6}{'R':>4}{'MFE':>6}")
tot = {"surf": [], "rej": []}
rows_out = []
for v in verd:
    t = v.get("bar_time") or ts_of(v)
    if isinstance(t, str):
        t = ts_of({"ts": t})
    cid = v.get("candidate_id") or ""
    # candidato E1 com números: match por proximidade temporal + regra + direção
    cc = [c for c in cands if c.get("rule") == v.get("rule") and c.get("direction") == v.get("direction")]
    best = None
    for c in cc:
        ct = c.get("t") or c.get("ts") or 0
        if isinstance(ct, str):
            ct = ts_of({"ts": ct})
        if best is None or abs(ct - t) < abs(best[0] - t):
            best = (ct, c)
    e = sl = None
    if best and abs(best[0] - t) <= 3600:
        e, sl = best[1].get("entry"), best[1].get("sl")
    is_long = (v.get("direction") or "").upper() == "LONG"
    o, R, mfe = resolve(t, e, sl, is_long)
    surf = bool(v.get("surfaced"))
    va = v.get("vetos_all") or []
    va = [x.get("veto") or x.get("name") or str(x) if isinstance(x, dict) else str(x) for x in va]
    veto = str(v.get("veto") or ",".join(va) or "-")
    (tot["surf"] if surf else tot["rej"]).append((o, R))
    rows_out.append(dict(t=t, dir=v.get("direction"), rule=v.get("rule"), grade=v.get("grade"),
                         surfaced=surf, veto=veto, res=o, R=R, mfe=mfe))
    print(f"{hm(t):<17}{(v.get('direction') or '?'):<6}{(v.get('rule') or '?')[:17]:<18}"
          f"{str(v.get('grade')):<7}{('SIM' if surf else 'NÃO'):<6}{veto[:33]:<34}{o:>6}"
          f"{(R if R is not None else 0):>4.0f}{(mfe if mfe is not None else 0):>6.2f}")

for k, lab in (("surf", "SURFACED"), ("rej", "REJEITADOS")):
    rs = [r for o, r in tot[k] if r is not None]
    w = sum(1 for o, _ in tot[k] if o == "WIN"); l = sum(1 for o, _ in tot[k] if o == "LOSS")
    print(f"\n{lab}: {len(tot[k])} · {w}W-{l}L · sumR {sum(rs):+.0f}")

# funil: por que 963 candidatos → 42 vereditos
wk_c = [c for c in cands if (lambda x: ts_of({"ts": x}) if isinstance(x, str) else (x or 0))(c.get("t") or c.get("ts")) >= W0]
from collections import Counter
print(f"\n=== FUNIL: {len(wk_c)} candidatos E1 na semana → {len(verd)} vereditos E2 ===")
print("candidatos por regra:", dict(Counter(c.get("rule") for c in wk_c).most_common(8)))
print("por materialidade:", dict(Counter(str(c.get("materiality")) for c in wk_c).most_common(6)))
print("vereditos por regra:", dict(Counter(v.get("rule") for v in verd).most_common(8)))

Path(REPO / "my-strategy/research/revalidation/reader_rejections_audit_20260828.json").write_text(
    json.dumps(rows_out, indent=1, default=str))
print("\ngravado reader_rejections_audit_20260828.json")
