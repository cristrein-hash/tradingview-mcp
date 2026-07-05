#!/usr/bin/env python3
"""ENGINE DE LEITURA SEQUENCIAL 15M — porte do V1.4g-RWS-A6 4H (WR67/streak4/DD4,4R) p/ 15M
(2026-07-05, diretriz Cris: replicar lógica CONTEXTUAL/SEQUENCIAL que funcionou no 4H LONG; parar de
limitar a snapshot). Alvo = MON+FORTE + hit-3R. Reads SEQUENCIAIS (multi-barra, no tempo):
  BUBBLES: buy_recent (acumulação janela) · burst_recent_vs_older (genuíno vs late-fake) ·
           large_buy_win8 (confirmação institucional) · sell_absorb (sell M/L absorvido = preço não caiu)
  RSI: bear_div_cluster em 20b (exaustão acumulada, anti-filtro) · rsi_above_ma
  NAS: nas_long_recent / nas_short_recent (contexto de rótulo)
  ESTRUTURA: not_range_middle (|supply-demand|>0.5ATR) · supply_far
Causalidade: tudo <= cj_t (bubbles por known_at; nas/smc por t; rsi por barra fechada). Universo selado."""
import json, glob, bisect, hashlib, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
U = [json.loads(l) for l in open(HERE / "results" / "lab_g_candidates.jsonl")]
R3 = {json.loads(l)["cj_t"]: json.loads(l) for l in open(HERE / "results" / "r3_target_universe_20260704.jsonl")}
LEG = {x["cj_t"]: x for x in (json.loads(l) for l in open(HERE / "results" / "htf_leg_features_20260705.jsonl"))}
def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
WEEKS = len({r["g_week"] for r in U})
MF = set(r["cj_t"] for r in U if fv(r, "is_monforte") == 1)

# series + rsi-ma + bubbles + nas por bloco
series = {}; nas = []
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    d = json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"], b)
    nas += [e for e in d["nas_events"] if e.get("t")]
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; N = len(S)
RSI = [b.get("rsi") for b in S]
RSIMA = [None] * N  # MA14 do RSI
for i in range(N):
    w = [RSI[j] for j in range(max(0, i - 13), i + 1) if RSI[j] is not None]
    RSIMA[i] = sum(w) / len(w) if w else None
# swing lows do RSI e do preço p/ bear-div (preço faz HH, RSI faz LH = bear div)
BUB = sorted([json.loads(l) for p in glob.glob(str(HERE / "bubbles" / "*.bubbles.jsonl")) for l in open(p)],
             key=lambda x: (x.get("known_at") or x["t"]))
BUBK = [(x.get("known_at") or x["t"]) for x in BUB]
nas.sort(key=lambda e: e["t"]); NAST = [e["t"] for e in nas]

def bub_upto(t0, wlo, whi):
    """bubbles com known_at<=t0 e t em [t0-whi, t0-wlo] (janelas em barras 15M)."""
    hi = bisect.bisect_right(BUBK, t0)
    return [BUB[i] for i in range(hi) if t0 - whi * 900 <= BUB[i]["t"] <= t0 - wlo * 900]

def seq_feats(cj_t):
    i = bisect.bisect_right(TS, cj_t) - 1
    if i < 40: return {}
    o = {}
    # BUBBLES sequenciais
    recent = bub_upto(cj_t, 0, 4)      # últimas 4 barras
    older = bub_upto(cj_t, 5, 10)      # 5-10 barras atrás
    win8 = bub_upto(cj_t, 0, 8)
    w = {"S": 1, "M": 2, "L": 3}
    buy_recent = sum(w[x["size"]] for x in recent if x["side"] == "BUY")
    buy_older = sum(w[x["size"]] for x in older if x["side"] == "BUY")
    o["buy_recent"] = buy_recent
    o["burst_recent_vs_older"] = buy_recent - buy_older
    o["large_buy_win8"] = int(any(x["side"] == "BUY" and x["size"] == "L" for x in win8))
    o["sell_ml_win8"] = sum(1 for x in win8 if x["side"] == "SELL" and x["size"] in ("M", "L"))
    o["buy_ml_recent"] = sum(1 for x in recent if x["side"] == "BUY" and x["size"] in ("M", "L"))
    # RSI sequencial
    o["rsi_above_ma"] = int(RSI[i] is not None and RSIMA[i] is not None and RSI[i] > RSIMA[i])
    # bear-div cluster: em 20 barras, quantos pontos onde preço HH mas RSI LH (janela 3)
    bd = 0
    for k in range(i - 20, i - 2):
        if k < 3: continue
        if S[k]["h"] == max(x["h"] for x in S[k - 2:k + 3]):  # swing high preço
            # RSI no swing anterior vs agora
            prev = [j for j in range(k - 12, k - 2) if S[j]["h"] == max(x["h"] for x in S[max(0,j-2):j+3])]
            if prev and RSI[k] is not None and RSI[prev[-1]] is not None and S[k]["h"] > S[prev[-1]]["h"] and RSI[k] < RSI[prev[-1]]:
                bd += 1
    o["rsi_bear_div_20"] = bd
    # NAS contexto
    j = bisect.bisect_right(NAST, cj_t) - 1
    o["nas_last_long"] = int(j >= 0 and nas[j]["dir"] == "LONG" and (cj_t - nas[j]["t"]) // 900 <= 24)
    o["nas_last_short_recent"] = int(j >= 0 and nas[j]["dir"] == "SHORT" and (cj_t - nas[j]["t"]) // 900 <= 4)
    return o

FT = {r["cj_t"]: seq_feats(r["cj_t"]) for r in U}
mf = [r for r in U if r["cj_t"] in MF]; rest = [r for r in U if r["cj_t"] not in MF]
def med(rows, k):
    v = sorted(FT[r["cj_t"]].get(k) for r in rows if k in FT[r["cj_t"]])
    return v[len(v) // 2] if v else None
print("MEDIANAS sequenciais (MON+FORTE vs resto):")
for k in ("buy_recent", "burst_recent_vs_older", "large_buy_win8", "sell_ml_win8", "buy_ml_recent",
          "rsi_above_ma", "rsi_bear_div_20", "nas_last_long", "nas_last_short_recent"):
    print(f"  {k:<22} MF={med(mf,k)}  resto={med(rest,k)}")

# porte do V1.4g-RWS-A6 (leitura sequencial) — congelado
def rws15m(r):
    f = FT.get(r["cj_t"], {})
    if not f: return False
    # 1. estrutura base (nao-range-middle + supply distinto) — do V1.4g
    supply = fv(r, "n_supply_overhead", 99); dem = fv(r, "in_demand")
    # 2. bubble buy recent (acumulacao)
    if f.get("buy_recent", 0) < 2: return False
    # 3. RWS: rsi_above_ma OU supply perto (nao longe demais)
    if f.get("rsi_above_ma") == 0 and supply <= 20: return False
    # 4. A6 anti burst-fake: burst concentrado late SEM confirmacao institucional (rescue NAS short)
    if f.get("burst_recent_vs_older", 0) >= 3 and f.get("large_buy_win8") == 0 and f.get("nas_last_short_recent") == 0:
        return False
    # 5. A7 anti RSI bear-div cluster
    if f.get("rsi_bear_div_20", 0) >= 2: return False
    return True

def panel(rows, tag):
    n = len(rows)
    if not n: print(f"  {tag:<26} vazio"); return None
    rs = sorted(rows, key=lambda r: r["cj_t"]); nets = [R3[r["cj_t"]]["net3"] for r in rs]
    h = sum(1 for r in rs if R3[r["cj_t"]]["R3"] >= 3); w = sum(1 for x in nets if x > 0)
    eq = pk = dd = 0.0; mL = cl = 0
    for x in nets:
        eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
        if x <= 0: cl += 1; mL = max(mL, cl)
        else: cl = 0
    yr = {}
    for r, x in zip(rs, nets): yr[r["yr"]] = round(yr.get(r["yr"], 0) + x, 1)
    mfin = sum(1 for r in rs if r["cj_t"] in MF)
    print(f"  {tag:<26} N{n:>4} hit3R {100*h/n:>5.1f}% WR {100*w/n:>5.1f}% NET {sum(nets):>7.1f} DD {dd:>6.1f} "
          f"stk-{mL} | {n/WEEKS:.2f}/sem | MF {mfin}/{len(MF)} prec {100*mfin/n:.0f}% | {yr}")
    return {"n": n, "hit": h / n, "stk": mL, "net": sum(nets), "mf": mfin}
print("\nENGINE SEQUENCIAL (porte V1.4g-RWS-A6):")
NB = [r for r in U if r["g_v5h"] != "BEAR" and r["g_knife"] == 0]
base = panel(NB, "não-BEAR (baseline)")
rws = [r for r in NB if rws15m(r)]
st1 = panel(rws, "RWS-15M sozinho")
# + estrutura de fundo (pool da Fase 2)
def struct(r):
    L = LEG.get(r["cj_t"], {})
    return (fv(r, "g_box96", .5) <= 0.45 and fv(r, "g_ema21_dist", 9) <= 0.2 and fv(r, "legpos60", 1) <= 0.35
            and fv(r, "g_sweep_depth", 0) >= 0.5 and L.get("h4_ema21_dist", 9) <= 0.5 and L.get("h4_retrace", 0) >= 0.3)
rws_struct = [r for r in rws if struct(r)]
st2 = panel(rws_struct, "RWS-15M & fundo-estrut")
json.dump({"rws_n": len(rws), "rws_hit": st1["hit"] if rws else None,
           "rws_struct_n": len(rws_struct), "rws_struct_hit": st2["hit"] if rws_struct else None,
           "medians_note": "sequenciais MF vs resto acima"},
          open(HERE / "results" / "rws_sequence_engine_20260705.json", "w"), indent=1)
print("OK → results/rws_sequence_engine_20260705.json")
