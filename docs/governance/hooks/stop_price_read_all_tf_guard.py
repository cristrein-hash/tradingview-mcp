#!/usr/bin/env python3
"""G8 — LEITURA DE PREÇO EXIGE TODOS OS TFS (Cris 2026-08-11).

Stop-hook: quando o Cris PEDE leitura de preço, BLOQUEIA (exit 2) o fim do turno se eu NÃO li todos os
TFs do stack MTF (5M/15M/1H/4H/1D). Fecha o erro recorrente de ler UM só TF (li OB só no 1H → mandei
o Cris à demanda profunda 4316 quando o timing real estava no 5M em 4394). Auto-disciplina de LLM não
segura → bloqueio determinístico externo, como os G1–G7.

Como funciona: no Stop, lê o transcript, encontra a ÚLTIMA mensagem do utilizador. Se ela pede leitura
de preço (regex PRICE_REQ), verifica os `chart_set_timeframe` que fiz NESTE turno + houve leitura de
dados (data_get_pine_boxes/study_values/ohlcv). Se faltam ≥2 TFs do stack → bloqueia e diz quais faltam.

Escape auditável: incluir `TF_READ_WAIVED: <razão>` na resposta (ex.: TradingView offline) → passa.
Anti-brick: se `stop_hook_active` (já é uma continuação forçada) → passa (evita loop infinito).

Núcleo `decide()` puro. py3 stdlib."""
import sys, re, json
from pathlib import Path

# stack MTF canónico exigido numa leitura de preço
REQUIRED_TF = {"5", "15", "60", "240", "D"}
# quantos TFs do stack podem faltar dos SWITCHES explícitos (1 = o TF-base, que se lê sem trocar)
MAX_MISSING = 1

# pedido de leitura de preço (PT + caps; o Cris escreve em maiúsculas)
PRICE_REQ = re.compile(
    r"leitura de pre[cç]o|l[êe]r?\s+o?\s*pre[cç]o|situa[cç][ãa]o do pre[cç]o|"
    r"qual\s+.{0,15}pre[cç]o|pre[cç]o\s+agora|como est[áa]\s+o?\s*pre[cç]o|onde est[áa]\s+o?\s*pre[cç]o|"
    r"avali[ae].{0,20}regi|le(ia|r)?\s+.{0,8}\bob\b|\bl[êe]r?\s+.{0,8}\bob\b|leitura de mercado|"
    r"analisa.{0,12}(gr[áa]fico|chart)|read price|price situation|le(ia|r)?\s+.{0,10}pre[cç]o",
    re.I)

WAIVE = re.compile(r"TF_READ_WAIVED\s*:\s*\S", re.I)

_TF_NORM = {"1h": "60", "4h": "240", "1d": "D", "d": "D", "day": "D", "daily": "D", "1w": "W", "w": "W"}


def _norm_tf(v):
    v = str(v).strip().lower()
    return _TF_NORM.get(v, v.upper() if v in ("d", "w") else v)


def decide(user_text, switched_tfs, had_data_read, assistant_text, stop_hook_active=False):
    """(ok, msg). Puro.
    user_text = última msg do utilizador; switched_tfs = set de TFs normalizados de chart_set_timeframe
    NESTE turno; had_data_read = bool (houve data_get_*); assistant_text = texto que respondi."""
    if stop_hook_active:
        return True, ""                              # anti-brick: já é continuação forçada
    if not user_text or not PRICE_REQ.search(user_text):
        return True, ""                              # não é pedido de leitura de preço
    if assistant_text and WAIVE.search(assistant_text):
        return True, ""                              # dispensa auditável (ex.: TV offline)
    covered = {_norm_tf(t) for t in (switched_tfs or set())}
    missing = REQUIRED_TF - covered
    if had_data_read and len(missing) <= MAX_MISSING:
        return True, ""                              # cobriu (o único que falta = TF-base lido sem trocar)
    falta = ", ".join(sorted(missing, key=lambda x: {"5": 0, "15": 1, "60": 2, "240": 3, "D": 4}.get(x, 9)))
    lidos = ", ".join(sorted(covered)) or "(nenhum switch)"
    return False, (
        "🛑 G8 — LEITURA DE PREÇO SEM TODOS OS TFS (Cris 2026-08-11)\n"
        "  O Cris pediu leitura de preço → é OBRIGATÓRIO ler o stack MTF COMPLETO antes de responder:\n"
        "  5M · 15M · 1H · 4H · 1D  (OB Detector + study_values em CADA um).\n"
        f"  TFs que leste este turno: {lidos}\n"
        f"  FALTAM: {falta}\n"
        "  RAIZ: ler UM só TF dá leitura errada — li OB só no 1H (demanda grossa 4316) e o timing real\n"
        "  estava no 5M (demanda 4394). Cada TF é uma região diferente; a resposta tem de convergir todos.\n"
        "  → PAUSA daemons (touch /tmp/claude_recheck.paused), chart_set_timeframe para cada TF em falta,\n"
        "    lê a OB+studies, RESTAURA o TF-base e despausa; só então responde.\n"
        "  → Se o TradingView estiver mesmo offline, escreve 'TF_READ_WAIVED: <razão>' na resposta.\n"
        "  (Bloqueio determinístico — auto-disciplina de LLM não segura.)\n")


# ---------- parsing do transcript ----------
def _iter_lines(transcript_path):
    try:
        with open(transcript_path, "r") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    yield json.loads(ln)
                except Exception:
                    continue
    except Exception:
        return


def _text_of(content):
    """extrai texto de um content (str ou lista de blocos)."""
    if isinstance(content, str):
        return content
    out = []
    if isinstance(content, list):
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str):
                out.append(b["text"])
    return "\n".join(out)


def _is_real_user(obj):
    """msg de utilizador REAL (não tool_result, não meta/hook)."""
    if obj.get("type") != "user":
        return False
    if obj.get("isMeta") or obj.get("toolUseResult") is not None:
        return False
    msg = obj.get("message") or {}
    content = msg.get("content")
    # tool_result vem como lista com blocos type=tool_result → ignora
    if isinstance(content, list) and any(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
        return False
    return True


def gather(transcript_path):
    """Devolve (user_text, switched_tfs, had_data_read, assistant_text) do ÚLTIMO turno."""
    rows = list(_iter_lines(transcript_path))
    # índice da última msg de utilizador real
    last_u = -1
    for i, o in enumerate(rows):
        if _is_real_user(o):
            last_u = i
    if last_u < 0:
        return "", set(), False, ""
    user_text = _text_of((rows[last_u].get("message") or {}).get("content"))
    switched, had_read, atext = set(), False, []
    for o in rows[last_u + 1:]:
        if o.get("type") == "assistant":
            content = (o.get("message") or {}).get("content")
            atext.append(_text_of(content))
            if isinstance(content, list):
                for b in content:
                    if not isinstance(b, dict) or b.get("type") != "tool_use":
                        continue
                    name = b.get("name") or ""
                    inp = b.get("input") or {}
                    if name.endswith("chart_set_timeframe"):
                        tf = inp.get("timeframe")
                        if tf is not None:
                            switched.add(_norm_tf(tf))
                    if "data_get_pine_boxes" in name or "data_get_study_values" in name or \
                       "data_get_ohlcv" in name or "data_get_pine" in name:
                        had_read = True
    return user_text, switched, had_read, "\n".join(atext)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    tp = data.get("transcript_path") or ""
    if not tp or not Path(tp).exists():
        return 0
    user_text, switched, had_read, atext = gather(tp)
    ok, msg = decide(user_text, switched, had_read, atext,
                     stop_hook_active=bool(data.get("stop_hook_active")))
    if ok:
        return 0
    sys.stderr.write(msg)
    return 2


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        t = []
        REQ = "QUAL SITUAÇÃO DO PREÇO? é boa compra?"
        FULL = {"5", "15", "60", "240", "D"}
        # 1) pediu preço + leu todos os 5 TFs + data read → passa
        ok, _ = decide(REQ, FULL, True, "resposta", False)
        t.append(("pediu+todos TFs → passa", ok is True))
        # 2) pediu preço + só 1 TF (1H) → BLOQUEIA
        ok, m = decide(REQ, {"60"}, True, "resposta", False)
        t.append(("pediu+só 1H → bloqueia", ok is False and "FALTAM" in m))
        # 3) pediu preço + leu 4 dos 5 (falta base 1H, lido sem switch) → passa (MAX_MISSING=1)
        ok, _ = decide(REQ, {"5", "15", "240", "D"}, True, "resposta", False)
        t.append(("4 de 5 (base lido) → passa", ok is True))
        # 4) pediu preço + trocou TFs mas SEM data read → bloqueia
        ok, _ = decide(REQ, FULL, False, "resposta", False)
        t.append(("switch sem data read → bloqueia", ok is False))
        # 5) NÃO é pedido de preço → passa mesmo sem TFs
        ok, _ = decide("commita o ficheiro e faz push", set(), False, "resposta", False)
        t.append(("não-pedido → passa", ok is True))
        # 6) waiver auditável → passa
        ok, _ = decide(REQ, {"60"}, True, "TF_READ_WAIVED: TradingView offline", False)
        t.append(("waiver → passa", ok is True))
        # 7) anti-brick stop_hook_active → passa
        ok, _ = decide(REQ, {"60"}, True, "resposta", True)
        t.append(("stop_hook_active → passa (anti-brick)", ok is True))
        # 8) variações de frase do Cris
        for phrase in ["LEIA NO 5 MIN E AVALIE REGIÕES", "faz a leitura de preço agora",
                       "lê a OB", "como está o preço?", "situação do preço"]:
            ok, _ = decide(phrase, {"60"}, True, "x", False)
            t.append((f"detecta pedido: {phrase[:22]!r}", ok is False))
        # 9) normalização 1H/4H/1D
        ok, _ = decide(REQ, {"5", "15", "1H", "4H", "1D"}, True, "x", False)
        t.append(("normaliza 1H/4H/1D → passa", ok is True))
        for lab, r in t:
            print(f"  [{'OK' if r else 'FAIL'}] {lab}")
        allok = all(r for _, r in t)
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    sys.exit(main())
