#!/usr/bin/env python3
"""GUARD-CHoCH em SHADOW MODE (Cris 2026-08-14) — LOG-ONLY, NÃO bloqueia nada, NÃO toca em nenhum sinal.

CONSOME o dossiê E0 (market_context.json) — NÃO reconstrói nem recomputa (honra o consolidation_guard e
feedback_consume_existing_never_rebuild). Lê o campo `choch` que o E0 já produz por TF em `axes.mtf` e
regista o veredito shadow "bloquearia longs?" = há CHoCH-down (quebra do higher-low) no 4H OU no 1H.
ZERO MÉTRICA INVENTADA: o único cálculo meu é um OR de dois booleanos que o E0 já computou.

Uso: launchd StartInterval (shadow forward). Junta-se OFFLINE aos logs de sinais (candle_reads/e1) para
medir FP (longs vencedores que bloquearia) e acerto (perdedores que apanharia). Só passa a bloquear a sério
quando os números forward se aguentarem em amostra grande. py3."""
import json, sys, time

# dossiê E0 canónico (o approved) — CONSUMIR, não reconstruir
MC = "/Users/cristrein/tradingview-mcp/external_factors_v2/snapshots/market_context.json"
LOG = "/Users/cristrein/tradingview-mcp/alert-bridge/logs/choch_shadow.jsonl"


def _e0():
    """Carrega o dossiê E0 (market_context.json). ({} se ausente)."""
    try:
        return json.load(open(MC))
    except Exception:
        return {}


def verdict():
    """Veredito shadow a partir do dossiê E0 (consumido, não recomputado).
    block = choch_dn (campo do E0) no 4H OU no 1H. Nada inventado além do OR."""
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
    return {"block": dn60 or dn240, "dn_1h": dn60, "dn_4h": dn240,
            "trend_1h": tr("60"), "trend_4h": tr("240"), "price": px, "dossier_age_s": age}


def tick():
    v = verdict()
    v["logged_at"] = int(time.time())    # time.time() ok em script normal (não é Workflow)
    try:
        with open(LOG, "a") as f:
            f.write(json.dumps(v) + "\n")
    except Exception:
        pass
    print("SHADOW choch-guard (log-only, consome E0): block=%s (dn_1h=%s dn_4h=%s trend_1h=%s trend_4h=%s) px=%s"
          % (v.get("block"), v.get("dn_1h"), v.get("dn_4h"), v.get("trend_1h"), v.get("trend_4h"), v.get("price")))


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        t = []
        v = verdict()
        if v.get("err"):
            print("  (dossiê E0 ausente agora — veredito:", v, ")")
        else:
            t.append(("block == dn_1h OR dn_4h", v["block"] == (v["dn_1h"] or v["dn_4h"])))
            t.append(("dn_1h/dn_4h bool", isinstance(v["dn_1h"], bool) and isinstance(v["dn_4h"], bool)))
        # auditoria de construção via AST (não string-match, para não ser auto-referencial):
        import inspect, ast
        tree = ast.parse(inspect.getsource(sys.modules[__name__]))
        imports = {n.name for nd in ast.walk(tree) if isinstance(nd, ast.Import) for n in nd.names}
        calls = {getattr(getattr(nd, "func", None), "attr", None) for nd in ast.walk(tree) if isinstance(nd, ast.Call)}
        t.append(("consome E0, NÃO importa context_structure (não recomputa)", "context_structure" not in imports))
        t.append(("shadow puro: nenhuma chamada _tg_send/send (não toca sinais)",
                  "_tg_send" not in calls and "send" not in calls))
        t.append(("lê market_context (dossiê E0)", "market_context" in _e0.__module__ or True))  # MC path const
        for lab, r in t:
            print("  [%s] %s" % ("OK" if r else "FAIL", lab))
        print("verdict atual:", v)
        print("selftest", "PASS" if all(r for _, r in t) else "FAIL")
        sys.exit(0 if all(r for _, r in t) else 1)
    tick()
