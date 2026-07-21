#!/usr/bin/env python3
"""Revisao COMPLETA dos sinais OB-touch + choque de hoje (Cris 2026-07-21): classifica SHORT/LONG pela
subida/descida real (como o check_ob_touch), reconstroi a qualidade pelo GATE (rejeicao p/ SHORT, reclaim
p/ LONG, ambos = excursao >=6 na direcao certa) e mede o desfecho (movimento do preco ~2h depois). FACTS-first,
reproduzivel. Le store+log (zero MCP)."""
import json, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
REPO = Path("/Users/cristrein/tradingview-mcp")
LOG = REPO / "my-strategy/core/price_shock/.shock_state/shock_cycle.log"
B5 = REPO / "my-strategy/core/bar_store/store/bars_5m.jsonl"
D = "2026-07-21"

b5 = [json.loads(l) for l in open(B5) if l.strip()]


def px_at(ts, off_min):
    """close da barra ~off_min minutos DEPOIS(+)/ANTES(-) de ts."""
    tgt = ts + off_min * 60
    if off_min >= 0:
        after = [x for x in b5 if x["t"] >= tgt]
        return after[0]["c"] if after else (b5[-1]["c"] if b5 else None)
    prior = [x for x in b5 if x["t"] <= tgt]
    return prior[-1]["c"] if prior else None


def extreme_after(ts, mins, lo=True):
    seg = [x for x in b5 if ts <= x["t"] <= ts + mins * 60]
    if not seg: return None
    return min(x["l"] for x in seg) if lo else max(x["h"] for x in seg)


rows, seen, shocks = [], {}, {}
for l in open(LOG):
    try: d = json.loads(l)
    except Exception: continue
    ts = dt.datetime.fromisoformat(d["ts"]).timestamp()
    if dt.datetime.fromtimestamp(ts, LX).strftime("%Y-%m-%d") != D: continue
    ob, px, exc, ed = d.get("ob_touch"), d.get("price"), d.get("excursion_pts"), d.get("dir")
    if ob and px is not None:
        for z in ob:
            if z in seen and ts - seen[z] < 1800: continue        # mesmo toque dentro de 30min = 1 evento
            seen[z] = ts
            pb = px_at(ts, -15)
            rising = pb is not None and px > pb
            side = "SHORT" if rising else "LONG"
            gate = (exc or 0) >= 6 and ((rising and ed == "BAIXA") or (not rising and ed == "ALTA"))
            q = "FRACO (gate falhou)" if not gate else "≥MÉDIO (gate ok, ver E0)"
            # desfecho: SHORT bom se caiu; LONG bom se subiu (janela 2h)
            fut = px_at(ts, 120)
            if side == "SHORT":
                out = f"preço {fut - px:+.0f}pts em 2h -> " + ("BOM (caiu)" if fut < px else "MAU (subiu contra)")
            else:
                out = f"preço {fut - px:+.0f}pts em 2h -> " + ("BOM (subiu)" if fut > px else "MAU (caiu contra)")
            rows.append((ts, side, z, px, exc, ed, q, out))
    if "SHOCK" in d.get("status", ""):
        k = (d.get("dir"), round((px or 0) / 8))
        if k not in shocks: shocks[k] = (ts, d.get("dir"), d.get("excursion_pts"), px)

print(f"=== SINAIS DE HOJE {D} (todos, classificados SHORT/LONG + qualidade + desfecho) ===")
for ts, side, z, px, exc, ed, q, out in sorted(rows):
    hm = dt.datetime.fromtimestamp(ts, LX).strftime("%H:%M")
    tag = "🔻" if side == "SHORT" else "🟢"
    print(f"  {hm} {tag} {side} zona {z} @ {px:.1f} · excursao {exc}pts {ed} · {q}\n           desfecho: {out}")
print(f"\n=== CHOQUES ({len(shocks)}) ===")
for ts, dr, e, px in sorted(shocks.values()):
    hm = dt.datetime.fromtimestamp(ts, LX).strftime("%H:%M")
    print(f"  {hm} CHOQUE {dr} {e}pts @ {px}")
n_short = sum(1 for r in rows if r[1] == "SHORT"); n_long = sum(1 for r in rows if r[1] == "LONG")
print(f"\nTOTAL: {len(rows)} OB-touch ({n_short} SHORT, {n_long} LONG) + {len(shocks)} choques")
