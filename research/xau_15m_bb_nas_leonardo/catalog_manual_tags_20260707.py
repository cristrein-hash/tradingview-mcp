#!/usr/bin/env python3
"""CATÁLOGO das tags manuais do Cris no gráfico (2026-07-07, nova meta: detectar mais fundos).
Cruza: círculos (fundos marcados) + text_note (VELA DE FUNDO / ENTRY / inválidos) + trades #C/#S
(com outcome do cache). Organiza cronologicamente. Passo 1 da catalogação."""
import json, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
SH = Path("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/d1341f00-be87-4e4d-a046-9208ee4563a5/scratchpad/shapes_v2.json")
rows = json.load(open(SH))
def t0(r):
    pts = r.get("points") or []
    return pts[0]["time"] if pts and isinstance(pts[0], dict) and pts[0].get("time") else None
def p0(r):
    pts = r.get("points") or []
    return pts[0]["price"] if pts and isinstance(pts[0], dict) and pts[0].get("price") else None
def ds(t): return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M") if t else "??"
def norm(s): return " ".join((s or "").upper().split())
# classificar notas
NOTE_CLASS = {}
for r in rows:
    if r["name"] != "text_note": continue
    txt = norm(r["text"]); t = t0(r)
    if "ENTRY" in txt: cls = "ENTRY"
    elif "NÃO VALIDO" in txt or "NAO VALIDO" in txt or "NÃO VÁLIDO" in txt: cls = "INVALIDO"
    elif "POLARIDADE" in txt: cls = "POLARIDADE_TOPO"
    elif "FUNDO" in txt: cls = "FUNDO"
    else: cls = "OUTRO"
    NOTE_CLASS.setdefault(cls, []).append({"t": t, "date": ds(t), "price": p0(r), "text": r["text"].strip()})
# trades: label text (#C/#S) + long_position, casar por time
labels = [r for r in rows if r["name"]=="text" and r["text"].strip().startswith("#")]
lps = [r for r in rows if r["name"]=="long_position"]
circles = [r for r in rows if r["name"]=="circle"]
print("=== CONTAGEM ===")
for k,v in NOTE_CLASS.items(): print(f"  notas {k}: {len(v)}")
print(f"  círculos (fundos marcados): {len(circles)}")
print(f"  trades #C/#S: {len(labels)}")
# cronologia das notas de FUNDO e ENTRY e INVALIDO
def dump(cls):
    print(f"\n=== {cls} ({len(NOTE_CLASS.get(cls,[]))}) cronológico ===")
    for n in sorted(NOTE_CLASS.get(cls,[]), key=lambda x: x["t"] or 0):
        print(f"  {n['date']}  price {n['price']:.0f}  :: {n['text']}")
dump("INVALIDO"); dump("POLARIDADE_TOPO")
# salvar catálogo bruto
cat = {"notes": NOTE_CLASS,
       "circles": sorted([{"t": t0(r), "date": ds(t0(r)), "price": p0(r)} for r in circles], key=lambda x: x["t"] or 0),
       "trades": sorted([{"t": t0(r), "date": ds(t0(r)), "label": r["text"].strip()} for r in labels], key=lambda x: x["t"] or 0)}
json.dump(cat, open(HERE/"results"/"catalog_manual_tags_20260707.json","w"), indent=1, default=str)
print("\nOK → results/catalog_manual_tags_20260707.json")
