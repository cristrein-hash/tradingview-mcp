#!/usr/bin/env python3
"""COPILOT/JOURNAL — gerador do journal diário profundo (P2). Monta o material do dia, corre `claude -p`
(Opus, subscrição Max, SEM ANTHROPIC_API_KEY = custo zero), e escreve entries/AAAA-MM-DD.md + entries.jsonl
(bloco json) + lessons.jsonl (lições novas). Fallback determinístico se o claude falhar (nunca perde o dia).
Read-only sobre dados; NUNCA negoceia. py3.9.
Uso: python3 daily_journal.py [AAAA-MM-DD]        (escreve em entries/)
     python3 daily_journal.py --dry [AAAA-MM-DD]  (escreve em _dryrun/ + imprime, não toca no oficial)"""
import os, re, sys, json, shutil, subprocess, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import material as mat
LX = ZoneInfo("Europe/Lisbon")
PROMPTS = HERE / "prompts"
MODEL = os.environ.get("COPILOT_JOURNAL_MODEL", "opus")
CLAUDE = shutil.which("claude") or str(Path.home() / ".local/bin/claude")


def _extract_json(body):
    m = re.search(r"```json\s*(\{.*\})\s*```", body or "", re.S)
    if not m:
        m = re.search(r"(\{[\s\S]*\})\s*$", body or "")
    try:
        return json.loads(m.group(1)) if m else None
    except Exception:
        return None


def run_claude(grounding, instr_file="daily_instruction.md"):
    if not Path(CLAUDE).exists():
        return None, "claude CLI ausente"
    charter = (PROMPTS / "system_charter.md").read_text()
    instr = (PROMPTS / instr_file).read_text()
    prompt = f"GROUNDING (JSON determinístico — ecoa os números, não inventes):\n{json.dumps(grounding, ensure_ascii=False)}\n\n{instr}"
    env = dict(os.environ); env.pop("ANTHROPIC_API_KEY", None)     # força auth da assinatura Max (custo zero)
    try:
        r = subprocess.run([CLAUDE, "-p", prompt, "--append-system-prompt", charter,
                            "--output-format", "json", "--model", MODEL],
                           capture_output=True, text=True, timeout=420, env=env)
    except subprocess.TimeoutExpired:
        return None, "timeout claude -p"
    if r.returncode != 0:
        return None, f"claude rc={r.returncode}: {(r.stderr or r.stdout)[:200]}"
    try:
        body = json.loads(r.stdout).get("result", r.stdout)
    except Exception:
        body = r.stdout
    return body, None


def _fallback(M):
    """Entry mínima factual se o LLM falhar — nunca se perde o material do dia."""
    s = M.get("session", {})
    L = [f"# Journal — {M['date']} ({M['weekday']}, Lisboa)", "", "## 0. Snapshot da sessão",
         f"- {json.dumps(s, ensure_ascii=False)}", "", "## 3. Trades do Cris",
         f"- {len(M['cris_trades']) if isinstance(M['cris_trades'], list) else M['cris_trades']}",
         "", "_(fallback determinístico — claude -p indisponível; material preservado)_"]
    return "\n".join(L)


def main():
    dry = "--dry" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    date_str = args[0] if args else dt.datetime.now(LX).strftime("%Y-%m-%d")
    M = mat.build_material(date_str)
    body, err = run_claude(M)
    used_fallback = False
    if err or not body:
        body = _fallback(M); used_fallback = True

    outdir = (HERE / "_dryrun") if dry else (HERE / "entries")
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f"{date_str}.md").write_text(body)
    struct = _extract_json(body) or {"date": date_str, "parse_error": True}
    struct["date"] = date_str; struct["generated_ts"] = dt.datetime.now(LX).strftime("%Y-%m-%d %H:%M Lisboa")
    struct["fallback"] = used_fallback
    if not dry:
        with open(HERE / "entries.jsonl", "a") as fh:
            fh.write(json.dumps(struct, ensure_ascii=False) + "\n")
        for ls in struct.get("lessons", []) or []:
            with open(HERE / "lessons.jsonl", "a") as fh:
                fh.write(json.dumps({"date": date_str, **ls}, ensure_ascii=False) + "\n")
    print(f"journal {date_str}: {'DRY ' if dry else ''}{len(body)} chars -> {outdir.name}/{date_str}.md"
          + (f" | ERRO claude: {err} (fallback)" if used_fallback else "")
          + f" | trades={struct.get('trades')}")


if __name__ == "__main__":
    main()
