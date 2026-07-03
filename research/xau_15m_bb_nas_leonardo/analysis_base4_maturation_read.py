#!/usr/bin/env python3
"""LEITURA DE MATURAÇÃO da base #4 FINAL (N435) — winner vs loser, multi-fatorial, por EPISÓDIO.
EXPLORATÓRIO/CARACTERIZAÇÃO (não validação; sem OOS por cânone; nenhum gate novo é 'aprovado' aqui).

Executa o engine aprovado real (exec) e, sobre os MESMOS trades/séries, mede lentes contextuais:
  A) ENTRADA TARDIA (sensação Cris): lateness = (entry − flush_low)/ATR; extensão vs EMA21; R por bucket.
  B) SL APERTADO (sensação Cris): losers com recuperação pós-stop (MFE forward ≥ +1R/+2R do entry
     original em ≤96 barras) = stop prematuro; contrafactual painel com SL pad −0.15/−0.30 ATR.
  C) SUPPLY OVERHEAD (padrão visual dos prints / família A do L2): room_above = (max high 96b − entry)/ATR.
  D) EPISÓDIO (cânone): cluster de entradas ≤8 barras; stops múltiplos no mesmo episódio falho.
  E) POSIÇÃO NA PERNA/TRAJETÓRIA: pos20, rsi_cj, dist ao topo recente; por regime v5h e por ano.
  F) Slice Cris-BEAR-2026 (t ≥ 2026-01-29): mini-painel da zona de divergência v5×Cris.
Checklist anti-miopia: multi-fatorial ✓ · trajetória ✓ · dois objetivos (preservar runner E cortar loser) ✓ ·
feature set das primitives ✓ · leitura convergente, não single-axis-gate ✓.
"""
import sys, json, math
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
ns = {"__name__": "engine_exec", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile(open(HERE / "engine_substrate4_v5_hourcausal.py").read(),
             "engine_substrate4_v5_hourcausal.py", "exec"), ns)
cand, ROWS, PRIMK, letrun = ns["cand"], ns["ROWS"], ns["PRIMK"], ns["letrun"]

sel = sorted([c for c in cand if c["v5h"] != "BEAR"], key=lambda z: z["cj_t"])
assert len(sel) == 435 and abs(sum(c["R"] for c in sel) - 291.5) < 0.5

rmap = {}
for r in ROWS: rmap.setdefault(r["cj_t"], r)

def keyseek(bar, *names):
    for n in names:
        if n in bar: return bar[n]
    return None

T = []
for gid, c in enumerate(sel, 1):
    r = rmap[c["cj_t"]]; s = PRIMK[r["block"]]["series"]
    tm = {b["t"]: i for i, b in enumerate(s)}
    p, cj = tm[r["t"]], tm[r["cj_t"]]
    atr = s[p]["atr"] or s[cj]["atr"]
    entry = s[cj]["c"]; flush = min(x["l"] for x in s[p:cj + 1]); sl = flush - 0.1 * atr
    risk = entry - sl
    ema = keyseek(s[cj], "ema21", "ema")
    hi96 = max(x["h"] for x in s[max(0, cj - 95):cj + 1])
    lo20 = min(x["l"] for x in s[max(0, cj - 19):cj + 1]); hi20 = max(x["h"] for x in s[max(0, cj - 19):cj + 1])
    # walk p/ MFE + resolução + recuperação pós-stop
    HZ = 480; stop_j = None; mfe = 0.0
    end = min(cj + HZ, len(s) - 1)
    for j in range(cj + 1, end + 1):
        mfe = max(mfe, (s[j]["h"] - entry) / risk)
        if stop_j is None and s[j]["l"] <= sl:
            stop_j = j
            break
    rec1 = rec2 = None
    if stop_j is not None:
        m2 = 0.0
        for j in range(stop_j + 1, min(stop_j + 97, len(s))):
            m2 = max(m2, (s[j]["h"] - entry) / risk)
        rec1, rec2 = m2 >= 1.0, m2 >= 2.0
    hour = dt.datetime.utcfromtimestamp(c["cj_t"]).hour
    T.append({"gid": gid, "t": c["cj_t"], "yr": c["yr"], "reg": c["v5h"], "R": c["R"], "win": c["R"] > 0,
              "risk_atr": risk / atr, "lateness": (entry - flush) / atr,
              "ext_ema": ((entry - ema) / atr) if ema else None,
              "room_above": (hi96 - entry) / atr,
              "pos20": (entry - lo20) / ((hi20 - lo20) or atr),
              "rsi": s[cj].get("rsi") or 50, "mfe": round(mfe, 2),
              "stopped": stop_j is not None, "rec1": rec1, "rec2": rec2, "hour": hour,
              "cj": cj, "block": r["block"], "sl": sl, "entry": entry, "atr": atr, "p": p})

W = [t for t in T if t["win"]]; L = [t for t in T if not t["win"]]

def med(xs):
    xs = sorted(x for x in xs if x is not None)
    return xs[len(xs) // 2] if xs else None

def panel(rows, tag):
    R = [x["R"] for x in rows]; n = len(R)
    if not n: print(f"{tag}: vazio"); return
    sm = sum(R); w = sum(1 for x in R if x > 0); eq = pk = dd = 0
    for x in R: eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
    mL = mW = cl = cw = 0
    for x in R:
        if x > 0: cw += 1; cl = 0
        else: cl += 1; cw = 0
        mW = max(mW, cw); mL = max(mL, cl)
    py = {y: round(sum(x["R"] for x in rows if x["yr"] == y), 1) for y in (2024, 2025, 2026)}
    print(f"{tag:<34} N{n:>4} WR{100*w/n:>5.1f}% run{sum(1 for x in R if x>=3):>3} | sumR{sm:>7.1f} avgR{sm/n:>6.3f} "
          f"DD{dd:>6.1f} r/DD{abs(sm/dd) if dd<0 else 99:>5.2f} streak-{mL}/+{mW} | yr {py[2024]}/{py[2025]}/{py[2026]}")

print("\n========== A) LENTES W vs L (medianas) ==========")
for k in ("lateness", "risk_atr", "ext_ema", "room_above", "pos20", "rsi", "mfe"):
    print(f"{k:<12} W={med([t[k] for t in W])!r:>8}  L={med([t[k] for t in L])!r:>8}")

print("\n========== A2) ENTRADA TARDIA — R por bucket de lateness ==========")
for lo, hi in [(0, 0.8), (0.8, 1.2), (1.2, 1.8), (1.8, 99)]:
    b = [t for t in T if lo <= t["lateness"] < hi]
    if b: print(f"lateness [{lo},{hi}): N{len(b):>3} WR{100*sum(t['win'] for t in b)/len(b):>5.1f}% "
                f"avgR{sum(t['R'] for t in b)/len(b):+.3f} runners{sum(1 for t in b if t['R']>=3)}")

print("\n========== B) SL APERTADO — losers com recuperação pós-stop ==========")
stopped = [t for t in L if t["stopped"]]
print(f"losers={len(L)} · stopped={len(stopped)} · rec>=+1R pós-stop: {sum(1 for t in stopped if t['rec1'])} "
      f"({100*sum(1 for t in stopped if t['rec1'])/max(1,len(stopped)):.0f}%) · rec>=+2R: "
      f"{sum(1 for t in stopped if t['rec2'])} ({100*sum(1 for t in stopped if t['rec2'])/max(1,len(stopped)):.0f}%)")
print("contrafactual SL pad (mesmos 435, letrun re-executado):")
for pad in (0.0, 0.15, 0.30):
    rows = []
    for t in T:
        s = PRIMK[t["block"]]["series"]
        R = letrun(s, t["cj"], t["entry"], t["sl"] - pad * t["atr"], t["atr"])
        rows.append({"R": R if R is not None else t["R"], "yr": t["yr"], "win": (R or 0) > 0})
    panel(rows, f"  SL flush-0.1ATR - pad {pad:.2f}ATR")

print("\n========== C) SUPPLY OVERHEAD — R por bucket de room_above ==========")
for lo, hi in [(0, 0.5), (0.5, 1.5), (1.5, 3.0), (3.0, 99)]:
    b = [t for t in T if lo <= t["room_above"] < hi]
    if b: print(f"room_above [{lo},{hi}): N{len(b):>3} WR{100*sum(t['win'] for t in b)/len(b):>5.1f}% "
                f"avgR{sum(t['R'] for t in b)/len(b):+.3f} runners{sum(1 for t in b if t['R']>=3)}")

print("\n========== D) EPISÓDIOS (cluster ≤8 barras = 2h) ==========")
eps = []; cur = [T[0]]
for a, b in zip(T, T[1:]):
    if b["t"] - a["t"] <= 8 * 900: cur.append(b)
    else: eps.append(cur); cur = [b]
eps.append(cur)
multi = [e for e in eps if len(e) > 1]
fail_ep = [e for e in eps if sum(t["R"] for t in e) <= -1.5]
print(f"episódios={len(eps)} · multi-entrada={len(multi)} · episódios-falha (sumR<=-1.5)={len(fail_ep)} "
      f"(R desperdiçado em stops extra dos multi: {sum(sum(x['R'] for x in e[1:] if x['R']<=0) for e in multi):.1f})")
print(f"1ª entrada do episódio: WR {100*sum(1 for e in eps if e[0]['win'])/len(eps):.1f}% · "
      f"entradas 2+: WR {100*sum(t['win'] for e in multi for t in e[1:])/max(1,sum(len(e)-1 for e in multi)):.1f}%")

print("\n========== E) POR REGIME v5h / HORA ==========")
for rg in ("BULL", "RANGE"):
    panel([t for t in T if t["reg"] == rg], f"  regime {rg}")
buck = {}
for t in T: buck.setdefault(t["hour"] // 4, []).append(t)
for h in sorted(buck):
    b = buck[h]
    print(f"  hora UTC {h*4:02d}-{h*4+3:02d}: N{len(b):>3} WR{100*sum(t['win'] for t in b)/len(b):>5.1f}% avgR{sum(t['R'] for t in b)/len(b):+.3f}")

print("\n========== F) SLICE CRIS-BEAR-2026 (t >= 2026-01-29) ==========")
cut = int(dt.datetime(2026, 1, 29, tzinfo=dt.timezone.utc).timestamp())
panel([t for t in T if t["t"] >= cut], "  dentro do BEAR-Cris (v5 deixou passar)")
panel([t for t in T if t["t"] < cut], "  antes do BEAR-Cris")

print("\n========== PAINEL BASE (controle) ==========")
panel(T, "BASE #4 N435")
json.dump(T, open(HERE / "base4_maturation_features.json", "w"))
print("features salvas: base4_maturation_features.json")
