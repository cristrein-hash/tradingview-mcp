#!/usr/bin/env python3
"""L2 — Momentum-led leg resolver for ACUMULACAO bars.

TESE: os pivôs finos confirmam TARDE (fs3 sozinho ~51% = moeda-ao-ar). O RETORNO de close
LIDERA o pivô. Mas momentum sozinho tem erros nos topos/fundos (momentum residual do passado
enquanto a estrutura já virou). A cura NÃO é vetar com estrutura grossa (fs3-veto piora a
precisão) — é exigir CONFLUÊNCIA de três horizontes de momentum coerentes ENTRE SI e uma
confirmação leve da direção da perna fina (fd3), que anda mais rápido que a estrutura fs3.

REGRA (confluência causal, tudo <= i):
  UP   se ret20>+2.0%  E  ret10>+0.8%  E  ret5>+0.3%  E  fd3==UP
  DOWN se ret20<-2.0%  E  ret10<-0.8%  E  ret5<-0.3%  E  fd3==DOWN
  senão -> None (mantém ACUMULACAO)

Os limiares decrescem com o horizonte (2.0/0.8/0.3) => a perna acelera na direção certa
(não é só deriva antiga): ret20 pede amplitude, ret10/ret5 pedem que a inclinação PERSISTA
até ao presente (anti-reversão). fd3 confirma que a micro-estrutura fina concorda.

Calibrado no harness (AC bars 2019+): precisão ~85% (vs 51% do fs3 sozinho, ~80% do momentum
puro), especificidade ~76% (mantém o AC genuíno de baixo-momentum), sem sobre-resolver, e
fragmentação 436 episódios (< 458 do momentum puro apesar de menos resolvidos = os resolves
agrupam-se em tendências genuínas, não pingam isolados). Escolhido por MAXIMIZAR precisão+
especificidade+baixa-fragmentação, cedendo só o recall (secundário). CAUSAL: só usa o dict `c`."""

NAME = "L2 momentum-led (3-horizon confluence + fd3 confirm)"
LENS = "O retorno de close lidera o pivô; 3 horizontes de momentum alinhados + direção da perna fina confirmam."

# limiares (% de retorno de close), decrescentes com o horizonte = aceleração persistente
T20, T10, T5 = 2.0, 0.8, 0.3

def resolve(c):
    r20, r10, r5 = c["ret20"], c["ret10"], c["ret5"]
    fd3 = c["fd3"]
    # confluência UP: amplitude (ret20) + persistência (ret10, ret5) + micro-perna fina
    if r20 > T20 and r10 > T10 and r5 > T5 and fd3 == "UP":
        return "UP"
    # confluência DOWN (simétrica)
    if r20 < -T20 and r10 < -T10 and r5 < -T5 and fd3 == "DOWN":
        return "DOWN"
    return None
