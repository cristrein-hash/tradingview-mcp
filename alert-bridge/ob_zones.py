#!/usr/bin/env python3
"""CAMINHO DE LEITURA CANÓNICO das zonas OB Detector (Cris 2026-08-04: "tem que ser PERMANENTE, não podes
errar fluxo e caminho de leitura"). ÚNICA fonte de zonas estruturais = o OB Detector v11 REAL, lido do store
`pine_boxes_{tf}.json` (que o bar-store capta via MCP periodicamente) OU, on-demand, via MCP data_get_pine_boxes.
NUNCA aproximar/inferir/inventar zonas — foi esse o erro que custou trades em 04/08.

Uso: `read_ob_zones()` devolve as zonas reais por TF. Consumir isto ao construir/validar qualquer zona.
py3.9, sem dependências."""
import json, time
from pathlib import Path

BASE = Path(__file__).resolve().parent
STORE = BASE.parent / "my-strategy/core/bar_store/store"
OB_NAME = "OB Detector"            # substring do estudo (Custom OB Detector v11)


def _from_store(tf):
    """Zonas OB Detector do store pine_boxes_{tf}.json (captado via MCP pelo bar-store). None se ausente/stale."""
    f = STORE / f"pine_boxes_{tf}.json"
    try:
        d = json.loads(f.read_text())
        studies = (d.get("data") or {}).get("studies") or []
        for st in studies:
            if OB_NAME in st.get("name", ""):
                zones = [{"low": z["low"], "high": z["high"]} for z in st.get("zones", [])
                         if "low" in z and "high" in z]
                return {"zones": sorted(zones, key=lambda z: -z["high"]), "ts": d.get("ts"),
                        "age_s": int(time.time() - d["ts"]) if d.get("ts") else None, "src": f"store:{f.name}"}
    except Exception:
        pass
    return None


def read_ob_zones(tfs=("15", "60", "240", "1D")):
    """Zonas OB Detector REAIS por TF (caminho canónico). Consome o store; NUNCA aproxima."""
    out = {}
    for tf in tfs:
        z = _from_store(tf)
        if z:
            out[tf] = z
    return out


def zones_near(price, tfs=("15", "60", "240"), span=200):
    """Zonas OB reais a <=span pts do preço (as que importam agora). Ordenadas por proximidade."""
    seen = []
    for tf, blk in read_ob_zones(tfs).items():
        for z in blk["zones"]:
            mid = (z["low"] + z["high"]) / 2
            if abs(mid - price) <= span:
                seen.append({**z, "tf": tf, "side": "acima" if z["low"] > price else ("abaixo" if z["high"] < price else "dentro")})
    seen.sort(key=lambda z: abs((z["low"] + z["high"]) / 2 - price))
    # dedup por sobreposicao (mesma zona em TFs diferentes)
    uniq = []
    for z in seen:
        if not any(abs(z["low"] - u["low"]) < 5 and abs(z["high"] - u["high"]) < 5 for u in uniq):
            uniq.append(z)
    return uniq


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        # lê o store real; valida que devolve zonas OB do TF 15 e 60 (existem no store)
        z = read_ob_zones(("15", "60"))
        ok1 = isinstance(z, dict)
        ok2 = any(len(blk["zones"]) > 0 for blk in z.values()) if z else False
        for lab, ok in (("read_ob_zones devolve dict", ok1), (">=1 TF com zonas reais", ok2)):
            print(f"  [{'OK' if ok else 'FAIL'}] {lab}")
        print("selftest", "PASS" if (ok1 and ok2) else "FAIL")
        sys.exit(0 if (ok1 and ok2) else 1)
    # dump ao vivo
    z = read_ob_zones()
    for tf, blk in z.items():
        print(f"OB Detector {tf} (age {blk['age_s']}s, {blk['src']}):")
        for zz in blk["zones"]:
            print(f"   {zz['low']}-{zz['high']}")
