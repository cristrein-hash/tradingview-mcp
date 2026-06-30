#!/usr/bin/env python3
"""GROUND-TRUTH DE REGIME (desenho à mão do Cris no XAU 4H, lido via MCP draw_get_properties).
Materializa os 30 retângulos -> cris_regime_boxes.csv + classifica macro vs counter-pullback (containment) +
alinha as BORDAS (viradas de regime) com (a) os pivôs M8 (15M 2024+) e (b) swings reais do RAW 4H (snap).
⚠️ Desenho do Cris = RÉGUA (hindsight), NUNCA feature. Só verificação quantificável pré-build. Determinístico."""
import json,csv,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp")
OUT=Path(__file__).parent; OUT.mkdir(parents=True,exist_ok=True)
# 30 boxes lidos do chart (id, t1, t2, p1, p2, rgb). p1/p2 = cantos (ordem variável).
BOXES=[
 ("gilSKe",1769727600,1782770400,5446.73,3955.25,(178,40,51)),
 ("MDd3Qx",1745416800,1747418400,3450.10,3121.78,(178,40,51)),
 ("VGDk89",1747418400,1756490400,3453.01,3180.11,(255,152,0)),
 ("NV0uga",1756476000,1769742000,5587.13,3453.68,(76,175,80)),
 ("k9cYyF",1585144800,1597183200,2070.51,1445.39,(76,175,80)),
 ("x9bb4e",1597154400,1618279200,2067.82,1444.05,(242,54,69)),
 ("pXF6sU",1624269600,1644346800,1874.66,1706.98,(255,152,0)),
 ("ctpXPs",1714629600,1723442400,2446.55,2272.55,(255,152,0)),
 ("R7sW6a",1712944800,1714629600,2433.72,2272.55,(242,54,69)),
 ("Cr8lB6",1702897200,1708498800,2087.47,1984.40,(255,152,0)),
 ("uxjSl6",1723413600,1745416800,2444.33,3501.28,(76,175,80)),
 ("fEjQFW",1708484400,1713146400,2429.35,2065.06,(76,175,80)),
 ("rd5XkL",1683309600,1696975200,2040.60,1807.36,(247,82,95)),
 ("Ld9omJ",1696960800,1701716400,2141.94,1884.23,(76,175,80)),
 ("QXb1s9",1701716400,1702897200,2141.94,1885.98,(242,54,69)),
 ("MkUdMC",1677596400,1683525600,1807.36,2078.17,(56,142,60)),
 ("NP71QK",1667556000,1675364400,1667.58,1960.23,(56,142,60)),
 ("xRYAeE",1675350000,1678201200,1960.23,1807.36,(242,54,69)),
 ("FMYMok",1646780400,1667512800,2063.32,1620.41,(242,54,69)),
 ("f49FEm",1658714400,1660312800,1714.76,1806.48,(56,142,60)),
 ("DlnPJb",1606777200,1609988400,1960.10,1819.89,(56,142,60)),
 ("QbBY8a",1618221600,1624024800,1913.36,1707.73,(56,142,60)),
 ("UhaHKi",1730412000,1731639600,2759.94,2536.95,(242,54,69)),
 ("FmARNx",1740466800,1740754800,2925.52,2824.04,(242,54,69)),
 ("nUVqkV",1743703200,1744164000,3124.48,2964.24,(242,54,69)),
 ("YqCzoc",1760983200,1762354800,4376.99,3901.62,(242,54,69)),
 ("ju8H9y",1766761200,1767380400,4537.23,4275.51,(242,54,69)),
 ("NHUqdI",1774274400,1776708000,4099.31,4889.94,(76,175,80)),
 ("wI1rsJ",1777917600,1778637600,4779.02,4500.53,(76,175,80)),
 ("nj89el",1781157600,1781632800,4373.08,4023.79,(76,175,80)),
]
def fam(rgb):
    r,g,b=rgb
    if g>120 and r<120: return "BULL"        # 76,175,80 / 56,142,60
    if r>150 and g<100: return "BEAR"        # 242,54,69 / 178,40,51 / 247,82,95
    if r>200 and 120<g<180: return "RANGE"   # 255,152,0
    return "?"
def D(ts): return dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
rows=[]
for bid,t1,t2,p1,p2,rgb in BOXES:
    ts0,ts1=min(t1,t2),max(t1,t2)
    rows.append({"id":bid,"start":ts0,"end":ts1,"start_d":D(ts0),"end_d":D(ts1),
                 "dur_days":round((ts1-ts0)/86400,1),"hi":max(p1,p2),"lo":min(p1,p2),"family":fam(rgb),"rgb":rgb})
# macro vs pullback: pullback = contido no TEMPO dentro de outro box de família OPOSTA e maior
def opp(a,b): return {"BULL":"BEAR","BEAR":"BULL"}.get(a)==b
for r in rows:
    r["role"]="MACRO"
    for o in rows:
        if o is r: continue
        if o["start"]<=r["start"] and o["end"]>=r["end"] and o["dur_days"]>r["dur_days"] and opp(r["family"],o["family"]):
            r["role"]="PULLBACK"; r["parent"]=o["id"]; r["parent_fam"]=o["family"]; break
# CSV
with open(OUT/"cris_regime_boxes.csv","w",newline="") as fh:
    w=csv.writer(fh); w.writerow(["id","role","family","parent_fam","start","end","start_d","end_d","dur_days","hi","lo"])
    for r in sorted(rows,key=lambda x:x["start"]):
        w.writerow([r["id"],r["role"],r["family"],r.get("parent_fam",""),r["start"],r["end"],r["start_d"],r["end_d"],r["dur_days"],r["hi"],r["lo"]])
macro=[r for r in rows if r["role"]=="MACRO"]; pull=[r for r in rows if r["role"]=="PULLBACK"]
print(f"=== GROUND-TRUTH REGIME (Cris, XAU 4H) — {len(rows)} boxes ===")
print(f"MACRO: {len(macro)} | counter-PULLBACK: {len(pull)}")
from collections import Counter
print("macro por família:",dict(Counter(r['family'] for r in macro)))
print("pullback por tipo:",dict(Counter((r.get('parent_fam'),'->',r['family']) for r in pull)))
print("\n--- TIMELINE MACRO (ordenada) ---")
for r in sorted(macro,key=lambda x:x["start"]):
    print(f"  {r['family']:5} {r['start_d']} -> {r['end_d']} ({r['dur_days']:>5}d) [{r['lo']:.0f}-{r['hi']:.0f}] {r['id']}")
print("\n--- COUNTER-PULLBACKS (aninhados) ---")
for r in sorted(pull,key=lambda x:x["start"]):
    typ=f"{r['family']}_em_{r['parent_fam']}"
    print(f"  {typ:13} {r['start_d']} ({r['dur_days']:>4}d) [{r['lo']:.0f}-{r['hi']:.0f}] {r['id']}")
# ---- ALINHAMENTO com M8 (15M, só overlap 2024+) ----
m8=[]
with open(ROOT/"research/xau_15m_bb_nas_leonardo/true_reversals_M8.csv") as fh:
    for d in csv.DictReader(fh): m8.append((int(d["t"]),d["kind"],float(d["price"])))
m8.sort()
def nearest_m8(ts):
    best=None;bd=None
    for t,k,p in m8:
        dd=abs(t-ts)
        if bd is None or dd<bd: bd=dd;best=(t,k,p)
    return best,bd
edges=[]  # (ts, "REGIME_A->REGIME_B") nas viradas de MACRO
sm=sorted(macro,key=lambda x:x["start"])
for i,r in enumerate(sm):
    edges.append((r["start"],f"->{r['family']}",r["id"]))
print("\n--- ALINHAMENTO bordas MACRO (2024+) vs pivô M8 mais próximo ---")
M8MIN=m8[0][0]
for ts,lab,bid in edges:
    if ts<M8MIN: continue
    (t,k,p),bd=nearest_m8(ts)
    print(f"  borda {lab:8} {D(ts)} ({bid}) -> M8 {k} {D(t)} a {bd/3600:.0f}h ({bd/86400:.1f}d)")
# ---- SNAP no RAW 4H: swing real perto da borda ----
raw=[json.loads(l) for l in (ROOT/"my-strategy/research/revalidation/raw_4h_ohlc.jsonl").read_text().splitlines()]
raw.sort(key=lambda b:b["t"])
def snap(ts,win=10):
    near=[b for b in raw if abs(b["t"]-ts)<=win*4*3600]
    if not near: return None
    lo=min(near,key=lambda b:b["l"]); hi=max(near,key=lambda b:b["h"])
    return lo,hi
print("\n--- SNAP bordas MACRO no RAW 4H (swing real ±10 barras) ---")
for ts,lab,bid in edges:
    s=snap(ts)
    if not s: continue
    lo,hi=s
    print(f"  borda {lab:8} {D(ts)} -> swing-low {lo['l']:.0f}@{D(lo['t'])} | swing-high {hi['h']:.0f}@{D(hi['t'])}")
print(f"\n-> {OUT/'cris_regime_boxes.csv'} (macro {len(macro)} + pullback {len(pull)})")
print("M8 range:",D(m8[0][0]),"a",D(m8[-1][0]),"| RAW 4H:",D(raw[0]['t']),"a",D(raw[-1]['t']))
