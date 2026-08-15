#!/usr/bin/env python3
"""G6 — DAEMON-RELOAD RATE-LIMITER (Cris 2026-08-11).
BLOQUEIA (exit 2) reiniciar o MESMO daemon vezes demais numa janela curta. Fecha o B8: no dia 10/08
reiniciei daemons ~5× (cada fix) e cada restart zerou o anti-spam em memória → re-envio do mesmo sinal 3-5×
ao Telegram. Regra: junta as mudanças, reinicia UMA vez.

Deteta `launchctl kickstart|load|unload|bootstrap|bootout ... com.cristrein.<daemon>`. Regista timestamps por
label em ~/.claude/.daemon_reload_log.jsonl. Bloqueia se >= MAX reloads do mesmo label em WINDOW_S.
Escape: `RELOAD_OK` no comando (reinício deliberado justificado). Núcleo `decide()` puro. py3 stdlib."""
import sys, re, json, time
from pathlib import Path

LOG = Path.home() / ".claude" / ".daemon_reload_log.jsonl"
WINDOW_S = 600      # 10 min
MAX = 3             # >=3 reloads do mesmo daemon em 10 min = bloqueia o 4º
LABEL_RE = re.compile(r"(com\.cristrein\.[\w.-]+)")
ACTION_RE = re.compile(r"launchctl\s+(kickstart|load|unload|bootstrap|bootout|kill)", re.I)


def label_of(command):
    if not ACTION_RE.search(command):
        return None
    m = LABEL_RE.search(command)
    return m.group(1) if m else None


def decide(command, history, now):
    """(ok, msg, label). history = [(ts,label)]. Puro."""
    lbl = label_of(command)
    if not lbl:
        return True, "", None
    if re.search(r"\bRELOAD_OK\b", command):
        return True, "", lbl
    recent = [t for (t, l) in history if l == lbl and now - t < WINDOW_S]
    if len(recent) >= MAX:
        return False, (
            f"🛑 G6 — RESTART A MAIS DO MESMO DAEMON (Cris 2026-08-11)\n"
            f"  {lbl} já foi reiniciado {len(recent)}× nos últimos {WINDOW_S//60} min.\n"
            f"  RAIZ B8: restarts repetidos zeram o anti-spam em memória → mesmo sinal 3-5× no Telegram (dia 10/08).\n"
            f"  → JUNTA as mudanças e reinicia UMA vez; ou espera a janela; ou usa RELOAD_OK se for mesmo deliberado.\n"), lbl
    return True, "", lbl


def _history(now):
    out = []
    try:
        for l in LOG.read_text().splitlines():
            if not l.strip():
                continue
            try:
                e = json.loads(l)
                out.append((e.get("ts") or 0, e.get("label") or ""))
            except Exception:
                continue
    except Exception:
        pass
    return [(t, l) for (t, l) in out if now - t < WINDOW_S * 3]   # poda


def _append(label, now):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps({"ts": int(now), "label": label}) + "\n")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") not in (None, "Bash"):
        return 0
    cmd = ((data.get("tool_input") or {}).get("command")) or ""
    now = time.time()
    ok, msg, lbl = decide(cmd, _history(now), now)
    if lbl and ok:
        _append(lbl, now)      # regista o reload permitido
    if ok:
        return 0
    try:
        import _guard_log; _guard_log.fire("pre_daemon_reload", "block", msg.split("\n")[0][:120])
    except Exception:
        pass
    sys.stderr.write(msg)
    return 2


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        now = 1000000; L = "com.cristrein.entry-validator"
        hist3 = [(now - 60, L), (now - 120, L), (now - 180, L)]   # 3 recentes
        t = []
        ok, _, _ = decide(f"launchctl kickstart -k gui/501/{L}", [], now)
        t.append(("1º reload passa", ok is True))
        ok, _, _ = decide(f"launchctl kickstart -k gui/501/{L}", hist3, now)
        t.append(("4º em 10min bloqueia", ok is False))
        ok, _, _ = decide(f"launchctl kickstart -k gui/501/{L} RELOAD_OK", hist3, now)
        t.append(("RELOAD_OK escapa", ok is True))
        # daemon diferente não conta
        ok, _, _ = decide(f"launchctl kickstart -k gui/501/com.cristrein.vela-no-nivel", hist3, now)
        t.append(("outro daemon passa", ok is True))
        # velho (>10min) não conta
        old = [(now - 700, L), (now - 800, L), (now - 900, L)]
        ok, _, _ = decide(f"launchctl kickstart -k gui/501/{L}", old, now)
        t.append(("reloads velhos não contam", ok is True))
        # comando não-launchctl passa
        ok, _, lbl = decide("git status", hist3, now)
        t.append(("nao-launchctl passa", ok is True and lbl is None))
        for lab, r in t:
            print(f"  [{'OK' if r else 'FAIL'}] {lab}")
        allok = all(r for _, r in t)
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    sys.exit(main())
