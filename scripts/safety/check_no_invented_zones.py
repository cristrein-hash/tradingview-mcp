#!/usr/bin/env python3
"""TRIPWIRE anti-invenção-de-zona (Cris 2026-07-20, indignado — garantia executável, não promessa).

Falha LOUD se algum ficheiro de DAEMON LIVE inventa zonas/níveis em vez de ler o indicador canónico
(OB Detector / SVP / SMC via pine_boxes). Apanha os 2 padrões exatos que o Claude cometeu:
  A. computar uma banda estatística própria (Bollinger/stdev) sobre preço — `mean + M*sd`, `** 0.5` de variância;
  B. literais de PREÇO XAU hardcoded (>3500 e <5000) usados como nível/zona à mão.
Regra: um ficheiro que fala de zona/nível/magnet/band TEM de ler `pine_boxes` (OB Detector) — senão é invenção.

Corre standalone (pre-commit / watchdog): `python3 scripts/safety/check_no_invented_zones.py`
Exit 0 = PASS · Exit 1 = INVENÇÃO DETETADA (bloqueia). py3.9 stdlib."""
import re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
# ficheiros de DAEMON LIVE que decidem/alertam (não research, não testes)
LIVE_GLOBS = [
    "my-strategy/core/price_shock/*.py",
    "my-strategy/strategies/**/*_cycle.py",
    "my-strategy/strategies/**/*_engine*.py",
    "alert-bridge/context_*.py",
    "alert-bridge/e1_detector.py",
    "alert-bridge/e2_quality.py",
]
ZONE_WORDS = re.compile(r"\b(zona|zone|magnet|íman|iman|banda|band|supply|demand|n[íi]vel|level)\b", re.I)
# A) banda estatística computada à mão sobre preço (mean±k*sd OU upper,lower= ; NÃO pstdev de normalização)
BOLLINGER = re.compile(r"(mean\s*[+\-]\s*\w+\s*\*\s*sd)|(\b(upper|lower)\s*,\s*(upper|lower)\s*=)|bollinger", re.I)
# B) literal de preço XAU hardcoded COM casa decimal (3500.x..4999.x) — nível à mão (exclui inteiros tipo 3600s)
PRICE_LIT = re.compile(r"(?<![\w.])(3[5-9]\d\d|4[0-4]\d\d)\.\d(?![\w])")
# leitura canónica de zona (o que É permitido)
CANON = re.compile(r"pine_boxes|data_get_pine_boxes|OB Detector|Smart Money|Session Volume|study_values", re.I)
# linhas isentas: comentário DERRUBADO / anúncio explícito / constante de PONTOS (delta, não preço)
EXEMPT = re.compile(r"DERRUBAD|INVEN|#.*(ponto|pts|delta)|_PTS\b|SHOCK_|MAJOR_|ATR|RETAIN|WINDOW|COOLDOWN|min_rr|legMag", re.I)


def scan():
    viol = []
    for g in LIVE_GLOBS:
        for f in REPO.glob(g):
            if not f.is_file():
                continue
            txt = f.read_text(errors="ignore")
            canon_here = bool(CANON.search(txt))          # o ficheiro lê o indicador real?
            for i, ln in enumerate(txt.splitlines(), 1):
                if EXEMPT.search(ln) or ln.strip().startswith("#"):
                    continue
                bol = BOLLINGER.search(ln)
                # preço hardcoded só conta se a linha (ou o ficheiro) fala de zona
                pl = PRICE_LIT.search(ln) if (ZONE_WORDS.search(ln)) else None
                if bol:
                    viol.append((f, i, "banda estatística computada (Bollinger/stdev) — usa OB Detector", ln.strip()[:80]))
                if pl and not canon_here:
                    viol.append((f, i, "preço XAU hardcoded como nível SEM ler pine_boxes/OB", ln.strip()[:80]))
    return viol


def main():
    viol = scan()
    if not viol:
        print("NO_INVENTED_ZONES_PASS — nenhuma invenção de zona no código live (fonte = OB Detector/SVP/SMC)")
        return 0
    print("🔴 INVENÇÃO DE ZONA DETETADA — derruba e lê o indicador canónico (OB Detector/SVP/SMC):")
    for f, i, why, ln in viol:
        print(f"  {f.relative_to(REPO)}:{i}  {why}\n      | {ln}")
    print(f"\nTOTAL: {len(viol)} violação(ões). check_no_invented_zones = FAIL.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
