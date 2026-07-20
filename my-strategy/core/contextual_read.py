#!/usr/bin/env python3
"""LEITURA CONTEXTUAL COMPLETA — a ÚNICA leitura de contexto (Cris 2026-07-20, "resolva a bagunça").

Carrega TODOS os indicadores que o store já coleta, por TF, numa vista única e organizada. É a peça central
do CONTEXTUAL_READ_PROTOCOL: antes de QUALQUER trabalho de contexto/zona/nível/análise/decisão, corre-se ISTO
— nunca um subconjunto ad-hoc, nunca invenção. Fonte = store (pine_boxes + study_values + bars), zero MCP.

Indicadores (inventário FIXO, o que o chart tem):
  ZONAS (pine_boxes): Custom OB Detector v11 · Smart Money Concepts · HTF Power of Three · Sessions
  VALORES (study_values): RSI(+MA) · DMI(ADX/+DI/-DI) · SVP(Up/Down/Total) · NAS(RSI/dist/sinais) ·
                          Market Order Bubbles · Choppiness · Volume · SMC PlotCandle
TFs: 1D · 4H(240) · 1H(60) · 15M · 5M.

Uso: python3 contextual_read.py            (imprime a vista completa)
     from contextual_read import read_all  (devolve o dict completo)"""
import json, sys, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
STORE = Path(__file__).resolve().parent / "bar_store/store"
CRP_TOKEN = Path(__file__).resolve().parent / ".crp_state.json"   # prova de "li TODOS os indicadores" (guard)
TFS = [("1D", "1D"), ("4H", "240"), ("1H", "60"), ("15M", "15"), ("5M", "5")]
BARS = {"1D": "bars_1d.jsonl", "15": "bars_15m.jsonl", "5": "bars_5m.jsonl"}   # 60/240 = RAW rev


def _num(s):
    """'4,007.74' / '−0.48' / '29.5 K' -> float (ou None)."""
    if isinstance(s, (int, float)): return float(s)
    t = str(s).replace(",", "").replace("−", "-").replace("–", "-").strip()
    mult = 1
    if t.endswith("K"): mult, t = 1000, t[:-1].strip()
    if t.endswith("M"): mult, t = 1_000_000, t[:-1].strip()
    try: return float(t) * mult
    except Exception: return None


def _load(f):
    try: return json.loads((STORE / f).read_text())
    except Exception: return {}


def _price():
    for bf in ("bars_5m.jsonl", "bars_15m.jsonl"):
        try:
            rows = [json.loads(x) for x in (STORE / bf).read_text().splitlines() if x.strip()]
            if rows: return rows[-1]["c"]
        except Exception: pass
    return None


def _zones(res):
    d = _load(f"pine_boxes_{res}.json").get("data") or {}
    out = {}
    for s in d.get("studies") or []:
        nm = s.get("name") or "?"
        zs = [(z.get("high"), z.get("low")) for z in (s.get("zones") or []) if z.get("high") and z.get("low")]
        if zs: out.setdefault(nm, []).extend(zs)
    return out


def _values(res):
    d = _load(f"study_values_{res}.json").get("data") or {}
    out = {}
    for s in d.get("studies") or []:
        out[s.get("name") or "?"] = {k: _num(v) for k, v in (s.get("values") or {}).items()}
    return out


def read_all():
    px = _price()
    ctx = {"ts": int(dt.datetime.now(dt.timezone.utc).timestamp()), "price": px, "tf": {}}
    for label, res in TFS:
        z = _zones(res); v = _values(res)
        ctx["tf"][label] = {"zones": z, "values": v}
    try: CRP_TOKEN.write_text(json.dumps({"ts": ctx["ts"], "price": ctx["price"]}))   # marca leitura completa feita
    except Exception: pass
    return ctx


def _short(nm):
    for k in ("OB Detector", "Smart Money", "HTF Power", "Sessions", "Volume Profile",
              "Directional", "Relative Strength", "Choppiness", "NAS", "Bubbles"):
        if k.lower() in nm.lower(): return k
    return nm[:16]


def print_view():
    ctx = read_all(); px = ctx["price"]
    print(f"═══ LEITURA CONTEXTUAL COMPLETA · {dt.datetime.now(LX):%H:%M Lisboa} · preço {px} ═══")
    for label, _ in TFS:
        t = ctx["tf"][label]
        print(f"\n[{label}]")
        # ZONAS — mais próximas do preço primeiro; marca a que CONTÉM o preço
        for nm, zs in t["zones"].items():
            if "session" in nm.lower(): continue        # Sessions = ruído visual, salta no print
            zz = sorted(zs, key=lambda z: abs((z[0] + z[1]) / 2 - (px or 0)))[:4]
            tag = []
            for hi, lo in zz:
                mark = "◄PREÇO" if px and lo <= px <= hi else ("↑" if px and lo > px else "↓")
                tag.append(f"{lo:.1f}-{hi:.1f}{mark}")
            print(f"  {_short(nm):18} {' · '.join(tag)}")
        # VALORES-chave
        vv = t["values"]
        def g(study, key):
            for nm, d in vv.items():
                if study.lower() in nm.lower() and key in d: return d[key]
            return None
        line = []
        rsi, rma = g("Relative", "RSI"), g("Relative", "RSI-based MA")
        if rsi is not None: line.append(f"RSI {rsi:.1f}/{rma:.1f}" if rma else f"RSI {rsi:.1f}")
        adx = g("Directional", "ADX")
        if adx is not None: line.append(f"ADX {adx:.0f} (+DI {g('Directional','+DI'):.0f}/-DI {g('Directional','-DI'):.0f})")
        chop = g("Choppiness", "CHOP")
        if chop is not None: line.append(f"CHOP {chop:.0f}")
        up, dn = g("Volume Profile", "Up"), g("Volume Profile", "Down")
        if up is not None: line.append(f"SVP U/D {up/1000:.0f}K/{dn/1000:.0f}K")
        nrsi, ndist = g("NAS", "NAS_RSI"), g("NAS", "NAS_DISTANCE_FROM_EMA_ATR")
        if ndist is not None: line.append(f"NASdistEMA {ndist:+.2f}")
        smc = g("Smart Money", "PlotCandle")
        if smc is not None: line.append(f"SMC {smc:.1f}")
        if line: print(f"  {'IND':18} {' · '.join(line)}")


if __name__ == "__main__":
    print_view()
