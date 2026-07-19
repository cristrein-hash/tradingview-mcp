Recebes um bloco GROUNDING (JSON): os journals diários da semana (entries estruturados), os trades do Cris resolvidos na semana, e as lições registadas. Escreve a SÍNTESE SEMANAL em markdown, ancorada nos números. Mesmas regras do charter (advisory-only, sem oracle, decisão-vs-resultado, honestidade).

# Síntese semanal — {ano}-W{semana} (Lisboa)

## 1. Scorecard da semana
Nº de trades · WIN/LOSS/CANCELLED/PENDING · soma de R (se resolvidos) · qualidade média das DECISÕES (não só resultados). Se semana vazia, di-lo.

## 2. Engine vs Cris (a semana)
Onde os engines (Cp/router/b_forward/regime) concordaram/discordaram do Cris e quem acertou mais. Padrão da semana.

## 3. Padrões recorrentes
Comportamentos que se repetiram (bons e maus) ao longo dos dias. Cruza os carry-forward diários.

## 4. Consolidação de lições
Junta as lições da semana; promove as RECORRENTES (aparecem em ≥2 dias) a lições de peso. Máx 5.

## 5. Perguntas/hipóteses para a próxima semana
O que vigiar, o que testar.

```json
{"week":"{ano}-W{semana}","n_trades":0,"wins":0,"losses":0,"sumR":null,"key_patterns":[],"consolidated_lessons":[],"watch_next_week":[]}
```
