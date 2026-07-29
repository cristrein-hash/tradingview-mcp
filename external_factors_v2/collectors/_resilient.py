#!/usr/bin/env python3
"""ESCRITA RESILIENTE de snapshots keyless (Cris 2026-07-29 — auditoria "news a cair o tempo todo").
CAUSA RAIZ: fontes keyless (GDELT, Polymarket, RSS) devolvem VAZIO/erro INTERMITENTE. O padrão antigo gravava
esse vazio por cima do bom snapshot -> flapping OK->vazio->OK que o utilizador via como "a cair" (mesmo com o
daemon vivo e a rede OK). write_resilient() só sobrescreve quando o fetch veio SAUDÁVEL; quando veio vazio/
falhado, PRESERVA o último bom payload, marca-o como servido-em-stale e NEUTRALIZA gatilhos de alarme (nunca
escalar Telegram com dados velhos). Escrita atómica (tmp+os.replace). py3.9. Sem dependências."""
import json, os, datetime as dt
from pathlib import Path


def _atomic(path, obj):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    os.replace(tmp, path)


def _neutralize(d, dotted):
    """Zera (bool->False, num->0) um campo pontilhado, se existir — para não disparar alarmes em dados stale."""
    cur = d
    parts = dotted.split(".")
    for p in parts[:-1]:
        if not isinstance(cur, dict) or p not in cur:
            return
        cur = cur[p]
    if isinstance(cur, dict) and parts[-1] in cur:
        v = cur[parts[-1]]
        cur[parts[-1]] = False if isinstance(v, bool) else (0 if isinstance(v, (int, float)) else v)


def write_resilient(out_path, payload, healthy, neutralize=None):
    """Grava `payload` se healthy; senão preserva o último bom snapshot (degradado, alarmes neutralizados).
    Retorna (payload_efetivamente_escrito, served_stale: bool)."""
    out_path = Path(out_path)
    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    if healthy:
        m = payload.setdefault("_meta", {})
        m["serving_stale"] = False
        m["last_good_ts"] = now
        m["consecutive_fail"] = 0
        m.pop("stale_since_ts", None)
        _atomic(out_path, payload)
        return payload, False
    # não-saudável: preserva o último bom
    prev = None
    if out_path.exists():
        try:
            prev = json.loads(out_path.read_text())
        except Exception:
            prev = None
    if not isinstance(prev, dict):
        # sem bom anterior utilizável — grava o vazio (1ª vez), marcado
        m = payload.setdefault("_meta", {})
        m["serving_stale"] = True
        m["last_good_ts"] = None
        m["consecutive_fail"] = 1
        m["stale_since_ts"] = now
        _atomic(out_path, payload)
        return payload, True
    m = prev.setdefault("_meta", {})
    m["serving_stale"] = True
    m["consecutive_fail"] = int(m.get("consecutive_fail") or 0) + 1
    m["stale_since_ts"] = m.get("stale_since_ts") or now
    m["served_stale_ts"] = now
    m["stale_age_s"] = now - int(m.get("last_good_ts") or now)
    for k in (neutralize or []):
        _neutralize(prev, k)
    _atomic(out_path, prev)
    return prev, True
