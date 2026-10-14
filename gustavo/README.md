# `gustavo/` — extensão de tx_rend (2007–2025) + infraestrutura do Censo

Pipeline paralelo ao `src/` do projeto principal. Constrói uma base
estendida para Roraima que:

- estende a série de tx_rend de 7 para **19 anos** (2007–2025)
- adiciona as **18 variáveis de infraestrutura** do Censo Escolar
  (Almeida & Mussato, 2023, Quadro 3)
- deriva **4 dimensões + 1 índice (IIE)** pelo método do artigo aplicado **ano a ano**
  (`zano`), mantendo as 18 originais na base (18 → 4 → 1: na hora do modelo basta
  escolher quais colunas usar)

**Não modifica nada em `src/` nem em `dados/`** — todo o output fica em
`gustavo/saida/`.

## Como usar

- Para rodar o pipeline: veja `COMO_RODAR.md`
- Para entender os parquets de saída: veja `saida/README.md`
- Para entender o que cada script faz: docstring no topo de cada `.py`
- Histórico de decisões e correções: `docs/relatorio_01..05` (o 05 é o fechamento das 18 variáveis, 14/10/2026)

## Estrutura

- `programas/` — scripts de produção (`01_` a `05_`, + `99_pipeline.py`)
- `programas/diagnostico/` — scripts pontuais (não entram no pipeline)
- `testes/` — `01_validar_base.py` (integridade, todos os estágios), `02_validar_indices.py` (05: índices) e `03_validar_censo_pos04.py` (auditoria do parquet pós-04)
- `analises/` — análises de decisão (não validam o pipeline, não usam o alvo): `01_escolha_metodo_infra.py` (histórica: comparou prop/zano/zref19; lê o instantâneo de 3 métodos em `saida/_backup_2026-10-14/`) e `02_preenchimento_2007_2011.py` (como tratar IDA/IDP/IIE em 2007–2011)
- `cache/` — cache por ano, apagável (regenera dos zips em ~10 min)
- `docs/` — relatórios longos em markdown
- `saida/` — parquets e relatórios finais (ver `saida/README.md`)
- `saida/_backup_2026-10-14/` — cópia parcial dos arquivos antes da correção do relatório 04 (scripts 03/04/99, teste 01, `base_atual.parquet` antigo = 04 antigo; o README raiz antigo não foi preservado) e o instantâneo do 05 com 3 normalizações (`*_3metodos.*`)

## Pipeline em 5 etapas

| Etapa | Script | Lê de | Escreve em |
|---|---|---|---|
| 01 | `01_tx_rend_bruto.py` | zips INEP (`dados/origem/indicadores/`) | `etapas/01_tx_rend_bruto.parquet` (12.597 × 238) |
| 02 | `02_tx_rend_selecionado_longitudinal.py` | cache `tx_rend/` + `01` | `etapas/02a_*.parquet` (19 col) + `etapas/02b_*.parquet` (30 col) |
| 03 | `03_censo_features.py` | zips Censo (`dados/bruto/censo/`, `dados/origem/censo/`) | `etapas/03_censo_features.parquet` (16.449 × 21) + `relatorios/fontes_features_censo.csv` |
| 04 | `04_merge_features.py` | `02b` + `03` | `etapas/04_base_com_censo.parquet` (12.597 × 49) |
| 05 | `05_indices_infra.py` | `04` | `etapas/05_base_com_indices.parquet` (12.597 × 55) + `base_atual.parquet` |

O `99_pipeline.py` roda os 5 em ordem, com `--force` e `--from`.

## Estado atual

Última execução completa: **14/10/2026**. `01_validar_base.py`: **45 checks / 0
falhas**; `02_validar_indices.py`: **41 / 0**; `03_validar_censo_pos04.py --completo`: **35 / 0**.

- **`saida/base_atual.parquet`** — 12.597 × 55, cópia do `05`:
  30 colunas do tx_rend longitudinal + 18 variáveis do Censo (`Int8`) + `INFRA_FONTE_ARTIGO`
  + 5 colunas derivadas (`Float64`: `DIM_{IIB,IDA,IDP,IEP}_zano` e `IIE_zano`)
  + `INFRA_ITENS_COMPLETOS` (`Int8`).

### Como o Censo é lido (regra de fonte — relatório 04)

O INEP mantém colunas no layout mesmo quando a pergunta não foi feita (valor 0
para todas as escolas). Por isso cada variável usa, em cada ano, a **primeira
coluna realmente coletada** (≥ 1 escola do Brasil com valor 1), começando pela
coluna do artigo. Se nenhuma foi coletada, o valor é `NaN`, nunca 0.

- 2019–2025: as 18 vêm das colunas do artigo (`INFRA_FONTE_ARTIGO = 1`).
- 2012–2018: água e banheiro usam colunas substitutas (`IN_AGUA_FILTRADA`,
  `IN_BANHEIRO_DENTRO_PREDIO`), pergunta diferente da do artigo.
- 2007–2011: despensa, refeitório, secretaria e os dois pátios não foram
  coletados no Brasil (`NaN`). IDA e IDP usam, nesses anos, só os itens que existem
  (2 e 3 itens); ver "Índices" abaixo.

### Índices de infraestrutura (18 → 4 → 1) — método final, relatório 05

| Nível | Colunas | Observação |
|---|---|---|
| nenhum | — | só tx_rend |
| 18 itens | `IIB_*`, `IDA_*`, `IDP_*`, `IEP_*` | binárias; 5 delas só de 2012 em diante |
| 4 dimensões | `DIM_{IIB,IDA,IDP,IEP}_zano` | soma dos itens do ano, z-score dentro do ano |
| 1 índice | `IIE_zano` | PC1 das 4 dimensões, pesos calculados no próprio ano |

- **Sem dado futuro:** cada ano usa só os dados do próprio ano (o teste 02 prova isso
  executando o 05 em dados perturbados).
- **Cobertura:** as 4 dimensões e o IIE existem para 100% das escolas nos 19 anos.
- **Limitação 2007–2011:** IDA usa 2 itens e IDP 3 itens (o Censo não perguntava os
  outros); IIB e IEP usam todos os itens em todos os anos. Medido em 2012+, a versão
  parcial concorda com a completa em Spearman ~0,89–0,93 (IDA/IDP) e ~0,99 (IIE); há
  queda de persistência na virada 2011→2012 (relatório 05, §5).
- `INFRA_ITENS_COMPLETOS` (0 em 2007–2011, 1 depois) e `INFRA_FONTE_ARTIGO` marcam o
  regime do período: servem para filtrar e auditar, **não como feature**.
- `prop` e `zref19` foram descartados (relatório 05, §3). `05_indices_infra.py --com-prop`
  acrescenta `DIM_*_prop` e `IIE_prop` se algum teste exigir.

## Pendências documentadas

- **Recorte de referência de 2019 (só para reproduzir a Tabela 1 do artigo):** 152 escolas (artigo: 165). Não afeta mais a base. Diferença =
  escolas fora da base de rendimento; reproduzir a Tabela 1 do artigo exigiria
  extrair as colunas de filtro e a de escola indígena do Censo 2019.
- **IDA, IDP e IIE de 2007–2011 são aproximações** (menos itens); decisão e custo medido no relatório 05, §5.
- **D8 (4 colunas: indígena, localização diferenciada, matrículas AF/EM) e
  TDI/ATU/IED** continuam não construídos — decisão do orientador.
- ~~Normalização padrão~~: decidida em 14/10/2026 (`zano`, ano a ano; relatório 05).
- `programas/diagnostico/*.py`: caminhos corrigidos em 14/10 (verificados por import; os scripts não foram reexecutados).
- ~~`out of memory` em 2010~~: o `03` agora processa os anos em sequência.

## Próximo passo proposto

**Modelo A/B/C…** — as variáveis de infraestrutura melhoram a previsão de
abandono? Mesmo walk-forward, mesmos modelos, mesmos folds; variar só o bloco de
features (tabela acima). Implementação sugerida: `programas/06_modelo.py` ou
notebook lendo `saida/base_atual.parquet`.
