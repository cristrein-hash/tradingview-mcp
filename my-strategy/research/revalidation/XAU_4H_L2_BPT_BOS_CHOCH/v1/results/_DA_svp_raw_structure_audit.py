#!/usr/bin/env python3
"""AUDITORIA READ-ONLY da estrutura do session_vp no RAW SVP_LUX_RAW (decide se POC/VAL/VAH e reconstruivel
causalmente). NAO fabrica nada. Imprime: chaves de topo do registro, estrutura de session_vp, e SE ha volume
por nivel de preco (sem volume-por-nivel => VA nao computavel => mantem BLOCKED). Le poucos registros.
Verified at: 2026-06-23."""
import gzip, json, os

SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"


def short(v, n=240):
    s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    return s[:n] + (" …" if len(s) > n else "")


def main():
    print(f"# arquivo: {os.path.basename(SVP)}  exists={os.path.exists(SVP)}")
    n = 0
    with gzip.open(SVP, "rt") as fh:
        for line in fh:
            rec = json.loads(line)
            n += 1
            if n == 1:
                print("\n## TOP-LEVEL KEYS:", sorted(rec.keys()))
                print("  symbol:", rec.get("symbol"), "| tf:", rec.get("timeframe"),
                      "| replay_current_dt:", rec.get("replay_current_dt"))
            svp = rec.get("session_vp")
            if svp is not None and n <= 3:
                print(f"\n## REGISTRO {n} session_vp — type={type(svp).__name__}")
                if isinstance(svp, dict):
                    print("  session_vp KEYS:", sorted(svp.keys()))
                    for k, v in svp.items():
                        if isinstance(v, list):
                            print(f"    [{k}] list len={len(v)} sample0={short(v[0]) if v else 'empty'}")
                            if v and isinstance(v[0], (list, dict)):
                                print(f"        item-type={type(v[0]).__name__} "
                                      f"item-len/keys={len(v[0]) if isinstance(v[0],(list,dict)) else '-'}")
                        else:
                            print(f"    [{k}] = {short(v)}")
                elif isinstance(svp, list):
                    print("  session_vp is LIST len=", len(svp), " sample0=", short(svp[0]) if svp else "empty")
            if n >= 3:
                break
    # varredura leve: quantos registros tem session_vp nao-vazio nos primeiros 200
    have = 0
    with gzip.open(SVP, "rt") as fh:
        for i, line in enumerate(fh):
            if i >= 200:
                break
            r = json.loads(line)
            s = r.get("session_vp")
            if s:
                have += 1
    print(f"\n## cobertura: {have}/200 primeiros registros tem session_vp nao-vazio")


if __name__ == "__main__":
    main()
