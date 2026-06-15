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
    ap.add_argument("--event", default="human_review_decision",
                    choices=["signal_emitted", "human_review_decision"],
                    help="signal_emitted = notificação de candidato (sem decisão); "
                         "human_review_decision = decisão humana (exige --decision)")
    ap.add_argument("--decision", default=None, choices=["KEEP", "BLOCK"],
                    help="decisão humana (obrigatória só p/ event=human_review_decision)")
    ap.add_argument("--reason", default="", help="justificativa curta da decisão")
    ap.add_argument("--reviewed-by", default="human", help="quem revisou")
    ap.add_argument("--journal-path", default=None,
                    help="caminho do JSONL append-only; se ausente, só imprime no stdout (não grava)")
    # Execução real (opcional). candidate != trade; KEEP != entrada executada.
    ap.add_argument("--entry-taken", action="store_true",
                    help="marca que uma entrada REAL foi tomada (default: false)")
    ap.add_argument("--execution-mode", default="NONE",
                    choices=["NONE", "MANUAL", "MCP_MONITORED", "BROKER_AUTHORIZED"],
                    help="camada de execução/monitoramento (default NONE; MCP/broker são camadas FUTURAS autorizadas, não ativadas aqui)")
    ap.add_argument("--entry-ts", default=None, help="timestamp da entrada real (ISO)")
    ap.add_argument("--entry-price", type=float, default=None, help="preço de entrada real")
    ap.add_argument("--stop-price", type=float, default=None, help="preço de stop real")
    ap.add_argument("--target-plan", default=None, help="plano de alvo (texto livre)")
    ap.add_argument("--position-size", default=None, help="tamanho de posição (texto livre)")
    ap.add_argument("--execution-note", default="", help="nota livre de execução")
    ap.add_argument("--broker", default=None, help="broker (camada futura; ex.: PEPPERSTONE)")
    ap.add_argument("--broker-order-id", default=None, help="id de ordem do broker (camada futura)")
    ap.add_argument("--monitoring-mode", default=None, help="modo de monitoramento (camada futura; ex.: MCP_CHART)")
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

    def write_line(obj):
        rendered = json.dumps(obj, ensure_ascii=False)
        if args.journal_path:
            with open(args.journal_path, "a") as f:
                f.write(rendered + "\n")
            print(f"[journal] appended 1 line ({obj['event_type']}) -> {args.journal_path}")
        else:
            print(rendered)

    # EVENTO 1: signal_emitted — notificação de candidato (append-only, não mutar).
    # NÃO envia Telegram; só registra que o candidato foi gerado. Decisão humana vem
    # depois como evento separado, ligado pelo mesmo signal_hash.
    if args.event == "signal_emitted":
        write_line({
            "event_type": "signal_emitted",
            "signal_hash": cand.get("signal_hash"),
            "strategy": cand.get("strategy"),
            "suite": cand.get("suite"),
            "symbol": cand.get("symbol"),
            "timeframe": cand.get("timeframe"),
            "candidate_timestamp": cand.get("timestamp"),
            "signal_generated": True,
            "signal_sent": False,
            "signal_channel": "TELEGRAM_DRAFT",
            "telegram_allowed": False,
            "dry_run": True,
        })
        return 0

    # EVENTO 2: human_review_decision — exige --decision.
    if not args.decision:
        print("error: --decision is required for event=human_review_decision.", file=sys.stderr)
        return 2

    # entry_taken=true exige no mínimo entry_ts + entry_price + stop_price.
    # (KEEP NÃO implica entrada; default entry_taken=false não exige nada.)
    if args.entry_taken:
        missing = [k for k, v in (("entry_ts", args.entry_ts),
                                  ("entry_price", args.entry_price),
                                  ("stop_price", args.stop_price)) if v in (None, "")]
        if missing:
            print(f"error: entry_taken=true requires {missing} — nothing written.", file=sys.stderr)
            return 2

    line = {
        "event_type": "human_review_decision",
        "signal_hash": cand.get("signal_hash"),
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
        # execução real (candidate != trade). entry_taken=false => sem trade real.
        "entry_taken": bool(args.entry_taken),
        "execution_mode": args.execution_mode,
        "entry_ts": args.entry_ts,
        "entry_price": args.entry_price,
        "stop_price": args.stop_price,
        "target_plan": args.target_plan,
        "position_size": args.position_size,
        "execution_note": args.execution_note,
        "broker": args.broker,
        "broker_order_id": args.broker_order_id,
        "monitoring_mode": args.monitoring_mode,
        "telegram_allowed": False,
        "outcome_status": "PENDING",
    }

    write_line(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
