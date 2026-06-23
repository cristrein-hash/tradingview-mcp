#!/usr/bin/env python3
"""AUDITORIA READ-ONLY #3 — study_values vem como LIST; dump correto + _feature_availability + busca global por
qualquer plot POC/VAH/VAL/Value-Area/Volume-Profile no registro RAW SVP. Decide RAW_ORIGINAL_OK (saida plotada
do indicador) vs BLOCKED (nao ha VA no RAW). NAO fabrica nada. Verified at: 2026-06-23."""
import gzip, json

SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
VA_TOKENS = ("poc", "vah", "val", "value area", "value_area", "volume profile", "volume_profile",
             "vp_", "session vp", "session_vp", "developing")


def main():
    with gzip.open(SVP, "rt") as fh:
        for line in fh:
            if "2023-03-08T02:59:59" not in line:
                continue
            rec = json.loads(line)
            print(f"REGISTRO @ {rec.get('replay_current_dt')} bar_index={rec.get('bar_index')}")

            # _feature_availability
            fa = rec.get("_feature_availability")
            print("\n## _feature_availability:", json.dumps(fa, ensure_ascii=False)[:500] if fa else fa)

            # study_values como LIST
            sv = rec.get("study_values")
            print(f"\n## study_values type={type(sv).__name__} len={len(sv) if isinstance(sv,list) else '-'}")
            if isinstance(sv, list):
                for st in sv:
                    name = st.get("name") if isinstance(st, dict) else None
                    keys = list(st.keys()) if isinstance(st, dict) else None
                    print(f"  - study name={name!r} keys={keys}")
                    # dump valores plotados (procura POC/VA)
                    blob = json.dumps(st, ensure_ascii=False)
                    if any(t in blob.lower() for t in VA_TOKENS) or (name and any(t in str(name).lower() for t in ("lux", "profile", "volume", "vp"))):
                        print(f"      >>> VA-CANDIDATE payload={blob[:400]}")

            # busca GLOBAL no registro inteiro por tokens VA (exceto session_vp ja conhecido)
            full = json.dumps({k: v for k, v in rec.items() if k != "session_vp"}, ensure_ascii=False).lower()
            present = [t for t in VA_TOKENS if t in full]
            print(f"\n## tokens VA presentes no registro (fora session_vp): {present}")
            break


if __name__ == "__main__":
    main()
