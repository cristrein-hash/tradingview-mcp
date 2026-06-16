"""Forward Outcome Layer — MVP Fase 1: relatório de QUALIDADE forward (read-only).

Responde: o `indicator_signals.jsonl` está limpo, completo, rastreável e útil como
fonte forward de comportamento live? Mede densidade, completude de payload, duplicatas
e parse errors. NÃO calcula R, NÃO compara backtest, NÃO envia Telegram, NÃO muta nada
fora de `reports/`.

Uso:
  python3 report_forward_quality.py                 # lê event store, escreve reports/forward_quality_latest.md(+json)
  python3 report_forward_quality.py --no-write       # só imprime, não escreve arquivo
  python3 report_forward_quality.py --symbol XAUUSD --since 2026-06-01
"""
from __future__ import annotations

import argparse
import collections
import json
import os

import ingest_live_signals as ing


REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
XAU_TOKENS = ("XAUUSD",)  # XAU-only subset (PEPPERSTONE:XAUUSD / XAUUSD variants)


# --- métricas -----------------------------------------------------------------


def _day(dt):
    return dt.date().isoformat() if dt else None


def _is_xau(rec):
    hay = f"{rec.get('base_symbol') or ''}|{rec.get('symbol') or ''}".upper()
    return any(t in hay for t in XAU_TOKENS)


def compute_metrics(records, meta):
    n = len(records)
    dts = [r["ts_signal_dt"] for r in records if r["ts_signal_dt"]]
    dmin = min(dts) if dts else None
    dmax = max(dts) if dts else None

    per_day = collections.Counter(_day(r["ts_signal_dt"]) for r in records if r["ts_signal_dt"])
    per_symbol = collections.Counter(r.get("base_symbol") or "(vazio)" for r in records)
    per_provider = collections.Counter(r.get("provider") or "(nenhum)" for r in records)
    per_indicator = collections.Counter(r.get("indicator_name") or "(vazio)" for r in records)
    per_tf = collections.Counter(r.get("timeframe") or "(vazio)" for r in records)

    # completude de payload (métrica 6)
    fields = ["has_timestamp", "has_symbol", "has_timeframe", "has_source",
              "has_signal_type", "has_payload", "has_ingestion_hash"]
    completeness = {f: sum(1 for r in records if r[f]) for f in fields}

    # duplicatas (métrica 7): por ingestion_hash se existir; senão por tupla
    hashes = [r["ingestion_hash"] for r in records if r["ingestion_hash"]]
    hash_counts = collections.Counter(hashes)
    dup_by_hash = sum(c - 1 for c in hash_counts.values() if c > 1)
    no_hash = n - len(hashes)
    tuple_counts = collections.Counter(
        (r["ts_signal"], r.get("symbol"), r.get("indicator_name"), r.get("signal_type"))
        for r in records if not r["ingestion_hash"]
    )
    dup_by_tuple = sum(c - 1 for c in tuple_counts.values() if c > 1)
    total_dups = dup_by_hash + dup_by_tuple
    dup_rate = (total_dups / n) if n else 0.0

    # clusters por hora (métrica 11)
    per_hour = collections.Counter(
        r["ts_signal_dt"].hour for r in records if r["ts_signal_dt"]
    )

    # XAU subset (métrica 10)
    xau = [r for r in records if _is_xau(r)]
    xau_tf = collections.Counter(r.get("timeframe") or "(vazio)" for r in xau)
    xau_ind = collections.Counter(r.get("indicator_name") or "(vazio)" for r in xau)
    xau_recent = sorted(
        [r for r in xau if r["ts_signal_dt"]], key=lambda r: r["ts_signal_dt"]
    )[-8:]
    xau_per_day = collections.Counter(_day(r["ts_signal_dt"]) for r in xau if r["ts_signal_dt"])

    span_days = ((dmax - dmin).days + 1) if (dmin and dmax) else None
    avg_per_day = (n / span_days) if span_days else None

    return {
        "n": n,
        "meta": meta,
        "range": {"min": dmin.isoformat() if dmin else None,
                   "max": dmax.isoformat() if dmax else None,
                   "span_days": span_days,
                   "avg_signals_per_day": round(avg_per_day, 1) if avg_per_day else None},
        "per_symbol": dict(per_symbol.most_common()),
        "per_provider": dict(per_provider.most_common()),
        "per_indicator": dict(per_indicator.most_common()),
        "per_timeframe": dict(per_tf.most_common()),
        "completeness": {f: {"count": completeness[f], "pct": round(100 * completeness[f] / n, 2) if n else 0}
                          for f in fields},
        "duplicates": {"by_ingestion_hash": dup_by_hash, "by_tuple_fallback": dup_by_tuple,
                        "records_without_hash": no_hash, "total": total_dups,
                        "rate_pct": round(100 * dup_rate, 4)},
        "parse_errors": meta["parse_errors"],
        "top_days": dict(collections.Counter(per_day).most_common(5)),
        "per_hour_utc": {str(h): per_hour.get(h, 0) for h in range(24)},
        "xau_subset": {
            "n": len(xau),
            "per_timeframe": dict(xau_tf.most_common()),
            "per_indicator": dict(xau_ind.most_common()),
            "per_day_recent": dict(sorted(xau_per_day.items())[-7:]),
            "recent": [{"ts_signal": r["ts_signal"], "symbol": r.get("symbol"),
                         "tf": r.get("timeframe"), "indicator": r.get("indicator_name"),
                         "signal_type": r.get("signal_type")} for r in xau_recent],
        },
    }


# --- render -------------------------------------------------------------------


def _tbl(counter_dict, k="item", v="n", top=None):
    items = list(counter_dict.items())
    if top:
        items = items[:top]
    out = [f"| {k} | {v} |", "|---|---|"]
    out += [f"| {a} | {b} |" for a, b in items]
    return "\n".join(out)


def render_md(m):
    r = m["range"]
    L = []
    L.append("# Forward Signal Quality — MVP Fase 1 (read-only)")
    L.append("")
    L.append("> Mede QUALIDADE/OPERAÇÃO do event store live, **não** edge. Sem R, sem comparação "
             "backtest, sem Telegram. Fonte: `alert-bridge/logs/indicator_signals.jsonl` (read-only).")
    L.append("")
    L.append("## 1–2. Volume e range temporal")
    L.append(f"- **Sinais lidos (após filtros):** {m['n']}  ·  linhas totais no arquivo: {m['meta']['total_lines']}  ·  "
             f"filtrados fora: {m['meta']['filtered_out']}")
    L.append(f"- **Filtros:** symbol=`{m['meta']['symbol_filter']}` · since=`{m['meta']['since']}` · limit=`{m['meta']['limit']}`")
    L.append(f"- **Range:** {r['min']} → {r['max']}  ·  span {r['span_days']} dias  ·  **~{r['avg_signals_per_day']} sinais/dia**")
    L.append("")
    L.append("## 3. Dias de maior densidade (top 5)")
    L.append(_tbl(m["top_days"], "dia", "sinais"))
    L.append("")
    L.append("## 4. Sinais por símbolo")
    L.append(_tbl(m["per_symbol"], "base_symbol", "sinais"))
    L.append("")
    L.append("## 5. Provider / indicador")
    L.append("**Provider:**")
    L.append(_tbl(m["per_provider"], "provider", "sinais"))
    L.append("")
    L.append("**Indicador (top 10):**")
    L.append(_tbl(m["per_indicator"], "indicador", "sinais", top=10))
    L.append("")
    L.append("**Timeframe:**")
    L.append(_tbl(m["per_timeframe"], "timeframe", "sinais"))
    L.append("")
    L.append("## 6. Completude de payload")
    L.append("| campo | presentes | % |")
    L.append("|---|---|---|")
    for f, d in m["completeness"].items():
        L.append(f"| {f} | {d['count']} | {d['pct']}% |")
    L.append("")
    d = m["duplicates"]
    L.append("## 7. Duplicatas")
    L.append(f"- por `ingestion_hash`: **{d['by_ingestion_hash']}**  ·  por tupla (sem hash): {d['by_tuple_fallback']}  ·  "
             f"registros sem hash: {d['records_without_hash']}")
    L.append(f"- **total duplicatas: {d['total']}  ·  taxa: {d['rate_pct']}%**")
    L.append("")
    L.append("## 8–9. Integridade")
    L.append(f"- **Parse errors (JSON inválido):** {m['parse_errors']}")
    L.append("- **Quarantine vivo:** `indicator_signals_quarantined.jsonl` (0 bytes na auditoria 2026-06-16 — vazio).")
    L.append("")
    L.append("## 10. Subset XAU (PEPPERSTONE:XAUUSD / XAUUSD)")
    x = m["xau_subset"]
    L.append(f"- **Sinais XAU:** {x['n']}")
    L.append("- **Por timeframe:**")
    L.append(_tbl(x["per_timeframe"], "tf", "sinais"))
    L.append("- **Por indicador:**")
    L.append(_tbl(x["per_indicator"], "indicador", "sinais"))
    L.append("- **Por dia (últimos 7 dias com XAU):**")
    L.append(_tbl(x["per_day_recent"], "dia", "sinais"))
    L.append("- **Últimos 8 sinais XAU:**")
    L.append("| ts_signal | symbol | tf | indicador | signal_type |")
    L.append("|---|---|---|---|---|")
    for s in x["recent"]:
        L.append(f"| {s['ts_signal']} | {s['symbol']} | {s['tf']} | {s['indicator']} | {s['signal_type']} |")
    L.append("")
    L.append("## 11. Clusters por hora (UTC) — densidade/ruído")
    L.append(_tbl({h: v for h, v in m["per_hour_utc"].items() if v}, "hora_utc", "sinais"))
    L.append("")
    L.append("## 12. Limitações (não esquecer)")
    L.append("- **Missing negatives:** o event store loga o que disparou, não o que *deveria* ter disparado. Não mede recall.")
    L.append("- **Payload drift / indicator version drift:** `indicator_version` muda no tempo; mesma `signal_type` pode ter semântica diferente entre versões.")
    L.append("- **Sem outcome/R ainda:** este MVP mede só qualidade/operação. R e comparação backtest são fases futuras.")
    L.append("- **Não valida edge.** Densidade alta ≠ edge; é sinal de ruído a investigar.")
    L.append("")
    L.append("_Gerado por `report_forward_quality.py` (read-only). Não altera o event store._")
    return "\n".join(L)


def _main(argv=None):
    ap = argparse.ArgumentParser(description="Forward signal quality report (read-only)")
    ap.add_argument("--path", default=None)
    ap.add_argument("--symbol", default=None, help="filtrar por substring de símbolo (ex.: XAUUSD)")
    ap.add_argument("--since", default=None, help="YYYY-MM-DD")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--no-write", action="store_true", help="não escrever arquivo, só imprimir resumo")
    ap.add_argument("--json", action="store_true", help="também escrever .json")
    args = ap.parse_args(argv)

    path = args.path or ing.default_event_store()
    if not os.path.isfile(path):
        raise SystemExit(f"HARD STOP: event store não encontrado: {path}")

    records, meta = ing.load_signals(path, symbol=args.symbol, since=args.since, limit=args.limit)
    m = compute_metrics(records, meta)
    md = render_md(m)

    if args.no_write:
        print(md)
        return

    os.makedirs(REPORTS_DIR, exist_ok=True)
    md_path = os.path.join(REPORTS_DIR, "forward_quality_latest.md")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(md + "\n")
    out = {"md": md_path}
    if args.json:
        js_path = os.path.join(REPORTS_DIR, "forward_quality_latest.json")
        with open(js_path, "w", encoding="utf-8") as fh:
            json.dump(m, fh, default=str, indent=2)
        out["json"] = js_path
    print(json.dumps({"written": out, "n": m["n"], "range": m["range"]}, default=str, indent=2))


if __name__ == "__main__":
    _main()
