#!/usr/bin/env python3
"""Teste dry-run da plotagem canônica (sem chart real, sem MCP).

Valida:
  1. tick offsets via a função canônica price_to_ticks_offset (draw_xau_4h_trades.py)
     caso de referência: entry=2400, stop=2390, target=2430, mintick=0.01
       -> stopLevel=1000, profitLevel=3000
  2. cor do label winner/loser (#1a8917 verde se close_R>0; #cc0000 vermelho se <=0)
  3. validações direcionais (entry>stop, target>entry, ticks>0, campos obrigatórios)

Ver docs/CANONICAL_TRADE_PLOTTING.md. Read-only: NÃO toca chart, NÃO plota, NÃO usa MCP.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from draw_xau_4h_trades import price_to_ticks_offset, MINTICK  # função canônica real

WIN_COLOR = "#1a8917"
LOSS_COLOR = "#cc0000"


def label_color(close_r):
    """Convenção canônica: verde se winner (close_R>0), vermelho se loser (<=0)."""
    return WIN_COLOR if close_r > 0 else LOSS_COLOR


def validate_long_trade(entry, stop, target):
    """Hard stop em violação. Retorna (stop_ticks, profit_ticks)."""
    for name, v in (("entry", entry), ("stop", stop), ("target", target)):
        if v is None:
            raise ValueError(f"campo obrigatório ausente: {name}")
    if not entry > stop:
        raise ValueError(f"long inválido: entry({entry}) deve ser > stop({stop})")
    if not target > entry:
        raise ValueError(f"target({target}) deve ser > entry({entry})")
    st = price_to_ticks_offset(entry, stop)
    pt = price_to_ticks_offset(entry, target)
    if not (st > 0 and pt > 0):
        raise ValueError(f"ticks devem ser > 0 (stop={st}, profit={pt})")
    return st, pt


def run():
    fails = []

    # 1. caso de referência
    st, pt = validate_long_trade(2400, 2390, 2430)
    if st != 1000:
        fails.append(f"stopLevel esperado 1000, obtido {st}")
    if pt != 3000:
        fails.append(f"profitLevel esperado 3000, obtido {pt}")
    if MINTICK != 0.01:
        fails.append(f"MINTICK esperado 0.01, obtido {MINTICK}")

    # 2. cor winner/loser
    if label_color(3.0) != WIN_COLOR:
        fails.append("winner (close_R=3.0) deveria ser verde #1a8917")
    if label_color(-1.0) != LOSS_COLOR:
        fails.append("loser (close_R=-1.0) deveria ser vermelho #cc0000")
    if label_color(0.0) != LOSS_COLOR:
        fails.append("close_R=0 (<=0) deveria ser loser/vermelho")

    # 3. validações direcionais (devem levantar)
    for args in [(2400, 2410, 2430), (2400, 2390, 2395 - 6)]:  # stop>=entry / target<=entry
        try:
            validate_long_trade(*args)
            fails.append(f"validação NÃO levantou para args inválidos {args}")
        except ValueError:
            pass
    try:
        validate_long_trade(2400, None, 2430)  # campo faltando
        fails.append("validação NÃO levantou para campo ausente")
    except ValueError:
        pass

    if fails:
        print("FAIL:")
        for f in fails:
            print("  -", f)
        return 1
    print("PASS — entry=2400 stop=2390 target=2430 -> stopLevel=1000 profitLevel=3000; "
          "winner=verde loser=vermelho; validações direcionais OK.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
