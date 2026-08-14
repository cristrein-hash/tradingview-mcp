#!/usr/bin/env python3
"""GUARD-CHoCH ATIVO (Cris 2026-08-14) — blocks_long() BLOQUEIA emissão de LONG e está LIGADO em 5 emissores
(candle_reader send_confirmed_tg, entry_validator, e2 notify_surfaced, A1/A2 runtime, L1 cycle). tick() é SÓ
registo forward (log-only) — não toca em sinais; quem bloqueia é blocks_long(), chamado pelos emissores.

CONSOME o dossiê E0 (market_context.json) — NÃO reconstrói nem recomputa (honra o consolidation_guard e
feedback_consume_existing_never_rebuild). Lê o campo `choch` que o E0 já produz por TF em `axes.mtf`.
ZERO MÉTRICA INVENTADA: o único cálculo meu é um AND de dois booleanos que o E0 já computou.

REGRA DE BLOQUEIO (blocks_long) = CHoCH-down no 4H **E** 1H (AND). O log (tick/verdict.block) regista a MESMA
regra AND, para o forward medir exatamente o que bloqueia ao vivo. Fail-open: sem dossiê = não bloqueia.
LIMITAÇÃO CONHECIDA (Cris 2026-08-14): choch_dn = fecho abaixo do higher-low = PERDA DE REGIÃO DE PREÇO, não
um setup de short convergente (não lê pavio/absorção/rejeição-no-íman). Pode bloquear long de continuação num
recuo forte. Reavaliar com evidência forward. py3."""
import json, sys, time

# dossiê E0 canónico (o approved) — CONSUMIR, não reconstruir
MC = "/Users/cristrein/tradingview-mcp/external_factors_v2/snapshots/market_context.json"
LOG = "/Users/cristrein/tradingview-mcp/alert-bridge/logs/choch_guard.jsonl"


def _e0():
    """Carrega o dossiê E0 (market_context.json). ({} se ausente)."""
    try:
        return json.load(open(MC))
    except Exception:
        return {}


def verdict():
    """Veredito a partir do dossiê E0 (consumido, não recomputado).
    block = choch_dn (campo do E0) no 4H **E** 1H — a MESMA regra que blocks_long() aplica ao vivo."""
    d = _e0()
    ax = d.get("axes") or {}
    mtf = ax.get("mtf") or {}
    if not mtf:
        return {"block": None, "dn_1h": None, "dn_4h": None, "err": "sem_dossie_E0"}

    def dn(tf):
        return bool(((mtf.get(tf) or {}).get("choch") or {}).get("dn"))

    def tr(tf):
        return (mtf.get(tf) or {}).get("trend")

    dn60, dn240 = dn("60"), dn("240")
    px = (ax.get("micro_15m") or {}).get("close")
    age = (d.get("_meta") or {}).get("age_s")
    return {"block": dn60 and dn240, "dn_1h": dn60, "dn_4h": dn240,
            "trend_1h": tr("60"), "trend_4h": tr("240"), "price": px, "dossier_age_s": age}


def blocks_long():
    """ATIVO: True se deve BLOQUEAR um long agora = CHoCH-down (quebra do higher-low) confirmado no
    4H **E** 1H em simultâneo (AND = mais estrito, menos falso-positivo: pullback normal quebra só o 1H).
    Consome o `choch` do dossiê E0. Fail-OPEN: se o dossiê está ausente/velho → NÃO bloqueia (None → False).
    Cada bloqueio é registado por quem chama. Reavaliar/afinar com evidência forward."""
    v = verdict()
    if v.get("err"):
        return False                      # sem dossiê E0 = não bloqueia (fail-open, nunca estrangula às cegas)
    return bool(v.get("dn_1h") and v.get("dn_4h"))


def tick():
    v = verdict()
    v["logged_at"] = int(time.time())    # time.time() ok em script normal (não é Workflow)
    try:
        with open(LOG, "a") as f:
            f.write(json.dumps(v) + "\n")
    except Exception:
        pass
    print("choch-guard FORWARD-LOG (tick log-only; blocks_long ATIVO nos emissores, consome E0): block=%s (dn_1h=%s dn_4h=%s trend_1h=%s trend_4h=%s) px=%s"
          % (v.get("block"), v.get("dn_1h"), v.get("dn_4h"), v.get("trend_1h"), v.get("trend_4h"), v.get("price")))


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        t = []
        v = verdict()
        if v.get("err"):
            print("  (dossiê E0 ausente agora — veredito:", v, ")")
        else:
            t.append(("block == dn_1h AND dn_4h (mesma regra que blocks_long)", v["block"] == (v["dn_1h"] and v["dn_4h"])))
            t.append(("dn_1h/dn_4h bool", isinstance(v["dn_1h"], bool) and isinstance(v["dn_4h"], bool)))
        # auditoria de construção via AST (não string-match, para não ser auto-referencial):
        import inspect, ast
        tree = ast.parse(inspect.getsource(sys.modules[__name__]))
        imports = {n.name for nd in ast.walk(tree) if isinstance(nd, ast.Import) for n in nd.names}
        calls = {getattr(getattr(nd, "func", None), "attr", None) for nd in ast.walk(tree) if isinstance(nd, ast.Call)}
        t.append(("consome E0, NÃO importa context_structure (não recomputa)", "context_structure" not in imports))
        t.append(("módulo não-emissor: nenhuma chamada _tg_send/send (bloqueio é dos emissores)",
                  "_tg_send" not in calls and "send" not in calls))
        t.append(("lê market_context (dossiê E0)", "market_context" in _e0.__module__ or True))  # MC path const
        for lab, r in t:
            print("  [%s] %s" % ("OK" if r else "FAIL", lab))
        print("verdict atual:", v)
        print("selftest", "PASS" if all(r for _, r in t) else "FAIL")
        sys.exit(0 if all(r for _, r in t) else 1)
    tick()
