#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import re
import subprocess
import sys
import textwrap

BASE_DIR = Path.home() / "tradingview-mcp"
BRIDGE_DIR = BASE_DIR / "alert-bridge"
STRATEGY_DIR = BASE_DIR / "my-strategy"

RESEARCH_LOG = BRIDGE_DIR / "logs/setup_research_log.jsonl"
OUTCOME_LOG = BRIDGE_DIR / "logs/setup_outcome_log.jsonl"
OUTCOME_SCHEMA = STRATEGY_DIR / "research/setup_outcome_schema.md"
RULES = STRATEGY_DIR / "strategy_rules.json"
OP_PROMPT = STRATEGY_DIR / "operational_prompt.md"
MACRO_CONTEXT = STRATEGY_DIR / "macro_context_daily.md"

DEFAULT_HORIZONS = [5, 10, 20, 50]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_jsonl(path: Path):
    if not path.exists():
        return []

    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def append_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def outcome_key(row):
    return (
        row.get("event_id", ""),
        int(row.get("bars_after", -1))
    )


def already_evaluated_keys():
    return {outcome_key(row) for row in load_jsonl(OUTCOME_LOG)}


def parse_event_dt(event):
    ts = event.get("received_at") or event.get("evaluated_at")
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        return None


def missing_horizons(event_id, horizons, done):
    return [h for h in horizons if (event_id, h) not in done]



def is_test_or_connectivity_event(event):
    text = " ".join(str(event.get(k, "")) for k in [
        "alert_type",
        "event",
        "reason",
        "expected_recheck",
        "alert_message",
        "telegram_reason",
        "drawing_name",
    ]).lower()

    if event.get("is_system_test") is True:
        return True

    test_markers = [
        "test_connectivity",
        "system_test",
        "teste manual",
        "teste controlado",
        "teste named tunnel",
        "teste local",
        "teste de conectividade",
        "cloudflare reiniciado",
        "webhook fixo",
        "named tunnel",
        "ssl ok",
    ]

    return any(marker in text for marker in test_markers)


def select_events(
    limit: int,
    horizons=None,
    since: str = "",
    timeframes=None,
    alert_types=None,
    skip_partial_50: bool = False,
    newest_first: bool = False,
    include_tests: bool = False,
):
    events = load_jsonl(RESEARCH_LOG)
    done = already_evaluated_keys()
    horizons = horizons or DEFAULT_HORIZONS

    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            if since_dt.tzinfo is None:
                since_dt = since_dt.replace(tzinfo=timezone.utc)
        except Exception:
            raise SystemExit(f"Erro: --since inválido: {since}. Use YYYY-MM-DD ou ISO datetime.")

    timeframe_set = set(str(x).strip() for x in (timeframes or []) if str(x).strip())
    alert_type_set = set(str(x).strip() for x in (alert_types or []) if str(x).strip())

    if newest_first:
        events = list(reversed(events))

    selected = []
    for event in events:
        event_id = event.get("event_id")
        if not event_id:
            continue

        if not include_tests and is_test_or_connectivity_event(event):
            continue

        if since_dt:
            dt = parse_event_dt(event)
            if not dt or dt < since_dt:
                continue

        if timeframe_set and str(event.get("timeframe", "")).strip() not in timeframe_set:
            continue

        if alert_type_set and str(event.get("alert_type", "")).strip() not in alert_type_set:
            continue

        missing = missing_horizons(event_id, horizons, done)

        # If all requested horizons already evaluated, skip.
        if not missing:
            continue

        # Useful for avoiding old events that only need the heavy 50-candle horizon.
        if skip_partial_50 and missing == [50]:
            continue

        event["_missing_horizons_for_dry_run"] = missing
        selected.append(event)

        if len(selected) >= limit:
            break

    return selected


def build_prompt(events, horizons):
    return textwrap.dedent(f"""
    Você está rodando como CLAUDE SETUP OUTCOME EVALUATOR.

    Objetivo:
    Avaliar o que aconteceu depois de alertas/reavaliações reais registrados no setup_research_log.jsonl.

    Leia obrigatoriamente:
    {OP_PROMPT}
    {RULES}
    {MACRO_CONTEXT}
    {OUTCOME_SCHEMA}

    Eventos para avaliar:
    ```json
    {json.dumps(events, ensure_ascii=False, indent=2)}
    ```

    Horizontes de avaliação:
    {horizons}

    Tarefa:
    - Use TradingView MCP apenas para buscar dados OHLCV necessários.
    - Para cada evento, use o symbol e timeframe do próprio evento.
    - Avalie os candles posteriores ao alerta.
    - Se ainda não houver candles suficientes para algum horizonte, marque outcome_label="insufficient_data".
    - Não invente resultado.
    - Não altere strategy_rules.json.
    - Não execute ordens.
    - Não crie alertas.
    - Não desenhe.
    - Não edite Pine Script.
    - Seja conservador com ajustes de estratégia.
    - Por padrão, should_adjust_strategy deve ser false.
    - Use should_adjust_strategy=true somente quando houver evidência recorrente em múltiplos eventos independentes, não por um caso isolado nem por múltiplos horizontes do mesmo evento.
    - Um único evento favorável, mesmo com MFE alto, deve gerar apenas suggested_learning e/ou proposed_adjustment_summary, mantendo should_adjust_strategy=false.
    - Múltiplos horizontes do mesmo event_id não contam como amostra independente.
    - Propostas que aumentem risco, afrouxem RSI, removam Bubbles ou promovam OBSERVAÇÃO para SETUP VÁLIDO exigem amostra mínima recorrente e devem permanecer como hipótese se a amostra for pequena.
    - Propostas operacionais de higiene, como dedup/cooldown de alertas repetidos, também devem ser suggested_learning primeiro, salvo evidência clara de repetição em vários event_id.

    Como inferir direção:
    - Se a direção/classificação indicar long/compra/demand/support/BOTTOM/LONG, direção provável = long.
    - Se indicar short/venda/supply/resistance/TOP/SHORT, direção provável = short.
    - Se for breakout, inferir pela direção do rompimento quando possível.
    - Se for invalidação, avaliar como evento de risco/breakdown, não como entrada.
    - Se estiver incerto, use inferred_direction="unknown" e direction_confidence="low".

    Como medir:
    Para long:
    - MFE = maior high após o alerta - preço do alerta.
    - MAE = menor low após o alerta - preço do alerta.

    Para short:
    - MFE = preço do alerta - menor low após o alerta.
    - MAE = preço do alerta - maior high após o alerta.

    Para unknown:
    - Calcule high_after, low_after e close_after.
    - MFE/MAE podem ser null.

    Labels sugeridos:
    - favorable_reaction: moveu claramente a favor da direção inferida.
    - adverse_reaction: moveu claramente contra.
    - sideways_noise: pouco movimento, sem direção útil.
    - breakout_continuation: breakout continuou.
    - false_breakout: breakout falhou rapidamente.
    - invalidation_confirmed: invalidação continuou na direção da quebra.
    - setup_missed: havia setup útil, mas não foi alertado como tal.
    - insufficient_data: candles insuficientes.
    - unclear: dados ou direção inconclusivos.

    Responda SOMENTE com JSON válido entre os marcadores:

    OUTCOME_JSON_START
    {{
      "evaluated_at": "{now_iso()}",
      "outcomes": [
        {{
          "event_id": "id exato do evento",
          "evaluated_at": "{now_iso()}",
          "symbol": "symbol",
          "timeframe": "timeframe",
          "alert_type": "alert_type",
          "drawing_name": "drawing_name",
          "strategy_layer": "Intraday|Swing|Ambas|unknown",
          "source_timeframe": "1H|30M|4H|1D|unknown",
          "price_at_alert": 0,
          "bars_after": 5,
          "close_at_alert": 0,
          "high_after": 0,
          "low_after": 0,
          "close_after": 0,
          "max_favorable_excursion": null,
          "max_adverse_excursion": null,
          "mfe_percent": null,
          "mae_percent": null,
          "inferred_direction": "long|short|breakdown|breakout|unknown",
          "direction_confidence": "high|medium|low",
          "direction_source": "texto do Claude / alert_type / drawing_name / unknown",
          "would_have_helped": false,
          "would_have_hurt": false,
          "was_noise": false,
          "outcome_label": "insufficient_data",
          "classification_at_signal": "classificação original",
          "was_setup_valid": false,
          "was_near_setup": false,
          "was_observation": false,
          "was_no_trade": false,
          "was_invalidated": false,
          "had_rsi_extreme_text": false,
          "had_bubbles_text": false,
          "had_top_bottom_text": false,
          "had_rejection_text": false,
          "had_rr_text": false,
          "macro_mentioned": false,
          "what_worked": "",
          "what_failed": "",
          "confluences_confirmed": [],
          "confluences_missing": [],
          "suggested_learning": "",
          "should_adjust_strategy": false,
          "proposed_adjustment_summary": ""
        }}
      ]
    }}
    OUTCOME_JSON_END

    Regras do JSON:
    - Incluir uma linha por evento e por horizonte.
    - Se há 2 eventos e 4 horizontes, retornar 8 outcomes.
    - Usar JSON válido.
    - Não usar markdown fora dos marcadores.
    - Não usar comentários.
    - Não usar trailing commas.
    """).strip()


def parse_outcome_json(stdout: str):
    match = re.search(
        r"OUTCOME_JSON_START\s*(\{.*?\})\s*OUTCOME_JSON_END",
        stdout,
        re.DOTALL
    )
    if not match:
        return None

    raw = match.group(1).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def main():
    parser = argparse.ArgumentParser(description="Evaluate setup outcomes via Claude + TradingView MCP")
    parser.add_argument("--limit", type=int, default=3, help="Number of unevaluated events to process")
    parser.add_argument("--horizons", default="5,10,20,50", help="Comma-separated candle horizons")
    parser.add_argument("--dry-run", action="store_true", help="Print prompt summary only, do not call Claude")
    parser.add_argument("--since", default="", help="Only select events received after this date/time, e.g. 2026-05-04")
    parser.add_argument("--timeframes", default="", help="Comma-separated timeframes to include, e.g. 15,30,60")
    parser.add_argument("--alert-types", default="", help="Comma-separated alert types to include")
    parser.add_argument("--skip-partial-50", action="store_true", help="Skip events missing only the 50-candle horizon")
    parser.add_argument("--newest-first", action="store_true", help="Select newest pending events first")
    parser.add_argument("--include-tests", action="store_true", help="Include test/connectivity events")
    args = parser.parse_args()

    horizons = [int(x.strip()) for x in args.horizons.split(",") if x.strip()]
    timeframes = [x.strip() for x in args.timeframes.split(",") if x.strip()]
    alert_types = [x.strip() for x in args.alert_types.split(",") if x.strip()]

    events = select_events(
        args.limit,
        horizons=horizons,
        since=args.since,
        timeframes=timeframes,
        alert_types=alert_types,
        skip_partial_50=args.skip_partial_50,
        newest_first=args.newest_first,
        include_tests=args.include_tests,
    )

    if not events:
        print("Nenhum evento pendente para avaliar.")
        return

    prompt = build_prompt(events, horizons)

    if args.dry_run:
        print(f"Eventos selecionados: {len(events)}")
        for e in events:
            missing = e.get("_missing_horizons_for_dry_run", [])
            print("-", e.get("event_id"), e.get("symbol"), e.get("timeframe"), e.get("alert_type"), "| missing:", missing)
        return

    # Remove internal dry-run helper keys before sending to Claude.
    for e in events:
        e.pop("_missing_horizons_for_dry_run", None)

    cmd = [
        "claude",
        "-p",
        prompt,
        "--allowedTools",
        "Read,mcp__tradingview__*"
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            text=True,
            capture_output=True,
            timeout=900
        )
    except subprocess.TimeoutExpired:
        print("Erro: avaliação excedeu timeout de 900s.")
        sys.exit(1)

    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()

    if result.returncode != 0:
        print("Claude retornou erro.")
        print(stderr)
        sys.exit(result.returncode)

    parsed = parse_outcome_json(stdout)
    if not parsed:
        print("Erro: não consegui extrair OUTCOME_JSON.")
        print(stdout[-2000:])
        sys.exit(1)

    outcomes = parsed.get("outcomes", [])
    if not outcomes:
        print("Nenhum outcome retornado.")
        return

    # Remove outcomes already evaluated, for safety.
    done = already_evaluated_keys()
    fresh = []
    for row in outcomes:
        key = outcome_key(row)
        if key in done:
            continue
        fresh.append(row)

    if fresh:
        append_jsonl(OUTCOME_LOG, fresh)

    print(f"Eventos avaliados pelo Claude: {len(events)}")
    print(f"Outcomes recebidos: {len(outcomes)}")
    print(f"Outcomes novos salvos: {len(fresh)}")
    print(f"Arquivo: {OUTCOME_LOG}")


if __name__ == "__main__":
    main()
