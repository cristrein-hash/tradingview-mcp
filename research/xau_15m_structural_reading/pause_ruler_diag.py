#!/usr/bin/env python3
"""SANITY_PROBE — diagnóstico factual do gate 0/10: para cada vela-foco, a zona de pausa mais
próxima (banda, estado na vela, gap em ATR, known antes?). Sem tuning, sem métricas — factos."""
import json, sys, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/"research/xau_15m_structural_leg_engine"))
from f1_structural_leg_machine import Data
import pause_ruler_gate as G
GT = REPO/"research/xau_15m_bb_nas_leonardo/results/catalog_manual_tags_20260707.json"

def main():
    D = Data()
    # reconstruir zonas exatamente como no gate (importa o walk copiando o main até zones)
    # para simplicidade: reexecutar o gate main capturando zones via monkeypatch do _publish? —
    # em vez disso, repetir o walk chamando G.main é pesado; replico via G apenas se necessário.
    # Aqui: leio o result e recomputo zonas com o MESMO código (execução única do walk).
    import io, contextlib
    buf = io.StringIO()
    zones_ref = []
    orig = G._publish
    def cap(zones, leg_zone_ids, p, i, t, a):
        orig(zones, leg_zone_ids, p, i, t, a)
        zones_ref.append(zones[-1])
    G._publish = cap
    with contextlib.redirect_stdout(buf):
        G.main()
    zones = zones_ref
    cat = json.load(open(GT))
    fundos = sorted(cat["notes"]["FUNDO"], key=lambda x: x["t"])
    for nn, f in enumerate(fundos, 1):
        if nn not in G.FOCO: continue
        t, px = f["t"], f["price"]
        i = bisect.bisect_right(D.TS, t)-1; a = D.ATR[i] or 5.0
        best = None
        for z in zones:
            if z["known_at"] >= t: continue
            gap = max(z["lo"]-px, px-z["hi"], 0)/a
            end = min(x for x in (z["inv_at"], z["kill_at"], z["sup_at"], t+1) if x is not None)
            estado = "VIVA" if end > t else ("INV" if z["inv_at"] and z["inv_at"] <= t else
                                             "KILL" if z["kill_at"] and z["kill_at"] <= t else "SUP")
            item = {"gap": round(gap, 2), "band": [round(z["lo"], 1), round(z["hi"], 1)],
                    "estado": estado,
                    "known": dt.datetime.utcfromtimestamp(z["known_at"]).strftime("%m-%d %H:%M")}
            if best is None or gap < best["gap"]: best = item
        print(f"#{nn:>2} {f['date']} px{px:.0f}: mais próxima -> {best}")

if __name__ == "__main__":
    main()
