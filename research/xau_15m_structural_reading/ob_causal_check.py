#!/usr/bin/env python3
"""MEDIDOR B — VERIFICAÇÃO CAUSAL DO OB DETECTOR nos HTFs (prereg XAU_15M_HTF_ANCHOR_OB_PREREG.md).
Leitura DIRETA dos RAW 30M/1H do HD (zero primitives): para cada marca, o ÚLTIMO snapshot com
replay_current_date <= t mostra as zonas Custom OB v11 VIVAS naquele instante (semântica alive-at-T
nativa — causal por construção, sem reconstrução). MEDIDOR contínuo, sem cortes/votos.
Conjuntos: BULL 26 vs C-losers 6 (OB-1H) · RANGE 4 (OB-30M) · BEAR-set scorable (OB-1H e OB-30M).
Medidas por marca: n_zonas · inside (px dentro de zona) · dist_atr à zona mais próxima ABAIXO
(normalização ATR15 da marca). Scorabilidade: 30M/1H congelam 2026-05-25 (marcas depois = UNSCORABLE).
Trajetória/contexto: as zonas OB SÃO estado acumulado do indicador no HTF; leitura multi-fatorial
junto ao Medidor A (mapa HTF) — nunca eixo único de decisão. Sem entry/backtest."""
import json, gzip, sys, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0]/"xau_15m_structural_leg_engine"))
from f1_structural_leg_machine import Data
GT = HERE.parents[0]/"xau_15m_bb_nas_leonardo/results/catalog_manual_tags_20260707.json"
BASE = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD"
H1 = [f"{BASE}/1H/XAUUSD_60m_replay_2024-05-25_to_2025-05-25.jsonl.gz",
      f"{BASE}/1H/XAUUSD_60m_replay_2025-05-25_to_2025-11-25.jsonl.gz",
      f"{BASE}/1H/XAUUSD_60m_replay_2025-11-25_to_2026-05-25.jsonl.gz"]
M30 = [f"{BASE}/30M/XAUUSD_30m_replay_2024-05-25_to_2024-11-25.jsonl.gz",
       f"{BASE}/30M/XAUUSD_30m_replay_2024-11-25_to_2025-05-25.jsonl.gz",
       f"{BASE}/30M/XAUUSD_30m_replay_2025-05-25_to_2025-11-25.jsonl.gz",
       f"{BASE}/30M/XAUUSD_30m_replay_2025-11-25_to_2026-05-25.jsonl.gz"]
FREEZE = int(dt.datetime(2026, 5, 25).timestamp())
RANGE_DATES = {"2025-08-01", "2025-08-20", "2025-11-18", "2025-11-21"}
C_LOSERS = [("C1", "2025-09-16 22:00", 3691.44), ("C2", "2025-10-09 05:45", 4039.83),
            ("C3", "2025-10-19 22:00", 4259.23), ("C4", "2025-12-25 23:00", 4488.94),
            ("C5", "2026-01-13 13:30", 4617.97), ("C6", "2026-03-02 23:00", 5338.57)]

def ts(s): return int(dt.datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc).timestamp())

def ob_zones_at(files, marks):
    """marks = lista de (key, t). Devolve {key: [zonas Custom OB no último snapshot <= t]}.
    Uma passagem por ficheiro; snapshots monotónicos por replay_current_date."""
    marks = sorted(marks, key=lambda m: m[1])
    out = {k: None for k, _ in marks}
    last = None; mi = 0
    for f in files:
        with gzip.open(f, "rt", errors="replace") as fh:
            for ln in fh:
                try:
                    r = json.loads(ln)
                except Exception:
                    continue
                rt = r.get("replay_current_date")
                if rt is None:
                    continue
                while mi < len(marks) and rt > marks[mi][1]:
                    out[marks[mi][0]] = last; mi += 1
                if mi >= len(marks):
                    return out
                pb = r.get("pine_boxes") or []
                ob = next((s for s in pb if "Custom OB" in (s.get("name") or "")), None)
                if ob is not None:
                    last = ob.get("zones") or []
    while mi < len(marks):
        out[marks[mi][0]] = last; mi += 1
    return out

def measure(zones, px, a):
    if zones is None:
        return {"n_zonas": None, "inside": None, "dist_atr_below": None}
    inside = any(z["low"] <= px <= z["high"] for z in zones)
    below = [px-z["high"] for z in zones if z["high"] <= px]
    return {"n_zonas": len(zones), "inside": int(inside),
            "dist_atr_below": round(min(below)/a, 2) if below else None}

def main():
    D = Data()
    cat = json.load(open(GT))
    fundos = cat["notes"]["FUNDO"]
    bull = [x for x in fundos if x["date"] < "2026-03-01" and x["date"][:10] not in RANGE_DATES]
    rng = [x for x in fundos if x["date"][:10] in RANGE_DATES]
    bear = [x for x in fundos if x["date"] >= "2026-03-01"]
    inval = [x for x in cat["notes"]["INVALIDO"] if x["date"] >= "2026-03-01"]
    assert (len(bull), len(rng), len(bear)) == (26, 4, 12)
    assert len(inval) == 3, f"INVALIDO mar/2026 = {len(inval)} != 3"
    def atr_at(t):
        return D.ATR[bisect.bisect_right(D.TS, t)-1] or 5.0
    # marcas por fonte
    h1_marks, m30_marks, meta = [], [], {}
    def add(key, t, px, grp, tf):
        if t > FREEZE:
            meta[key] = {"grp": grp, "t": t, "px": px, "unscorable": True}; return
        meta[key] = {"grp": grp, "t": t, "px": px, "unscorable": False}
        (h1_marks if tf == "1H" else m30_marks).append((key, t))
    for x in bull: add(f"BULL_{x['date']}", x["t"], x["price"], "FUNDO_BULL", "1H")
    for cid, dstr, px in C_LOSERS: add(f"{cid}_{dstr}", ts(dstr), px, "C_LOSER", "1H")
    for x in bear: add(f"BEARH_{x['date']}", x["t"], x["price"], "FUNDO_BEAR_1H", "1H")
    for x in inval: add(f"INVH_{x['date']}", x["t"], x["price"], "INVALIDO_1H", "1H")
    for x in rng: add(f"RNG_{x['date']}", x["t"], x["price"], "FUNDO_RANGE_30M", "30M")
    for x in bear: add(f"BEARM_{x['date']}", x["t"], x["price"], "FUNDO_BEAR_30M", "30M")
    for x in inval: add(f"INVM_{x['date']}", x["t"], x["price"], "INVALIDO_30M", "30M")
    z1 = ob_zones_at(H1, h1_marks)
    z30 = ob_zones_at(M30, m30_marks)
    rows = []
    for key, m in sorted(meta.items(), key=lambda kv: (kv[1]["grp"], kv[1]["t"])):
        if m["unscorable"]:
            rows.append({"key": key, "grp": m["grp"], "verdict": "UNSCORABLE_HTF_FREEZE"}); continue
        zones = z1.get(key) if key in z1 else z30.get(key)
        rows.append({"key": key, "grp": m["grp"],
                     **measure(zones, m["px"], atr_at(m["t"]))})
    out = {"prereg": "XAU_15M_HTF_ANCHOR_OB_PREREG.md", "freeze": "2026-05-25",
           "rows": rows, "note": "MEDIDOR contínuo — sem cortes; leitura = READER; caminho = CRIS"}
    (HERE/"results/ob_causal_check_result.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    for r in rows:
        if r.get("verdict"):
            print(f"{r['grp']:>16} {r['key']:<28} UNSCORABLE"); continue
        print(f"{r['grp']:>16} {r['key']:<28} zonas {str(r['n_zonas']):>4} inside {r['inside']} distBelow {r['dist_atr_below']}")
    print("MEASURED_OK")

if __name__ == "__main__":
    main()
