# Visão geral do projeto — Risco de abandono escolar em Roraima

Documento de referência para entender o projeto e apoiar decisões futuras.
Reúne objetivo, decisões, inventário de dados, o que o pipeline faz, resultados
até agora e o que está em aberto.

- **Data de referência:** 02/11/2026
- **Fontes deste resumo:** `Relatórios do Projeto/00–07`, `abandono-escolar/CLAUDE.md`,
  `gustavo/README.md`, `gustavo/docs/relatorio_01..05` e inspeção direta das pastas de dados.
- Os detalhes ficam nos documentos de origem. Este arquivo é o mapa. Quando houver
  conflito, valem os documentos de origem e o código.

---

## 1. O projeto em uma página

| | |
|---|---|
| **Título** | Risco de abandono escolar em Roraima |
| **Tipo** | PIBIC/UERR (Edital 35/2026) + artigo da disciplina de Mineração de Dados |
| **Orientador** | Prof. Bruno Cesar Barreto Figueiredo (UERR) |
| **Grupo** | Gustavo, Gabriela Monteiro, João Ricardo |
| **Unidade de análise** | escola-ano (nunca o aluno) |
| **Alvo** | taxa de **abandono** do ano seguinte (`t+1`), nos **anos finais do fundamental** e no **ensino médio** |
| **Uso pretendido** | priorizar escolas para diagnóstico e apoio. **Nunca ranquear nem punir** |

**Pergunta de pesquisa**

> Com os indicadores educacionais de uma escola de Roraima no ano `t`, é possível
> estimar a taxa de abandono esperada no ano `t+1`, nos anos finais do ensino
> fundamental e no ensino médio, para apoiar ações preventivas de gestão?

**O que o projeto não faz**

- não prevê alunos individuais;
- não trata de **evasão** (aluno que não volta no ano seguinte), só de **abandono**
  (aluno que deixa de frequentar durante o ano);
- não é causal: dizer que "a variável X ajuda a prever" não equivale a dizer que "X causa abandono".

---

## 2. Estrutura do repositório

```
Dados-do-Projeto/                  raiz (git: GustavoGGI/Dados-do-Projeto)
├── VISAO_GERAL_DO_PROJETO.md      este arquivo
├── README.md                      arquitetura de pastas e fluxo
├── Relatórios do Projeto/         planejamento: 00_LEIA_PRIMEIRO … 07_PLANOS
├── Artigos/                       Almeida & Mussato (2023), base das 18 variáveis de infraestrutura
├── abandono-escolar/              pipeline OFICIAL (git próprio: gabsma25/abandono-escolar)
│   ├── CLAUDE.md                  fonte de verdade: regras invioláveis, dados, decisões
│   ├── src/                       download do INEP, extração, recorte RR, base 2019–2025
│   └── dados/                     ~5,6 GB, fora do git (exceto MANIFEST.csv)
├── gustavo/                       pipeline ESTENDIDO: 2007–2025 + infraestrutura do Censo
│   ├── programas/01…05, 99        scripts de produção
│   ├── testes/01…03               validações automáticas
│   ├── cache/                     recorte RR por ano (tx_rend e Censo), versionado no git
│   └── saida/base_atual.parquet   base consumida pelo modelo
└── old/                           material antigo (notebooks v1), só histórico
```

**Duas bases convivem hoje.** É importante não confundi-las:

| | Base oficial | Base estendida |
|---|---|---|
| Arquivo | `abandono-escolar/dados/processado/base_longitudinal_rr_2019_2025.parquet` | `gustavo/saida/base_atual.parquet` |
| Período | 2019–2025 (7 anos) | **2007–2025 (19 anos)** |
| Dimensão | 6.054 × 59 | 12.597 × 55 |
| Rendimento (aprovação/reprovação/abandono) | sim | sim |
| TDI, ATU, IED | **sim** | **não** |
| 18 variáveis de infraestrutura + índices | não | **sim** |
| Chaves e alvo | `ANO` + `CO_ENTIDADE`; `ABANDONO_*_T1` | iguais |

As duas usam as mesmas chaves e o mesmo alvo, então podem ser unidas por merge
(ver §8, decisão D-A).

---

## 3. Decisões já tomadas

### 3.1 Desenho e método (de `06_DECISOES_PROBLEMAS_PERGUNTAS.md`)

| # | Decisão |
|---|---|
| D1–D2 | Fonte do alvo: `tx_rend` do INEP diretamente. A Base dos Dados foi descartada, porque não tem `tx_rend`. |
| D3–D4 | A base v1.0 do orientador é referência. O código `src/base_longitudinal.py` a reproduz. |
| D5 | Dois modelos separados: **anos finais (AF)** e **ensino médio (EM)**. |
| D6 | Alvo = abandono de `t+1` (sufixo `_T1`). |
| D7 | INSE só para comparar grupos, **não como feature**. |
| D8–D9 | Pé-de-Meia entra como período pré/pós-2024, com cuidado de vazamento. |
| D10 | Manter todas as escolas na base e filtrar só na hora de treinar (`elegivel_analise`). |
| D11 | Escola indígena e localização diferenciada: incluir. |
| D12 | Escolas multisseriadas: usar a média do fundamental, com flag. |
| D13 | IED 2019–2020 e HAD: incluir **se** a metodologia do INEP for consistente. Ainda não decidido (P019). |
| D14 | Variáveis categóricas com One-Hot (não target encoding). |
| D15 | Cada modelo só vê as features da sua etapa. |
| D16 | Corrigir os 4 problemas do notebook v1 **antes** de tentar melhorar o resultado. |

**Dois cenários de uso** (de `abandono-escolar/CLAUDE.md`):

- **Cenário A, pós-fechamento:** usa o rendimento do ano `t`. Serve para previsão.
- **Cenário B, alerta antecipado:** exclui aprovação, reprovação e abandono de `t`.
  Usa TDI, ATU, IED e as taxas de `t−1`. Fica mais perto de explicar o abandono.

### 3.2 Decisões do pipeline estendido (`gustavo/`, relatórios 01–05)

- **Série estendida para 2007–2025.** O INEP publica `tx_rend` por escola desde 2007,
  em 3 gerações de layout (`.xls` em 2007–2011, `tap_/tre_/tab_` em 2012–2020,
  `1_CAT_/2_CAT_/3_CAT_` em 2021–2025). A harmonização é feita **pela posição da coluna,
  com uma trava no rótulo do cabeçalho**.
- **18 variáveis de infraestrutura** de Almeida & Mussato (2023, Quadro 3), em 4 dimensões:
  - IIB, infraestrutura básica: água, energia, coleta de lixo, banheiro;
  - IDA, dependências administrativas: despensa, refeitório, diretoria, sala dos professores, secretaria;
  - IDP, dependências pedagógicas: biblioteca, laboratório de informática, 2 pátios, quadra;
  - IEP, equipamentos: computador, impressora, projetor, internet.
- **Regra de fonte do Censo:** em cada ano, usa-se a primeira coluna **realmente coletada**
  (pelo menos uma escola do Brasil com valor 1). Se nenhuma foi coletada, o valor é `NaN`,
  **nunca 0**. Essa regra corrigiu um erro anterior: água, banheiro e projetor estavam
  zerados em 2019–2021, porque o INEP mantém no layout colunas cuja pergunta não foi feita.
- **Índices (14/10/2026, método final `zano`):** cada dimensão é a soma dos itens disponíveis
  no ano, padronizada (z-score) dentro do ano. O **IIE** é o primeiro componente principal
  (PC1) das 4 dimensões, com pesos calculados no próprio ano. Assim **nenhum dado futuro**
  entra no cálculo, o que o teste 02 comprova.
  - Descartados: `zref19`, que usa média e desvio de 2019 e por isso é dado futuro para
    anos anteriores, e `prop`, que traz a mesma informação em outra escala.
- **2007–2011:** o Censo não perguntava sobre 5 itens (despensa, refeitório, secretaria e os
  2 pátios). Nesses anos IDA usa 2 itens e IDP usa 3. É uma limitação registrada: a ordenação
  das escolas nessa versão parcial concorda 0,89–0,93 com a versão completa nas dimensões e
  0,99 no IIE (Spearman).
- `INFRA_FONTE_ARTIGO` e `INFRA_ITENS_COMPLETOS` são **marcadores de período, não features**.

### 3.3 Regras que valem sempre

- `origem/`, `bruto/` e `externo/` são **somente leitura**. O `gustavo/` só escreve dentro de `gustavo/`.
- Nenhuma escolha de método usa o desfecho (regra 3 do CLAUDE.md). Comparar desempenho
  preditivo entre métodos só dentro do walk-forward.
- Ausência estrutural (a escola não oferece a etapa ou o Censo não perguntava) é `NaN`, nunca 0.

---

## 4. Dados baixados hoje

Local: `abandono-escolar/dados/`, ~5,6 GB. O `MANIFEST.csv` registra o sha256 de cada
arquivo (336 entradas). Uma cópia idêntica está em `C:\Users\Gabriela\Pmonkey\abandono-escolar\dados`.

### 4.1 Indicadores educacionais do INEP (`origem/indicadores/`, 2,1 GB, 103 zips)

| Indicador | O que mede | Escola | Município | Brasil/UF |
|---|---|---|---|---|
| `tx_rend` | aprovação, reprovação, **abandono** | 2019–2025 | 2019–2025 | 2019–2024 (**falta 2025**) |
| `TDI` | distorção idade-série | 2019–2025 | 2019–2025 | 2019–2025 |
| `ATU` | média de alunos por turma | 2019–2025 | 2019–2024 (**falta 2025**) | 2019–2025 |
| `IED` | esforço docente (níveis 1–6) | 2019–2025 | 2019–2025 | 2019–2025 |
| `HAD` | horas-aula diárias | 2019–2025 | 2019–2025 | 2019–2025 |

Extraídos em `bruto/indicadores/` (1,3 GB) e recortados para RR em
`interim/indicadores_rr/`: `tx_rend`, `TDI` e `ATU` de 2019–2025, `IED` só de 2021–2025.
**O HAD e o IED de 2019–2020 estão baixados, mas não são processados** (P019, aguardando o orientador).

### 4.2 Censo Escolar (`origem/censo/` 675 MB + `bruto/censo/` 1,6 GB)

| Ano | Arquivo extraído | Conteúdo |
|---|---|---|
| 2019–2024 | `microdados_ed_basica_{ano}.csv` | tabela de **escolas** (Brasil inteiro, 1 linha por escola) |
| 2025 | `Tabela_Escola_2025_V2.csv`, `Tabela_Docente_…`, `Tabela_Matricula_…`, `Tabela_Turma_…` | escolas + docentes, matrículas e turmas |

### 4.3 Outros

- `externo/base_longitudinal_v1/`: base v1.0 do orientador (CSV, dicionário, logs, validação).
- `origem/doc/`: `Leia-me-2021.pdf`, `Nota-2021.pdf`.

### 4.4 O que existe só como recorte de RR (sem o dado bruto aqui)

Em `gustavo/cache/`, versionado no git:

- `tx_rend/{ano}.parquet` de **2007 a 2018**: recorte de RR das planilhas antigas;
- `censo/{ano}.parquet` + `{ano}_nacional.json` de **2007 a 2018**: colunas de infraestrutura
  de RR e a estatística nacional usada pela regra de fonte.

Os zips originais de 2007–2018 estavam na máquina do Gustavo, mas **não estão nesta pasta**.
Desde 02/11/2026, os scripts `01` e `03` usam o cache quando falta o zip do ano, e o `--force`
não apaga esses anos. Para reprocessar 2007–2018 do zero, é preciso baixar esses zips de novo (§5).

---

## 5. O que existe para baixar (INEP e outros)

| Fonte | Anos (aprox.) | Situação aqui | Uso possível | Observação |
|---|---|---|---|---|
| `tx_rend` escolas 2007–2018 | 2007–2018 | só o cache de RR | reprocessar do zero / auditoria | nomes antigos: `tx_rendimento_escolas_{ano}.zip` |
| Censo Escolar 2007–2018 | 2007–2018 | só o cache de RR | auditoria; **variáveis novas** (indígena, matrículas…) para anos antigos | o cache só tem as colunas de infraestrutura |
| TDI escolas < 2019 | série longa | não baixado | TDI na base 2007–2025 | nome antigo `tdi_escolas_{ano}.zip` |
| ATU escolas < 2019 | série longa | não baixado | idem | `media_alunos_turma_escolas_{ano}.zip` |
| HAD escolas < 2019 | série longa | não baixado | idem | `horas_aula_escolas_{ano}.zip` |
| IED escolas < 2019 | a partir de ~2013 (confirmar) | não baixado | idem | `esforco_docente_escolas_{ano}.zip` |
| AFD, adequação da formação docente | ~2013+ (confirmar) | **não baixado** | contexto docente | indicador educacional do INEP |
| ICG, complexidade de gestão; IRD, regularidade docente | ~2013–2014+ (confirmar) | não baixado | contexto da escola | idem |
| INSE, nível socioeconômico | 2019, 2021, 2023 | não baixado | **só comparação de grupos** (D7) | depende do Saeb, cobre cerca de metade das escolas |
| IDEB / Saeb | bienal | não baixado | contexto de desempenho | cobertura parcial |
| Pé-de-Meia | 2024+ | não baixado | flag pré/pós; beneficiários por escola, se houver | cuidado com vazamento (D9) |
| `ATU_2025_MUNICIPIOS`, `tx_rend_brasil_regioes_ufs_2025` | 2025 | faltam | completar o inventário | não usados no modelo |

As séries antigas de TDI, ATU, HAD e IED foram vistas nos zips do Gustavo (relatório 01).
As faixas exatas de anos marcadas "confirmar" **não foram verificadas no portal do INEP**.

---

## 6. O que o pipeline faz

### 6.1 Pipeline oficial (`abandono-escolar/`, 2019–2025)

```
origem/ (zips INEP) → bruto/ (planilhas) → interim/indicadores_rr/ (recorte RR) → processado/ (base 6.054 × 59)
```

Ele mesmo baixa os arquivos do INEP (verificando o certificado TLS e o sha256 do manifesto),
extrai, recorta RR e monta a base longitudinal com tx_rend, TDI, ATU, IED, lags, deltas e alvos.
Comando: `python -m src.bootstrap` (ver `abandono-escolar/README.md`).

### 6.2 Pipeline estendido (`gustavo/`, 2007–2025)

| Etapa | Script | Faz | Saída |
|---|---|---|---|
| 01 | `01_tx_rend_bruto.py` | lê os zips de tx_rend (3 layouts) e filtra RR | `01_tx_rend_bruto.parquet` (12.597 × 238) |
| 02 | `02_tx_rend_selecionado_longitudinal.py` | 12 taxas com nomes unificados + `_LAG1`, `_DELTA1`, `_T1` | `02a` (19 col.), `02b` (30 col.) |
| 03 | `03_censo_features.py` | 18 variáveis de infraestrutura com a regra de fonte | `03_censo_features.parquet` (16.449 × 21) |
| 04 | `04_merge_features.py` | `02b` + `03`, merge LEFT por `ANO + CO_ENTIDADE` | `04_base_com_censo.parquet` (12.597 × 49) |
| 05 | `05_indices_infra.py` | 4 dimensões `zano` + IIE (PC1 do ano) | `05_base_com_indices.parquet` = **`base_atual.parquet`** (12.597 × 55) |

```bash
cd gustavo
python programas/99_pipeline.py            # com cache (~10 s)
python programas/99_pipeline.py --force    # reprocessa os anos que têm dado bruto (~7 min)
python testes/01_validar_base.py           # 45 checks
python testes/02_validar_indices.py        # 41 checks (inclui teste de vazamento)
python testes/03_validar_censo_pos04.py --completo   # 35 checks contra o dado original
```

Dependências: `abandono-escolar/requirements.txt` + `xlrd`. No Windows, se a saída for
redirecionada, use `PYTHONUTF8=1` (os scripts imprimem "→").

**Última execução: 02/11/2026.** Com `--force`, os anos de 2019–2025 foram reprocessados a partir
dos dados brutos e os de 2007–2018 vieram do cache. A base saiu **idêntica, célula por célula**,
à versão de 14/10, e os três testes passaram sem falhas.

### 6.3 Colunas da `base_atual.parquet`

| Grupo | Colunas |
|---|---|
| Identificação | `ANO`, `ANO_ALVO`, `CO_ENTIDADE`, `NO_ENTIDADE`, `CO_MUNICIPIO`, `NO_MUNICIPIO`, `LOCALIZACAO`, `DEPENDENCIA`, `REDE_PUBLICA`, `DISP_REND` |
| Rendimento em `t` | `APROVACAO_*`, `REPROVACAO_*`, `ABANDONO_*` (FUN, FUN_AI, FUN_AF, MED) |
| Histórico | `ABANDONO_*_LAG1`, `ABANDONO_*_DELTA1` |
| **Alvos** | `ABANDONO_FUN_T1`, `ABANDONO_FUN_AF_T1`, `ABANDONO_MED_T1` |
| Infraestrutura | 18 itens `IIB_*`, `IDA_*`, `IDP_*`, `IEP_*` (0/1, `NaN` quando não coletado) |
| Índices | `DIM_IIB_zano`, `DIM_IDA_zano`, `DIM_IDP_zano`, `DIM_IEP_zano`, `IIE_zano` |
| Marcadores (não são features) | `INFRA_FONTE_ARTIGO`, `INFRA_ITENS_COMPLETOS` |

---

## 7. Números e conclusões atuais

### 7.1 Tamanho real das amostras

A base tem 12.597 escolas-ano (988 escolas distintas), mas **poucas têm o alvo de cada etapa**:

| | Escolas-ano com alvo | Por ano |
|---|---|---|
| Anos finais (`ABANDONO_FUN_AF_T1`) | **4.349** | ~220–256 |
| Ensino médio (`ABANDONO_MED_T1`) | **2.629** | ~100–181 |

2025 não tem alvo, porque o abandono de 2026 ainda não foi publicado. Com essas amostras pequenas,
**modelos simples e poucas features** são mais seguros.

### 7.2 Abandono médio por ano (% , média simples entre escolas)

| Ano | AF | EM | | Ano | AF | EM |
|---|---|---|---|---|---|---|
| 2007 | 7,4 | 12,8 | | 2017 | 4,6 | 8,6 |
| 2010 | 6,5 | 9,4 | | 2018 | 5,7 | 10,2 |
| 2013 | 5,4 | 9,8 | | 2019 | 5,2 | 10,1 |
| 2015 | 6,8 | 10,3 | | **2020** | **1,0** | **1,6** |
| 2016 | 5,4 | 8,2 | | 2021 | 3,0 | 5,5 |
| | | | | **2022** | **4,9** | **11,3** |
| | | | | 2023 | 3,0 | 7,2 |
| | | | | 2024 | 2,6 | 5,5 |
| | | | | 2025 | 2,4 | 5,9 |

- Tendência de queda de longo prazo.
- **2020 é uma anomalia**, ligada à pandemia (ano letivo remoto e atípico).
- **2022 é um pico** pós-pandemia: o abandono no EM dobrou em relação a 2021.
- A partir de 2024 começa o Pé-de-Meia no EM. Comparar EM com AF pode mostrar o efeito.
- Muitos zeros no alvo, na base 2019–2025: 44% das escolas no AF e 32% no EM.

### 7.3 Resultados de modelagem (base oficial 2019–2025)

| Experimento | Etapa | Resultado |
|---|---|---|
| v1_old (pipeline correto, split temporal) | AF | R² 0,162 no teste de 2025; **R² −0,078** na validação de 2024 |
| v1 atual (com 4 problemas conhecidos) | AF | RandomForest R² 0,184; GradientBoosting R² 0,201 |
| v1 atual | EM | RandomForest R² 0,121; GradientBoosting R² 0,091 |

**Demonstrado:**

- existe sinal preditivo;
- **TDI é a variável mais importante** em todos os modelos e etapas;
- o pipeline de dados funciona e é reprodutível (sha256 + testes).

**Ainda não demonstrado:**

- estabilidade entre anos (o R² negativo em 2024 indica que não generaliza bem);
- ganho sobre o **baseline de persistência** ("abandono de t+1 = abandono de t"), que nunca foi calculado;
- utilidade operacional (Recall@K);
- **o papel da infraestrutura.** As 18 variáveis e o IIE estão prontos, mas **nenhum modelo
  foi treinado com a `base_atual.parquet`**. Modelos treinados antes de 14/10 com água,
  banheiro ou projetor de 2019–2021 usaram dados errados.

---

## 8. Decisões pendentes

| # | Decisão | Opções | Impacto |
|---|---|---|---|
| D-A | **Unir as duas bases?** | (a) merge de TDI/ATU/IED da base oficial na `base_atual`, deixando 2007–2018 vazio; (b) baixar TDI/ATU antigos e processar 2007–2018; (c) manter separadas | (a) leva menos de 1 dia e não exige download; sem isso, a base estendida fica sem o melhor preditor |
| D-B | Período de treino | 2019–2025 (tem TDI/IED) ou 2007–2025 (mais dados, sem TDI) | define as features possíveis |
| Q4 | Pico de 2022 | incluir no treino / excluir / usar como teste | muda o split temporal |
| Q5 / P019 | IED 2019–2020 e HAD | incluir no modelo, só na análise, ou ficar fora | os arquivos já estão baixados |
| Q8 | Features do fundamental no modelo de EM | usar como contexto ou isolar (D15 diz isolar) | features finais |
| Q9 | Infraestrutura | 18 itens, 4 dimensões, só IIE ou nada | testar como blocos no walk-forward |
| — | Virada 2011→2012 da infraestrutura | aceitar dimensões parciais, usar só IIB/IEP em 2007–2011, ou núcleo fixo de 13 itens | relatório 05, §5 |
| Q10 | Limiar de "alto risco" | 5%, 10%, percentil 75/80 | Precision@K / Recall@K |
| Q3 | Critério de "bom o suficiente" | R², MAE, Recall@K | quando parar e escrever |
| Q2 | Base v1.0 do orientador | só referência ou oficial | adaptação do pipeline |
| Q6–Q7 | Prazos e divisão de trabalho | — | ritmo |

---

## 9. Próximos passos sugeridos

Seguem a ordem de `07_PLANOS.md`, ajustada ao estado atual.

1. **Fase 2, pipeline de modelagem limpo:** filtrar `REDE_PUBLICA == 1`; imputação dentro do
   `Pipeline`; categóricas via `ColumnTransformer`; **baseline de persistência**;
   **walk-forward** ano a ano; decidir o pico de 2022.
2. **Decidir D-A.** Recomendação: fazer o merge de TDI/ATU/IED na `base_atual` (uma etapa `06`
   no `gustavo/` com um teste), para comparar na mesma base: rendimento × rendimento+TDI ×
   +infraestrutura.
3. **Testes por bloco de features** no walk-forward, nos cenários A e B: só rendimento; +TDI/ATU;
   +infraestrutura (itens, dimensões ou IIE). É aqui que se responde se a infraestrutura importa.
4. **Fase 3, enriquecimento:** escola indígena, terra indígena e assentamento (Censo); flag de
   elegibilidade; multisseriada; Pé-de-Meia; INSE só para avaliar por grupo.
5. **Fase 4:** classificação de alto risco com Recall@K e Precision@K, comparada ao baseline
   "ordenar pelo abandono em t".
6. **Fase 5:** refinamento, importância de variáveis (permutation e SHAP), artigo e relatório PIBIC.

---

## 10. Cuidados importantes

- **Vazamento:** nunca usar o alvo de uma etapa como feature da outra (`ABANDONO_FUN_T1` para
  prever `ABANDONO_MED_T1`); índices e normalizações só com dados do próprio ano ou de anos
  anteriores.
- **R² não é acurácia.** Com muitos zeros e outliers (RMSE > MAE), reportar sempre MAE, RMSE,
  baseline e Recall@K juntos.
- **Painel não balanceado:** escolas entram e saem, e algumas mudam de nome ou localização.
- **Defasagem:** o abandono de `t+1` só é publicado no ano seguinte. Em novembro/2026, o último
  alvo conhecido é o de 2025.
- **Ética:** dados públicos e agregados por escola. O resultado serve para apoio, não para ranking.

---

## 11. Histórico curto

| Data | Marco |
|---|---|
| 15/09/2026 | download dos dados de 2019–2025 (MANIFEST) |
| 17/09/2026 | base v1.0 entregue pelo orientador |
| 30/09/2026 | ritmo avaliado como "ótimo" pelo orientador |
| após 30/09/2026 | zips de IED 2019–2020 e HAD 2019–2024 entram em `origem/` (P019) |
| 01/10/2026 | bootstrap completo do pipeline oficial (110 zips, ~3h52) |
| out/2026 | experimentos v1_old e v1 atual; análise crítica do orientador (12 pontos) |
| out/2026 | `gustavo/` estende tx_rend para 2007–2025 (relatórios 01–03) |
| 14/10/2026 | correção do erro de coleta do Censo; 18 variáveis e índices `zano` fechados (relatórios 04–05) |
| 02/11/2026 | dados copiados para `Dados-do-Projeto/abandono-escolar/`; `01`/`03` passam a usar o cache em anos sem dado bruto; pipeline reprocessado e base idêntica confirmada |
