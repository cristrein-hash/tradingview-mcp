#!/usr/bin/env python3
"""RAW-READ GUARD (Cris 2026-08-16) — leitura de RAW só pelo leitor canónico.
BLOQUEIA (exit 2) qualquer Bash/Write/Edit que leia um `raw_replay/*.gz` DIRETAMENTE (gzip.open/gunzip/zcat)
SEM importar/usar `raw_reader`. Fecha a dor recorrente: cada script re-implementava o parse do RAW (grp copiado,
list-vs-dict, ohlcv[-1], zones-vs-all_boxes, barra-0) e PARTIA. Agora há UM leitor validado (my-strategy/core/
raw_reader.py, selftest contra registo real) e este guard proíbe re-implementá-lo.

Passa se: usa `raw_reader`; OU é o próprio leitor/coletor/hook; OU declara escape auditável `RAW_READER_OK`.
Núcleo decide() puro = testável. py3 stdlib."""
import sys, json, re

# EXEMPT = o coletor, hooks, e o escape auditável. NÃO o mero import 'raw_reader' (hole-1 2026-08-16: um
# ficheiro que importe raw_reader podia AINDA fazer gzip.open manual e passar). O próprio leitor/guard eximem-se
# por FICHEIRO (fpath), não por texto.
EXEMPT = ("run_xau_replay_feature_collect", "/hooks/", ".claude/hooks", "raw_reader_ok")
SELF_FILES = ("raw_reader.py", "raw_read_guard.py")
DIRECT = re.compile(r"gzip\.open|gzip\.gzipfile|\bgunzip\b|\bzcat\b", re.I)


def decide(text, fpath=""):
    """(ok, msg) puro. Bloqueia leitura direta de raw_replay/TradingData *.gz sem raw_reader."""
    low = (text or "").lower(); fp = (fpath or "").lower()
    if any(fp.endswith(s) for s in SELF_FILES):        # editar o próprio leitor/guard = ok (por ficheiro)
        return True, ""
    if any(x in low for x in EXEMPT):
        return True, ""
    # hole-2 (2026-08-16): apanha também o path do HD (TradingData) sem o literal 'raw_replay'. Limite honesto:
    # se o path vier SÓ de variável (nenhum literal de path no texto), a hook de TEXTO não o vê (irredutível).
    reads_raw_gz = (".gz" in low) and ("raw_replay" in low or "tradingdata" in low)
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
    ok, msg = decide(text, ti.get("file_path") or "")
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
        # 7) HOLE-1 FECHADO: importa raw_reader MAS faz gzip.open manual de raw_replay → BLOQUEIA
        ok, _ = decide("import raw_reader as RR\nimport gzip\ngzip.open('raw_replay/x.jsonl.gz')")
        t.append(("import raw_reader + gzip.open manual bloqueia (hole-1)", ok is False))
        # 8) editar o próprio raw_reader.py (fpath) → passa
        ok, _ = decide("import gzip; gzip.open('.../raw_replay/x.gz')", fpath="/x/my-strategy/core/raw_reader.py")
        t.append(("editar raw_reader.py passa (fpath)", ok is True))
        # 9) HOLE-2 ALARGADO: path TradingData (sem literal raw_replay) + gunzip → BLOQUEIA
        ok, _ = decide("gunzip -c '/Volumes/HD/TradingData/XAUUSD/15M/x.jsonl.gz' | head")
        t.append(("TradingData sem 'raw_replay' bloqueia (hole-2)", ok is False))
        for lab, r in t:
            print("  [%s] %s" % ("OK" if r else "FAIL", lab))
        allok = all(r for _, r in t)
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    sys.exit(main())
