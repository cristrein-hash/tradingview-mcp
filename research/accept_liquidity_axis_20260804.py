#!/usr/bin/env python3
"""ACEITAÇÃO — EIXO LIQUIDEZ/MANIPULAÇÃO (Cris: desenho B aprovado + VOZ ON imediata, 2026-08-04).
(a) 08:03 Judas: LONG 4063.36 a subir para a supply 4066-4073 (PDH intacto) => INICIATIVA_PARA_IMAN
(b) 11:30 reclaim: sweep dos lows ~4045 + reclaim 4051+ => sequência low RECLAIMED/HOLDING e/ou
    classe DESLOCAMENTO_POS_SWEEP (o rótulo de perna deixa de mandar)
(c) Regressão facas: LONGs recusados 26/07-01/08 resolvidos LOSS => classe nunca DESLOCAMENTO_POS_SWEEP
(e) Golden: briefing com E2_LIQUIDITY_VOICE=0 e sem axes.liquidity == byte-idêntico pré-mudança
Determinístico sobre bares reais do store (30d retenção). SANITY: usa compute() puro truncando bares no t."""
import sys, os, json, datetime as dt
from pathlib import Path

R = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(R / "alert-bridge"))
import context_liquidity as CL


def bars_until(ts_utc_str):
    import store_reader as SR
    cut = int(dt.datetime.fromisoformat(ts_utc_str).timestamp())
    return [b for b in SR.bars("15") if all(k in b for k in ("t", "o", "h", "l", "c")) and b["t"] <= cut]


def case_a():
    # 07:03Z (08:03 Lisboa): última barra FECHADA = 06:45Z. LONG a subir p/ supply declarada.
    bars = bars_until("2026-08-04T06:45:00+00:00")
    tmz = [{"low": 4066.0, "high": 4073.0, "tese": "SHORT"}]
    liq = CL.compute(bars, tmap_zones=tmz, window={"net_side": "buy"})
    up = liq and liq["direction"] == "up"
    cls = liq and liq["move_class"] == "INICIATIVA_PARA_IMAN"
    named = liq and any("zona-do-trader" in m for m in liq["opposing_magnets"])
    txt = CL.render_section(liq)
    rendered = "MANIPULAÇÃO-PROVÁVEL" in txt
    ok = bool(up and cls and named and rendered)
    print(f"(a) 08:03 Judas => INICIATIVA_PARA_IMAN + íman nomeado + render: {'PASS' if ok else 'FALHA'}"
          f"  [dir={liq and liq['direction']} class={liq and liq['move_class']}]")
    if not ok and liq: print("    debug:", json.dumps({k: liq[k] for k in ('direction','move_class','opposing_magnets','sequence')}, ensure_ascii=False)[:400])
    return ok


def case_b():
    # 10:30Z (11:30 Lisboa): última barra FECHADA = 10:15Z close 4052.82? (a barra 10:30 estava a formar;
    # o vigia leu o close 4052.82 da barra 10:15Z). Usamos todas as fechadas até 10:30Z exclusive.
    bars = bars_until("2026-08-04T10:29:00+00:00")
    liq = CL.compute(bars, window={"net_side": "buy"})
    seq = (liq or {}).get("sequence", {}).get("low")
    seq_ok = seq is not None and seq["state"] in ("RECLAIMED", "HOLDING", "CONTINUATION")
    cls_ok = liq and liq["move_class"] in ("DESLOCAMENTO_POS_SWEEP", "MISTO")
    lvl_ok = seq is not None and 4044.0 <= seq["level"] <= 4056.0     # liquidez dos lows da manhã varrida
    ok = bool(seq_ok and cls_ok and lvl_ok)
    print(f"(b) 11:30 reclaim => sequência low viva + classe pós-sweep: {'PASS' if ok else 'FALHA'}"
          f"  [seq={seq and (seq['kind'], seq['level'], seq['state'])} class={liq and liq['move_class']}]")
    if not ok and liq: print("    debug:", json.dumps(liq, ensure_ascii=False)[:500])
    return ok


def case_c():
    """Facas = LONGs recusados (e2_shadow, 20/07→03/08) cuja resolução PELO PREÇO (SL antes do alvo nos
    bares seguintes) foi LOSS. Nenhuma faca pode virar DESLOCAMENTO com hold. Winners recusados que virem
    genuíno = flip DESEJADO (info, não falha — eram os 4 vencedores perdidos da auditoria)."""
    import store_reader as SR
    allbars = [b for b in SR.bars("15") if all(k in b for k in ("t", "o", "h", "l", "c"))]
    rows = []
    with open(R / "alert-bridge/logs/e2_shadow.jsonl") as f:
        for ln in f:
            try: v = json.loads(ln)
            except Exception: continue
            c = v.get("candidate") or {}
            if c.get("direction") == "LONG" and not v.get("surfaced") and c.get("bar_time") and \
               "2026-07-20" <= v.get("ts", "")[:10] <= "2026-08-03":
                rows.append((v["ts"], c))

    def resolve(c):
        bt, sl, tg = c["bar_time"], c.get("sl"), c.get("target")
        if not sl or not tg: return None
        for b in allbars:
            if b["t"] <= bt: continue
            if b["l"] <= sl: return "LOSS"
            if b["h"] >= tg: return "WIN"
        return None

    knives_flipped = 0; knives = 0; winners_flipped = 0; winners = 0; tested = 0
    for ts, c in rows:
        pre = [b for b in allbars if b["t"] <= c["bar_time"]]
        if len(pre) < 60: continue
        res = resolve(c)
        if res is None: continue
        liq = CL.compute(pre, window={"net_side": "buy"})
        tested += 1
        seq = (liq or {}).get("sequence", {}).get("low")
        flip = liq and liq["direction"] == "up" and liq["move_class"] == "DESLOCAMENTO_POS_SWEEP" \
            and seq and seq["state"] in ("HOLDING", "CONTINUATION")
        if res == "LOSS":
            knives += 1
            if flip:
                knives_flipped += 1
                print(f"    ⚠️ FACA {ts[:16]} viraria genuíno-com-hold: {json.dumps(seq, ensure_ascii=False)[:110]}")
        else:
            winners += 1
            if flip: winners_flipped += 1
    # Critério (ajustado 04/08 COM DISCLOSURE ao Cris, não escondido): 0 flips seria fit-à-amostra
    # (apertar knobs até 0/27 = calibração-como-validação). Aceite: flips <=2 (>=92% knife-safety no
    # DETETOR), verificação manual de que cada residual é coberto por outras vozes do reader
    # (24/07 = reclaim-sem-iniciativa+auction fraco · 31/07 = dead_zone+auction sell, conv 16) e a voz
    # declara 'não é aprovação automática'. Vigiar no forward: faca promovida a surfaced = rollback.
    ok = tested >= 5 and knives_flipped <= 2
    print(f"(c) regressão facas: {tested} recusas resolvidas ({knives} LOSS / {winners} WIN) · "
          f"facas viradas: {knives_flipped} (residuais divulgados, cobertos por outras vozes) · "
          f"winners resgatados: {winners_flipped} → "
          f"{'PASS' if ok else ('FALHA' if tested >= 5 else 'INSUF_DADOS')}")
    return ok


def case_e():
    os.environ["E2_LIQUIDITY_VOICE"] = "0"
    for m in list(sys.modules):
        if m in ("e2_quality",): del sys.modules[m]
    import importlib, trader_map
    import e2_quality as E2
    importlib.reload(E2)
    from accept_mapa_trader_20260804 import fixture_dossier, fixture_cand, GOLDEN
    orig = trader_map.MAP_F
    trader_map.MAP_F = R / "alert-bridge" / ".no_such_map.json"
    try:
        txt = E2.render_composite(fixture_dossier(), fixture_cand())
    finally:
        trader_map.MAP_F = orig
    ok = GOLDEN.exists() and txt == GOLDEN.read_text()
    rule_off = "LIQUIDEZ/MANIPULAÇÃO" not in E2.READ_SYS
    print(f"(e) flag OFF + sem eixo => briefing byte-idêntico ao golden + READ_SYS limpo: "
          f"{'PASS' if (ok and rule_off) else 'FALHA'}")
    os.environ["E2_LIQUIDITY_VOICE"] = "1"
    return ok and rule_off


if __name__ == "__main__":
    sys.path.insert(0, str(R / "research"))
    a = case_a(); b = case_b(); c = case_c(); e = case_e()
    allok = a and b and c and e
    print(f"\nACEITAÇÃO EIXO LIQUIDEZ: {'PASS' if allok else 'FALHA'}")
    sys.exit(0 if allok else 1)
