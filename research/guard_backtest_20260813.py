#!/usr/bin/env python3
"""TESTE do guard direccional CONTRA os trades de hoje (13/08) — ANTES de implementar (Cris 14/08).
NÃO inventa nada: reusa a função CHoCH/trend do próprio E0 `context_structure.structure()` (causal,
close-only, sem repintar) e corre-a sobre as barras RAW nativas, cortadas ANTES de cada momento.
Depois sobrepõe os LONGs que dispararam (reader + validador) e mede: quantos o guard teria bloqueado.
Read-only. Só imprime. py3."""
import json, sys, datetime
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import context_structure as CS          # a função do próprio E0
import store_reader as SR               # RAW nativo (60/240) + 15m

DAY0 = 1786579200   # 2026-08-13 00:00 UTC
DAY1 = 1786665600   # 2026-08-14 00:00 UTC


def struct_at(bars, t):
    """E0 structure() causal: usa só barras com tempo <= t (sem lookahead). None se poucas."""
    sub = [b for b in bars if b["t"] <= t]
    if len(sub) < 20:
        return None
    H = [b["h"] for b in sub]; L = [b["l"] for b in sub]; C = [b["c"] for b in sub]
    return CS.structure(H, L, C)         # i=default=última (=<=t)


def load_bars(tf):
    try:
        return SR.bars(tf, 4000) or []
    except Exception:
        return []


def gather_longs():
    """LONGs induzidos hoje: reader (candle_reads) + estratégias (e1_candidates: R9/R10/zone_reject/etc).
    (t, fonte, entry)."""
    out = []
    try:
        for l in open("/Users/cristrein/tradingview-mcp/alert-bridge/logs/candle_reads.jsonl"):
            l = l.strip()
            if not l: continue
            d = json.loads(l); ts = d.get("ts", "")
            if not ts.startswith("2026-08-13"): continue
            rd = d.get("read")
            if isinstance(rd, str):
                try: rd = json.loads(rd)
                except: rd = {}
            if (rd or {}).get("direction") == "LONG":
                t = int(datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
                out.append((t, "reader", (rd or {}).get("entry")))
    except Exception as e:
        print("(reader load err:", e, ")")
    # estratégias (e1_candidates): rule LONG, com bar_time + entry
    try:
        for l in open("/Users/cristrein/tradingview-mcp/alert-bridge/logs/e1_candidates.jsonl"):
            l = l.strip()
            if not l: continue
            d = json.loads(l)
            ts = d.get("ts", "")
            if not ts.startswith("2026-08-13"): continue
            if d.get("direction") != "LONG": continue
            t = int(d.get("bar_time") or 0) or int(datetime.datetime.fromisoformat(ts.replace("Z","+00:00")).timestamp())
            lv = d.get("levels") or {}
            out.append((t, "e1:" + str(d.get("rule", "?")), lv.get("entry") or d.get("entry")))
    except Exception as e:
        print("(e1 load err:", e, ")")
    return sorted(out)


def main():
    b15 = load_bars("15"); b60 = load_bars("60"); b240 = load_bars("240")
    print("RAW nativo: 15m=%d 60=%d 240=%d bars" % (len(b15), len(b60), len(b240)))

    # 1) TIMELINE horário do trend/CHoCH E0 (causal) — o que o guard veria
    print("\n=== TIMELINE E0 (causal, função do próprio E0) — hora a hora ===")
    print("  hora(UTC) | trend15 trend60 trend240 | choch_dn 15/60")
    t = DAY0 + 6 * 3600     # começa 06:00 UTC (madrugada em diante)
    while t < min(DAY1, (b15[-1]["t"] if b15 else DAY1) + 1):
        s15 = struct_at(b15, t); s60 = struct_at(b60, t); s240 = struct_at(b240, t)
        if s15:
            hh = datetime.datetime.utcfromtimestamp(t).strftime("%H:%M")
            print("  %s | %-5s %-5s %-5s | dn15=%s dn60=%s" % (
                hh, s15["trend"], (s60 or {}).get("trend"), (s240 or {}).get("trend"),
                s15["choch"]["dn"], (s60 or {}).get("choch", {}).get("dn")))
        t += 3600

    # 2) LONGs induzidos vs guard CORRIGIDO (choch_dn = quebra de estrutura, o sinal certo)
    longs = gather_longs()
    print("\n=== %d LONGs induzidos hoje (reader + estratégias) — guard CHoCH ===" % len(longs))
    print("  regra: BLOQUEAR long se choch_dn (quebra de higher-low) no 4H OU 1H (função do próprio E0).")
    blk = 0
    for (t, src, entry) in longs:
        s60 = struct_at(b60, t); s240 = struct_at(b240, t)
        dn60 = (s60 or {}).get("choch", {}).get("dn")
        dn240 = (s240 or {}).get("choch", {}).get("dn")
        block = bool(dn60 or dn240)
        blk += block
        hh = datetime.datetime.utcfromtimestamp(t).strftime("%H:%M")
        print("  %s %-16s entry=%s | choch_dn 1H=%s 4H=%s → %s" % (
            hh, src, entry, dn60, dn240, "🔴 BLOCK" if block else "passa"))
    if longs:
        n = len(longs)
        print("\n  RESULTADO: guard CHoCH (4H ou 1H) bloquearia %d/%d (%.0f%%) dos longs induzidos." % (
            blk, n, 100 * blk / n))


if __name__ == "__main__":
    main()
