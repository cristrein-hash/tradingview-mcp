#!/usr/bin/env python3
"""BLOCKER — RAW lineage / source guard para labs XAU 15M (XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1 §D).
Le o GATE MANIFEST de um lab e BLOQUEIA (exit 1) se a fonte for suspeita. Prova mecanica de RAW-first
ANTES de qualquer resultado. Sem PASS, o lab nao roda.

Regras que bloqueiam:
  - manifest ausente / sem bloco json / chaves obrigatorias em falta
  - raw_file declarado inexistente
  - derived_file sem source_ref OU sem checksum
  - checksum sha256 declarado != sha256 real do ficheiro
  - SLIM/proxy em qualquer path/source_ref
  - fonte contaminada (Fractal-MTF / FaseD / Kaufman-ER) usada como fonte
  - resample HTF como fonte com allow_resample=false
  - staging/cache/tmp como fonte sem lineage
  - HTF (4H/1D/htf) usado sem htf_stale_declared
Saida OK: 'RAW_LINEAGE_PASS'."""
import sys, os, re, json, argparse, hashlib

REQUIRED = ["lab_name","strategy","direction","timeframe","raw_files","derived_files",
            "allow_resample","structural_buckets","outputs","stop_conditions"]
BANNED_SOURCE = ["slim", "fractal-mtf", "fractal_mtf", "fased", "fase_d", "fased∩", "kaufman-er", "kaufman_er"]
STAGING_HINTS = ["/staging/", "/cache/", "/tmp/", "scratchpad"]

def load_manifest(path):
    if not os.path.exists(path):
        return None, f"manifest inexistente: {path}"
    txt = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r"```json\s*(\{.*?\})\s*```", txt, re.DOTALL)
    if not m:
        return None, "manifest sem bloco ```json``` machine-readable"
    try:
        return json.loads(m.group(1)), None
    except Exception as e:
        return None, f"bloco json invalido: {e}"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()

def walk_strings(obj):
    if isinstance(obj, str): yield obj
    elif isinstance(obj, dict):
        for v in obj.values(): yield from walk_strings(v)
    elif isinstance(obj, list):
        for v in obj: yield from walk_strings(v)

def main():
    ap = argparse.ArgumentParser(description="BLOCKER RAW lineage/source guard para labs XAU 15M (protocolo V1).")
    ap.add_argument("--manifest", required=True, help="path do GATE MANIFEST do lab (.md com bloco json)")
    ap.add_argument("--strict-existence", action="store_true", help="FAIL se raw_file nao existe (default: WARN se HD /Volumes ausente)")
    a = ap.parse_args()

    fails, warns = [], []
    man, err = load_manifest(a.manifest)
    if err:
        print(f"RAW_LINEAGE_FAIL\n  - {err}"); return 1

    for k in REQUIRED:
        if k not in man: fails.append(f"chave obrigatoria ausente no manifest: '{k}'")

    allow_resample = bool(man.get("allow_resample", False))

    # raw files existencia
    for rf in man.get("raw_files", []):
        if not isinstance(rf, str): fails.append(f"raw_file nao-string: {rf}"); continue
        if not os.path.exists(rf):
            if rf.startswith("/Volumes/") and not a.strict_existence:
                warns.append(f"raw_file HD externo ausente (montar antes de correr o lab): {rf}")
            else:
                fails.append(f"raw_file declarado inexistente: {rf}")

    # derived files: source_ref + checksum obrigatorios; verificar sha256 se declarado e ficheiro existe
    for df in man.get("derived_files", []):
        if not isinstance(df, dict): fails.append(f"derived_file nao-objeto: {df}"); continue
        p = df.get("path", "")
        if not df.get("source_ref"): fails.append(f"derived sem source_ref: {p}")
        ck = df.get("checksum", "")
        if not ck: fails.append(f"derived sem checksum: {p}")
        if p and any(h in p for h in STAGING_HINTS): fails.append(f"staging/cache/tmp como fonte (sem lineage): {p}")
        if ck and ck not in ("PENDING", "sha256:PENDING") and os.path.exists(p):
            real = sha256(p)
            if real != ck: fails.append(f"checksum divergente em {p}: manifest={ck} real={real}")

    # fonte contaminada / SLIM / resample em qualquer string
    for s in walk_strings(man):
        low = s.lower()
        for b in BANNED_SOURCE:
            if b in low: fails.append(f"fonte proibida/contaminada referenciada: '{b}' em '{s[:80]}'")
        if "resample" in low and not allow_resample:
            fails.append(f"resample como fonte com allow_resample=false: '{s[:80]}'")

    # HTF sem declaracao de stale
    uses_htf = any(re.search(r"(4h|1d|htf|60m|30m)", str(x).lower()) for x in (man.get("raw_files", []) + [d.get("path","") for d in man.get("derived_files", []) if isinstance(d,dict)] + man.get("fields", [])))
    if uses_htf and not str(man.get("htf_stale_declared", "")).strip():
        fails.append("usa HTF (4H/1D/30M/1H/htf) mas 'htf_stale_declared' vazio — declarar freeze ou 'none'")

    # scripts declarados: scan leve por SLIM
    for sc in man.get("scripts", []):
        if isinstance(sc, str) and os.path.exists(sc):
            body = open(sc, encoding="utf-8", errors="replace").read().lower()
            if re.search(r"[^a-z]slim[^a-z]", body): warns.append(f"script referencia 'slim' (verificar): {sc}")

    for w in warns: print(f"WARN  {w}")
    if fails:
        print("RAW_LINEAGE_FAIL")
        for f in fails: print(f"  - {f}")
        return 1
    print("RAW_LINEAGE_PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
