#!/usr/bin/env python3
"""FREEZE dos inputs para o cruzamento do ground-truth (Cris 2026-07-23).
Congela num diretório estável os DOIS inputs de que o cruzamento precisa, para não derivarem enquanto o store
ao vivo cresce:
  1. signals_measured.json  — os 60 sinais FRACO/FORTE já emitidos, com zona/dir/q + MFE/MAE/verdito medidos.
  2. bars_5m_window.jsonl   — as barras 5M da janela (do 1o sinal -30min ao ultimo +120min), fatia estavel.
Quando o Cris plotar os trades ideais, o joiner cruza a marcacao dele (ts/preco) contra estes dois ficheiros.
Reproduzivel. py3.9.
"""
import json, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
REPO = Path(__file__).resolve().parents[1]
LOG = REPO / "my-strategy/core/price_shock/.shock_state/shock_cycle.log"
B5 = REPO / "my-strategy/core/bar_store/store/bars_5m.jsonl"
OUT = REPO / "research/groundtruth_20260723"; OUT.mkdir(exist_ok=True)
WIN_MIN = 90

bars = [json.loads(l) for l in open(B5) if l.strip()]
bars.sort(key=lambda x: x["t"])
price_at = lambda ts: next((b["c"] for b in reversed(bars) if b["t"] <= ts), None)
fwd = lambda ts, m: [b for b in bars if ts < b["t"] <= ts + m * 60]

# sinais ja emitidos
sigs = []
for l in open(LOG):
    try: d = json.loads(l)
    except Exception: continue
    ot = d.get("ob_touch")
    if not ot: continue
    try: ts = int(dt.datetime.fromisoformat(d.get("ts")).timestamp())
    except Exception: continue
    for z in (ot if isinstance(ot, list) else [ot]):
        if isinstance(z, dict) and z.get("q"):
            sigs.append({"ts": ts, "iso": d.get("ts"), **z})
sigs.sort(key=lambda s: s["ts"])
seen = {}; uniq = []
for s in sigs:
    k = (s.get("zone"), s.get("dir"), s.get("q"))
    if k in seen and s["ts"] - seen[k] < 20 * 60: continue
    seen[k] = s["ts"]; uniq.append(s)

measured = []
for s in uniq:
    entry = price_at(s["ts"]); w = fwd(s["ts"], WIN_MIN)
    if entry is None or not w: continue
    hi = max(b["h"] for b in w); lo = min(b["l"] for b in w)
    mfe, mae = (entry - lo, hi - entry) if s["dir"] == "SHORT" else (hi - entry, entry - lo)
    if mfe >= 15 and mfe >= 1.5 * max(mae, 1): verd = "WIN"
    elif mfe >= 10 and mfe > mae: verd = "ok"
    else: verd = "-"
    measured.append({"iso_lisboa": dt.datetime.fromtimestamp(s["ts"], LX).strftime("%Y-%m-%d %H:%M"),
                     "ts": s["ts"], "dir": s["dir"], "q": s["q"], "mode": s.get("mode"),
                     "zone": s.get("zone"), "entry": round(entry, 1),
                     "mfe": round(mfe, 1), "mae": round(mae, 1), "verd": verd})

# janela de barras estavel (1o sinal -30min .. ultimo +120min)
lo_t = min(s["ts"] for s in uniq) - 30 * 60
hi_t = max(s["ts"] for s in uniq) + 120 * 60
window = [b for b in bars if lo_t <= b["t"] <= hi_t]

(OUT / "signals_measured.json").write_text(json.dumps(measured, ensure_ascii=False, indent=1))
with open(OUT / "bars_5m_window.jsonl", "w") as fh:
    for b in window:
        fh.write(json.dumps(b, ensure_ascii=False) + "\n")

span = lambda t: dt.datetime.fromtimestamp(t, LX).strftime("%d/%m %H:%M")
(OUT / "README.md").write_text(
    f"# Ground-truth inputs CONGELADOS · {dt.datetime.fromtimestamp(hi_t, LX).strftime('%Y-%m-%d')}\n\n"
    f"Snapshot estavel para cruzar com os trades ideais do Cris (camada-2).\n\n"
    f"- **signals_measured.json** — {len(measured)} sinais FRACO/FORTE ja emitidos, com MFE/MAE/verdito (janela {WIN_MIN}min).\n"
    f"- **bars_5m_window.jsonl** — {len(window)} barras 5M, {span(lo_t)} -> {span(hi_t)} (Lisboa).\n\n"
    f"## Como cruzar\n"
    f"Quando o Cris plotar os trades ideais (via chart/MCP pine_boxes/labels), o joiner alinha cada trade dele\n"
    f"por timestamp/preco contra `bars_5m_window.jsonl` e compara com o que o motor emitiu em `signals_measured.json`:\n"
    f"- trade ideal do Cris SEM sinal nosso no mesmo instante = MISS (o motor nao viu).\n"
    f"- sinal nosso FRACO num instante que o Cris marcou como trade bom = MISLABEL (rebaixou um bom).\n"
    f"- sinal nosso FORTE onde o Cris NAO marcou trade = FALSO-FORTE.\n"
    f"Dai sai o ground-truth: que leitura teria dado o rotulo certo.\n")

print(f"CONGELADO em {OUT}/")
print(f"  signals_measured.json : {len(measured)} sinais")
print(f"  bars_5m_window.jsonl  : {len(window)} barras · {span(lo_t)} -> {span(hi_t)} Lisboa")
print(f"  README.md")
