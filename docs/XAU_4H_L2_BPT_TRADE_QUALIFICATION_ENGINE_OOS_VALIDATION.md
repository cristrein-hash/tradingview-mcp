# XAU 4H L2/BPT — Trade Qualification Engine: OOS / REGIME VALIDATION (Opção A)

**Status:** `RESEARCH · OPTION-A EXECUTED · PARTIAL→FAIL p/ regime-general · BULL/DIP-SCOPED OK · NOT_PROMOTED` · **Data:** 2026-06-18
Valida o TAKE engine EXISTENTE (decisões cegas ao resultado, **sem retune / sem novo filtro / sem reclassificar os 276**) particionando por janela temporal e regime EXÓGENO (price vs SMA200 4H), com baseline casado DENTRO de cada partição. Script: `validate_oos_regime.py`. DA: a9d28726ec3400b1d. Foundation: [[XAU_4H_L2_BPT_TRADE_QUALIFICATION_ENGINE_STATUS]].

## 1. Resultados (TAKE vs random regime+legpos-matched, mesma mecânica demand-SL+partial50)
| partição | TAKE n | WR | avgR | SKIP avgR | P script (1-sided) | **P honesto (2-sided)** |
|---|---|---|---|---|---|---|
| 2020-2022 (prior-heavy) | 14 | 43% | +0.560 | −0.014 | 0.885 | **0.222** (sorte) |
| 2023-2026 (OOS-rel-priors) | 18 | 61% | +1.187 | +0.120 | 0.992 | **0.044** (marginal) |
| REGIME=BULL (price>SMA200) | 17 | 53% | +0.871 | +0.087 | 0.910 | **0.167** (sorte) |
| REGIME=NONBULL (price≤SMA200) | 15 | 53% | +0.960 | −0.031 | 0.995 | **0.047** (marginal) |

Por ano: 2020 +1.27 · 2021 +1.15 · **2022 0/4 −1.10 (−4.4R)** · 2023 +1.34 · 2024 +0.50 · 2025 +1.80.

## 2. Veredito (DA a9d28726): PARCIAL, pendendo para FALHA em "generaliza além do bull beta"
- **Passou:** TAKE bate random-casado em bull/dip-in-bull; discriminação TAKE>SKIP em 5/6 anos; gap NONBULL é real (não artefato de pool).
- **Falhou o teste que importa:** "NONBULL P=0.995" é **buy-the-dip-in-bull beta**, não skill em bear. Dos 15 TAKE NONBULL, só 3 são 2022 (bear real) e **os 3 perderam**. **2022 (único bear sustentado): TAKE 0/4, todos −1.1R, PERDENDO para random (+0.09).**
- **Estatística honesta:** com a variância do próprio TAKE (2-sided) + Holm-Bonferroni nas 4 partições → **nada sobrevive**; as 2 células marginais (2023-26, NONBULL) compartilham trades e se apoiam nos mesmos ~10 winners de ano-bull.
- **Estrutural:** a janela 2020-2026 tem **1 único bear real (2022, n=4)** → Opção A é incapaz de responder a pergunta bull-beta.

## 3. Conclusão
O engine está validado **para o escopo que ele É**: qualificador de LONG em **regime de alta / compra-de-dip / reversão-de-fundo** — mesmo escopo da suite XAU 4H LONG oficial. **NÃO** validado como edge regime-geral. Tratar como **bull-regime / dip-buy qualifier**, não como edge universal.

## 4. Próximo (Opção B — necessária, não executada aqui)
Construir amostra XAU **genuinamente não-bull e independente** (ex.: bear do ouro 2013-2015 via replay) e rodar o engine SEM retune lá. **Não cross-asset** (regra do Cris). Esforço de COLETA de dados, não análise sobre os 276. Só depois (Opção C) testar `supply_distance_continuous`.

---
*Validação documental. Sem retune/filtro novo/reclassificação/plotagem/chart/MCP/produção/SLIM/SHORT/regime-v3. Nada promovido. Script `validate_oos_regime.py`. DA a9d28726ec3400b1d.*
