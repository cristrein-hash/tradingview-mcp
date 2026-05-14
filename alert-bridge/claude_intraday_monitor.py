#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request
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

TARGETS_FILE = BRIDGE_DIR / "monitor_targets_intraday.json"
POLICY_FILE = BRIDGE_DIR / "notification_policy.json"
ENV_FILE = BRIDGE_DIR / ".env"
LOG_DIR = BRIDGE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

OP_PROMPT = STRATEGY_DIR / "operational_prompt.md"
RULES = STRATEGY_DIR / "strategy_rules.json"
INTRADAY_PROMPT = STRATEGY_DIR / "intraday_scan_prompt.md"
MACRO_CONTEXT = STRATEGY_DIR / "macro_context_daily.md"

LAST_RESULT_FILE = LOG_DIR / "claude_intraday_monitor_last.json"
EVENTS_LOG = LOG_DIR / "claude_intraday_monitor_events.jsonl"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_iso(value: str):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def split_text(text: str, limit: int = 3800):
    chunks = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut == -1:
            cut = limit
        chunks.append(text[:cut])
        text = text[cut:].lstrip()
    if text:
        chunks.append(text)
    return chunks


def send_telegram(text: str):
    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Telegram não configurado no .env")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    ok = True
    for chunk in split_text(text):
        data = urlencode({
            "chat_id": chat_id,
            "text": chunk,
            "disable_web_page_preview": "true"
        }).encode("utf-8")

        req = Request(url, data=data, method="POST")
        with urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        ok = ok and bool(result.get("ok"))

    return ok


def load_policy():
    if POLICY_FILE.exists():
        return json.loads(POLICY_FILE.read_text())

    return {
        "telegram_policy": {
            "non_critical_cooldown_minutes_per_target": 60,
            "critical_events_bypass_cooldown": True,
            "send_short_summary_only": True
        },
        "critical_events": [
            "INTRADAY_SETUP_VALIDO",
            "INTRADAY_SETUP_FORTE",
            "INTRADAY_SETUP_EXCELENTE",
            "setup_invalidated",
            "risk_alert",
            "price_hit_invalidation",
            "price_hit_target"
        ]
    }


def build_prompt(targets: dict, test_mode: bool) -> str:
    active_targets = [
        t for t in targets.get("targets", [])
        if t.get("status") == "active"
    ]

    mode_text = "MODO TESTE: envie resumo completo de todos os alvos intraday." if test_mode else "MODO PRODUÇÃO: foque em mudanças relevantes."

    return textwrap.dedent(f"""
    Você está rodando como CLAUDE INTRADAY INTERNAL MONITOR.

    {mode_text}

    Leia obrigatoriamente estes arquivos antes de qualquer análise:
    {OP_PROMPT}
    {RULES}
    {INTRADAY_PROMPT}
    {MACRO_CONTEXT}

    Arquivo de alvos intraday internos:
    {TARGETS_FILE}

    Alvos intraday ativos para reavaliar:
    ```json
    {json.dumps(active_targets, ensure_ascii=False, indent=2)}
    ```

    Tarefa:
    - Use o TradingView MCP.
    - Reavalie apenas os alvos intraday ativos.
    - Para cada alvo, mude para o símbolo e timeframe principal.
    - Use timeframes secundários apenas se necessário.
    - Aplique a intraday_strategy_layer do strategy_rules.json.
    - Use macro_context_daily.md apenas como filtro de risco/timing/confiança.
    - Não faça novas buscas web nesta rodada; use apenas macro_context_daily.md como contexto macro salvo.
    - Não execute ordens.
    - Não edite Pine Script.
    - Não altere strategy_rules.json.
    - Não tente criar alertas no TradingView, pois alert_create MCP está falhando neste ambiente.
    - Nesta rodada, NÃO desenhe.
    - Seja objetivo.

    Mudança relevante intraday inclui:
    - INTRADAY_EM_OBSERVACAO virar INTRADAY_SETUP_VALIDO, FORTE ou EXCELENTE;
    - INTRADAY_NO_TRADE virar INTRADAY_EM_OBSERVACAO ou superior;
    - setup intraday invalidar;
    - RSI intraday entrar ou sair de extremo;
    - preço tocar nível local crítico;
    - probabilidade qualitativa subir ou cair;
    - prioridade subir ou cair;
    - US500 15M confirmar rejeição com RSI saindo de sobrecompra;
    - ETHUSD tocar zona 2261–2270 com RSI baixo;
    - XAUUSD confirmar ou perder zona 4658–4677.

    Formato obrigatório no topo da resposta:

    INTRADAY_MONITOR_META
    CHANGES_RELEVANT: YES ou NO
    CHANGE_COUNT: número
    HIGHEST_PRIORITY: ativo/timeframe ou nenhum

    Depois responda:

    INTRADAY MONITOR — RODADA
    Health:
    Hora:

    1. Resumo geral:
    - total de alvos:
    - mudanças relevantes:
    - maior prioridade agora:

    2. Alvos:
    Para cada alvo:
    - Ativo / TF:
    - Classificação anterior:
    - Classificação atual:
    - Direção:
    - Probabilidade qualitativa:
    - Confluências principais:
    - Bloqueio principal:
    - Mudança relevante? Sim/Não
    - Próxima ação:

    3. Ranking intraday atual:
    Liste do maior para o menor interesse operacional.

    4. Ação tomada:
    Normalmente: nenhuma ordem, nenhum Pine, nenhum alerta TradingView, nenhum desenho.

    MUITO IMPORTANTE — OBRIGATÓRIO:
    Ao final da resposta, você DEVE incluir um bloco JSON puro entre os marcadores abaixo.
    Esse bloco é obrigatório para o script local atualizar monitor_targets_intraday.json.
    Não omita esse bloco em nenhuma circunstância.
    Mesmo se não houver mudanças relevantes, inclua o JSON com relevant_change=false para todos os targets.
    Mesmo se algum alvo falhar, inclua esse target no JSON com a melhor informação disponível.
    Não use markdown dentro do JSON.
    Não coloque comentários dentro do JSON.
    Não coloque vírgulas finais inválidas.
    Use apenas JSON válido.

    STATE_UPDATE_JSON_START
    {{
      "summary": "resumo curto da rodada",
      "highest_priority": "ativo/timeframe ou nenhum",
      "targets": [
        {{
          "id": "id exato do target",
          "classification_current": "classificação atual",
          "probability_label_current": "Baixa | Média-baixa | Média | Média-alta | Alta",
          "priority_current": "Baixa | Média | Média-alta | Alta",
          "relevant_change": true,
          "critical_event": false,
          "event_types": ["probability_changed"],
          "change_reason": "motivo curto da mudança",
          "next_action": "próxima ação curta"
        }}
      ]
    }}
    STATE_UPDATE_JSON_END

    Regras para o JSON:
    - Inclua todos os targets ativos.
    - Use o id exatamente como veio em monitor_targets_intraday.json.
    - critical_event deve ser true se houver INTRADAY_SETUP_VALIDO, FORTE, EXCELENTE, invalidação, alvo ou risco crítico.
    - event_types deve conter tipos como:
      probability_changed, priority_changed, classification_observation_changed,
      zone_touched, rsi_entered_extreme, rsi_exited_extreme,
      INTRADAY_SETUP_VALIDO, INTRADAY_SETUP_FORTE, INTRADAY_SETUP_EXCELENTE,
      setup_invalidated, risk_alert, price_hit_invalidation, price_hit_target.
    """).strip()


def parse_state_update(stdout: str):
    match = re.search(
        r"STATE_UPDATE_JSON_START\s*(\{.*?\})\s*STATE_UPDATE_JSON_END",
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


def parse_changes_relevant(stdout: str):
    match = re.search(r"CHANGES_RELEVANT:\s*(YES|NO|SIM|NÃO|NAO)", stdout, re.IGNORECASE)
    if match:
        value = match.group(1).upper()
        return value in {"YES", "SIM"}

    if re.search(r"\bsem mudança relevante\b|\bsem mudanças relevantes\b|\bnenhuma mudança relevante\b", stdout, re.IGNORECASE):
        return False

    if re.search(r"mudança[s]? relevante[s]? detectada[s]?", stdout, re.IGNORECASE):
        return True

    return None


def parse_change_count(stdout: str):
    match = re.search(r"CHANGE_COUNT:\s*(\d+)", stdout, re.IGNORECASE)
    if match:
        return int(match.group(1))

    match = re.search(r"(\d+)\s+mudança[s]? relevante[s]? detectada[s]?", stdout, re.IGNORECASE)
    if match:
        return int(match.group(1))

    if re.search(r"\bsem mudança relevante\b|\bsem mudanças relevantes\b|\bnenhuma mudança relevante\b", stdout, re.IGNORECASE):
        return 0

    return None


def should_notify_target(target_before: dict, update: dict, policy: dict):
    if not update.get("relevant_change"):
        return False, "no_relevant_change"

    critical_events = set(policy.get("critical_events", []))
    event_types = set(update.get("event_types") or [])
    classification = str(update.get("classification_current", ""))

    is_critical = bool(update.get("critical_event")) or bool(event_types & critical_events)
    if classification in critical_events:
        is_critical = True

    if is_critical and policy.get("telegram_policy", {}).get("critical_events_bypass_cooldown", True):
        return True, "critical_event"

    cooldown_min = int(policy.get("telegram_policy", {}).get("non_critical_cooldown_minutes_per_target", 60))
    last_notified = parse_iso(target_before.get("last_notified_at", ""))

    if last_notified is None:
        return True, "no_previous_notification"

    elapsed = (datetime.now(timezone.utc) - last_notified).total_seconds() / 60.0
    if elapsed >= cooldown_min:
        return True, f"cooldown_elapsed_{int(elapsed)}m"

    return False, f"cooldown_active_{int(elapsed)}m"


def update_targets_file(targets_data: dict, state_update: dict, notified_ids: set):
    now = now_iso()
    updates_by_id = {
        item.get("id"): item
        for item in (state_update or {}).get("targets", [])
        if item.get("id")
    }

    for target in targets_data.get("targets", []):
        tid = target.get("id")
        update = updates_by_id.get(tid)

        target["last_checked_at"] = now

        if not update:
            continue

        if update.get("classification_current"):
            target["classification_last"] = update["classification_current"]

        if update.get("probability_label_current"):
            target["probability_label_last"] = update["probability_label_current"]

        if update.get("priority_current"):
            target["priority"] = update["priority_current"]

        target["last_relevant_change"] = bool(update.get("relevant_change"))
        target["last_change_reason"] = update.get("change_reason", "")
        target["last_event_types"] = update.get("event_types", [])
        target["last_next_action"] = update.get("next_action", "")

        if tid in notified_ids:
            target["last_notified_at"] = now

    TARGETS_FILE.write_text(json.dumps(targets_data, ensure_ascii=False, indent=2) + "\n")


def build_short_telegram_summary(state_update: dict, due_updates: list, stdout: str) -> str:
    highest = (state_update or {}).get("highest_priority") or "nenhum"
    summary = (state_update or {}).get("summary") or "Resumo não extraído."

    lines = [
        "⚡ [CLAUDE] Monitor Intraday",
        "",
        f"Mudanças notificadas: {len(due_updates)}",
        f"Maior prioridade: {highest}",
        "",
        f"Resumo: {summary}",
        "",
        "Alvos:"
    ]

    for item in due_updates[:6]:
        lines.append(
            f"- {item.get('id', 'sem_id')}: "
            f"{item.get('classification_current', '?')} | "
            f"Prob: {item.get('probability_label_current', '?')} | "
            f"Prioridade: {item.get('priority_current', '?')} | "
            f"{item.get('change_reason', '')}"
        )

    setup_valid_found = any(
        str(item.get("classification_current", "")) in {
            "INTRADAY_SETUP_VALIDO",
            "INTRADAY_SETUP_FORTE",
            "INTRADAY_SETUP_EXCELENTE"
        }
        for item in due_updates
    )

    if setup_valid_found:
        lines.insert(1, "🚨 Possível setup intraday válido detectado")

    lines.extend([
        "",
        "Ação:",
        "Sem ordens. Sem Pine. Sem alertas TradingView. Sem desenhos.",
        "Relatório completo salvo em:",
        "~/tradingview-mcp/alert-bridge/logs/claude_intraday_monitor_last.json"
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Claude intraday internal monitor")
    parser.add_argument("--test", action="store_true", help="Enviar resumo completo sempre")
    parser.add_argument("--notify-all", action="store_true", help="Enviar Telegram mesmo sem mudança relevante")
    args = parser.parse_args()

    if not TARGETS_FILE.exists():
        print(f"Arquivo não encontrado: {TARGETS_FILE}")
        sys.exit(1)

    targets_data = json.loads(TARGETS_FILE.read_text())
    policy = load_policy()
    prompt = build_prompt(targets_data, test_mode=args.test)

    cmd = [
        "claude",
        "-p",
        prompt,
        "--allowedTools",
        "Read,mcp__tradingview__*"
    ]

    started_at = datetime.now().isoformat()

    try:
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            text=True,
            capture_output=True,
            timeout=900
        )
    except subprocess.TimeoutExpired:
        msg = "⚠️ [CLAUDE] Monitor intraday excedeu timeout de 900s."
        send_telegram(msg)
        print(msg)
        sys.exit(1)

    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()

    state_update = parse_state_update(stdout)
    changes_relevant = parse_changes_relevant(stdout)
    change_count = parse_change_count(stdout)

    due_updates = []
    due_reasons = {}
    notified_ids = set()

    if state_update:
        before_by_id = {t.get("id"): t for t in targets_data.get("targets", [])}
        for update in state_update.get("targets", []):
            tid = update.get("id")
            before = before_by_id.get(tid, {})
            should_send, reason = should_notify_target(before, update, policy)
            due_reasons[tid] = reason
            if should_send:
                due_updates.append(update)
                notified_ids.add(tid)

    should_notify = bool(due_updates) or args.test or args.notify_all

    if state_update:
        update_targets_file(targets_data, state_update, notified_ids)

    data = {
        "started_at": started_at,
        "finished_at": datetime.now().isoformat(),
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "changes_relevant": changes_relevant,
        "change_count": change_count,
        "state_update_parsed": state_update is not None,
        "due_updates_count": len(due_updates),
        "due_reasons": due_reasons,
        "notified": False,
        "test_mode": args.test,
        "notify_all": args.notify_all,
        "stdout": stdout,
        "stderr": stderr
    }

    LAST_RESULT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    with EVENTS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

    if result.returncode != 0:
        text = (
            "⚠️ [CLAUDE] Monitor intraday falhou\n\n"
            f"STDOUT:\n{stdout}\n\n"
            f"STDERR:\n{stderr}"
        )
        send_telegram(text)
        print(text)
        sys.exit(result.returncode)

    print(stdout)
    print()

    if should_notify:
        if state_update and due_updates:
            telegram_text = build_short_telegram_summary(state_update, due_updates, stdout)
        elif args.test or args.notify_all:
            telegram_text = (
                "⚡ [CLAUDE] Monitor Intraday — teste\n\n"
                "Resumo completo salvo no log.\n\n"
                f"{stdout[:3000]}"
            )
        else:
            telegram_text = (
                "⚡ [CLAUDE] Monitor Intraday\n\n"
                "Mudança relevante detectada, mas state_update não foi extraído. Verificar log completo."
            )

        ok = send_telegram(telegram_text)
        data["notified"] = ok
        LAST_RESULT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        print("Telegram enviado:", ok)
    else:
        if state_update:
            print("Sem mudança relevante fora do cooldown. Telegram não enviado.")
        else:
            print("Aviso: não consegui extrair STATE_UPDATE_JSON. Telegram não enviado para evitar ruído.")


if __name__ == "__main__":
    main()
