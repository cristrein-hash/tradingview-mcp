#!/usr/bin/env python3
"""RAW-READ GUARD (Cris 2026-08-16) — leitura de RAW só pelo leitor canónico.
BLOQUEIA (exit 2) qualquer Bash/Write/Edit que leia um `raw_replay/*.gz` DIRETAMENTE (gzip.open/gunzip/zcat)
SEM importar/usar `raw_reader`. Fecha a dor recorrente: cada script re-implementava o parse do RAW (grp copiado,
list-vs-dict, ohlcv[-1], zones-vs-all_boxes, barra-0) e PARTIA. Agora há UM leitor validado (my-strategy/core/
raw_reader.py, selftest contra registo real) e este guard proíbe re-implementá-lo.

Passa se: usa `raw_reader`; OU é o próprio leitor/coletor/hook; OU declara escape auditável `RAW_READER_OK`.
Núcleo decide() puro = testável. py3 stdlib."""
import sys, json, re

EXEMPT = ("raw_reader", "run_xau_replay_feature_collect", "/hooks/", ".claude/hooks", "raw_reader_ok")
DIRECT = re.compile(r"gzip\.open|gzip\.gzipfile|\bgunzip\b|\bzcat\b", re.I)


def decide(text):
    """(ok, msg) puro. Bloqueia leitura direta de raw_replay/*.gz sem raw_reader."""
    low = (text or "").lower()
    if any(x in low for x in EXEMPT):
        return True, ""
    reads_raw_gz = ("raw_replay" in low) and (".gz" in low)
    if reads_raw_gz and DIRECT.search(low):
        return False, (
            "🛑 RAW-READ GUARD — leitura DIRETA de raw_replay/*.gz BLOQUEADA (Cris 2026-08-16)\n"
            "  Re-implementar o parse do RAW à mão = o erro recorrente (grp copiado, list-vs-dict, ohlcv[-1],\n"
            "  zones-vs-all_boxes, barra-0). Usa o LEITOR CANÓNICO, único validado:\n"
            "  → import raw_reader as RR   (my-strategy/core/raw_reader.py)\n"
            "     RR.resolve_gz('XAUUSD','15M') · RR.iter_records(gz)/RR.records(gz) · RR.bar(rec) ·\n"
            "     RR.values(rec,'Relative') · RR.boxes(rec,'Custom OB') · RR.bubbles(rec) · RR.series(gz)\n"
            "  → selftest que prova a leitura: python3 my-strategy/core/raw_reader.py --selftest\n"
            "  → exceção deliberada (fora do RAW canónico): declara 'RAW_READER_OK: <razão>' no comando/conteúdo.\n")
    return True, ""


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") not in (None, "Bash", "Write", "Edit"):
        return 0
    ti = data.get("tool_input") or {}
    text = " ".join(str(ti.get(k) or "") for k in ("command", "content", "new_string", "file_path"))
    ok, msg = decide(text)
    if ok:
        return 0
    try:
        import _guard_log; _guard_log.fire("raw_read", "block", "leitura direta raw_replay .gz sem raw_reader")
    except Exception:
        pass
    sys.stderr.write(msg)
    return 2


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        t = []
        # 1) gzip.open de raw_replay sem raw_reader → BLOQUEIA
        ok, _ = decide("import gzip\nfh=gzip.open('TradingData/raw_replay/XAUUSD/15M/x.jsonl.gz','rt')")
        t.append(("gzip.open raw_replay sem raw_reader bloqueia", ok is False))
        # 2) o mesmo MAS via raw_reader → passa
        ok, _ = decide("import raw_reader as RR\nfor r in RR.iter_records(gz): ...")
        t.append(("via raw_reader passa", ok is True))
        # 3) gunzip de raw_replay .gz no shell sem raw_reader → bloqueia
        ok, _ = decide("gunzip -c 'TradingData/raw_replay/XAUUSD/15M/x.jsonl.gz' | head")
        t.append(("gunzip raw_replay bloqueia", ok is False))
        # 4) gzip.open de outro .gz (não raw_replay) → passa (não é o RAW)
        ok, _ = decide("gzip.open('/tmp/whatever.gz','rt')")
        t.append(("gz não-raw_replay passa", ok is True))
        # 5) escape auditável → passa
        ok, _ = decide("# RAW_READER_OK: inspeção pontual da estrutura\ngunzip -c raw_replay/x.gz | head")
        t.append(("RAW_READER_OK passa", ok is True))
        # 6) o próprio coletor → passa
        ok, _ = decide("run_xau_replay_feature_collect.py escreve raw_replay/x.jsonl.gz via gzip.open")
        t.append(("coletor passa", ok is True))
        for lab, r in t:
            print("  [%s] %s" % ("OK" if r else "FAIL", lab))
        allok = all(r for _, r in t)
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    sys.exit(main())
