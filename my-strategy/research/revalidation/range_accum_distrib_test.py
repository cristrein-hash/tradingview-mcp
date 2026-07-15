#!/usr/bin/env python3
"""TESTE DE GENERALIZAÇÃO (Cris 2026-07-15): em TODOS os episódios de RANGE do histórico, features
CAUSAIS no onset (crashPre / dd252 / predecessor) preveem a DIREÇÃO DE RESOLUÇÃO (subiu=acum / caiu=
distrib)? Rótulo de resolução = HINDSIGHT (só para o teste): o regime para onde o engine SAI do range
(BULL=up/acum, BEAR=down/distrib), cruzado com preço forward. Features = causais (onset). Macro-only.

Pré-registo das definições (sem afinar depois de ver):
 - RANGE episódio = run contíguo de 'RANGE' em build_layer1, duração >= 5 dias.
 - crashPre = existe crash (ret 2d <= -6%, o MESMO limiar do engine) na janela [onset-15, onset].
 - dd252@onset = drawdown do topo de 252d no onset (reporto valores; limiares como EXPLORATÓRIO).
 - resolução = regime de saída (1ª barra não-RANGE após o episódio). edge/None = UNRESOLVED (excluído).
 - erro perigoso p/ long = FN: crashPre=False mas resolve BEAR (deixa passar distribuição).
"""
import macro_structural_v3 as M, datetime as dt
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
T, H, L, C, N = M.T, M.H, M.L, M.C, M.N
reg = M.build_layer1()
CRASH_THR = -6.0; CRASH_WIN = 15; MINDUR = 5

# episódios run-length
epis = []
for i in range(N):
    if epis and epis[-1][0] == reg[i]: epis[-1][2] = i
    else: epis.append([reg[i], i, i])

crash_at = [((C[i]/C[i-2]-1)*100 <= CRASH_THR) if i >= 2 else False for i in range(N)]
rows = []
for k, (s, a, b) in enumerate(epis):
    if s != "RANGE": continue
    if (T[b]-T[a]) < MINDUR*86400: continue
    if a < 260: continue                                    # warmup dd252
    exit_reg = epis[k+1][0] if k+1 < len(epis) else None     # resolução (pós-range)
    if exit_reg not in ("BULL", "BEAR"): continue            # UNRESOLVED / edge -> exclui
    pred = epis[k-1][0] if k > 0 else "NENHUM"
    crashPre = any(crash_at[j] for j in range(max(2, a-CRASH_WIN), a+1))
    hi252 = max(H[max(0, a-252):a+1]); dd = (hi252-C[a])/hi252*100
    # cruzamento de preço: onset->saída e saída->+20d
    px_in_out = (C[b]-C[a])/C[a]*100
    fwd = min(N-1, b+20); px_out_fwd = (C[fwd]-C[b])/C[b]*100
    resolved_down = exit_reg == "BEAR"
    rows.append(dict(a=a, b=b, dur=int((T[b]-T[a])/86400), pred=pred, crashPre=crashPre, dd=dd,
                     exit=exit_reg, down=resolved_down, pio=px_in_out, pof=px_out_fwd))

print(f"RANGE episódios resolvidos (dur>=5d): N={len(rows)}  ({ds(T[rows[0]['a']])} … {ds(T[rows[-1]['a']])})")
nb = sum(r["down"] for r in rows)
print(f"BASE RATE: resolve BEAR(distrib) {nb}/{len(rows)} ({100*nb/len(rows):.0f}%) · BULL(acum) {len(rows)-nb} ({100*(len(rows)-nb)/len(rows):.0f}%)\n")
print(f"  {'onset':10} {'dur':>4} {'pred':>5} {'crashPre':>8} {'dd252':>6} {'->SAI':>5} {'in-out%':>7} {'out+20%':>7}  {'natureza'}")
for r in rows:
    nat = "DISTRIB(down)" if r["down"] else "ACUM(up)"
    print(f"  {ds(T[r['a']]):10} {r['dur']:>4} {str(r['pred']):>5} {str(r['crashPre']):>8} {r['dd']:>5.1f}% "
          f"{r['exit']:>5} {r['pio']:>+6.1f}% {r['pof']:>+6.1f}%  {nat}")

def cm(pred_down, rows):
    TP = sum(1 for r in rows if pred_down(r) and r["down"])
    FP = sum(1 for r in rows if pred_down(r) and not r["down"])
    FN = sum(1 for r in rows if not pred_down(r) and r["down"])
    TN = sum(1 for r in rows if not pred_down(r) and not r["down"])
    prec = TP/(TP+FP) if TP+FP else float('nan'); rec = TP/(TP+FN) if TP+FN else float('nan')
    acc = (TP+TN)/len(rows)
    return TP, FP, FN, TN, prec, rec, acc

print("\n== PREDITOR: crashPre => prevê DISTRIB(down) ==")
TP, FP, FN, TN, prec, rec, acc = cm(lambda r: r["crashPre"], rows)
print(f"  TP{TP} FP{FP} FN{FN} TN{TN} | precisão {prec:.2f} · recall-distrib {rec:.2f} · acc {acc:.2f}")
print(f"  FN (deixa passar distribuição = long em armadilha): {FN}  <== erro perigoso p/ long")
for thr in (8.0, 10.0, 12.0, 15.0):
    TP, FP, FN, TN, prec, rec, acc = cm(lambda r: r["dd"] >= thr, rows)
    print(f"  dd252>={thr:>4}% : TP{TP} FP{FP} FN{FN} TN{TN} | prec {prec:.2f} · recall {rec:.2f} · acc {acc:.2f} · FN {FN}")
for thr in (8.0, 10.0, 12.0):
    f = lambda r, t=thr: r["crashPre"] or r["dd"] >= t
    TP, FP, FN, TN, prec, rec, acc = cm(f, rows)
    print(f"  crashPre OR dd>={thr:>4}%: TP{TP} FP{FP} FN{FN} TN{TN} | prec {prec:.2f} · recall {rec:.2f} · acc {acc:.2f} · FN {FN}")
