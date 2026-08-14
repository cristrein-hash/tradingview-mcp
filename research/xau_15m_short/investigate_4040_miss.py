#!/usr/bin/env python3
"""RE-INVESTIGAÇÃO (Cris 2026-07-20): porque o SHORT do 4040 não foi acionado — os 3 erros.
FACTS-first, reprodutível. Lê o store 1H/15M/5M (zero MCP). Não conclui — mede.
Erro 1: topo pré-existente (quinta ~12-13h 1H perto de 4040)? · Erro 2: OB/SVP na região? ·
Erro 3: no fecho da 15M do spike, quão abaixo estava o preço vs o high (close-late).
Uso: python3 investigate_4040_miss.py"""
import json, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
REPO = Path("/Users/cristrein/tradingview-mcp")
S = REPO / "my-strategy/core/bar_store/store"
REV = REPO / "my-strategy/research/revalidation"


def jl(f):
    try: return [json.loads(x) for x in Path(f).read_text().splitlines() if x.strip()]
    except Exception: return []


def lx(t): return dt.datetime.fromtimestamp(int(t), LX)


print("=== ERRO 1: TOPO PRÉ-EXISTENTE perto de 4040 (1H, 2026-07-15→07-20) ===")
h1 = [b for b in jl(REV / "raw_1h_ohlc.jsonl")
      if "2026-07-1" in lx(b["t"]).strftime("%Y-%m-%d") and lx(b["t"]).strftime("%Y-%m-%d") >= "2026-07-15"]
# highs perto de 4040 (>=4035)
near = [b for b in h1 if b["h"] >= 4035]
print(f"  barras 1H com high>=4035 na semana: {len(near)}")
for b in near:
    print(f"    {lx(b['t']).strftime('%a %m-%d %H:%M')}  O{b['o']:.1f} H{b['h']:.1f} L{b['l']:.1f} C{b['c']:.1f}")
# o topo máximo da semana ANTES de hoje
pre = [b for b in h1 if lx(b["t"]).strftime("%Y-%m-%d") < "2026-07-20"]
if pre:
    top = max(pre, key=lambda b: b["h"])
    print(f"  >> TOPO 1H pré-hoje: {top['h']:.2f} em {lx(top['t']).strftime('%a %m-%d %H:%M')} Lisboa")

print("\n=== ERRO 3: 15M CLOSE-LATE no spike de hoje (a barra que fechou a ~4022) ===")
m15 = [b for b in jl(S / "bars_15m.jsonl") if lx(b["t"]).strftime("%Y-%m-%d") == "2026-07-20"]
spike15 = max(m15, key=lambda b: b["h"]) if m15 else None
if spike15:
    b = spike15
    print(f"  barra 15M do topo: {lx(b['t']).strftime('%H:%M')}  O{b['o']:.1f} H{b['h']:.1f} L{b['l']:.1f} C{b['c']:.1f}")
    print(f"  HIGH {b['h']:.1f} vs CLOSE {b['c']:.1f}  =>  no fecho da 15M o preço já estava {b['c']-b['h']:.1f} pts abaixo do topo")
print("\n=== ERRO 3b: as barras 5M do spike (o que a 15M esconde) ===")
m5 = [b for b in jl(S / "bars_5m.jsonl") if lx(b["t"]).strftime("%Y-%m-%d") == "2026-07-20" and 12 <= lx(b["t"]).hour <= 13]
for b in sorted(m5, key=lambda x: x["t"]):
    if b["h"] >= 4030 or b["l"] <= 4020:
        print(f"    5M {lx(b['t']).strftime('%H:%M')}  O{b['o']:.1f} H{b['h']:.1f} L{b['l']:.1f} C{b['c']:.1f}  range {b['h']-b['l']:.1f}")

print("\n=== ERRO 2: OB/SVP na região 4040 (pine_boxes 15M snapshot atual) ===")
try:
    pb = json.loads((S / "pine_boxes_15.json").read_text()).get("data") or {}
    for s in (pb.get("studies") or []):
        nm = (s.get("name") or "")
        nb = len(s.get("boxes") or [])
        if nb: print(f"    estudo com boxes: {nm[:40]} ({nb} boxes)")
except Exception as e:
    print("    (pine_boxes ilegível:", e, ")")
print("  NOTA: SVP/OB exatos da quinta exigem o RAW histórico (snapshot atual só tem o estado de agora).")
