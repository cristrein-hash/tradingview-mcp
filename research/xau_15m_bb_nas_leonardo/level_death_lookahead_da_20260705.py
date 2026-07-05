#!/usr/bin/env python3
"""DA VETOR B — look-ahead operacional na morte de nível (macro_level_test_entry).
sustained_death devolve k-run+1 (INÍCIO da run de 16 closes) — mas a morte só é CONHECÍVEL na
16ª barra (completion). Candidatos com fi em (início, completion] são excluídos usando até 15
closes FUTUROS. Quantificar: painel E1 (testa-A w32) sob morte-backdated (original) vs
morte-conhecível (e = completion). Se hit cair, o look-ahead inflava o painel."""
import json, bisect, random
import datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = (HERE / "macro_leg_position_veto_20260705.py").read_text()
exec(src.split("VETOS = {")[0])
N = len(S)
ATR = [b.get("atr") or 5.0 for b in S]
HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]

def swings(w, kind):
    arr = HI if kind == "H" else LO
    out = []
    for k in range(w, N - w):
        v = arr[k]
        seg = arr[k - w:k + w + 1]
        if (v == max(seg) if kind == "H" else v == min(seg)) and arr[k - w:k].count(v) == 0:
            out.append((k, v))
    return out

# família A w32, construção EXATA do macro_level_test_entry
A_LV = []
for k, H in swings(32, "H"):
    br = None
    for j in range(k + 32, min(k + 32 + 2880, N)):
        if CL[j] > H + 0.1 * ATR[j]:
            br = j; break
        if CL[j] < H - 6 * ATR[j]:
            break
    if br is None:
        continue
    c = 0; death_bd = N; death_kn = N
    for k2 in range(br, N):
        if CL[k2] < H - 0.25 * ATR[k2]:
            c += 1
            if c >= 16:
                death_bd = k2 - 15    # original (backdated)
                death_kn = k2         # conhecível (16º close)
                break
        else:
            c = 0
    A_LV.append({"lv": H, "s": br, "e_bd": death_bd, "e_kn": death_kn, "src": k})
LOOK = 30 * 96

def tests(fi, flo, a, mode):
    for z in A_LV:
        e = z["e_bd"] if mode == "bd" else z["e_kn"]
        if z["s"] < fi <= e and fi - z["src"] <= LOOK and abs(flo - z["lv"]) <= 1.0 * a:
            return True
    return False

UNIV = [u for u in U if u["cj_t"] in R3]
rows_bd, rows_kn = [], []
for u in UNIV:
    fi = bisect.bisect_right(TS, u["cj_t"]) - 1
    a = u.get("g_atr") or 5.0
    flo = u["g_sl"] + 0.1 * a
    if tests(fi, flo, a, "bd"):
        rows_bd.append(u)
    if tests(fi, flo, a, "kn"):
        rows_kn.append(u)

def pan(rows, tag):
    n = len(rows); h = sum(1 for u in rows if R3[u["cj_t"]]["R3"] >= 3)
    s = sum(R3[u["cj_t"]]["net3"] for u in rows)
    print(f"  {tag:<34} N{n:>5} hit3R {100*h/max(1,n):>5.1f}% sumR {s:>+8.1f}")
    return n, h, s

print("E1 testa-A(w32) — morte backdated (ORIGINAL, com look-ahead) vs conhecível (causal):")
nb, hb, sb = pan(rows_bd, "E1 morte-backdated (original)")
nk, hk, sk = pan(rows_kn, "E1 morte-conhecível (causal)")
extra = [u for u in rows_kn if u not in rows_bd]
if extra:
    he = sum(1 for u in extra if R3[u["cj_t"]]["R3"] >= 3)
    se = sum(R3[u["cj_t"]]["net3"] for u in extra)
    print(f"  candidatos EXCLUÍDOS pelo look-ahead: N{len(extra)} hit3R {100*he/len(extra):.1f}% sumR {se:+.1f}")
print("  (se o painel causal for pior, o look-ahead estava a inflar E1)")
