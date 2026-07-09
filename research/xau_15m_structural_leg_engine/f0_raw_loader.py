#!/usr/bin/env python3
"""F0 — RAW LOADER sancionado (XAU 15M STRUCTURAL LEG ENGINE, spec v1.2 §7; manifest docs/architecture).
Lê EXCLUSIVAMENTE os 9 blocos RAW .jsonl.gz do HD externo declarados no manifest (PROIBIDO primitives,
raw_features_*, superseded/). HD desmontado = BLOCKED fail-loud. Extrai a camada de PREÇO (tails ohlcv
de barras 15M FECHADAS), dedup por bar time com assert de igualdade OHLC nas sobreposições de borda
(divergência O/H/L/C > 1e-6 = STOP; volume divergente = WARN, mantém o bloco posterior), ordena,
verifica monotonicidade, detecta gaps (fim-de-semana / fronteira de bloco / outros) e materializa
cache derivado DECLARADO (results/f0_bars_cache.jsonl + sha256 para o manifest).
Leitura multi-fatorial/trajetória não se aplica aqui (F0 é ingestão, não análise de separação).
Nenhum evento, nenhuma entry, nenhum indicador, nenhum backtest."""
import sys, os, re, json, gzip, hashlib, datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
MANIFEST = REPO/"docs/architecture/XAU_15M_STRUCTURAL_LEG_ENGINE_GATE_MANIFEST.md"
RES = HERE/"results"; RES.mkdir(exist_ok=True)
CACHE = RES/"f0_bars_cache.jsonl"
TOL = 1e-6

def manifest():
    m = re.search(r"```json\s*(\{.*?\})\s*```", MANIFEST.read_text(), re.DOTALL)
    assert m, "manifest sem bloco json"
    return json.loads(m.group(1))

def sha256(path, cap=None):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()

def load_blocks(raw_files):
    """Uma passagem por bloco, em ordem de replay. Semântica do tail ohlcv (descoberta F0,
    fail-loud da v1): tail[-1] = barra CORRENTE possivelmente EM FORMAÇÃO (evolui entre snapshots);
    tail[:-1] = barras FECHADAS. Regra causal: um bar time só é CLOSED quando visto em profundidade
    >=1 do fim do tail (ou quando um snapshot posterior traz bar time maior). Assert de igualdade
    OHLC APENAS entre versões CLOSED (intra e inter-bloco); provisional é sobrescrito livremente."""
    bars = {}           # bar_time -> [o,h,l,c,v, block_idx]
    closed = set()
    provisional_src = {}
    per_block = []
    conflicts = []
    for bi, rf in enumerate(raw_files):
        p = Path(rf)
        assert p.exists(), f"BLOCKED: RAW ausente (HD desmontado?): {rf}"
        n_lines = 0; n_bars_new = 0; tmin = None; tmax = None
        with gzip.open(p, "rt", errors="replace") as fh:
            for ln in fh:
                try:
                    r = json.loads(ln)
                except Exception:
                    continue
                tail = r.get("ohlcv")
                if not tail:
                    continue
                n_lines += 1
                last_i = len(tail)-1
                for i, b in enumerate(tail):
                    t = b.get("time")
                    if t is None:
                        continue
                    row = [b.get("open"), b.get("high"), b.get("low"), b.get("close"),
                           b.get("volume"), bi]
                    is_closed = i < last_i
                    old = bars.get(t)
                    if old is None:
                        bars[t] = row; n_bars_new += 1
                        if tmin is None or t < tmin: tmin = t
                        if tmax is None or t > tmax: tmax = t
                    elif t in closed and is_closed:
                        # CLOSED vs CLOSED: divergência real = STOP
                        for k, name in ((0,"open"),(1,"high"),(2,"low"),(3,"close")):
                            a, c = old[k], row[k]
                            if a is not None and c is not None and abs(a-c) > TOL:
                                conflicts.append({"t": t, "field": name, "a": a, "b": c,
                                                  "block_a": old[5], "block_b": bi})
                        if row[4] is not None:
                            old[4] = row[4]   # volume: mantém o mais recente (WARN-level, não usado em F1.5)
                    else:
                        # provisional -> sobrescreve com a versão mais recente
                        bars[t] = row
                    if is_closed:
                        closed.add(t)
                        provisional_src.pop(t, None)
                    elif t not in closed:
                        provisional_src[t] = bi
        per_block.append({"file": p.name, "snapshot_lines": n_lines, "new_bars": n_bars_new,
                          "t_min": tmin, "t_max": tmax})
    never_closed = sorted(provisional_src)
    return bars, per_block, conflicts, never_closed

def dsu(t): return dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M")

def classify_gaps(ts, per_block):
    """gaps = delta>900s entre barras consecutivas; classifica weekend / fronteira / outro."""
    # fronteiras: fim de cada bloco k -> início do bloco k+1 (usa t_max/t_min por bloco)
    boundaries = []
    for k in range(len(per_block)-1):
        boundaries.append((per_block[k]["t_max"], per_block[k+1]["t_min"]))
    gaps = []
    for i in range(1, len(ts)):
        d = ts[i]-ts[i-1]
        if d <= 900:
            continue
        a, b = ts[i-1], ts[i]
        wd_a = dt.datetime.utcfromtimestamp(a).weekday()  # 4=sex
        kind = "other"
        if wd_a == 4 and d <= 60*3600:
            kind = "weekend"
        for (ba, bb) in boundaries:
            if abs(a-ba) <= 3600*2:
                kind = "block_boundary"; break
        if d <= 2*3600 and kind == "other":
            kind = "session_break"
        gaps.append({"from": dsu(a), "to": dsu(b), "hours": round(d/3600, 2), "kind": kind})
    return gaps, boundaries

def build(write_cache=True, hash_raws=True):
    man = manifest()
    raw_files = man["raw_files"]
    for banned in ("primitives", "raw_features", "superseded", "slim"):
        assert not any(banned in rf.lower() for rf in raw_files), f"fonte banida no manifest: {banned}"
    bars, per_block, conflicts, never_closed = load_blocks(raw_files)
    assert not conflicts, f"STOP fail-loud: divergência OHLC CLOSED-vs-CLOSED: {conflicts[:5]}"
    # barras nunca vistas como fechadas (fim de stream/bloco): EXCLUÍDAS da série (anti-forming-bar)
    for t in never_closed:
        bars.pop(t, None)
    ts = sorted(bars)
    assert all(ts[i] > ts[i-1] for i in range(1, len(ts))), "monotonicidade violada"
    gaps, boundaries = classify_gaps(ts, per_block)
    out = {"n_bars": len(ts), "t_min": dsu(ts[0]), "t_max": dsu(ts[-1]),
           "per_block": per_block, "n_conflicts": 0,
           "never_closed_excluded": [dsu(t) for t in never_closed],
           "n_gaps": len(gaps),
           "gaps_by_kind": {},
           "gaps_non_trivial": [g for g in gaps if g["kind"] == "other"],
           "block_boundaries": [{"from": dsu(a), "to": dsu(b)} for a, b in boundaries]}
    for g in gaps:
        out["gaps_by_kind"][g["kind"]] = out["gaps_by_kind"].get(g["kind"], 0) + 1
    if hash_raws:
        out["raw_sha256"] = {Path(rf).name: sha256(rf) for rf in raw_files}
    if write_cache:
        with open(CACHE, "w") as fh:
            for t in ts:
                o, h, l, c, v, bi = bars[t]
                fh.write(json.dumps({"t": t, "o": o, "h": h, "l": l, "c": c, "v": v})+"\n")
        out["cache"] = {"path": str(CACHE), "sha256": sha256(CACHE),
                        "source_ref": "derivado 1:1 dos 9 RAW .jsonl.gz do manifest (tails ohlcv, dedup por bar time, assert OHLC)"}
    return bars, ts, out

def load_cached():
    """Uso pelos módulos F1/F1.5: lê o cache declarado VERIFICANDO o sha256 contra o manifest
    (DA F0-F1.5 correção 2 — cache adulterado/stale = fail-loud); se ausente, reconstrói do RAW."""
    if CACHE.exists():
        man = manifest()
        decl = next((d["checksum"] for d in man.get("derived_files", [])
                     if d.get("path") == str(CACHE)), None)
        if decl:
            real = sha256(CACHE)
            assert real == decl, f"STOP: cache sha divergente do manifest: {real} != {decl}"
        bars = {}
        for ln in open(CACHE):
            b = json.loads(ln)
            bars[b["t"]] = [b["o"], b["h"], b["l"], b["c"], b["v"], -1]
        return bars, sorted(bars)
    bars, ts, _ = build(write_cache=True, hash_raws=False)
    return bars, ts

if __name__ == "__main__":
    bars, ts, out = build()
    (RES/"f0_raw_loader_result.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k not in ("raw_sha256", "gaps_non_trivial", "block_boundaries")}, indent=2))
    print("gaps 'other':", len(out["gaps_non_trivial"]))
    print("F0_PASS")
