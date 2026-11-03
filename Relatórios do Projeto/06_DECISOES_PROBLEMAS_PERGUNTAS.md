# 06 — Decisões, problemas e perguntas

Registro do que já foi decidido, do que está dando errado, e do que
ainda depende de decisão.

---

# Parte A — Decisões tomadas

| # | Decisão | Origem |
|---|---|---|
| D1 | Base dos Dados **não** será fonte do alvo (falta tx_rend) | Conversa 30/09 |
| D2 | Fonte do alvo: tx_rend do INEP diretamente | Relatório diário |
| D3 | Base longitudinal v1.0 do orientador é referência, não substitui o código | README |
| D4 | `src/base_longitudinal.py` reproduz a base v1.0 | Log do bootstrap 01/10 |
| D5 | Separar em dois conjuntos (anos finais e EM) | Relatório diário |
| D6 | Alvo é a taxa de abandono do ano seguinte (t+1) | Relatório diário |
| D7 | INSE só para comparação de grupos, não como feature | Relatório diário |
| D8 | Pé-de-Meia entra na metodologia como período pré/pós-2024 | Sugestões do grupo |
| D9 | Cuidado com leakage do Pé-de-Meia | Sugestões do grupo |
| D10 | Manter todas as escolas na base; criar `elegivel_analise` | Sugestões do grupo |
| D11 | Escola indígena / localização diferenciada: incluir já | Sugestões do grupo |
| D12 | Multisseriadas: usar média do fundamental com flag | Sugestões do grupo |
| D13 | IED 2019–2020 e HAD: incluir se metodologia consistente | Sugestões do grupo |
| D14 | Categóricas com One-Hot (não target encoding) | Análise do v1 |
| D15 | Cada modelo só vê features da sua etapa | Análise do v1 |
| D16 | Corrigir os 4 problemas do v1 antes de tentar melhorar resultado | Análise do orientador |

---

# Parte B — Problemas conhecidos

**Dois prefixos, desde 2026-11-02.** `Pnnn` = problema de **dados**, com a
linha oficial em `abandono-escolar/docs/problemas.csv` (a numeração é a do
código e dos testes). `Mnnn` = problema de **método ou ambiente**, registrado
só neste documento. A colisão anterior (dois sistemas usando "P": P021 e P022
significavam coisas diferentes aqui e no `abandono-escolar`) foi resolvida
assim: P021 → M001, P022 → M002, P024 → M003, P025 → M004.

## P001 a P006 — herdados do repositório da Gabriela

Ver `docs/problemas.csv` no repositório. Cobre descobertas sobre os
dados do INEP (nomes de arquivo inconsistentes, etc.).

## P007 — md5 do INEP desatualizado

- O md5 publicado pelo INEP não confere com o arquivo do zip em 6
  planilhas de indicadores.
- **Consequência:** usar sha256 do manifesto como referência.
- **Status:** conhecido, tratado.

## P019 — IED 2019–2020 e HAD fora do desenho

- IED 2019–2020 e HAD estão nos dados mas não entram na base.
- **Motivo:** aguardando decisão com o orientador.
- **Pergunta:** a metodologia do INEP é consistente entre anos?
- **Status:** pendente.

## P020 — md5 do INEP desatualizado (caso específico)

- Caso irmão do P007 (HAD escolas 2020 e 2021).

## M001 — v1 atual tem 4 problemas metodológicos (antigo P021)

- Não filtra escolas públicas.
- Imputação quebrada por tipo.
- Imputação antes do split.
- Categóricas descartadas.
- **Correção:** ver `07_PLANOS.md`, Fase 2.
- **Status:** a corrigir.

## M002 — Instabilidade temporal do modelo (antigo P022)

- R² positivo no teste 2025, negativo na validação 2024.
- **Não é bug**, é característica dos dados.
- **Hipóteses:** pico de 2022, poucas observações, mudança
  comportamental pós-pandemia.
- **Status:** em análise.

## P023 — Base do orientador ausente

- `dados/externo/base_longitudinal_v1/` não estava no clone local.
- **Ação:** pedir ao orientador.
- **Status:** resolvido — em 2026-11-02 a pasta existe com os 6 arquivos.
  Linha proposta para `problemas.csv`.

## M003 — Bootstrap lento em pasta sincronizada (antigo P024)

- Tempo real ~3h52min (esperado ~44 min).
- **Causa provável:** pasta `Meu Drive` (Google Drive) atrapalhando
  I/O.
- **Recomendação:** mover para pasta local sem sync.
- **Status:** recomendação.

## M004 — Métricas de classificação ausentes (antigo P025)

- O projeto é de regressão, mas o uso real pede classificação
  (Recall@K).
- **Ação:** implementar segunda tarefa na Fase 4.
- **Status:** planejado.

---

# Parte C — Perguntas abertas

## Q1 — Sobre `src/base_longitudinal.py`

Quem escreve/valida? A Gabriela já fez? Está definitivo ou vai mudar?

**Impacto:** afeta reprodutibilidade do trabalho do Gustavo.

## Q2 — Sobre a base v1.0 do orientador

Será usada só como referência ou vira base oficial?

**Impacto:** se vira oficial, o pipeline precisa se adaptar a ela.

## Q3 — Critério de "bom o suficiente"

Qual R² / MAE / Recall@K é aceitável para o artigo?

**Impacto:** define quando parar de melhorar e começar a escrever.

## Q4 — Pico de 2022

Opção A (incluir no treino), B (treinar sem 2022) ou C (usar 2022 como
teste natural)?

**Impacto:** muda todo o split temporal. Decisão com o orientador.

## Q5 — IED 2019–2020 e HAD

Incluir no modelo ou só na análise? A metodologia é consistente entre
anos?

**Impacto:** afeta features da Fase 3. Ver P019.

## Q6 — Prazo das entregas

Quando vence o PIBIC? Quando vence o artigo da disciplina?

**Impacto:** define ritmo.

## Q7 — Divisão de trabalho nas próximas fases

Quem faz o pipeline corrigido? Quem faz a classificação? Quem escreve
o artigo?

**Impacto:** organização.

## Q8 — Features cruzadas entre etapas

No modelo de EM, usar features do fundamental como contexto? Ou
isolar completamente?

**Impacto:** define features finais.

## Q9 — Infraestrutura do Censo no modelo

As 18 variáveis do artigo da Gabriela (IIB, IDA, IDP, IEP) entram como
features ou só como caracterização?

**Impacto:** mais features = mais risco de overfitting.

## Q10 — Métricas de classificação

Qual limiar define "alto risco"? 5%, 10%, percentil 80?

**Impacto:** afeta Precision@K e Recall@K.