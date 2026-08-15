#!/usr/bin/env python3
"""Contextual-Read guard (PreToolUse Bash|Write|Edit) — Cris 2026-07-20.

Bloqueio EXECUTÁVEL mais forte que memória (memória é ignorável, provado). DUAS regras:

  A. SUBSTITUIÇÃO (qualquer tool): computar uma banda/std como nível OU hardcodar um preço-zona = inventar um
     substituto de indicador → BLOQUEIA.
  B. COMPLETUDE (Bash que lê indicador): tocar num indicador PARCIAL (pine_boxes / study_values /
     data_get_pine_* / OB Detector / SMC / SVP / RSI / DMI ...) SEM ter corrido a leitura COMPLETA
     (`my-strategy/core/contextual_read.py`, token `.crp_state.json` fresco ≤15min) → BLOQUEIA.
     Força-me a ler TODOS os indicadores em profundidade ANTES de cherry-pick / decisão / invenção.

Exit: 0 = passa · 2 = BLOQUEIA (stderr → Claude vê como feedback de sistema)."""
import json, sys, re, time
from pathlib import Path

TOKEN = Path("/Users/cristrein/tradingview-mcp/my-strategy/core/.crp_state.json")
CRP_FRESH_S = 900   # a leitura completa vale 15 min

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
tn = data.get("tool_name", "")
ti = data.get("tool_input") or {}
text = " ".join(str(ti.get(k, "")) for k in ("command", "content", "new_string", "file_path"))
if not text.strip():
    sys.exit(0)
low = text.lower()

# --- Regra C (Cris 2026-08-14): DERIVAR ESTRUTURA de OHLC crua SEM ler o indicador real ---
# Fecha o buraco do estudo faca-vs-dip: re-derivei choch/pivots de RAW OHLC p/ decisão, sem ler OB/SMC.
# Dispara MESMO em /research/ (a isenção larga não a bypassa). Bypass = ler o indicador (pine_boxes) OU
# token READ_OB_ZONES OU leitura completa fresca. Só o próprio leitor/guards ficam isentos.
_SELF = ("/hooks/", "contextual_read", "read_ob_zones", ".crp_state", "crp_guard", "check_no_invented")
if tn == "Bash" and not any(x in low for x in _SELF) and re.search(r"python3?\s+\S+\.py|python3?\s*<<", text):
    _blob = text
    _mm = re.search(r"python3?\s+(\S+\.py)", text)
    if _mm:
        try:
            _blob += "\n" + Path(_mm.group(1)).read_text(errors="ignore")[:20000]
        except Exception:
            pass
    _deriv = re.search(r"choch|fractal_pivot|context_structure|def structure|pivot_high|pivot_low|"
                       r"higher[\s-]?low|lower[\s-]?high", _blob, re.I)
    _ohlc = re.search(r"raw_\dh_ohlc|bars_\d+m|_native_bars|store_reader\.bars|ohlcv", _blob, re.I)
    _hasob = re.search(r"READ_OB_ZONES|pine_boxes|data_get_pine_boxes|ob_zones|\.polarity_state", _blob, re.I)
    if _deriv and _ohlc:
        _fresh = False
        try:
            _fresh = (time.time() - float(json.loads(TOKEN.read_text())["ts"])) < CRP_FRESH_S
        except Exception:
            _fresh = False
        if _hasob or _fresh:
            if re.search(r"READ_OB_ZONES", _blob):     # log do bypass por token
                try:
                    _Lg = Path.home() / ".claude/hooks/logs"; _Lg.mkdir(parents=True, exist_ok=True)
                    open(_Lg / "bypass_uses.log", "a").write(json.dumps(
                        {"ts": int(time.time()), "guard": "contextual_read_C", "token": "READ_OB_ZONES",
                         "cmd": text[:200]}) + "\n")
                except Exception:
                    pass
        else:
            print("🛑 CONTEXTUAL-READ GUARD — DERIVAÇÃO-SEM-INDICADOR BLOQUEADO (Cris 2026-08-14)\n"
                  "  Script deriva estrutura (choch/pivots) de OHLC crua SEM ler o OB/SMC real — o erro do estudo faca-vs-dip.\n"
                  "  → LÊ o indicador real primeiro: MCP data_get_pine_boxes (OB Detector) ou store pine_boxes_*.json.\n"
                  "  → OU corre my-strategy/core/contextual_read.py (token fresco ≤15min) OU declara READ_OB_ZONES (derivas de OB lida).\n"
                  "  Estrutura/zona vem SEMPRE do indicador, NUNCA re-derivada de OHLC crua.", file=sys.stderr)
            try:
                import _guard_log; _guard_log.fire("contextual_read_ruleC", "block", "deriva estrutura de OHLC sem ler indicador")
            except Exception:
                pass
            sys.exit(2)

# isenções: o próprio leitor/guards/bar-store/research/limpezas + token de derivação legítima de OB já lida
EXEMPT = ("/hooks/", "contextual_read", "check_no_invented_zones", "/research/", "test_", "bar_store_cycle",
          "read_ob_zones", "derrubad", "invenç", "invenc", ".crp_state", "crp_guard")
if any(x in low for x in EXEMPT):
    sys.exit(0)

fp = str(ti.get("file_path", ""))
live = ("python" in low) or any(g in fp for g in ("my-strategy/", "alert-bridge/", "external_factors_v2/"))


def block(kind, extra):
    print(f"🛑 CONTEXTUAL-READ GUARD — {kind} BLOQUEADO (mais forte que memória, por design)\n"
          f"{extra}\n"
          "  → LÊ TODOS os indicadores primeiro: `python3 my-strategy/core/contextual_read.py`\n"
          "     (OB Detector/SMC/SVP + RSI/DMI/NAS/Bubbles/CHOP, todos os TFs, cada zona marcada vs preço).\n"
          "  → Dias anteriores: MCP `chart_scroll_to_date` + `data_get_pine_boxes` (zonas OB persistem).\n"
          "  → Zona/nível vem SEMPRE do indicador lido, NUNCA computado/hardcodado. Deriva de OB lida = token 'READ_OB_ZONES'.\n"
          "  (docs/architecture/CONTEXTUAL_READ_PROTOCOL.md)", file=sys.stderr)
    try:
        import _guard_log; _guard_log.fire("contextual_read", "block", kind)
    except Exception:
        pass
    sys.exit(2)


# --- Regra A: SUBSTITUIÇÃO inventada (qualquer tool que escreve/corre código live) ---
BAND = re.compile(r"(mean\s*[+\-]\s*\w+\s*\*\s*sd)|(\b(upper|lower)\s*,\s*(upper|lower)\s*=)|bollinger", re.I)
ZONE = re.compile(r"(lo|hi|zona|zone|banda|band|magnet|íman|iman)\W{0,12}(3[5-9]\d\d|4[0-4]\d\d)\.\d", re.I)
if live and (BAND.search(text) or ZONE.search(text)):
    block("SUBSTITUIÇÃO", "  Detetado: banda estatística ou preço-zona hardcodado a substituir o indicador real.")

# --- Regra B: COMPLETUDE — tocar num indicador parcial exige leitura COMPLETA feita ---
IND = re.compile(r"pine_boxes|study_values|data_get_pine_(boxes|lines|labels|tables|shapes)|data_get_study_values|"
                 r"ob detector|smart money|session volume|\bsvp\b|choppiness|directional movement|\brsi\b", re.I)
if tn == "Bash" and IND.search(text):
    fresh = False
    try:
        fresh = (time.time() - float(json.loads(TOKEN.read_text())["ts"])) < CRP_FRESH_S
    except Exception:
        fresh = False
    if not fresh:
        block("COMPLETUDE", "  Tocaste num indicador PARCIAL sem a leitura completa recente (cherry-pick = como falhei hoje).")
sys.exit(0)
