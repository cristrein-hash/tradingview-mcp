#!/usr/bin/env python3
"""GUARD: contrato SL-FIRST (consolidação 2026-08-21, ordem Cris).

A auditoria 19/08 apontou "SL-first reimplementado 4×". O protocolo de consolidação (extração lado a
lado + teste de equivalência) revelou que NÃO são 4 duplicados fundíveis:
  1. scoreboard.resolve       — sinais market-entry (entrada ao preço do sinal, barras após t do sinal)
  2. a1_causal_entry (B/A1A2) — MOTOR SELADO (outcome faz parte da matemática aprovada 15/07)
  3. journal lib/resolve      — semântica LIMIT deliberada (só conta após fill; não avalia SL/TP na
                                 barra do fill) = contrato DIFERENTE por desenho (ordens reais do Cris)
  4. journal capture          — DELEGA no 3 (já consolidado)
Fundir 1 e 3 seria ERRADO (contratos distintos); tocar no 2 é proibido. O que é partilhado e tem de
ficar travado é o TIE-BREAK: SL e TP na MESMA barra ⇒ LOSS, em TODAS as implementações.

Este guard executa esse contrato: testes sintéticos nos executáveis (scoreboard, journal) e verificação
de ordem-no-source nos motores selados (a1_causal_entry, l2_engine). Exit 1 = alguém quebrou o contrato."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "my-strategy/core/scoreboard"))
sys.path.insert(0, str(REPO / "copilot/journal/lib"))


def main():
    fails = []
    # 1) scoreboard: same-bar → LOSS (long e short)
    import scoreboard as SB
    T = [0, 10]; H = [100, 120]; L = [100, 90]; C = [100, 100]
    r = SB.resolve({"t": 0, "entry": 100, "sl": 95, "tgt": 115, "dir": "LONG"}, T, H, L, C)
    if r["out3"] != "LOSS":
        fails.append(f"scoreboard LONG same-bar deu {r['out3']} (esperado LOSS)")
    r2 = SB.resolve({"t": 0, "entry": 100, "sl": 105, "tgt": 85, "dir": "SHORT"}, T, H, L, C)
    if r2["out3"] != "LOSS":
        fails.append(f"scoreboard SHORT same-bar deu {r2['out3']} (esperado LOSS)")
    # 2) journal: same-bar pós-fill → LOSS
    import resolve as JR
    rec = {"status": "FILLED", "entry": 100, "sl": 95, "tp": 115, "direction": "long",
           "detected_epoch": 0, "filled_bar_t": 5}
    out = JR.resolve_trade(dict(rec), [{"t": 10, "h": 120, "l": 90, "c": 100}])
    if out.get("status") != "LOSS":
        fails.append(f"journal LONG same-bar deu {out.get('status')} (esperado LOSS)")
    rec2 = {"status": "FILLED", "entry": 100, "sl": 105, "tp": 85, "direction": "short",
            "detected_epoch": 0, "filled_bar_t": 5}
    out2 = JR.resolve_trade(dict(rec2), [{"t": 10, "h": 120, "l": 80, "c": 100}])
    if out2.get("status") != "LOSS":
        fails.append(f"journal SHORT same-bar deu {out2.get('status')} (esperado LOSS)")
    # 3) motores selados: ordem SL-antes-de-alvo no source (não executamos matemática selada aqui)
    src = (REPO / "my-strategy/research/revalidation/a1_causal_entry.py").read_text()
    if not (0 < src.find("if L[mrk] <= sl") < src.find("if H[mrk] >= tgt")):
        fails.append("a1_causal_entry: ordem SL-first alterada no source")
    src2 = (REPO / "my-strategy/strategies/xau_4h_long/reversal/L2_BPT_ZONE_TREND_EXIT/l2_engine.py").read_text()
    if not (0 < src2.find("if L[j] <= sl") < src2.find("if regime_at(j) == 'BEAR'")):
        fails.append("l2_engine: ordem stop-first alterada no source")
    if fails:
        print("FAIL — contrato SL-first quebrado:")
        for f in fails:
            print("  ", f)
        return 1
    print("PASS — SL-first (same-bar => LOSS) idêntico em scoreboard, journal, a1_causal, l2_engine")
    return 0


if __name__ == "__main__":
    sys.exit(main())
