#!/usr/bin/env python3
"""Headless Telegram DRAFT — L1 · EMA21 CONTINUATION (Production v2, peça 4).

Lê UMA linha JSON (decisão humana do journal OU outcome) via stdin e gera APENAS o
TEXTO do sinal no stdout. NUNCA envia Telegram, nunca toca secrets/receiver. É um
rascunho para revisão humana — telegram_allowed permanece false por design.

KEEP  -> draft de sinal de entrada (DRAFT_ONLY / HUMAN_REVIEW).
BLOCK -> draft de "no signal / blocked", nunca sinal de entrada.

NÃO faz: envio, MCP/chart, daemon, produção, escrita de arquivo. Standalone.

Uso:
  ... | python3 journal.py --decision KEEP ... | python3 telegram_draft.py
  python3 telegram_draft.py < uma_linha.json
"""
import json, sys


def main():
    raw = sys.stdin.read().strip()
    if not raw:
        print("error: no JSON on stdin (pipe journal.py or outcome.py output)", file=sys.stderr)
        return 2
    # aceita 1 linha JSON; se vierem várias, usa a última
    obj = None
    for ln in raw.splitlines():
        ln = ln.strip()
        if ln:
            try: obj = json.loads(ln)
            except Exception: pass
    if obj is None:
        print("error: invalid JSON on stdin", file=sys.stderr)
        return 2

    strategy = obj.get("strategy", "L1 · EMA21 CONTINUATION")
    suite = obj.get("suite", "XAU 4H LONG — CONTINUATION")
    symbol = obj.get("symbol", "PEPPERSTONE:XAUUSD")
    tf = obj.get("timeframe", "240")
    ts = obj.get("candidate_timestamp", "?")
    decision = obj.get("human_decision", "BLOCK")
    flags = obj.get("block_or_review_flags") or obj.get("block_or_review") or {}
    reason = obj.get("reason", "")
    # outcome fields (opcionais, se a linha for um outcome_result)
    r_result = obj.get("r_result"); result_status = obj.get("result_status")

    def fmt_flags(fl):
        if not isinstance(fl, dict):
            return "  (sem flags)"
        out = []
        for k, v in fl.items():
            if k == "values":
                continue
            out.append(f"  {'⚠️' if v else '·'} {k}: {v}")
        vals = fl.get("values") or {}
        if vals:
            out.append(f"  valores: {json.dumps(vals, ensure_ascii=False)}")
        return "\n".join(out) if out else "  (sem flags)"

    event_type = obj.get("event_type")
    lines = []
    lines.append(f"📋 {suite}")
    lines.append(f"   {strategy}")
    lines.append(f"{symbol} · {tf} · {ts}")
    lines.append("")

    # signal_emitted = NOTIFICAÇÃO DE CANDIDATO (não é ordem de entrada, não é trade validado)
    if event_type == "signal_emitted":
        lines.append("🔔 CANDIDATE NOTIFICATION — revise o chart")
        lines.append("Candidato L1 gerado. NÃO é entrada aprovada nem trade validado.")
        lines.append("A decisão de ENTRAR é humana e vem depois (journal: human_review_decision).")
        if obj.get("signal_hash"):
            lines.append(f"signal_hash: {obj.get('signal_hash')}")
        lines.append("")
        lines.append("status: DRAFT_ONLY / CANDIDATE_NOTIFICATION · telegram_allowed: false · NÃO ENVIADO")
        print("\n".join(lines))
        return 0

    entry_taken = bool(obj.get("entry_taken"))
    execution_mode = obj.get("execution_mode") or "NONE"
    if decision == "KEEP" and not entry_taken:
        lines.append("✅ KEEP / NO ENTRY RECORDED — candidato aprovado, SEM entrada real registrada")
        lines.append("Flags BLOCK/REVIEW (exaustão):")
        lines.append(fmt_flags(flags))
        lines.append("")
        lines.append("Entrada LONG (rascunho) — confirmar manualmente no chart antes de operar.")
    elif decision == "KEEP" and entry_taken:
        lines.append("🟢 KEEP / REAL ENTRY RECORDED — entrada real registrada")
        lines.append(f"execução: {execution_mode} · entry {obj.get('entry_price')} · stop {obj.get('stop_price')} · @ {obj.get('entry_ts')}")
        if obj.get("target_plan"): lines.append(f"alvo: {obj.get('target_plan')}")
        if obj.get("position_size"): lines.append(f"size: {obj.get('position_size')}")
        lines.append("Flags BLOCK/REVIEW (exaustão):")
        lines.append(fmt_flags(flags))
    else:
        lines.append(f"⛔ DECISÃO HUMANA: {decision} — NO SIGNAL / BLOCKED")
        lines.append("Flags BLOCK/REVIEW (exaustão):")
        lines.append(fmt_flags(flags))
        lines.append("")
        lines.append("Nenhum sinal de entrada gerado.")
    if reason:
        lines.append(f"Motivo: {reason}")
    if result_status is not None or r_result is not None:
        lines.append(f"Outcome (post-hoc, RAW): {result_status} r={r_result}")
    lines.append("")
    lines.append("status: DRAFT_ONLY / HUMAN_REVIEW · telegram_allowed: false · NÃO ENVIADO")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
