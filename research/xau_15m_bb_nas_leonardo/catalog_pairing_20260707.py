#!/usr/bin/env python3
"""Pareamento FUNDO->ENTRY + cruzamento com trades winners (2026-07-07)."""
import json, datetime as dt, bisect
from pathlib import Path
HERE = Path(__file__).resolve().parent
cat = json.load(open(HERE/"results"/"catalog_manual_tags_20260707.json"))
def ds(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M") if t else "??"
fundos = sorted([n for n in cat["notes"]["FUNDO"] if n["t"]], key=lambda x:int(x["t"]))
entrys = sorted([n for n in cat["notes"]["ENTRY"] if n["t"]], key=lambda x:int(x["t"]))
circles = cat["circles"]; trades = cat["trades"]
inval = cat["notes"].get("INVALIDO",[])
print(f"FUNDOS(nota) {len(fundos)} · ENTRYS(nota) {len(entrys)} · circulos {len(circles)} · trades {len(trades)} · invalidos {len(inval)}")
FT = [int(f["t"]) for f in fundos]
print("\n=== PAREAMENTO FUNDO -> ENTRY (entry apos fundo, no retest) ===")
pairs = []
for e in entrys:
    et = int(e["t"]); i = bisect.bisect_right(FT, et)-1
    fnd = fundos[i] if i>=0 and et-FT[i] <= 60*3600 else None
    lag_h = (et-int(fnd["t"]))/3600 if fnd else None
    pairs.append((fnd, e, lag_h))
    if fnd:
        print(f"  FUNDO {ds(fnd['t'])} ({fnd['price']:.0f})  ->  ENTRY {ds(et)} ({e['price']:.0f})  lagH={lag_h:.1f}")
    else:
        print(f"  ENTRY {ds(et)} ({e['price']:.0f}) sem fundo pareado <=60h")
SH = json.load(open("/private/tmp/claude-501/-Users-cristrein-tradingview-mcp/d1341f00-be87-4e4d-a046-9208ee4563a5/scratchpad/shapes_v2.json"))
tl = [r for r in SH if r["name"]=="text" and r["text"].strip().startswith("#")]
def gt0(r):
    pts=r.get("points") or []; return int(pts[0]["time"]) if pts and pts[0].get("time") else None
wins=[]; loss=[]
for r in tl:
    txt=r["text"].strip(); t=gt0(r)
    (wins if "✓" in txt else loss).append((ds(t), txt, t))
print(f"\n=== TRADES #C/#S: winners {len(wins)} · losers {len(loss)} ===")
# quantos winners/losers estao perto (<=12h) de VELA DE FUNDO marcada?
def near(t, arr, w=12*3600):
    return any(abs(int(x['t'])-t)<=w for x in arr if x['t'])
wn = sum(1 for d,txt,t in wins if t and near(t,fundos))
ln = sum(1 for d,txt,t in loss if t and near(t,fundos))
print(f"  winners perto de VELA DE FUNDO (<=12h): {wn}/{len(wins)}")
print(f"  losers  perto de VELA DE FUNDO (<=12h): {ln}/{len(loss)}")
wne = sum(1 for d,txt,t in wins if t and near(t,entrys))
lne = sum(1 for d,txt,t in loss if t and near(t,entrys))
print(f"  winners perto de VELA DE ENTRY (<=12h): {wne}/{len(wins)}")
print(f"  losers  perto de VELA DE ENTRY (<=12h): {lne}/{len(loss)}")
print("\n=== VELAS DE FUNDO cronologico (conjunto ampliado) ===")
for f in fundos: print(f"  {ds(f['t'])}  {f['price']:.0f}")
json.dump({"pairs":[{"fundo":ds(p[0]['t']) if p[0] else None,"entry":ds(p[1]['t']),"lag_h":p[2]} for p in pairs],
           "wins":[(d,txt) for d,txt,t in wins],"loss":[(d,txt) for d,txt,t in loss]},
          open(HERE/"results"/"catalog_pairing_20260707.json","w"), indent=1, default=str)
print("OK -> results/catalog_pairing_20260707.json")
