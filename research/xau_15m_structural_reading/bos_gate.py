#!/usr/bin/env python3
"""GATE BOS × 10 FALHAS BULL (ordem Cris 2026-07-10). Estrutura = eventos BOS do SMC LuxAlgo lidos
DIRETO do RAW 15M do HD (first-appearance por id, re-seed por bloco, anti-flood >10/snapshot —
maquinaria canónica; known_at = replay time do snapshot em que o label aparece). Zero primitives.
BOS de ALTA (causal): close do bar do known_at > preço do label (swing high ROMPIDO para cima).
Zona = polaridade do high rompido, geometria do reparo (corpos ±4 barras do swing bar; largura
[0,7, 2,5]·ATR; teto = high+0,1·ATR). Vida: invalidação tolerante (fecho >0,5·ATR abaixo OU 2
fechos consecutivos). SEM filtro de autoridade (REJECTED). Gate: as 10 velas BULL falhadas +
densidade zonas/semana (trava de sujeira, referência escada ~1/sem). Leitura de trajetória
estrutural (evento de rompimento + corpos + vida), não snapshot. Sem entry/outcome/backtest."""
import json, gzip, sys, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/"research/xau_15m_structural_leg_engine"))
from f1_structural_leg_machine import Data
GT = REPO/"research/xau_15m_bb_nas_leonardo/results/catalog_manual_tags_20260707.json"
BASE = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M"
BLOCKS = ["XAUUSD_15m_replay_2024-05-25_to_2024-08-25.jsonl.gz",
          "XAUUSD_15m_replay_2024-08-25_to_2024-11-25.jsonl.gz",
          "XAUUSD_15m_replay_2024-11-25_to_2025-02-25.jsonl.gz",
          "XAUUSD_15m_replay_2025-02-25_to_2025-05-25.jsonl.gz",
          "XAUUSD_15m_replay_2025-05-25_to_2025-08-25.jsonl.gz",
          "XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz",
          "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
          "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
          "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
FALHAS = {8, 9, 11, 12, 13, 15, 17, 27, 29, 30}
BODY_W, MIN_W, MAX_W, BRK = 4, 0.7, 2.5, 0.5
EV_CACHE = HERE/"results/smc_bos_events.jsonl"

def extract_events():
    if EV_CACHE.exists():
        return [json.loads(l) for l in open(EV_CACHE)]
    events = []
    for bn in BLOCKS:
        seeded = False; max_id = -1
        with gzip.open(f"{BASE}/{bn}", "rt", errors="replace") as fh:
            for ln in fh:
                try: r = json.loads(ln)
                except Exception: continue
                rt = r.get("replay_current_date")
                pl = r.get("pine_labels") or []
                smc = next((s for s in pl if "Smart Money" in (s.get("name") or "")), None)
                if smc is None or rt is None: continue
                labs = smc.get("labels") or []
                if not labs: continue
                if not seeded:
                    max_id = max(l0["id"] for l0 in labs); seeded = True; continue
                new = [l0 for l0 in labs if l0["id"] > max_id]
                if not new: continue
                if len(new) > 10:            # anti-flood (init/overflow)
                    max_id = max(l0["id"] for l0 in labs); continue
                for l0 in new:
                    if "BOS" in (l0.get("text") or ""):
                        events.append({"known_at": rt, "price": l0["price"], "text": l0["text"],
                                       "size": l0.get("size"), "tc": l0.get("textColor")})
                max_id = max(l0["id"] for l0 in labs)
    with open(EV_CACHE, "w") as fh:
        for e in events: fh.write(json.dumps(e)+"\n")
    return events

def main():
    D = Data()
    n = len(D.TS)
    events = extract_events()
    # ORDEM CRIS: apenas BOS de LINHA CONTÍNUA (swing structure, size=='small'); internal fora
    events = [e for e in events if e.get("size") == "small"]
    # BOS de ALTA: close no known_at > preço do label
    zones = []
    for e in events:
        i = bisect.bisect_right(D.TS, e["known_at"])-1
        if i < 400 or i >= n: continue
        if D.C[i] <= e["price"]: continue          # não é rompimento para cima
        a = D.ATR[i] or 5.0
        # swing bar: barra mais recente antes de i cujo HIGH ~= preço do label
        sw = None
        for k in range(i, max(0, i-300), -1):
            if abs(D.H[k]-e["price"]) <= 0.02*a+0.05:
                sw = k; break
        if sw is None: continue
        a0, b0 = max(0, sw-BODY_W), min(n-1, sw+BODY_W)
        lo = min(D.C[a0:b0+1]); hi = e["price"]+0.1*a
        if (hi-lo) < MIN_W*a: lo = hi-MIN_W*a
        if (hi-lo) > MAX_W*a: lo = hi-MAX_W*a
        zones.append({"id": f"BOS{len(zones):05d}", "lo": lo, "hi": hi,
                      "swing_px": e["price"], "known_at": e["known_at"],
                      "inv_at": None, "pr": 0})
    # vida (tolerante) — passagem única
    for i in range(n):
        c, a, t = D.C[i], D.ATR[i] or 5.0, D.TS[i]
        for z in zones:
            if z["inv_at"] is not None or t < z["known_at"]: continue
            beyond = (z["lo"]-c)/a
            if beyond > 0:
                z["pr"] += 1
                if beyond > BRK or z["pr"] >= 2: z["inv_at"] = t+900
            else:
                z["pr"] = 0
    # gate das 10
    cat = json.load(open(GT))
    fundos = sorted(cat["notes"]["FUNDO"], key=lambda x: x["t"])
    rows = []
    for nn, f in enumerate(fundos, 1):
        if nn not in FALHAS: continue
        t, px = f["t"], f["price"]
        hit = None
        for z in zones:
            if z["known_at"] >= t: continue
            if z["inv_at"] is not None and z["inv_at"] <= t: continue
            if z["lo"] <= px <= z["hi"]:
                hit = {"id": z["id"], "band": [round(z["lo"], 1), round(z["hi"], 1)],
                       "swing": round(z["swing_px"], 1),
                       "idade_h": round((t-z["known_at"])/3600, 1)}
                break
        rows.append({"n": nn, "date": f["date"], "status": "COBERTO_BOS" if hit else "FALHA",
                     "zona": hit})
    # densidade (trava): zonas/semana no período total com macro BULL
    weeks = set()
    for z in zones:
        weeks.add(dt.datetime.utcfromtimestamp(z["known_at"]).strftime("%G-W%V"))
    span_w = (D.TS[-1]-D.TS[400])/(7*86400)
    out = {"n_eventos_bos_raw": len(events), "n_zonas_bos_alta": len(zones),
           "densidade_por_semana_total": round(len(zones)/span_w, 2),
           "referencia_escada": "~1/sem em markup",
           "gate_10": rows,
           "cobertos": sum(1 for r in rows if r["status"] == "COBERTO_BOS")}
    (HERE/"results/bos_gate_result.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    for r in rows:
        z = r["zona"]
        print(f"#{r['n']:>2} {r['date']} {r['status']:<12} " +
              (f"{z['id']} banda {z['band']} swing {z['swing']} idade {z['idade_h']}h" if z else "—"))
    print(json.dumps({k: out[k] for k in ('n_eventos_bos_raw', 'n_zonas_bos_alta',
          'densidade_por_semana_total', 'cobertos')}, ensure_ascii=False))
    print("BOS_GATE_OK")

if __name__ == "__main__":
    main()
