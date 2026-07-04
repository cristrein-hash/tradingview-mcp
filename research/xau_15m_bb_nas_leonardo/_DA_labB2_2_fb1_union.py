#!/usr/bin/env python3
"""DA LAB B r2 — ATAQUE 2: FB1 união protegida 226/435 (52%) — canon útil ou diluição?
a) reproduz união/dedup/painel; b) claims do discovery por componente (conv4 +0,881 / htfceil +1,874);
c) rb_p3 (n96): mede algo ou é catch-all? vs BULL-resto, vs nulls de mesmo N;
d) dedup é ORDER-GAMED? (conv4 ⊂ htfceil ⇒ ordem inversa mata conv4 pela própria regra <30%);
e) preço da proteção: o que sobra acionável fora da união."""
import json, random, hashlib
from pathlib import Path
from itertools import combinations

HERE = Path(__file__).parent
SB = 0.80
CANON = HERE / "results" / "lab_g_candidates.jsonl"
assert hashlib.sha256(CANON.read_bytes()).hexdigest() == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0]
U = [json.loads(l) for l in open(CANON)]
BASE = sorted([r for r in U if r["g_in_base435"] == 1 and r["g_v5h"] != "BEAR"], key=lambda r: r["cj_t"])
FEATS = {f["cj_t"]: f for f in json.load(open(HERE / "results" / "_labB_r2_regime_box_feats.json"))}
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def net(r): return r["g_R"] - SB / r["g_risk"]

C = {}
C["conv4"] = {i for i, b in enumerate(BASE) if fv(b, "h1n_clean_sky_atr", 99) <= 0.29 and fv(b, "h4n_clean_sky_atr", 99) <= 0.12}
C["box96top"] = {i for i, b in enumerate(BASE) if 0.906 <= b["g_box96"] < 0.947}
C["legtop"] = {i for i, b in enumerate(BASE) if fv(b, "legpos90") >= 0.804}
C["htfceil"] = {i for i, b in enumerate(BASE) if fv(b, "h1n_clean_sky_atr", 99) <= 0.39 and fv(b, "h4n_clean_sky_atr", 99) <= 0.17}
C["rb_p1"] = {i for i, b in enumerate(BASE) if b["g_v5h"] == "BULL" and FEATS[b["cj_t"]]["prev_hi_dist_atr"] is not None and FEATS[b["cj_t"]]["prev_hi_dist_atr"] >= -2 and FEATS[b["cj_t"]]["rbox_age_h"] <= 178}
C["rb_p2"] = {i for i, b in enumerate(BASE) if b["g_v5h"] == "RANGE" and FEATS[b["cj_t"]]["rbox_pos"] >= 0.9 and FEATS[b["cj_t"]]["prev_state"] == "BULL" and (FEATS[b["cj_t"]]["prev_hi_dist_atr"] or 0) > 0}
C["rb_p3"] = {i for i, b in enumerate(BASE) if b["g_v5h"] == "BULL" and 3 < FEATS[b["cj_t"]]["rbox_hi_dist_atr"] <= 8}
prot = set().union(*C.values())

def stats(idxs):
    s = [net(BASE[i]) for i in idxs]; n = len(s)
    if not n: return None
    run = sum(1 for i in idxs if BASE[i]["g_R"] >= 3)
    return dict(N=n, wr=round(100 * sum(1 for x in s if x > 0) / n, 1), avg=round(sum(s) / n, 3),
                sum=round(sum(s), 1), run=run, runrate=round(100 * run / n, 1))

print("a) reprodução: união", len(prot), "runners", sum(1 for i in prot if BASE[i]["g_R"] >= 3),
      "net", round(sum(net(BASE[i]) for i in prot), 1))
print("\nb) claims por componente (avgNET flagged):")
for k, s in C.items():
    print(f"   {k:<9} {stats(s)}")
print(f"   BASE      {stats(range(435))}")

print("\nc) rb_p3 catch-all?")
bull = {i for i, b in enumerate(BASE) if b["g_v5h"] == "BULL"}
print(f"   BULL total {stats(bull)}")
print(f"   rb_p3     {stats(C['rb_p3'])}   cobertura de BULL: {len(C['rb_p3'])}/{len(bull)} = {100*len(C['rb_p3'])/len(bull):.0f}%")
print(f"   BULL−rb_p3 {stats(bull - C['rb_p3'])}")
random.seed(11)
obs = sum(net(BASE[i]) for i in C["rb_p3"]); obr = sum(1 for i in C["rb_p3"] if BASE[i]["g_R"] >= 3)
ds, dr = [], []
bl = sorted(bull)
for _ in range(2000):
    pick = random.sample(bl, len(C["rb_p3"]))
    ds.append(sum(net(BASE[i]) for i in pick)); dr.append(sum(1 for i in pick if BASE[i]["g_R"] >= 3))
print(f"   null (2000 subsets de BULL, N={len(C['rb_p3'])}): sumNET obs {obs:.1f} pct {100*sum(1 for d in ds if d < obs)/len(ds):.1f}% | "
      f"runners obs {obr} pct {100*sum(1 for d in dr if d < obr)/len(dr):.1f}%")

# união inteira vs null mesmo-N na base (a união discrimina ou é quase-aleatória grande?)
obsU = sum(net(BASE[i]) for i in prot); obrU = sum(1 for i in prot if BASE[i]["g_R"] >= 3)
dsU, drU = [], []
for _ in range(2000):
    pick = random.sample(range(435), len(prot))
    dsU.append(sum(net(BASE[i]) for i in pick)); drU.append(sum(1 for i in pick if BASE[i]["g_R"] >= 3))
import statistics as stt
print(f"   união vs null mesmo-N(226) na BASE: sumNET obs {obsU:.1f} (null média {stt.mean(dsU):.1f} sd {stt.pstdev(dsU):.1f}) "
      f"pct {100*sum(1 for d in dsU if d < obsU)/len(dsU):.1f}% | runners obs {obrU} pct {100*sum(1 for d in drU if d < obrU)/len(drU):.1f}%")

print("\nd) dedup order-gaming:")
print(f"   conv4 ⊂ htfceil? {C['conv4'] <= C['htfceil']}  (conv4 n{len(C['conv4'])}, htfceil n{len(C['htfceil'])}, inter {len(C['conv4'] & C['htfceil'])})")
def dedup_order(order):
    seen = set(); out = {}
    for k in order:
        newm = C[k] - seen
        out[k] = round(100 * len(newm) / len(C[k]), 0) if C[k] else 0
        seen |= C[k]
    return out
o1 = list(C.keys()); o2 = list(reversed(o1))
print(f"   ordem oficial : {dedup_order(o1)}")
print(f"   ordem inversa : {dedup_order(o2)}  ← componentes <30% novos = kill pela regra do prereg")
print("   Jaccard par-a-par >20%:")
for a, b in combinations(C, 2):
    j = len(C[a] & C[b]) / len(C[a] | C[b]) if C[a] | C[b] else 0
    if j > 0.2: print(f"     {a}~{b}: J={j:.2f} inter {len(C[a]&C[b])}")

print("\ne) preço da proteção (o que sobra p/ lentes futuras):")
rest = set(range(435)) - prot
print(f"   fora da união: {stats(rest)}  → NET fora {round(sum(net(BASE[i]) for i in rest),1)} de 233,6; "
      f"runners fora {sum(1 for i in rest if BASE[i]['g_R']>=3)}/53")
# quanto do DD/streak mora DENTRO da união (se protegido, é inatacável por contexto)?
seq = sorted(range(435), key=lambda i: BASE[i]["cj_t"])
eq = pk = dd = 0.0; worst_window = []
cur = []
for i in seq:
    x = net(BASE[i]); eq += x
    if eq > pk: pk = eq; cur = []
    else: cur.append(i)
    if eq - pk < dd: dd = eq - pk; worst_window = list(cur)
inw = sum(1 for i in worst_window if i in prot)
print(f"   janela do max-DD ({round(dd,1)}): {len(worst_window)} trades, {inw} dentro da união protegida ({100*inw/len(worst_window):.0f}%)")
