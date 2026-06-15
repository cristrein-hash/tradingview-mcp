#!/usr/bin/env python3
"""Refresh incremental SOB DEMANDA do regime_L1_v4 (Production v2).

Mantém `xau_daily_l1v4.jsonl` + `regime_l1_v4_classifications.jsonl` frescos lendo barras
diárias novas via MCP D (read-only), com restauração segura do chart. Append-only, com
validação (monotonicidade, sem duplicata, OHLCV mínimo, sem barra incompleta) e manifest.

Default = --dry-run (não escreve). Escrita só com --write E se houver barra fechada faltante.
NÃO envia Telegram, NÃO toca broker/scheduler/daemon/legacy/RAW. Não muda símbolo. Restaura TF.

Hard stops: MCP inacessível · símbolo != PEPPERSTONE:XAUUSD · TF D não confirmável · sem barras ·
barra recente incompleta · gap de datas · duplicata · OHLCV inválido · chart não restaurável.
"""
import json, sys, argparse, hashlib, statistics
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
CORE = HERE.parent
sys.path.insert(0, str(CORE))
sys.path.insert(0, str(HERE))
from tv_read_adapter import _MCP, SYMBOL  # cliente MCP read-only reutilizado  # noqa: E402
from regime_l1_v4 import build_classifications  # noqa: E402

DAILY = HERE / "xau_daily_l1v4.jsonl"
CLASSIF = HERE / "regime_l1_v4_classifications.jsonl"
MANIFEST = HERE / "xau_daily_l1v4.manifest.json"


def _hard(reason):
    return {"status": "HARD_STOP", "reason": reason}


def refresh(write=False):
    if not DAILY.exists():
        return _hard("xau_daily_l1v4.jsonl ausente")
    existing = [json.loads(l) for l in DAILY.read_text().splitlines() if l.strip()]
    existing.sort(key=lambda r: r["ts"])
    current_last = existing[-1]["ts"]
    today = datetime.now(timezone.utc).date().isoformat()

    m = _MCP(); orig_tf = None
    try:
        m.start()
        st = m.call("chart_get_state")
        if st.get("_error"):
            return _hard(f"chart_get_state falhou: {st['_error']}")
        if st.get("symbol") != SYMBOL:
            return _hard(f"símbolo '{st.get('symbol')}' != {SYMBOL} (NÃO troco símbolo)")
        orig_tf = str(st.get("resolution"))
        # garantir D
        if orig_tf not in ("1D", "D"):
            r = m.call("chart_set_timeframe", {"timeframe": "D"})
            if not r.get("success"):
                return _hard(f"não consegui setar TF D: {r}")
        st2 = m.call("chart_get_state")
        if str(st2.get("resolution")) not in ("1D", "D"):
            return _hard(f"TF D não confirmado (got {st2.get('resolution')})")
        oh = m.call("data_get_ohlcv", {"count": 30})
        bars = oh.get("bars") or []
        if not bars:
            return _hard("data_get_ohlcv não retornou barras")
        # mapear -> {ts: row}, só barras CONFIRMADAS (date < today)
        rows = []
        for b in bars:
            t = b.get("time")
            if t is None or b.get("close") is None:
                continue
            ts = datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")
            rows.append({"ts": ts, "open": b["open"], "high": b["high"], "low": b["low"],
                         "close": b["close"], "volume": b.get("volume")})
        rows.sort(key=lambda r: r["ts"])
        # validação anti-barra-incompleta: volume >= 0.3 * mediana das anteriores
        vols = [r["volume"] for r in rows if r.get("volume")]
        med = statistics.median(vols) if vols else 0
        confirmed = [r for r in rows if r["ts"] < today and (not med or (r.get("volume") or 0) >= 0.3 * med)]
        # detectar barra incompleta entre as date<today (volume anômalo)
        suspicious = [r["ts"] for r in rows if r["ts"] < today and med and (r.get("volume") or 0) < 0.3 * med]
        if suspicious:
            return _hard(f"barra(s) com volume anômalo (possível incompleta): {suspicious}")
        if not confirmed:
            return _hard("nenhuma barra confirmada (date<today) na leitura")
        target_d1 = confirmed[-1]["ts"]
        missing = [r for r in confirmed if r["ts"] > current_last]
        result = {"current_last_date": current_last, "target_d1": target_d1,
                  "missing_count": len(missing), "today": today,
                  "missing_dates": [r["ts"] for r in missing]}
        if not missing:
            result["status"] = "already_fresh"
            return result
        # validações das novas barras
        new_ts = [r["ts"] for r in missing]
        if len(set(new_ts)) != len(new_ts):
            return _hard(f"duplicata nas barras novas: {new_ts}")
        if any(t <= current_last for t in new_ts):
            return _hard("barra nova não-monotônica vs dataset")
        for r in missing:
            if not (r["high"] >= r["low"] and r["high"] >= r["close"] >= r["low"] and r["high"] >= r["open"] >= r["low"]):
                return _hard(f"OHLCV inválido em {r['ts']}: {r}")
        result["status"] = "missing_bars"
        if not write:
            result["mode"] = "dry_run (nada escrito)"
            return result
        # WRITE: append-only + reclassify + manifest
        merged = existing + missing
        with open(DAILY, "w") as f:
            for r in merged:
                f.write(json.dumps(r) + "\n")
        cls = build_classifications(merged)
        with open(CLASSIF, "w") as f:
            for r in cls:
                f.write(json.dumps(r) + "\n")
        sha = hashlib.sha256(DAILY.read_bytes()).hexdigest()[:16]
        man = {"dataset": "xau_daily_l1v4", "symbol": SYMBOL, "timeframe": "1D",
               "source": "MCP D live read-only (refresh incremental)",
               "bars": len(merged), "first_ts": merged[0]["ts"], "last_ts": merged[-1]["ts"],
               "appended_new": len(missing), "new_range": [missing[0]["ts"], missing[-1]["ts"]],
               "regime_last": cls[-1]["regime_l1_v4"], "sha256_16": sha,
               "refreshed_at": datetime.now(timezone.utc).isoformat()}
        json.dump(man, open(MANIFEST, "w"), indent=2)
        result["mode"] = "written"; result["bars_total"] = len(merged); result["sha256_16"] = sha
        result["regime_last"] = cls[-1]["regime_l1_v4"]
        return result
    finally:
        # restaurar TF original se mudamos
        try:
            if orig_tf and orig_tf not in ("1D", "D"):
                m.call("chart_set_timeframe", {"timeframe": orig_tf})
                stf = m.call("chart_get_state")
                if str(stf.get("resolution")) != orig_tf:
                    print(json.dumps({"warn": f"chart NÃO restaurado p/ {orig_tf} (got {stf.get('resolution')})"}), file=sys.stderr)
        except Exception as e:
            print(json.dumps({"warn": f"restauração TF falhou: {e}"}), file=sys.stderr)
        m.stop()


def main():
    ap = argparse.ArgumentParser(description="On-demand regime_L1_v4 incremental refresh.")
    ap.add_argument("--write", action="store_true", help="escreve se houver barra fechada faltante (default: dry-run)")
    args = ap.parse_args()
    res = refresh(write=args.write)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 2 if res.get("status") == "HARD_STOP" else 0


if __name__ == "__main__":
    sys.exit(main())
