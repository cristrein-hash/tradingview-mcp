#!/usr/bin/env python3
"""ENGINE DE GRAMÁTICA SMC — a linguagem estrutural que o Cris lê, como SEQUÊNCIA (2026-07-05).
Família nunca testada: os prints do Cris mostram SMC (BOS/CHoCH/EQH/EQL + zonas) — a leitura dele
é a GRAMÁTICA desses eventos, não thresholds. Primitives têm smc_events e zones; nenhum tensor de
hoje os usou como sequência.

DESIGN CONGELADO:
  direção do evento: bull se close(t_evento) > price_do_evento (nível quebrado abaixo do close),
  bear caso contrário (EQH/EQL neutros). Causalidade declarada: t = barra do rótulo no capture.
  Para cada candidato (cj_t), janela 48h (192 barras) para trás:
    f1 cascade_bos_down   nº de BOS-bear consecutivos imediatamente antes (cascata de capitulação)
    f2 choch_up_recent    CHoCH-bull nas últimas 8 barras (virada estrutural no low)
    f3 eql_swept          EQL marcado na janela cujo nível foi rompido para baixo depois (sweep de liquidez)
    f4 t_since_choch_dn   barras desde o último CHoCH-bear (fase da perna)
    f5 demand_born_24h    zonas DEMAND nascidas nas últimas 24h com low ≤ preço (demanda fresca)
    f6 supply_born_24h    zonas SUPPLY nascidas nas últimas 24h acima (teto fresco)
    f7 trigram            identidade dos últimos 3 tokens direcionais (o "acorde" estrutural)
  TESTES (ledger fechado): enriquecimento is_cris60 por valor de f1-f6 (grupos ≥40) + top-10
  trigramas; null de permutação 2000× sobre o MÁXIMO lift do ledger inteiro; painel hit-3R/NET3."""
import json, glob, bisect, hashlib, random
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent

GT = HERE / "results" / "ground_truth_bottoms_20260705.json"
sha = hashlib.sha256(GT.read_bytes()).hexdigest()
assert sha == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
gt = json.load(open(GT)); assert len(gt) == 60
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
series = {}; EV = []; ZS = []
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]:
        series.setdefault(b["t"], b)
    EV += d["smc_events"]; ZS += d["zones"]
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]

def close_at(t):
    i = bisect.bisect_right(TS, t) - 1
    return S[i]["c"] if i >= 0 else None

seen = set(); events = []
for e in sorted(EV, key=lambda x: x["t"]):
    key = (e["t"], e["text"], round(e["price"], 2))
    if key in seen:
        continue
    seen.add(key)
    c = close_at(e["t"])
    if c is None:
        continue
    if e["text"] in ("BOS", "CHoCH"):
        tok = e["text"] + ("+" if c > e["price"] else "-")
    else:
        tok = e["text"]
    events.append({"t": e["t"], "tok": tok, "price": e["price"]})
ET = [e["t"] for e in events]
zs = sorted({(z["born_t"], z["text"], round(z["high"], 2), round(z["low"], 2)) for z in ZS})
ZT = [z[0] for z in zs]
print(f"eventos SMC únicos: {len(events)} · zonas únicas: {len(zs)}")

for u in U:
    u["is_cris60"] = 0
UT = sorted(range(len(U)), key=lambda k: U[k]["t"]); T = [U[k]["t"] for k in UT]
for g in gt:
    j = bisect.bisect_left(T, g["flush_t"] - 7200); best = None
    while j < len(T) and T[j] <= g["flush_t"] + 7200:
        u = U[UT[j]]
        if best is None or abs(u["t"] - g["flush_t"]) < abs(best["t"] - g["flush_t"]):
            best = u
        j += 1
    if best:
        best["is_cris60"] = 1

def gram(u):
    cj = u["cj_t"]; t0 = cj - 192 * 900
    hi = bisect.bisect_right(ET, cj)
    win = [events[i] for i in range(hi) if events[i]["t"] >= t0]
    o = {}
    # f1 cascata: BOS-/CHoCH- consecutivos no fim da sequência (ignorando EQH/EQL)
    dirs = [e["tok"] for e in win if e["tok"] not in ("EQH", "EQL")]
    n = 0
    for tok in reversed(dirs):
        if tok in ("BOS-", "CHoCH-"):
            n += 1
        else:
            break
    o["cascade_down"] = min(n, 6)
    # f2 CHoCH+ nas últimas 8 barras
    o["choch_up_recent"] = int(any(e["tok"] == "CHoCH+" and cj - e["t"] <= 8 * 900 for e in win))
    # f3 EQL varrido: EQL na janela cujo nível foi rompido para baixo depois do evento, antes do cj
    swept = 0
    for e in win:
        if e["tok"] != "EQL":
            continue
        i0 = bisect.bisect_right(TS, e["t"]); i1 = bisect.bisect_right(TS, cj)
        if any(S[k]["l"] < e["price"] for k in range(i0, i1)):
            swept = 1; break
    o["eql_swept"] = swept
    # f4 barras desde último CHoCH- (capado 96; 99 = nenhum)
    last = [e for e in win if e["tok"] == "CHoCH-"]
    o["t_since_choch_dn"] = min(96, (cj - last[-1]["t"]) // 900) if last else 99
    # f5/f6 zonas nascidas nas últimas 24h
    j0 = bisect.bisect_left(ZT, cj - 96 * 900); j1 = bisect.bisect_right(ZT, cj)
    px = close_at(cj) or 0
    o["demand_born_24h"] = min(6, sum(1 for j in range(j0, j1) if zs[j][1] == "DEMAND" and zs[j][3] <= px))
    o["supply_born_24h"] = min(6, sum(1 for j in range(j0, j1) if zs[j][1] == "SUPPLY" and zs[j][2] >= px))
    # f7 trigrama direcional
    o["trigram"] = "|".join(dirs[-3:]) if len(dirs) >= 3 else "none"
    return o

G = {u["cj_t"]: gram(u) for u in U}
base = sum(u["is_cris60"] for u in U) / len(U); NC = sum(u["is_cris60"] for u in U)

ledger = []
FEATS = ["cascade_down", "choch_up_recent", "eql_swept", "t_since_choch_dn", "demand_born_24h", "supply_born_24h"]
for f in FEATS:
    vals = sorted({G[u["cj_t"]][f] for u in U})
    if f == "t_since_choch_dn":
        groups = [("<=8", lambda v: v <= 8), ("9-24", lambda v: 8 < v <= 24), ("25-96", lambda v: 24 < v <= 96), ("nunca", lambda v: v == 99)]
    else:   # discretas 0..6: por valor E cauda >=v (cascatas/zonas acumuladas)
        groups = [(f"={v}", (lambda vv: (lambda x: x == vv))(v)) for v in vals]
        groups += [(f">={v}", (lambda vv: (lambda x: x >= vv))(v)) for v in vals if v >= 2]
    for tag, fn in groups:
        g = [u for u in U if fn(G[u["cj_t"]][f])]
        if len(g) >= 40:
            ledger.append((f, tag, g))
tri_counts = Counter(G[u["cj_t"]]["trigram"] for u in U)
for tri, cnt in tri_counts.most_common(10):
    if cnt >= 40:
        ledger.append(("trigram", tri, [u for u in U if G[u["cj_t"]]["trigram"] == tri]))

random.seed(5)
ids = [id(u) for u in U]
group_ids = [[id(u) for u in g] for _, _, g in ledger]
maxes = []
for _ in range(2000):
    lab = set(random.sample(ids, NC))
    m = 0.0
    for gi in group_ids:
        m = max(m, (sum(1 for x in gi if x in lab) / len(gi)) / base)
    maxes.append(m)
maxes.sort()

def pval(lift):
    return sum(1 for m in maxes if m >= lift) / len(maxes)

print(f"null max-lift ({len(ledger)} grupos, 2000 perms): q50 {maxes[1000]:.2f} · q95 {maxes[int(0.95*2000)]:.2f}")
print(f"\n{'feature':<18} {'grupo':>18} {'N':>5} {'cris':>4} {'prec%':>6} {'lift':>5} {'P':>7} {'hit3R%':>7} {'NET3':>8}")
rows = []
for f, tag, g in ledger:
    nc = sum(u["is_cris60"] for u in g)
    lift = (nc / len(g)) / base
    h3 = net = cnt = 0
    for u in g:
        r3 = R3.get(u["cj_t"])
        if r3:
            cnt += 1; h3 += r3["R3"] >= 3; net += r3["net3"]
    rows.append((f, tag, len(g), nc, lift, pval(lift), h3 / max(1, cnt), net))
rows.sort(key=lambda x: -x[4])
for f, tag, n, nc, lift, p, h3, net in rows[:18]:
    mark = " ***" if p <= 0.002 else ""
    print(f"{f:<18} {tag:>18} {n:>5} {nc:>4} {100*nc/n:>5.1f}% {lift:>5.2f} {p:>7.3f} {100*h3:>6.1f}% {net:>+8.1f}{mark}")
sig = [(f, t, round(l, 2), p) for f, t, n, nc, l, p, h3, net in rows if p <= 0.002]
print(f"\nSIGNIFICATIVOS P≤0,002: {sig if sig else 'NENHUM'}")
json.dump({"ledger": [{"f": f, "g": t, "n": n, "cris": nc, "lift": round(l, 3), "p": p,
                       "hit3r": round(h3, 3), "net3": round(float(net), 1)}
                      for f, t, n, nc, l, p, h3, net in rows],
           "significant": sig}, open(HERE / "results" / "smc_grammar_engine_20260705.json", "w"), indent=1)
print("OK → results/smc_grammar_engine_20260705.json")
