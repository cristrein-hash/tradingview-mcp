"""Ingestão READ-ONLY do event store live de sinais de indicadores.

Biblioteca + CLI. Lê `alert-bridge/logs/indicator_signals.jsonl` (uma linha JSON
por sinal), normaliza campos mínimos e é robusto a linhas inválidas. NUNCA escreve,
trunca ou bloqueia o event store — apenas itera o arquivo.

Identidades (ver SPEC §B):
  - `ingestion_hash` = o `signal_hash` gravado pelo receiver (id de evento/ dedup
    de ingestão). NÃO é o signal_hash estratégico da L1.

Uso CLI (read-only, só imprime um resumo):
  python3 ingest_live_signals.py [--path P] [--symbol XAUUSD] [--since YYYY-MM-DD] [--limit N]
"""
from __future__ import annotations

import argparse
import ast
import json
import os
from datetime import datetime, timezone

# --- resolução de path (marker-walk até a raiz do repo) -----------------------


def _repo_root(start: str | None = None) -> str:
    d = os.path.abspath(start or os.path.dirname(__file__))
    while True:
        if os.path.isdir(os.path.join(d, "alert-bridge")) and os.path.isdir(
            os.path.join(d, "my-strategy")
        ):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            # fallback: 4 níveis acima de core/forward_outcome
            return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        d = parent


def default_event_store() -> str:
    return os.path.join(_repo_root(), "alert-bridge", "logs", "indicator_signals.jsonl")


# --- parsing ------------------------------------------------------------------

# Campos mínimos esperados no registro (schema v1.0 do receiver).
EXPECTED_FIELDS = (
    "ts_signal",
    "symbol",
    "timeframe",
    "indicator_name",
    "signal_type",
    "payload_full",
    "signal_hash",
)


def _parse_ts(s):
    """ISO8601 -> datetime aware (UTC). Retorna None se não parsear."""
    if not s or not isinstance(s, str):
        return None
    try:
        t = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return t.astimezone(timezone.utc)
    except Exception:
        return None


def _provider_from_symbol(symbol: str | None):
    if isinstance(symbol, str) and ":" in symbol:
        return symbol.split(":", 1)[0]
    return None


def normalize(rec: dict) -> dict:
    """Registro bruto -> dict normalizado com campos canônicos + flags de completude.

    Não levanta exceção: campos ausentes viram None / False.
    """
    symbol = rec.get("symbol")
    provider = _provider_from_symbol(symbol)
    payload_full = rec.get("payload_full")

    # provider/raw_symbol também podem estar dentro do payload_full (string de dict py)
    payload_ok = bool(payload_full)
    if provider is None and isinstance(payload_full, str):
        try:
            p = ast.literal_eval(payload_full)
            if isinstance(p, dict):
                provider = p.get("provider")
        except Exception:
            pass

    ts_signal = rec.get("ts_signal")
    return {
        "ts_signal": ts_signal,
        "ts_signal_dt": _parse_ts(ts_signal),
        "ts_received": rec.get("ts_received"),
        "base_symbol": rec.get("base_symbol"),
        "symbol": symbol,
        "provider": provider,
        "timeframe": rec.get("timeframe"),
        "indicator_name": rec.get("indicator_name"),
        "signal_type": rec.get("signal_type"),
        "price": rec.get("price"),
        "priority": rec.get("priority"),
        "schema_version": rec.get("schema_version"),
        "ingestion_hash": rec.get("signal_hash"),  # signal_hash do receiver = id de ingestão
        # flags de completude de payload (SPEC §D, métrica 6)
        "has_timestamp": bool(ts_signal),
        "has_symbol": bool(symbol),
        "has_timeframe": bool(rec.get("timeframe")),
        "has_source": bool(rec.get("indicator_name")),
        "has_signal_type": bool(rec.get("signal_type")),
        "has_payload": payload_ok,
        "has_ingestion_hash": bool(rec.get("signal_hash")),
    }


def iter_raw(path: str):
    """Itera (lineno, parsed_dict | None, error | None). Robusto a linhas inválidas.

    Read-only: abre o arquivo em modo 'r' e apenas lê linha a linha.
    """
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield lineno, json.loads(line), None
            except Exception as e:  # JSON inválido
                yield lineno, None, f"{type(e).__name__}: {e}"


def load_signals(path: str | None = None, symbol: str | None = None,
                 since: str | None = None, limit: int | None = None):
    """Carrega sinais normalizados + estatísticas de ingestão.

    Args:
      path: caminho do event store (default = repo/alert-bridge/logs/indicator_signals.jsonl)
      symbol: substring case-insensitive para filtrar base_symbol/symbol (ex.: 'XAUUSD')
      since: 'YYYY-MM-DD' — mantém apenas ts_signal >= esse dia (UTC)
      limit: máximo de registros normalizados a reter (após filtros)

    Returns: (records: list[dict], meta: dict)
      meta inclui total_lines, parse_errors, kept, filtered_out, path, since, symbol.
    """
    path = path or default_event_store()
    since_dt = _parse_ts(since + "T00:00:00+00:00") if since else None

    records = []
    total_lines = 0
    parse_errors = 0
    filtered_out = 0
    sym_l = symbol.lower() if symbol else None

    for _lineno, rec, err in iter_raw(path):
        total_lines += 1
        if err is not None:
            parse_errors += 1
            continue
        n = normalize(rec)
        if sym_l is not None:
            hay = f"{n.get('base_symbol') or ''}|{n.get('symbol') or ''}".lower()
            if sym_l not in hay:
                filtered_out += 1
                continue
        if since_dt is not None:
            if n["ts_signal_dt"] is None or n["ts_signal_dt"] < since_dt:
                filtered_out += 1
                continue
        records.append(n)
        if limit is not None and len(records) >= limit:
            break

    meta = {
        "path": path,
        "total_lines": total_lines,
        "parse_errors": parse_errors,
        "kept": len(records),
        "filtered_out": filtered_out,
        "symbol_filter": symbol,
        "since": since,
        "limit": limit,
    }
    return records, meta


def _main(argv=None):
    ap = argparse.ArgumentParser(description="Read-only ingest of live indicator_signals event store")
    ap.add_argument("--path", default=None, help="event store path (default: repo event store)")
    ap.add_argument("--symbol", default=None, help="filter by symbol substring, e.g. XAUUSD")
    ap.add_argument("--since", default=None, help="keep ts_signal >= YYYY-MM-DD (UTC)")
    ap.add_argument("--limit", type=int, default=None, help="max records to keep")
    args = ap.parse_args(argv)

    path = args.path or default_event_store()
    if not os.path.isfile(path):
        raise SystemExit(f"HARD STOP: event store não encontrado: {path}")

    recs, meta = load_signals(path, symbol=args.symbol, since=args.since, limit=args.limit)
    print(json.dumps({"meta": meta, "sample_first": recs[0] if recs else None,
                      "sample_last": recs[-1] if recs else None}, default=str, indent=2))


if __name__ == "__main__":
    _main()
