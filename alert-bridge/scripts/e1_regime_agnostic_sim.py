#!/usr/bin/env python3
"""SIMULAÇÃO OFFLINE (Cris 2026-07-18) — re-pontua os candidatos E1 logados sob o esquema REGIME-AGNÓSTICO
proposto, para quantificar: quantas REVERSÕES (contra-regime) o gate atual decapita, e quantas um gate de
PRESENÇA-de-contexto recuperaria + custo no funil. ZERO mudança live — lê logs/e1_candidates.jsonl.
Aproximação fiel dos campos logados (breakdown antigo + dossier.mtf). py3.9."""
import json, sys
from pathlib import Path
from collections import Counter
LOG = Path(__file__).resolve().parents[1] / "logs" / "e1_candidates.jsonl"


def regime_of(mtf):
    """DOWN/UP/RANGE a partir dos trends HTF logados (240 âncora, 60 apoio)."""
    ts = [(mtf.get(t) or {}).get("trend") for t in ("240", "60")]
    if "DOWN" in ts and "UP" not in ts: return "DOWN"
    if "UP" in ts and "DOWN" not in ts: return "UP"
    return "RANGE"


def at_htf_extreme(mtf):
    """pos_in_leg perto de 0 ou 1 no 4H/1H = extremo (contexto de reversão legítimo)."""
    for t in ("240", "60"):
        p = (mtf.get(t) or {}).get("pos")
        if p is not None and (p <= 0.15 or p >= 0.85):
            return True
    return False


def new_score(cand):
    """Esquema regime-agnóstico: PRESENÇA de contexto + caminho de reversão. Sem agreement de regime."""
    b = (cand.get("materiality") or {}).get("confluence_breakdown") or {}
    mtf = (cand.get("dossier") or {}).get("mtf") or {}
    s = 0; parts = {}
    # 1. estrutura HTF legível (presença, qualquer lado)
    parts["mtf_context"] = 1 if any((mtf.get(t) or {}).get("trend") for t in ("240", "60")) else 0
    # 2. zona presente (era direction-specific; presença OU extremo)
    parts["zone_ctx"] = 1 if (b.get("zone") or at_htf_extreme(mtf)) else 0
    # 3. auction presente
    parts["auction_ctx"] = 1 if b.get("auction") else 0
    # 4. momentum legível
    parts["momentum_ctx"] = 1 if (b.get("momentum") or 0) >= 1 else 0
    # 5. caminho de REVERSÃO: extremo HTF
    parts["reversal_ctx"] = 1 if at_htf_extreme(mtf) else 0
    # 6. macro
    parts["macro"] = 1 if b.get("macro") else 0
    return sum(parts.values()), parts


def main():
    rows = [json.loads(l) for l in LOG.read_text().splitlines()
            if l.strip() and ('"2026-07-17' in l or '"2026-07-18' in l)]
    tot = len(rows)
    old_pass = sum(1 for r in rows if (r.get("materiality") or {}).get("pass"))
    # contra-regime = direção oposta ao regime HTF
    def counter_regime(r):
        reg = regime_of((r.get("dossier") or {}).get("mtf") or {})
        d = r.get("direction")
        return (reg == "DOWN" and d == "LONG") or (reg == "UP" and d == "SHORT")
    killed_score = [r for r in rows if not (r.get("materiality") or {}).get("pass")
                    and (r.get("materiality") or {}).get("min_rr_ok")
                    and ((r.get("materiality") or {}).get("confluence") or 0) < 2]
    killed_cr = [r for r in killed_score if counter_regime(r)]
    killed_cr_ctx = [r for r in killed_cr if new_score(r)[0] >= 2]
    print(f"=== base: {tot} candidatos · old materiality PASS: {old_pass} ===")
    print(f"mortos por score<2 (com RR ok): {len(killed_score)}")
    print(f"  destes, CONTRA-REGIME (reversões decapitadas): {len(killed_cr)}")
    print(f"  destes, com CONTEXTO legível (novo gate ≥2 recuperaria): {len(killed_cr_ctx)}")
    # funil sob o novo esquema, vários limiares
    print("\n=== funil sob esquema REGIME-AGNÓSTICO (RR ok mantém-se pré-req) ===")
    rr_ok = [r for r in rows if (r.get("materiality") or {}).get("min_rr_ok")]
    for thr in (2, 3):
        new_pass = [r for r in rr_ok if new_score(r)[0] >= thr]
        cr_new = sum(1 for r in new_pass if counter_regime(r))
        print(f"  novo score ≥{thr}: admite {len(new_pass)} (vs {old_pass} atual) | contra-regime admitidos: {cr_new}")
    # distribuição do novo score
    nd = Counter(new_score(r)[0] for r in rr_ok)
    print("  distribuição novo score (RR ok):", dict(sorted(nd.items())))
    # --- gate DISCRIMINANTE agnóstico: "num nível real" (zona OU extremo HTF) + variações ---
    print("\n=== gate DISCRIMINANTE (agnóstico à direção, mas seletivo) ===")
    def at_level(r):
        b = (r.get("materiality") or {}).get("confluence_breakdown") or {}
        mtf = (r.get("dossier") or {}).get("mtf") or {}
        return bool(b.get("zone")) or at_htf_extreme(mtf)
    def auction_on(r):
        return bool(((r.get("materiality") or {}).get("confluence_breakdown") or {}).get("auction"))
    g_level = [r for r in rr_ok if at_level(r)]
    g_level_auc = [r for r in rr_ok if at_level(r) and auction_on(r)]
    cr = lambda lst: sum(1 for r in lst if counter_regime(r))
    print(f"  'num nível real' (zona|extremo HTF): admite {len(g_level)}/{len(rr_ok)} | contra-regime: {cr(g_level)}")
    print(f"  'nível real E auction ativa': admite {len(g_level_auc)}/{len(rr_ok)} | contra-regime: {cr(g_level_auc)}")
    # os 104 reversões decapitadas: quantas estão 'num nível real'?
    rec = [r for r in killed_cr if at_level(r)]
    print(f"  das {len(killed_cr)} reversões hoje decapitadas, 'num nível real' (recuperáveis, seletivo): {len(rec)}")

    # --- FILTRO NEUTRO agnóstico: act_dens (atividade de order-flow, NÃO lado) + colapso por nível ---
    print("\n=== FILTRO NEUTRO: act_dens (agnóstico à direção — mede atividade, não lado) ===")
    def actd(r):
        return ((r.get("dossier") or {}).get("act_dens"))
    vals = sorted(v for v in (actd(r) for r in rr_ok) if v is not None)
    if vals:
        import statistics as st
        q = lambda p: vals[min(len(vals)-1, int(p*len(vals)))]
        print(f"  act_dens (n={len(vals)}): min {vals[0]} q25 {q(.25)} mediana {st.median(vals)} q75 {q(.75)} max {vals[-1]}")
    for floor in (0.2, 0.3, 0.4, 0.5):
        adm = [r for r in rr_ok if (actd(r) or 0) >= floor]
        crn = sum(1 for r in adm if counter_regime(r))
        print(f"  act_dens ≥ {floor}: admite {len(adm)}/{len(rr_ok)} | contra-regime (reversões) preservadas: {crn}")
    # combinado: act_dens floor + colapso 'um read por (janela 1h, direção, nível arredondado)'
    print("\n=== NEUTRO combinado: act_dens≥0.3 + colapso (bar-hora × direção × nível~) ===")
    for floor in (0.3, 0.4):
        seen = set(); adm = 0; crn = 0
        for r in sorted(rr_ok, key=lambda x: x.get("bar_time") or 0):
            if (actd(r) or 0) < floor: continue
            bt = r.get("bar_time") or 0
            key = (bt // 3600, r.get("direction"), round((r.get("entry") or 0)))
            if key in seen: continue
            seen.add(key); adm += 1
            if counter_regime(r): crn += 1
        print(f"  act_dens≥{floor} + colapso: admite {adm}/{len(rr_ok)} | reversões: {crn}")

    # o caso de sexta: os 2 LONGs recusados e os 2 SHORTs surfaced
    print("\n=== casos GT de sexta (reclassificação) ===")
    for r in rows:
        rid = r.get("id", "")
        if any(k in rid for k in ("1784313075", "1784309400")) or \
           (r.get("direction") == "LONG" and (r.get("materiality") or {}).get("confluence", 9) and "2026-07-17T12:37" in (r.get("ts") or "")):
            ns, parts = new_score(r)
            print(f"  {r.get('ts','')[11:16]} {r.get('rule')} {r.get('direction')} old_score={(r.get('materiality') or {}).get('confluence')} -> new_score={ns} {parts}")


if __name__ == "__main__":
    sys.exit(main())
