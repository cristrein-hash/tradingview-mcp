#!/usr/bin/env python3
"""Consolidated systematic-error guards (registry-based active gates).

WHY: passive recalled memory does not change behavior at action time. Each recurring systematic error
that has cost the project a redo-cycle becomes an ACTIVE pre/post-action gate here. Adding a new failure
mode = one CHECKS entry, not a new hook file.

Registered on BOTH PreToolUse and PostToolUse (see settings.json). Determines event from stdin:
  - tool_response present  -> POST (can inspect output)
  - tool_response absent   -> PRE  (can inspect command / write-content only)

Each check: id, when ('pre'|'post'), tools (which tool_names), needs (all regex must hit),
            blocks (any regex here suppresses — avoids firing on negation/lock contexts), msg.
Fires the FIRST matching check via stderr exit 2. Dedup per (session, check, sig) for 12h.

Exit: 0 pass-through, 2 inject reminder.
"""
import json, sys, re, hashlib, time
from pathlib import Path

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool = data.get("tool_name") or ""
ti = data.get("tool_input") or {}
tr = data.get("tool_response")
is_post = tr is not None
event = "post" if is_post else "pre"

# text sources
command = ti.get("command", "") or ""
content = (ti.get("content") or ti.get("new_string") or "") or ""
fpath = ti.get("file_path", "") or ""
output = ""
if isinstance(tr, dict):
    output = tr.get("output") or tr.get("stdout") or tr.get("content") or ""
    if isinstance(output, list):
        output = " ".join(str(x) for x in output)
elif isinstance(tr, str):
    output = tr

# Skip self-tests of the guards themselves
if "/hooks/" in command or ".claude/hooks" in command:
    sys.exit(0)

def src(name):
    return {"command": command, "content": content, "output": output, "fpath": fpath}.get(name, "")

# ---------- REGISTRY ----------
CHECKS = [
 dict(id="OOS_LOCK", when="pre", tools=("Bash","Write","Edit"), source=("command","content"),
   needs=[r"(out[\s-]?of[\s-]?sample|\bOOS\b|cross[\s-]?asset|held[\s-]?out|2013[\s_-]?2016|EUR/?USD|USOUSD)",
          r"(valida|validation|promov|promote|generaliz|próximo|proximo|\bnext\b|recomen|precisa|needs|test)"],
   blocks=[r"(não|nao|sem |proibid|trav+|forbidden|NUNCA|jamais|dentro dos 276|no[\s-]?oos|lock)"],
   msg=("🔒 OOS/CROSS-ASSET — TRAVADO (Cris 3+ vezes). Validação mora DENTRO dos 276: convergência causal + "
        "null/jackknife + sub-janela + lift por episódio. NÃO recomendar OOS/held-out/cross-asset. "
        "Ver feedback_no_oos_no_crossasset_validation.")),

 dict(id="FABRICATED_AGENTS", when="pre", tools=("Write","Edit"), source=("content","fpath"),
   # exige ALEGAÇÃO de EXECUÇÃO de agente (não só 'N especialistas' que descreve engine determinístico)
   needs=[r"(agent[_ ]diagnostics|painel de agentes|\bspawn|subagent|agentes\s+(rodaram|spawn|execut|geraram|cegos)|"
          r"(rodaram|spawnei|invoquei|executei)\s+\d*\s*agentes|\d+\s+agentes\s+(cegos|paralelos|especialistas))"],
   blocks=[r"(hand-written|escritos? à mão|NÃO spawn|nao spawn|teatro|fabricad|deterministico|determinístic|síntese própria)"],
   msg=("🎭 AGENTES — foram REALMENTE spawnados via Agent tool, ou escritos à mão? Em 367c2e8 'agentes' "
        "hand-written passaram por reais = teatro. Se não spawnou de verdade, NÃO os chame de agentes; "
        "spawne com Agent ou rotule como síntese própria.")),

 dict(id="ORPHAN_SCRIPT", when="post", tools=("Bash",), source=("command","output"),
   needs=[r"python3?\s+(-c\s|-\s*<<|<<\s*['\"]?\w*EOF|<<\s*PY)",
          r"(written|wrote|\.csv|sumR|runner|lift|WR[\s=:])"],
   blocks=[r"\.py\b.*\.py"],
   msg=("💾 OUTPUT ÓRFÃO — análise via python inline/heredoc que produz resultado SEM script salvo = "
        "irreprodutível (erro 367c2e8 + T6 hoje). Materialize como .py salvo e commitado antes de concluir.")),

 dict(id="CAPPED_R_ARBITER", when="post", tools=("Bash",), source=("output",),
   needs=[r"(capped|capad[oa]|realR|\+?3\.9R|cap_)",
          r"(WR[\s=:\d]|\bPF\b|sumR|win[_\s]?rate)",
          r"(melhor|best|separ|conclu|promiss|veredito|aprovad|edge)"],
   blocks=[r"(uncapped|não[\s-]?cap|nao[\s-]?cap|let[\s-]?run|V[\s-]?stair|hit[\s-]?rate não|convexid)"],
   msg=("📏 RÉGUA CAPADA — realR capado (+3.9R) = HIT-RATE, não expectancy; cega à convexidade/runner. "
        "NÃO usar como árbitro de edge/separação/promoção. Reavaliar em R UNCAPPED (let-run/V-stair).")),

 dict(id="PARALLEL_CONTEXT_BUILD", when="pre", tools=("Write","Edit"), source=("content","fpath"),
   # escrever um reader de contexto/regime/trajetória/mtf/macro que re-lê bars/store = provável paralelo do E0
   needs=[r"(_leg_read|leg_read|def _leg|def .*regime|def .*trend|lower[\s-]?high|higher[\s-]?low|"
          r"bars_15m|bars_1h|bars_4h|store/bars|read.*bars_|trajector|multi[\s-]?tf|swing)",
          r"(sinal|signal|classify|FRACO|FORTE|contexto|context|direç|direction|regime|viés|vies|bias|decis)"],
   # se JÁ consome E0/market_context/existente OU é o próprio pipeline E0 = ok (não bloqueia)
   blocks=[r"(market_context|external_factors|E0[_\s.]|dossi|consum|CONSUMIR|já existe|ja existe|"
           r"feedback_consume_existing|latest\.json|axes\[|/research/|/memory/|/docs/|test_|_smoke|_validation)"],
   msg=("🧠 CONTEXTO PARALELO? Antes de construir leitura de contexto/regime/mtf/trajetória/macro: o DOSSIÊ E0 "
        "(external_factors_v2/snapshots/market_context.json) JÁ dá mtf multi-TF (15/60/240/1D trend+CHoCH) + "
        "macro (real_yield/DXY/vix/event-window) + confluence sell/buy + regime + magnets, fresco e vivo. "
        "CONSUMIR, não reconstruir um reader paralelo (auto-boicote recorrente). Ver feedback_consume_existing_never_rebuild.")),
]

def applies(c):
    if c["when"] != event: return False
    if tool and c["tools"] and tool not in c["tools"]: return False
    return True

for c in CHECKS:
    if not applies(c): continue
    blob = "\n".join(src(s) for s in c["source"])
    if not blob.strip(): continue
    if any(re.search(b, blob, re.IGNORECASE) for b in c.get("blocks", [])): continue
    if not all(re.search(n, blob, re.IGNORECASE) for n in c["needs"]): continue
    # dedup
    sig = hashlib.sha256((c["id"] + "|" + blob[:300]).encode()).hexdigest()[:16]
    d = Path("/tmp/.claude_syserr_guards"); d.mkdir(exist_ok=True)
    sid = data.get("session_id") or "x"
    ack = d / f"{sid}_{c['id']}_{sig}"
    now = time.time()
    for f in d.glob("*"):
        try:
            if now - f.stat().st_mtime > 12*3600: f.unlink()
        except Exception: pass
    if ack.exists(): break
    ack.touch()
    try:
        import _guard_log; _guard_log.fire("systematic_error", "block", c.get("id", ""))
    except Exception:
        pass
    print(c["msg"], file=sys.stderr)
    sys.exit(2)

sys.exit(0)
