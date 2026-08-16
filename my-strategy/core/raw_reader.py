#!/usr/bin/env python3
"""LEITOR RAW CANÓNICO dos datasets de replay (Cris 2026-08-16).
UM leitor validado — o ÚNICO caminho sancionado para ler o RAW `.gz` por-barra (OB/SMC/SVP/Bubbles/NAS/RSI
as-of). Extraído BYTE-FIEL do padrão provado (cp_engine `grp` + loop gz + ohlcv[-1]). A hook raw_read_guard
bloqueia `gzip.open` direto de `raw_replay/*.gz` sem importar este módulo.

Fecha a dor recorrente: cada script re-implementava o parse (`grp` copiado) e partia — list-de-estudos-por-nome,
`values` dict, `ohlcv[-1]`=barra-atual, `zones` vs `all_boxes`, barra-0 vazia, drift de nomes. Aqui é UM sítio,
provado por selftest contra um registo REAL. Consome o registry (docs/data/dataset_registry.json) para os paths.
py3 stdlib."""
import gzip, json, os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REGISTRY = REPO / "docs/data/dataset_registry.json"
# raízes possíveis do HD (TradingData). O registry guarda paths relativos "TradingData/...".
HD_ROOTS = ["/Volumes/GUTS_ LACIE", "/Volumes/GUTS_LACIE", str(REPO)]


# ── extração por-registo (o 'grp' provado, byte-fiel) ──
def study(rec, category, name_substr):
    """O estudo (dict) da categoria por substring de nome, case-insensitive. None se ausente (barra-0/drift)."""
    return next((x for x in (rec.get(category) or []) if name_substr.lower() in str(x.get("name", "")).lower()), None)


def values(rec, name_substr):
    """values dict de um study_values por nome (ex.: 'Relative Strength'->{'RSI':..}). {} se ausente."""
    s = study(rec, "study_values", name_substr)
    return (s.get("values") or {}) if s else {}


def bar(rec):
    """Barra ATUAL = última do buffer ohlcv. {t,o,h,l,c} ou None."""
    oh = rec.get("ohlcv") or []
    if not oh or not isinstance(oh[-1], dict) or oh[-1].get("time") is None:
        return None
    b = oh[-1]
    return {"t": b["time"], "o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"]}


def boxes(rec, name_substr):
    """Caixas OB/zonas normalizadas [{id,text,low,high}] de all_boxes. [] se ausente."""
    s = study(rec, "pine_boxes", name_substr)
    return [{"id": bx.get("id"), "text": str(bx.get("text", "")).upper(), "low": bx.get("low"), "high": bx.get("high")}
            for bx in ((s.get("all_boxes") if s else []) or [])]


def labels(rec, name_substr):
    """Labels [{id,text}] de um pine_labels por nome. [] se ausente."""
    s = study(rec, "pine_labels", name_substr)
    return [{"id": l.get("id"), "text": str(l.get("text", ""))} for l in ((s.get("labels") if s else []) or [])]


def bubbles(rec, name_substr="Bubbles"):
    """activations_per_plot do estudo de bolhas (ou o 1º pine_shapes_bubbles). {} se ausente."""
    s = study(rec, "pine_shapes_bubbles", name_substr) or next(iter(rec.get("pine_shapes_bubbles") or []), None)
    return (s.get("activations_per_plot") or {}) if s else {}


# ── stream / série ──
def iter_records(gz_path, limit=None):
    """Gerador de registos VÁLIDOS (dict com ohlcv), streaming (não carrega o ficheiro todo). SEM ordenar."""
    n = 0
    with gzip.open(gz_path, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if isinstance(r, dict) and r.get("ohlcv"):
                yield r
                n += 1
                if limit and n >= limit:
                    return


def records(gz_path):
    """Todos os registos válidos, ORDENADOS por replay_current_date (para labs)."""
    snaps = list(iter_records(gz_path))
    snaps.sort(key=lambda r: r.get("replay_current_date") or 0)
    return snaps


def series(gz_path):
    """Série de barras {t:{o,h,l,c}} do buffer (dedup por time — barras repetem entre snaps). Ordenada."""
    bars = {}
    for r in iter_records(gz_path):
        for b in (r.get("ohlcv") or []):
            if isinstance(b, dict) and b.get("time") is not None:
                bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"]}
    return dict(sorted(bars.items()))


# ── paths canónicos via registry (não hardcodar) ──
def _load_registry():
    d = json.loads(REGISTRY.read_text())
    return d.get("datasets", d if isinstance(d, list) else [])


def resolve_gz(symbol, timeframe, status="active"):
    """Devolve os paths .gz ABSOLUTOS (existentes no HD) para symbol/timeframe, do registry, ordenados por data."""
    out = []
    for ds in _load_registry():
        if ds.get("symbol") != symbol or ds.get("timeframe") != timeframe or ds.get("status") != status:
            continue
        rel = ds.get("raw_gz_path")
        if not rel:
            continue
        for root in HD_ROOTS:
            p = Path(root) / rel
            if p.exists():
                out.append((ds.get("start_date") or "", str(p)))
                break
    out.sort()
    return [p for _, p in out]


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        # prova a leitura contra um registo REAL do 1º gz 15M disponível
        gzs = resolve_gz("XAUUSD", "15M")
        t = []
        t.append(("registry resolve >=1 gz 15M", len(gzs) >= 1))
        if gzs:
            rec = None
            for r in iter_records(gzs[0], limit=50):
                if study(r, "study_values", "Relative") or study(r, "pine_boxes", "Custom OB"):
                    rec = r; break
            t.append(("achou registo com indicadores nos 1os 50", rec is not None))
            if rec:
                b = bar(rec)
                t.append(("bar() devolve t,o,h,l,c sãos", bool(b) and b["h"] >= b["l"] and b["t"] > 0))
                rsi = values(rec, "Relative").get("RSI")
                t.append(("values('Relative') tem chave RSI (mesmo que None)", "RSI" in values(rec, "Relative") or study(rec, "study_values", "Relative") is None))
                obs = boxes(rec, "Custom OB")
                t.append(("boxes('Custom OB') = lista (0+) com low/high", isinstance(obs, list) and all(("low" in x and "high" in x) for x in obs)))
                print("  amostra: bar=%s | RSI=%s | OB boxes=%d" % (b, rsi, len(obs)))
        for lab, r in t:
            print("  [%s] %s" % ("OK" if r else "FAIL", lab))
        allok = all(r for _, r in t)
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
