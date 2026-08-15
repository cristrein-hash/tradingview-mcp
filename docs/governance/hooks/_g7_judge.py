#!/usr/bin/env python3
"""Juiz LLM (Haiku) do G7 — 2o estagio anti-miopia (Cris 2026-08-15).
O regex do pre_analysis_myopia_guard e' so' o GATILHO (alta recall, baixa precisao). Este juiz LE o script
e classifica o DESENHO da analise contra uma rubrica ESTREITA e ESTRUTURADA (sim/nao por item), convertendo
keyword->raciocinio. Corre em contexto separado (sem apego ao plano). Devolve dict ou None (qualquer falha
= None -> o chamador faz fallback ao bloqueio+checklist atual, i.e. fail-closed seguro).

Rubrica (a mesma checklist do G7): is_market_analysis, multifatorial, trajetoria, dois_objetivos.
Cache por hash do (cmd+script) em /tmp/.claude_g7_judge (12h) — re-correr o mesmo script nao gasta tokens.
Reversivel: G7_JUDGE=off desliga (chamador cai no comportamento regex-only). py3 stdlib."""
import json, subprocess, re, hashlib, time, os
from pathlib import Path

CLAUDE = os.environ.get("CLAUDE_EXE", "/Users/cristrein/.local/bin/claude")
MODEL = os.environ.get("G7_JUDGE_MODEL", "claude-haiku-4-5")
# #2 (Cris 2026-08-15): 15s (o sucesso típico foi ~12.7s) — falha mais cedo, degrada mais depressa ao checklist.
TIMEOUT = int(os.environ.get("G7_JUDGE_TIMEOUT", "15"))
CACHE = Path("/tmp/.claude_g7_judge")
# #1 (Cris 2026-08-15): marca de "Haiku-lento". Após um timeout, o juiz salta durante SLOW_SKIP_S — evita
# pagar TIMEOUT repetido quando o Haiku está sobrecarregado (cada corrida cairia no checklist na mesma).
SLOW_MARK = Path("/tmp/.claude_g7_judge_slow")
SLOW_SKIP_S = int(os.environ.get("G7_JUDGE_SLOW_SKIP", "60"))

SYS = ("Es um juiz de metodologia de analise quantitativa de trading. Les o CODIGO de um script e classificas "
       "o DESENHO da analise contra uma rubrica fixa. Respondes SO com um objeto JSON, sem texto a' volta, sem "
       "markdown. Se estrito e literal: julgas o que o codigo FAZ, nao a intencao. Na duvida entre miope e "
       "robusto, marca o item como false (assume o pior).")

RUBRIC = (
    "Classifica o script abaixo. Devolve EXATAMENTE este JSON (booleans; porque = 1 frase curta):\n"
    '{"is_market_analysis": true se o script analisa leitura/separacao/filtro/estrutura de mercado a partir de '
    'barras/indicadores (OHLC, OB, SMC, SVP, RSI, bubbles, swings, choch); false se for commit, infra, aplicador '
    'de seed, selftest, plot puro, utilitario ou I/O;\n'
    ' "multifatorial": true se a DECISAO vem da convergencia de >=2 sub-estados ORTOGONAIS; false se decide por 1 '
    'fator isolado / 1 limiar unico;\n'
    ' "trajetoria": true se o estado deriva de LOOKBACK de barras passadas (markup, rejeicao, momentum, aceitacao '
    'dinamicos); false se e snapshot estatico na barra i;\n'
    ' "dois_objetivos": true se procura capturar runner/convexidade E evitar topo/loser; false se otimiza so um lado;\n'
    ' "porque": "<1 frase>"}\n'
    "Se is_market_analysis=false, mete as outras a null.\n\n# SCRIPT:\n")


def _hash(s):
    return hashlib.sha1(s.encode("utf-8", "ignore")).hexdigest()[:16]


def judge(cmd, script_text):
    """Devolve dict {is_market_analysis, multifatorial, trajetoria, dois_objetivos, porque} ou None."""
    if os.environ.get("G7_JUDGE", "on") == "off":
        return None
    # #1: janela "Haiku-lento" — se houve timeout recente, salta o juiz (não paga TIMEOUT de novo).
    try:
        if SLOW_MARK.exists() and (time.time() - SLOW_MARK.stat().st_mtime) < SLOW_SKIP_S:
            return None
    except Exception:
        pass
    try:
        blob = ((cmd or "") + "\n" + (script_text or ""))[:16000]
        h = _hash(blob)
        cf = None
        try:
            CACHE.mkdir(parents=True, exist_ok=True)
            cf = CACHE / (h + ".json")
            if cf.exists() and (time.time() - cf.stat().st_mtime) < 12 * 3600:
                return json.loads(cf.read_text())
        except Exception:
            cf = None
        try:
            r = subprocess.run([CLAUDE, "-p", RUBRIC + blob, "--append-system-prompt", SYS,
                                "--output-format", "json", "--model", MODEL],
                               capture_output=True, text=True, timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            try:
                SLOW_MARK.write_text(str(int(time.time())))   # arma a janela de skip
            except Exception:
                pass
            return None
        if r.returncode != 0:
            return None
        outer = json.loads(r.stdout)
        txt = outer.get("result") or ""
        m = re.search(r"\{.*\}", txt, re.S)
        if not m:
            return None
        v = json.loads(m.group(0))
        if "is_market_analysis" not in v:
            return None
        try:
            if cf:
                cf.write_text(json.dumps(v))
        except Exception:
            pass
        return v
    except Exception:
        return None
