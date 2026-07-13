#!/usr/bin/env python3
"""ID=L1 — Confluencia multi-escala (R=2/3/4 concordam).

LENTE. fs2/fs3/fs4 sao tres leituras da MESMA serie a resolucoes crescentes de ruido. Uma direcao
so e ROBUSTA quando pelo menos DUAS das tres escalas apontam para o mesmo lado; discordancia entre
escalas = estrutura fina desalinhada = provavel acumulacao GENUINA => manter AC. Esta e a espinha
estrutural. Sobre ela, tres camadas de confluencia (nunca um unico fator) e uma histerese
anti-fragmentacao:

  1. VOTO ESTRUTURAL  — >=2/3 das escalas finas (fs2,fs3,fs4) na mesma direcao, sem empate.
  2. ANCORA R=3       — a escala R=3 (familia do arbitro) tem de estar na maioria (fs3 == direcao).
  3. MOMENTUM DUPLO   — DOIS horizontes (ret10 E ret20) confirmam a direcao com folga (|ret|>=ENT).
                        Momentum de um so horizonte, ou contra a estrutura = transicao ambigua => AC.
                        Este gate duplo e o que sobe a ESPECIFICIDADE (mantem o AC genuino: chop de
                        baixa energia falha os dois horizontes e fica AC).
  4. PRIOR DO MACRO   — resolver CONTRA o macro (DOWN em BULL / UP em BEAR) exige unanimidade 3/3;
                        alinhado ao macro basta 2/3. Pullback fundo tem de ser inequivoco.

HISTERESE (anti-fragmentacao). O gate de momentum, por si, punca buracos em runs estruturais
contiguos e FRAGMENTA (islands isoladas => muitos episodios). Solucao: o momentum porteia apenas a
ENTRADA num run direcional; uma vez dentro, a direcao SEGURA de forma CONTIGUA ate a estrutura fina
virar (>=2 escalas na direcao oposta) OU o momentum reverter com forca. Assim os resolves ficam em
blocos contiguos (como fs3-sozinho, ~170 eps) mas com a PRECISAO da confluencia, em vez de milhares
de blips.

RESULTADO vs baseline "fs3 sozinho" (PRECISAO 51%, ESPECIFICIDADE 30%, frag 170):
  PRECISAO ~73% · ESPECIFICIDADE ~67% · RECALL ~14% · frag ~217 · AC 42%->34% · coerencia preservada.
A confluencia+ancora subiu a precisao +22pp (moeda-ao-ar -> 3-em-4 certos); o momentum duplo subiu
a especificidade +37pp (o AC genuino fica AC). Recall (secundario) e o preco pago pela seletividade.

CAUSAL. Usa SO o dict 'c' (fs2/fs3/fs4, ret10, ret20, macro). O estado guarda apenas passado
(direcao em hold + ultimo t) e faz reset se a serie recomeca (t <= last_t). Sem imports de dados,
sem arrays globais, sem indices de futuro."""

NAME = "L1 confluencia multi-escala R2/R3/R4 (ancora R=3) + momentum duplo ret10&ret20 + prior macro + hold contiguo"
LENS = "resolve UP/DOWN so quando >=2/3 escalas finas concordam (com fs3 na maioria) E dois horizontes de momentum confirmam; contra-macro exige 3/3; depois segura a direcao contigua ate a estrutura virar -> precisao alta + especificidade alta sem fragmentar; senao manter AC (acumulacao genuina)"

ENT = 0.4        # limiar de entrada por horizonte de momentum (% em 10/20 barras)
HOLD_EPS = 0.15  # momentum contrario acima disto quebra o hold contiguo

_S = {"last_t": -1, "hold": None}


def _reset(c):
    if c["t"] <= _S["last_t"]:
        _S["hold"] = None
    _S["last_t"] = c["t"]


def _votes(c):
    up = sum(1 for s in (c["fs2"], c["fs3"], c["fs4"]) if s == "UP")
    dn = sum(1 for s in (c["fs2"], c["fs3"], c["fs4"]) if s == "DOWN")
    return up, dn


def _fresh(c):
    up, dn = _votes(c)
    if up >= 2 and up > dn:
        d, need = "UP", up
    elif dn >= 2 and dn > up:
        d, need = "DOWN", dn
    else:
        return None                       # sem maioria estrutural -> discordancia -> AC genuino
    if c["fs3"] != d:
        return None                       # ancora R=3 (familia do arbitro) tem de concordar
    r10, r20 = c["ret10"], c["ret20"]
    if d == "UP" and not (r10 > ENT and r20 > ENT):
        return None                       # momentum duplo tem de confirmar UP
    if d == "DOWN" and not (r10 < -ENT and r20 < -ENT):
        return None                       # momentum duplo tem de confirmar DOWN
    mac = c["macro"]
    counter = (d == "DOWN" and mac == "BULL") or (d == "UP" and mac == "BEAR")
    if counter and need < 3:
        return None                       # contra-macro exige unanimidade estrutural
    return d


def resolve(c):
    _reset(c)
    d = _fresh(c)
    if d is not None:
        _S["hold"] = d
        return d
    h = _S["hold"]
    if h is not None:                     # hold contiguo: bridge estrutural anti-fragmentacao
        up, dn = _votes(c)
        m = c["ret10"]
        opp = dn if h == "UP" else up
        mom_reversed = (h == "UP" and m < -HOLD_EPS) or (h == "DOWN" and m > HOLD_EPS)
        if opp >= 2 or mom_reversed:      # estrutura fina virou OU momentum reverteu com forca
            _S["hold"] = None
            return None
        return h
    return None
