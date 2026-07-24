#!/usr/bin/env python3
"""ESTUDO DE DESFECHO DOS SINAIS JÁ EMITIDOS (Cris 2026-07-23) — camada de DADOS FRIOS do ground-truth.
NÃO reconstrói contexto/direção (isso é do dossiê E0 que o motor já consome). Apenas MEDE, para cada sinal
FRACO/FORTE que o motor ob_touch JÁ emitiu (shock_cycle.log), a excursão de preço REAL para a frente a partir
das barras 5M: quanto andou a favor (MFE) e contra (MAE) na direção do próprio sinal. Verdito = proxy
transparente (o árbitro final = os trades ideais que o Cris vai plotar). Reproduzível. py3.9.

Uso: python3 research/signal_forward_study_20260723.py [janela_min=90]
"""
import json, sys, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
REPO = Path(__file__).resolve().parents[1]
LOG = REPO / "my-strategy/core/price_shock/.shock_state/shock_cycle.log"
B5 = REPO / "my-strategy/core/bar_store/store/bars_5m.jsonl"
WIN_MIN = int(sys.argv[1]) if len(sys.argv) > 1 else 90

bars = [json.loads(l) for l in open(B5) if l.strip()]
bars.sort(key=lambda x: x["t"])


def price_at(ts):
    prior = [b for b in bars if b["t"] <= ts]
    return prior[-1]["c"] if prior else None


def fwd(ts, mins):
    return [b for b in bars if ts < b["t"] <= ts + mins * 60]


# --- recolha dos sinais já emitidos ---
sigs = []
for l in open(LOG):
    try: d = json.loads(l)
    except Exception: continue
    ot = d.get("ob_touch")
    if not ot: continue
    ts_iso = d.get("ts")
    try: ts = int(dt.datetime.fromisoformat(ts_iso).timestamp())
    except Exception: continue
    for z in (ot if isinstance(ot, list) else [ot]):
        if isinstance(z, dict) and z.get("q"):
            sigs.append({"ts": ts, "iso": ts_iso, **z})

# dedup por (zona,dir,q) dentro de 20min = 1 evento (re-disparos do mesmo toque)
sigs.sort(key=lambda s: s["ts"])
seen = {}; uniq = []
for s in sigs:
    k = (s.get("zone"), s.get("dir"), s.get("q"))
    if k in seen and s["ts"] - seen[k] < 20 * 60: continue
    seen[k] = s["ts"]; uniq.append(s)

# --- desfecho medido de cada sinal ---
rows = []
for s in uniq:
    entry = price_at(s["ts"])
    w = fwd(s["ts"], WIN_MIN)
    if entry is None or not w:
        continue
    hi = max(b["h"] for b in w); lo = min(b["l"] for b in w)
    if s["dir"] == "SHORT":
        mfe = entry - lo; mae = hi - entry
    else:
        mfe = hi - entry; mae = entry - lo
    # verdito proxy: WIN se favorável tradeável (>=15pts) e domina o adverso (>=1.5x); ok se >=10 e >adverso
    if mfe >= 15 and mfe >= 1.5 * max(mae, 1): verd = "WIN"
    elif mfe >= 10 and mfe > mae: verd = "ok"
    else: verd = "-"
    rows.append({**s, "entry": entry, "mfe": round(mfe, 1), "mae": round(mae, 1), "verd": verd})

# --- painel ---
hm = lambda ts: dt.datetime.fromtimestamp(ts, LX).strftime("%d/%m %H:%M")
print(f"=== ESTUDO DE DESFECHO · janela {WIN_MIN}min · {len(rows)} eventos (dedup 20min) ===\n")
print("--- FORTE (o que o motor tratou como sinal a sério) ---")
for r in rows:
    if r["q"] == "FORTE":
        print(f"  {hm(r['ts'])} {r['dir']:5} {str(r.get('mode',''))[:11]:11} zona {r.get('zone')} · MFE +{r['mfe']} / MAE {r['mae']} -> {r['verd']}")
print("\n--- FRACO que TERIA sido tradeável (favorável apesar do rótulo fraco) ---")
for r in rows:
    if r["q"] == "FRACO" and r["verd"] in ("WIN", "ok"):
        print(f"  {hm(r['ts'])} {r['dir']:5} {str(r.get('mode',''))[:11]:11} zona {r.get('zone')} · MFE +{r['mfe']} / MAE {r['mae']} -> {r['verd']} (era FRACO!)")


def agg(sel, name):
    g = [r for r in rows if sel(r)]
    if not g: return
    win = sum(1 for r in g if r["verd"] == "WIN"); okk = sum(1 for r in g if r["verd"] == "ok")
    amfe = sum(r["mfe"] for r in g) / len(g); amae = sum(r["mae"] for r in g) / len(g)
    print(f"  {name:20} N={len(g):3} · WIN {win} ({100*win/len(g):.0f}%) · ok {okk} · MFE med +{amfe:.1f} / MAE med {amae:.1f}")

print("\n=== AGREGADO ===")
agg(lambda r: r["q"] == "FORTE", "FORTE (todos)")
agg(lambda r: r["q"] == "FORTE" and r["dir"] == "SHORT", "FORTE SHORT")
agg(lambda r: r["q"] == "FRACO", "FRACO (todos)")
agg(lambda r: True, "TODOS")
print("\nNOTA: verdito = PROXY (MFE/MAE reais na direcao do sinal; sem SL/TP explicito no ob_touch).")
print("Arbitro final = trades ideais que o Cris vai plotar (camada-2 do ground-truth).")
