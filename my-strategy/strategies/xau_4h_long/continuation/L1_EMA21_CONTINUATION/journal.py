#!/usr/bin/env python3
"""Headless human-review journal — L1 · EMA21 CONTINUATION (Production v2, peça 3).

Recebe um JSON de candidato do scanner (via stdin), anexa a DECISÃO HUMANA e grava UMA
linha JSONL append-only no caminho de --journal-path. Default seguro: SEM --journal-path,
só imprime no stdout e NÃO escreve nada.

NÃO faz: Telegram, envio, chamar o scanner, MCP/chart, outcome, produção. Standalone.

Uso:
  python3 scanner.py --at <ts> | python3 journal.py --decision KEEP --reason "..." \
      --reviewed-by cris --journal-path /path/to/journal.jsonl
  # sem --journal-path: imprime a linha no stdout e não grava
"""
import json, sys, argparse
from datetime import datetime, timezone


def main():
    ap = argparse.ArgumentParser(description="Human-review journal for L1 scanner candidates.")
    ap.add_argument("--decision", required=True, choices=["KEEP", "BLOCK"],
                    help="decisão humana sobre o candidato")
    ap.add_argument("--reason", default="", help="justificativa curta da decisão")
    ap.add_argument("--reviewed-by", default="human", help="quem revisou")
    ap.add_argument("--journal-path", default=None,
                    help="caminho do JSONL append-only; se ausente, só imprime no stdout (não grava)")
    args = ap.parse_args()

    raw = sys.stdin.read().strip()
    if not raw:
        print("error: no candidate JSON on stdin (pipe scanner.py output)", file=sys.stderr)
        return 2
    try:
        cand = json.loads(raw)
    except Exception as e:
        print(f"error: invalid candidate JSON on stdin: {e}", file=sys.stderr)
        return 2

    line = {
        "event_type": "human_review_decision",
        "strategy": cand.get("strategy"),
        "suite": cand.get("suite"),
        "symbol": cand.get("symbol"),
        "timeframe": cand.get("timeframe"),
        "candidate_timestamp": cand.get("timestamp"),
        "candidate": cand.get("candidate"),
        "review_required": cand.get("review_required", True),
        "block_or_review_flags": cand.get("block_or_review"),
        "human_decision": args.decision,
        "reason": args.reason,
        "reviewed_by": args.reviewed_by,
        "review_ts": datetime.now(timezone.utc).isoformat(),
        "telegram_allowed": False,
        "outcome_status": "PENDING",
    }

    rendered = json.dumps(line, ensure_ascii=False)
    if args.journal_path:
        with open(args.journal_path, "a") as f:
            f.write(rendered + "\n")
        print(f"[journal] appended 1 line -> {args.journal_path}")
    else:
        # default seguro: sem caminho, não escreve — só mostra a linha
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
