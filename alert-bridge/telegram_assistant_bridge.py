#!/usr/bin/env python3
"""PONTE Telegram <-> Claude Code — workflow de trabalho remoto do Cris (chat privado @Cristrein_Trading_bot).
O Cris manda mensagens; cada uma corre `claude -p` headless no repo (autonomia total + sessão persistente)
e a resposta volta ao chat privado. WHITELIST DURA do chat_id (ignora todos os outros). Kill-switch em 3
camadas (/stop, flag file, launchctl). Sinais continuam à parte no grupo (não tocado). NUNCA loga o token.
py3.9, só urllib (sem libs de bot). Uso: python3 telegram_assistant_bridge.py [--whoami]"""
import os, sys, json, time, uuid, queue, threading, subprocess, urllib.parse, urllib.request, datetime as dt
from pathlib import Path

BASE = Path(__file__).resolve().parent          # alert-bridge/
REPO = BASE.parent                               # raiz do repo (cwd do claude)
ENV = BASE / ".env"
LOGS = BASE / "logs"; LOGS.mkdir(exist_ok=True)
CLAUDE = os.environ.get("CLAUDE_EXE", "/Users/cristrein/.local/bin/claude")
CWD = str(REPO)
FLAG_OFF = LOGS / ".bridge_off"                  # já gitignored (logs/*)
PIDFILE = LOGS / "assistant_bridge.pid"
OFFSET_F = LOGS / "assistant_bridge_offset.json"
SESSION_F = LOGS / "assistant_bridge_session.json"
AUDIT_F = LOGS / "assistant_bridge_audit.jsonl"
TG_POLL_TIMEOUT = 50
CLAUDE_TIMEOUT = 600
CHUNK = 4000
STARTED_AT = time.time()


def load_env():
    env = {}
    for line in ENV.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


# ---------------- Telegram (urllib) ----------------
def tg(method, params, token, timeout=60):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}", data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def send(token, chat_id, text):
    """Envia em chunks <=CHUNK, sem parse_mode (robusto a <,&,código,tabelas)."""
    text = text or "(vazio)"
    while text:
        chunk = text[:CHUNK]
        if len(text) > CHUNK:
            cut = chunk.rfind("\n")
            if cut > CHUNK * 0.5:
                chunk = chunk[:cut]
        try:
            tg("sendMessage", {"chat_id": chat_id, "text": chunk, "disable_web_page_preview": "true"}, token)
        except Exception as e:
            print(f"[send] falhou: {type(e).__name__}", flush=True)
        text = text[len(chunk):]


def typing(token, chat_id):
    try:
        tg("sendChatAction", {"chat_id": chat_id, "action": "typing"}, token)
    except Exception:
        pass


# ---------------- estado (offset / sessão) ----------------
def load_offset():
    try:
        return json.loads(OFFSET_F.read_text()).get("offset", 0)
    except Exception:
        return 0


def save_offset(o):
    tmp = OFFSET_F.with_suffix(".json.tmp"); tmp.write_text(json.dumps({"offset": o})); os.replace(tmp, OFFSET_F)


def load_session():
    try:
        return json.loads(SESSION_F.read_text())
    except Exception:
        s = {"session_id": str(uuid.uuid4()), "started": False, "created_at": int(time.time())}
        save_session(s); return s


def save_session(s):
    tmp = SESSION_F.with_suffix(".json.tmp"); tmp.write_text(json.dumps(s)); os.replace(tmp, SESSION_F)


def new_session():
    s = {"session_id": str(uuid.uuid4()), "started": False, "created_at": int(time.time())}
    save_session(s); return s


def audit(rec):
    rec["ts"] = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        with open(AUDIT_F, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ---------------- Claude ----------------
def run_claude(text):
    s = load_session()
    args = [CLAUDE, "-p", text, "--dangerously-skip-permissions", "--output-format", "json"]
    args += (["--resume", s["session_id"]] if s.get("started") else ["--session-id", s["session_id"]])
    env = dict(os.environ); env.pop("ANTHROPIC_API_KEY", None)
    try:
        r = subprocess.run(args, cwd=CWD, capture_output=True, text=True, timeout=CLAUDE_TIMEOUT, env=env)
    except subprocess.TimeoutExpired:
        return f"⚠️ timeout ({CLAUDE_TIMEOUT}s) — a tarefa era longa demais. Tenta partir em passos ou /new.", "timeout"
    except Exception as e:
        return f"⚠️ erro ao correr claude: {type(e).__name__}", "exc"
    if r.returncode != 0:
        # nunca ecoar stderr cru (pode ter paths/segredos) — só o código
        return f"⚠️ claude saiu com código {r.returncode}. (/new para reiniciar a sessão se persistir)", f"rc{r.returncode}"
    try:
        d = json.loads(r.stdout)
    except Exception:
        return "⚠️ resposta ilegível do claude.", "parsefail"
    sid = d.get("session_id")
    if sid:
        s["session_id"] = sid
    s["started"] = True
    save_session(s)
    if d.get("is_error"):
        return f"⚠️ claude reportou erro: {(d.get('result') or '')[:200]}", "is_error"
    return (d.get("result") or "(sem conteúdo)"), "ok"


# ---------------- comandos ----------------
def handle_command(token, chat_id, text, q):
    cmd = text.strip().split()[0].lower()
    if cmd in ("/new", "/reset"):
        new_session(); send(token, chat_id, "🆕 Nova sessão iniciada (contexto reiniciado).")
    elif cmd == "/stop":
        FLAG_OFF.touch(); send(token, chat_id, "⏸ Ponte PAUSADA. As tuas mensagens não serão processadas. /start para retomar.")
    elif cmd == "/start":
        FLAG_OFF.unlink(missing_ok=True); send(token, chat_id, "▶️ Ponte ATIVA.")
    elif cmd == "/status":
        s = load_session(); up = int(time.time() - STARTED_AT)
        off = "PAUSADA" if FLAG_OFF.exists() else "ativa"
        send(token, chat_id, f"📊 Ponte {off} | sessão {s['session_id'][:8]} (started={s.get('started')}) | "
                             f"fila={q.qsize()} | uptime={up//3600}h{(up%3600)//60}m")
    else:
        send(token, chat_id, "Comandos: /new (nova sessão) · /stop · /start · /status. Qualquer outro texto = trabalho comigo.")


# ---------------- worker (serializa chamadas claude) ----------------
def worker(token, q):
    while True:
        chat_id, text = q.get()
        if FLAG_OFF.exists():
            send(token, chat_id, "⏸ Ponte pausada (/start p/ retomar)."); q.task_done(); continue
        typing(token, chat_id)
        t0 = time.time()
        result, status = run_claude(text)
        dur = round(time.time() - t0, 1)
        send(token, chat_id, result)
        audit({"chat_id": chat_id, "in": text[:200], "status": status, "dur_s": dur, "out_len": len(result or "")})
        q.task_done()


# ---------------- poller ----------------
def poller(token, authz, q):
    offset = load_offset()
    print(f"[bridge] poller ativo | whitelist chat_id={authz} | cwd={CWD}", flush=True)
    while True:
        try:
            u = tg("getUpdates", {"offset": offset, "timeout": TG_POLL_TIMEOUT, "allowed_updates": json.dumps(["message"])},
                   token, timeout=TG_POLL_TIMEOUT + 15)
        except Exception as e:
            print(f"[poller] getUpdates erro: {type(e).__name__} — retry 3s", flush=True); time.sleep(3); continue
        if not u.get("ok"):
            time.sleep(3); continue
        for upd in u.get("result", []):
            offset = upd["update_id"] + 1; save_offset(offset)
            msg = upd.get("message") or {}
            chat = msg.get("chat", {}); chat_id = chat.get("id"); text = msg.get("text")
            if str(chat_id) != str(authz):
                continue  # WHITELIST DURA — ignora em silêncio (audita minimamente)
            if not text:
                send(token, chat_id, "(só processo texto por agora.)"); continue
            audit({"chat_id": chat_id, "in": text[:200], "status": "received"})
            if text.startswith("/"):
                handle_command(token, chat_id, text, q)          # imediato (kill-switch funciona mid-run)
            elif FLAG_OFF.exists():
                send(token, chat_id, "⏸ Ponte pausada (/start p/ retomar).")
            else:
                send(token, chat_id, "⏳ recebido, a trabalhar…")
                q.put((chat_id, text))


def main():
    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN"); authz = env.get("AUTHORIZED_CHAT_ID")
    if not token or not authz:
        print("FATAL: falta TELEGRAM_BOT_TOKEN ou AUTHORIZED_CHAT_ID no .env", flush=True); sys.exit(1)

    if "--whoami" in sys.argv:
        u = tg("getUpdates", {"timeout": 0}, token)
        for upd in u.get("result", []):
            c = (upd.get("message") or {}).get("chat", {})
            if c: print(f"chat_id={c.get('id')} type={c.get('type')} name={c.get('first_name') or c.get('title')}")
        return

    # instância única
    if PIDFILE.exists():
        try:
            old = int(PIDFILE.read_text().strip()); os.kill(old, 0)
            print(f"FATAL: já corre uma ponte (pid {old})", flush=True); sys.exit(1)
        except (ProcessLookupError, ValueError):
            pass
    PIDFILE.write_text(str(os.getpid()))

    q = queue.Queue()
    threading.Thread(target=worker, args=(token, q), daemon=True).start()
    try:
        poller(token, authz, q)
    finally:
        PIDFILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
