#!/usr/bin/env python3
"""L1 EMA21 4H LONG — camada de RISCO / CAPACIDADE / JOURNAL (FROZEN, 2026-07-09).

⚠️ NÃO WIRED A PRODUÇÃO/BROKER/RUNTIME. Funções PURAS (sem I/O, sem side-effects, sem envio).
Nenhum módulo de runtime importa este ficheiro — camada dormente até autorização explícita de go-live.
Fail-closed: qualquer violação OU ambiguidade => BLOCK. L1 é LONG-only.

Política inicial (Cris 2026-07-09): max 2 posições L1, max 2 no mesmo símbolo, risco agregado €200,
€100 por posição, sem 3º slot, sem hedge, broker manual-approval-only.
"""

RULES = {
    "max_open_l1_positions": 2,
    "max_same_symbol_l1_positions": 2,
    "max_total_l1_open_risk_eur": 200.0,
    "position_risk_mode": "fixed_equal",
    "each_position_risk_eur": 100.0,
    "duplicate_same_bar_signal": "BLOCK",
    "opposite_position_hedge": "NOT_ALLOWED_FOR_L1",
    "broker_execution": "MANUAL_APPROVAL_ONLY",
    "telegram_signal": "HUMAN_REVIEW_ONLY",
    "auto_broker_execution": "NOT_AUTHORIZED_YET",
}

JOURNAL_FIELDS = [
    "trade_id", "strategy_id", "symbol", "timeframe", "bar_time", "signal_time",
    "entry", "sl", "target", "risk_eur", "slot_index",
    "open_l1_positions_before", "open_l1_positions_after",
    "aggregate_open_risk_eur_before", "aggregate_open_risk_eur_after",
    "decision_state", "human_status", "broker_status", "telegram_status",
    "source_snapshot", "created_at",
]


def evaluate_capacity(open_positions, candidate, rules=RULES):
    """Decide se um novo candidato L1 pode ocupar um slot. FAIL-CLOSED.
    open_positions: lista de {symbol, bar_time, direction, risk_eur}.
    candidate: {symbol, bar_time, direction(='LONG'), risk_eur}.
    Retorna dict: allow, reasons[], slot_index, open_before/after, risk_before/after, decision_state."""
    reasons = []
    sym = candidate.get("symbol")
    bt = candidate.get("bar_time")
    direction = candidate.get("direction", "LONG")
    risk = candidate.get("risk_eur", rules["each_position_risk_eur"])
    open_before = len(open_positions)
    risk_before = round(sum(float(p.get("risk_eur", 0) or 0) for p in open_positions), 2)

    if not isinstance(risk, (int, float)):
        reasons.append("risk_not_numeric")
        risk = rules["each_position_risk_eur"]
    if direction != "LONG":
        reasons.append("direction_not_LONG_L1_is_long_only")
    if any((p.get("direction") not in (None, "LONG")) for p in open_positions):
        reasons.append("hedge_or_opposite_position_present")
    if bt is None or sym is None:
        reasons.append("missing_symbol_or_bar_time")
    if any(p.get("symbol") == sym and p.get("bar_time") == bt for p in open_positions):
        reasons.append("duplicate_same_bar_signal")
    if open_before >= rules["max_open_l1_positions"]:
        reasons.append("max_open_l1_positions_reached")
    if sum(1 for p in open_positions if p.get("symbol") == sym) >= rules["max_same_symbol_l1_positions"]:
        reasons.append("max_same_symbol_l1_positions_reached")
    if risk > rules["each_position_risk_eur"] + 1e-9:
        reasons.append("per_position_risk_exceeds_limit")
    if round(risk_before + risk, 2) > rules["max_total_l1_open_risk_eur"] + 1e-9:
        reasons.append("aggregate_open_risk_exceeds_limit")

    allow = (len(reasons) == 0)
    return {
        "allow": allow,
        "reasons": reasons,
        "slot_index": (open_before if allow else None),
        "open_before": open_before,
        "open_after": (open_before + 1 if allow else open_before),
        "risk_before": risk_before,
        "risk_after": (round(risk_before + risk, 2) if allow else risk_before),
        "decision_state": ("ALLOW_MANUAL_APPROVAL" if allow else "BLOCK"),
    }


def build_journal_record(candidate, cap, trade_id, signal_time, source_snapshot, created_at):
    """Monta o registro de journal (por-trade). human/broker/telegram = pendentes/não-executado.
    PURO: recebe timestamps por parâmetro (sem relógio interno). NÃO escreve em disco."""
    return {
        "trade_id": trade_id,
        "strategy_id": "L1_EMA21_CONTINUATION",
        "symbol": candidate.get("symbol"),
        "timeframe": candidate.get("timeframe", "240"),
        "bar_time": candidate.get("bar_time"),
        "signal_time": signal_time,
        "entry": candidate.get("entry"),
        "sl": candidate.get("sl"),
        "target": candidate.get("target"),
        "risk_eur": candidate.get("risk_eur", RULES["each_position_risk_eur"]),
        "slot_index": cap.get("slot_index"),
        "open_l1_positions_before": cap.get("open_before"),
        "open_l1_positions_after": cap.get("open_after"),
        "aggregate_open_risk_eur_before": cap.get("risk_before"),
        "aggregate_open_risk_eur_after": cap.get("risk_after"),
        "decision_state": cap.get("decision_state"),
        "human_status": "PENDING_REVIEW",
        "broker_status": "NOT_EXECUTED_MANUAL_ONLY",
        "telegram_status": "NOT_SENT",
        "source_snapshot": source_snapshot,
        "created_at": created_at,
    }
