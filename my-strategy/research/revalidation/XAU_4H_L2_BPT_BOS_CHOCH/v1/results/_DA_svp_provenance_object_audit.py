#!/usr/bin/env python3
"""SVP/SMC VOLUME PROVENANCE — auditoria EXAUSTIVA de objetos RAW por niveis POC/VAH/VAL plotados (nao so
histograma). Para cada timestamp critico, dump de TODOS os estudos em study_values, TODOS os grupos de
pine_lines/pine_boxes/pine_labels/pine_shapes (nome + niveis de preco), e session_vp completo. Flag de qualquer
objeto cujo nome/conteudo sugira POC/VAH/VAL/value-area/profile. NAO fabrica nada. Read-only. Verified at: 2026-06-23.

CORRECAO 2026-06-23: a linha que classificava session_vp.last3.v como 'per-bar [t,price,h,l]' ESTAVA ERRADA.
v = [time, POC, VAH, VAL] = VALUE-AREA (provado em _DA_svp_va_vs_ohlc_verify.py: 0/4000 == OHLC). A conclusao
correta sobre pine_lines/boxes/labels (VA NAO esta nesses containers, so SMC) permanece valida; o erro foi so na
interpretacao do session_vp. A VA real esta em svp_bars.jsonl (extract_svp.py) + DSPA F6. Ver
docs/XAU_4H_L2_BPT_SVP_VOLUME_PROVENANCE_AUDIT.md."""
import gzip, json, os

SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
RR = "repro_recovery"
F = [json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
CRIT = [4918, 4926, 8878, 4401, 5627, 3825, 3929, 3949, 1522]
ENTRY = {b: int(F[b]["ts_epoch"]) for b in CRIT}
DATES = {}
import datetime as dt
for b in CRIT:
    DATES[dt.datetime.utcfromtimestamp(ENTRY[b]).strftime("%Y-%m-%d")] = b
VA_TOK = ("poc", "vah", "val", "value area", "value_area", "value-area", "profile", "volume profile",
          "developing", "vwap", "session vol")


def to_ep(t):
    if t is None: return None
    t = float(t); return int(t / 1000) if t > 1e11 else int(t)


def lev_lines(grp):
    """extrai niveis de preco de um grupo pine_lines."""
    out = []
    for ln in (grp.get("lines") or grp.get("all_lines") or []):
        for k in ("y", "y1", "y2", "price", "level", "value"):
            if isinstance(ln, dict) and ln.get(k) is not None:
                out.append((k, ln.get(k)))
    return out[:8]


def boxes_lv(grp):
    out = []
    for bx in (grp.get("boxes") or grp.get("all_boxes") or []):
        if isinstance(bx, dict):
            out.append({k: bx.get(k) for k in ("top", "bottom", "high", "low", "text") if bx.get(k) is not None})
    return out[:8]


def main():
    found_any = False
    seen = set()
    with gzip.open(SVP, "rt") as fh:
        for line in fh:
            d8 = line[:60]
            hit_date = next((d for d in DATES if d in line), None)
            if not hit_date: continue
            rec = json.loads(line)
            oh = rec.get("ohlcv"); last = oh[-1] if isinstance(oh, list) and oh else None
            at = to_ep(last.get("time")) if isinstance(last, dict) else None
            b = DATES[hit_date]
            if at != ENTRY[b] or b in seen:  # so a barra de entry exata, 1x por episodio
                continue
            seen.add(b)
            print("=" * 90)
            print(f"EPISODIO {b} @ entry {dt.datetime.utcfromtimestamp(ENTRY[b])} (bar time match)")
            # 1. study_values
            print("  -- study_values:")
            for st in (rec.get("study_values") or []):
                nm = str(st.get("name")); vals = st.get("values") or {}
                flag = " <<<VA?" if any(t in (nm + json.dumps(vals)).lower() for t in VA_TOK) else ""
                print(f"     [{nm}] keys={list(vals.keys())}{flag}")
            # 2. pine_lines / boxes / labels / shapes — TODOS os grupos
            for cont in ("pine_lines", "pine_boxes", "pine_labels", "pine_shapes"):
                groups = rec.get(cont) or []
                if not isinstance(groups, list): continue
                for grp in groups:
                    nm = str(grp.get("name", "?"))
                    blob = json.dumps(grp, ensure_ascii=False).lower()
                    is_va = any(t in (nm.lower() + blob) for t in VA_TOK)
                    cnt = len(grp.get("lines") or grp.get("boxes") or grp.get("labels") or grp.get("shapes") or [])
                    mark = " <<<VA-CANDIDATE" if is_va else ""
                    if is_va or any(k in nm.lower() for k in ("volume", "profile", "vp", "session", "lux", "smc")):
                        print(f"  -- {cont}[{nm}] n={cnt}{mark}")
                        if cont == "pine_lines": print(f"       levels={lev_lines(grp)}")
                        if cont == "pine_boxes": print(f"       boxes={boxes_lv(grp)}")
                        if cont == "pine_labels":
                            txts = [str(l.get('text'))[:30] for l in (grp.get('labels') or [])][:6]
                            print(f"       labels={txts}")
                        if is_va: found_any = True
            # 3. session_vp completo
            svp = rec.get("session_vp") or {}
            l3 = svp.get("last3") or []
            print(f"  -- session_vp: keys={sorted(svp.keys())} n={svp.get('n')} ok={svp.get('ok')}")
            if l3:
                it = l3[-1]
                print(f"       last item: keys={list(it.keys()) if isinstance(it,dict) else type(it).__name__} sample={json.dumps(it)[:120]}")
                # checa se item parece price-level row (volume@price) vs per-bar [t,price,h,l]
                v = it.get("v") if isinstance(it, dict) else None
                if isinstance(v, list):
                    print(f"       item.v len={len(v)} -> {'per-bar [t,price,h,l]' if len(v)==4 and v[0]>1e9 else 'POSSIVEL price-level row?'}")
    print("\n" + "=" * 90)
    print(f"RESULTADO: objetos VA-candidate (POC/VAH/VAL/value-area/profile) encontrados? {'SIM' if found_any else 'NAO'}")
    print(f"episodios auditados: {sorted(seen)}")


if __name__ == "__main__":
    main()
