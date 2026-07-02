#!/usr/bin/env python3
"""SANITY_PROBE — cálculo de custo de carry XAU long (aritmética pura, NÃO análise de estratégia/leitura de barra).
Swap long ouro = negativo: financiar posição long custa a taxa USD (~5%/ano) + markup do broker. Custo em R/mês."""
rate=0.05  # taxa financiamento USD a.a. (SOFR ~4.3% + markup ~0.5-1%; confirmar contract-spec Pepperstone)
for preco in (3000,4600):
    usd=preco*100*rate/365   # 1 lote padrão = 100 oz
    print(f"Preço ${preco}: swap long ~ -${usd:.0f}/lote(100oz)/noite  (~-${usd*30:.0f}/mês/lote, +Wed 3x)")
print("\nCusto em R por MÊS = (taxa/12) / risco%_do_preço:")
for rp in (0.01,0.025,0.05):
    print(f"  risco {rp*100:.1f}% do preço -> {(rate/12)/rp:.2f} R/mês de carry")
print("\nAplicado aos teus swing reais (bruto - carry = líquido):")
for tag,m,rp,R in (("B3",5.4,0.024,6.25),("B6",9.2,0.060,6.71)):
    c=(rate/12)/rp*m
    print(f"  {tag}: +{R:.2f}R - {c:.2f}R ({m:.1f} meses) = +{R-c:.2f}R líquido")
