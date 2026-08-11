#!/usr/bin/env python3
"""G2 — SOURCE-CITATION GATE (Cris 2026-08-11).
BLOQUEIA (exit 2) um Write/Edit de CÓDIGO DE SINAL LIVE que introduz um NÍVEL-PREÇO XAU HARDCODED (invenção)
sem uma tag `# SOURCE:` a citar o indicador/RAW de onde vem. Fecha S3/S1: inventar zona/nível em vez de ler
o OB Detector/SVP/SMC que já tem o valor exato (dia −4R: régua inventada rejeitou short real por 0.36pt;
OB v11 já tinha 4032.55–4040.58).

Escopo honesto: apanha a invenção por LITERAL de preço (fiável, baixo falso-positivo — literais de preço XAU
não deviam existir em código de sinal; vêm do indicador). A invenção por FÓRMULA (bounce%, null-anchoring) é
indeterminável no write-time → fica para o G1/DA. Estudos/research/docs = livres (outros gates cobrem).

Passa se: ficheiro não é código de sinal; OU não há literal-preço novo; OU o conteúdo novo tem `# SOURCE:`
/`SOURCE:` OU lê um indicador real (pine_boxes/ob/study_values/market_read/svp/smc) no mesmo bloco.
Núcleo `decide()` puro. py3 stdlib."""
import sys, re, json
from pathlib import Path

PROTECTED = [
    r"alert-bridge/(entry_validator|vela_no_nivel|candle_reader|ob_watch|polarity_tracker|price_sentinel|e1_detector|e2_quality|claude_recheck)\.py$",
    r"strategies/.*(runtime|_cycle|scanner|detector)\.py$",
    r"my-strategy/core/.*(price_shock|regime|entry_router).*\.py$",
]
EXEMPT = [r"/research/", r"/docs/", r"\.md$", r"_study", r"a1a2_fvg_lab", r"/tests?/", r"selftest",
          r"__pycache__", r"/seeds/"]
# literal-preço XAU: 2000.x a 5999.x COM decimal (níveis têm decimais; evita ids/anos/janelas inteiras)
PRICE_LIT = re.compile(r"(?<![\w.])([2-5]\d{3})\.\d+(?![\w])")
# lê um indicador real → não é invenção
READS_REAL = re.compile(r"pine_boxes|study_values|ob_zones|ob_watch|market_read|_read_ob|OB Detector|"
                        r"svp|SVP|smc|SMC|session_vp|data_get_pine|snapshot\(", re.I)
HAS_SOURCE = re.compile(r"#\s*SOURCE\s*:|SOURCE:", re.I)


def is_protected(path):
    if any(re.search(p, path) for p in EXEMPT):
        return False
    return any(re.search(p, path) for p in PROTECTED)


def decide(file_path, new_content):
    """(ok, msg). Puro. new_content = o que está a ser escrito (Write content OU Edit new_string)."""
    if not file_path or not is_protected(file_path):
        return True, ""
    if not new_content:
        return True, ""
    # ignora linhas de comentário/nota e a própria tag SOURCE
    lits = []
    for m in PRICE_LIT.finditer(new_content):
        # contexto da linha
        start = new_content.rfind("\n", 0, m.start()) + 1
        end = new_content.find("\n", m.end()); end = end if end >= 0 else len(new_content)
        line = new_content[start:end]
        if line.lstrip().startswith("#"):        # literal em comentário = ok (ex.: nota/exemplo)
            continue
        lits.append((m.group(0), line.strip()[:80]))
    if not lits:
        return True, ""
    if HAS_SOURCE.search(new_content) or READS_REAL.search(new_content):
        return True, ""
    exemplos = "\n  ".join(f"{v}  «{ln}»" for v, ln in lits[:4])
    return False, (
        "🛑 G2 — NÍVEL-PREÇO HARDCODED SEM FONTE (Cris 2026-08-11)\n"
        f"  Estás a pôr um nível-preço XAU inventado em código de sinal ({Path(file_path).name}):\n  {exemplos}\n"
        "  RAIZ S3: inventar zona/nível em vez de LER o indicador que já tem o valor exato (OB Detector/SVP/SMC).\n"
        "  Dia −4R: régua inventada rejeitou um short real por 0.36pt; o OB v11 já tinha a zona exata.\n"
        "  → LÊ o indicador real (pine_boxes/ob_watch/market_read/study_values) em vez de hardcodar, OU\n"
        "  → se o nível vem MESMO de uma fonte, cita-a na linha: `# SOURCE: OB Detector v11 / study_values / RAW`.\n"
        "  (Bloqueio determinístico — auto-disciplina de LLM não segura.)\n")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") not in ("Write", "Edit"):
        return 0
    ti = data.get("tool_input") or {}
    fp = ti.get("file_path") or ""
    content = ti.get("content")
    if content is None:
        content = ti.get("new_string") or ""
    ok, msg = decide(fp, content)
    if ok:
        return 0
    sys.stderr.write(msg)
    return 2


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        t = []
        SIG = "alert-bridge/ob_watch.py"
        # 1) literal de preço em código de sinal sem fonte → BLOQUEIA
        ok, _ = decide(SIG, "    if price > 4337.10:\n        go_long()")
        t.append(("literal preço sem fonte bloqueia", ok is False))
        # 2) com # SOURCE: → passa
        ok, _ = decide(SIG, "    LVL = 4337.10  # SOURCE: OB Detector v11 supply\n")
        t.append(("com SOURCE passa", ok is True))
        # 3) lê indicador real no bloco → passa
        ok, _ = decide(SIG, "    z = ob_watch._read_ob('60'); lvl = z[0]['high']  # 4337.10 vem daqui")
        t.append(("le indicador real passa", ok is True))
        # 4) literal só em comentário → passa
        ok, _ = decide(SIG, "    # exemplo: a zona era 4032.55-4040.58 no OB v11\n    x = compute()")
        t.append(("literal em comentario passa", ok is True))
        # 5) constante não-preço (ATR mult, janela) → passa
        ok, _ = decide(SIG, "    SCALE = 2.5\n    WIN = 96\n    buf = 0.1 * atr")
        t.append(("constantes nao-preco passam", ok is True))
        # 6) ficheiro de estudo/research → passa (não protegido)
        ok, _ = decide("my-strategy/research/revalidation/a1a2_fvg_lab/study_v9.py", "if price > 4337.10: pass")
        t.append(("estudo passa", ok is True))
        # 7) doc → passa
        ok, _ = decide("docs/x.md", "nivel 4337.10")
        t.append(("doc passa", ok is True))
        for lab, r in t:
            print(f"  [{'OK' if r else 'FAIL'}] {lab}")
        allok = all(r for _, r in t)
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    sys.exit(main())
