#!/usr/bin/env python3
"""AUDITORIA READ-ONLY #2 — procura POC/VAL/VAH como SAIDA do indicador LuxAlgo SVP no RAW (study_values /
pine_lines / pine_labels), que seria RAW_ORIGINAL_OK (saida plotada as-of-bar), NAO derivado. Inspeciona um
registro proximo das datas dos episodios. Tambem dump completo de session_vp.last3 + n. NAO fabrica nada.
Verified at: 2026-06-23."""
import gzip, json, datetime as dt

SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
# datas-alvo dos episodios FUEL/WALL (2023-2025)
TARGETS = ["2023-03-08", "2023-03-09", "2025-09-28", "2022-", "2021-"]


def jshort(v, n=300):
    s = json.dumps(v, ensure_ascii=False)
    return s[:n] + (" …" if len(s) > n else "")


def main():
    seen = 0
    with gzip.open(SVP, "rt") as fh:
        for line in fh:
            if "2023-03-08" not in line and "2023-03-09" not in line and "2025-09-28" not in line:
                continue
            rec = json.loads(line)
            cdt = rec.get("replay_current_dt", "")
            seen += 1
            print("=" * 80)
            print(f"REGISTRO @ {cdt}  bar_index={rec.get('bar_index')}")
            # 1. study_values — procura LuxAlgo VP / POC / VAH / VAL
            sv = rec.get("study_values") or {}
            print("\n  study_values STUDIES:", list(sv.keys()) if isinstance(sv, dict) else type(sv).__name__)
            if isinstance(sv, dict):
                for sname, payload in sv.items():
                    low = sname = str(sname := sname).lower()
                    keys = list(payload.keys()) if isinstance(payload, dict) else payload
                    blob = json.dumps(payload, ensure_ascii=False).lower()
                    flag = any(t in (low + blob) for t in ("poc", "vah", "val", "value area", "volume profile", "vp"))
                    if flag or "lux" in low or "profile" in low or "volume" in low:
                        print(f"    >>> [{sname}] keys={keys}")
                        print(f"        payload={jshort(payload)}")
            # 2. pine_lines / pine_labels — POC/VA como linhas/labels plotadas
            for cont in ("pine_lines", "pine_labels"):
                items = rec.get(cont) or []
                hits = []
                for grp in (items if isinstance(items, list) else []):
                    gname = str(grp.get("name", "")).lower()
                    blob = json.dumps(grp, ensure_ascii=False).lower()
                    if any(t in (gname + blob) for t in ("poc", "vah", "val", "value", "profile", "lux vp", "volume")):
                        hits.append(grp.get("name"))
                print(f"  {cont}: studies={[str(g.get('name')) for g in (items if isinstance(items,list) else [])]} | VA-hits={hits}")
            # 3. session_vp completo
            svp = rec.get("session_vp") or {}
            print(f"\n  session_vp: n={svp.get('n')} ok={svp.get('ok')} id={svp.get('id')}")
            print(f"    last3 = {jshort(svp.get('last3'), 400)}")
            if seen >= 4:
                break


if __name__ == "__main__":
    main()
