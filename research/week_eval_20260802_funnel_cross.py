#!/usr/bin/env python3
"""AVALIAÇÃO DA SEMANA 27-31/07 — PARTE 2: funil do sistema vs os 6 trades ideais do Cris.
Para cada janela ideal (script parte 1): o E1 GEROU candidato compatível (direção igual, entry ±8 pts,
timestamp entre janela_início−2h e +3h)? O E2 LEU (verdict)? surfaced ou recusado (convicção/tese)?
Classifica cada trade ideal: SINALIZADO / GERADO-MAS-RECUSADO / NÃO-GERADO. Reprodutível."""
import json, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

LX = ZoneInfo("Europe/Lisbon")
R = Path("/Users/cristrein/tradingview-mcp")
E1F = R / "alert-bridge/logs/e1_candidates.jsonl"
E2F = R / "alert-bridge/logs/e2_verdicts.jsonl"

# (dir, entry, rr, janela_início, janela_tp) — datas Lisboa, da parte 1
W = [
    ("SHORT", 4106.06, 6.3, "2026-07-27 01:00", "2026-07-28 10:45"),
    ("SHORT", 4089.57, 4.1, "2026-07-27 13:00", "2026-07-28 06:30"),
    ("SHORT", 4088.35, 4.3, "2026-07-27 09:00", "2026-07-28 11:15"),
    ("SHORT", 4068.68, 2.5, "2026-07-28 01:00", "2026-07-28 02:30"),
    ("LONG",  4011.48, 5.8, "2026-07-28 15:15", "2026-07-29 20:00"),
    ("LONG",  4067.76, 4.0, "2026-07-29 19:30", "2026-07-29 19:45"),
]
TOL_PX = 8.0
PRE_H, POS_H = 2, 3


def ts_of(s):
    return dt.datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=LX).timestamp()


def parse_iso(x):
    try:
        return dt.datetime.fromisoformat(str(x).replace("Z", "+00:00")).timestamp()
    except Exception:
        try:
            return float(x)
        except Exception:
            return None


def load(f):
    return [json.loads(l) for l in open(f) if l.strip()]


def hm(t):
    return dt.datetime.fromtimestamp(t, LX).strftime("%d %H:%M")


def main():
    e1 = load(E1F); e2 = load(E2F)
    # cobertura dos logs
    e1ts = [parse_iso(r.get("ts")) for r in e1]; e1ts = [t for t in e1ts if t]
    e2ts = [parse_iso(r.get("ts")) for r in e2]; e2ts = [t for t in e2ts if t]
    print(f"cobertura E1: {hm(min(e1ts))} -> {hm(max(e1ts))} ({len(e1)} regs)")
    print(f"cobertura E2: {hm(min(e2ts))} -> {hm(max(e2ts))} ({len(e2)} regs)\n")

    for d, e, rr, w0s, w1s in W:
        w0, w1 = ts_of(w0s), ts_of(w1s)
        lo, hi = w0 - PRE_H * 3600, w0 + POS_H * 3600
        # E1: candidatos compatíveis na janela de entrada
        cands = []
        for r in e1:
            t = parse_iso(r.get("ts"))
            if t is None or not (lo <= t <= hi):
                continue
            c = r if "direction" in r else (r.get("cand") or {})
            if c.get("direction") != d:
                continue
            en = c.get("entry")
            if en is None or abs(float(en) - e) > TOL_PX:
                continue
            cands.append((t, c))
        # E2: verdicts compatíveis na mesma janela
        verds = []
        for r in e2:
            t = parse_iso(r.get("ts"))
            if t is None or not (lo <= t <= hi):
                continue
            if r.get("direction") != d and (r.get("cand") or {}).get("direction") != d:
                continue
            verds.append((t, r))
        surf = [v for _, v in verds if v.get("surfaced") or (v.get("read") or {}).get("surfaced")]
        if surf:
            cls = "SINALIZADO ✅"
        elif verds:
            cls = "GERADO-MAS-RECUSADO ⚠️"
        elif cands:
            cls = "GERADO (sem read na janela) ⚠️"
        else:
            # cobertura? se a janela é anterior ao início do log, marca sem-cobertura
            cls = "NÃO-GERADO ❌" if min(e1ts) <= w0 else "SEM-COBERTURA-LOG ∅"
        print(f"{d} {e} (+{rr}R) janela {w0s} -> {w1s}")
        print(f"   E1 candidatos compatíveis: {len(cands)} | E2 verdicts na janela: {len(verds)} | surfaced: {len(surf)}")
        for t, v in verds[:3]:
            rd = v.get("read") or {}
            conv = rd.get("conviction") or v.get("conviction")
            th = (rd.get("reasoning") or v.get("thesis") or "")[:110]
            sf = v.get("surfaced") or rd.get("surfaced")
            print(f"     · {hm(t)} surfaced={sf} conv={conv} {th}")
        print(f"   => {cls}\n")


if __name__ == "__main__":
    main()
