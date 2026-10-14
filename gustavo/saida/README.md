# Saída do pipeline `gustavo/`

Cada arquivo aqui é uma etapa do pipeline de construção da base.
A ordem numérica reflete a sequência de execução.

Para reconstruir tudo: `python programas/99_pipeline.py --force`

---

## `base_atual.parquet`

**Cópia da última etapa pronta.** É o arquivo que o notebook de modelo
consome.

- Dimensões: 12.597 × 64
- Conteúdo: idêntico ao `etapas/05_base_com_indices.parquet`
- Como trocar a base do modelo: substitua este arquivo por qualquer
  `.parquet` de `etapas/` (a maioria dos scripts usa as mesmas chaves
  `ANO + CO_ENTIDADE`, então o merge continua funcionando)

**Quando ele é atualizado:** pelo `05_indices_infra.py` (última etapa).
Se você rodar as etapas individualmente, o `base_atual.parquet` não muda
até o `05` rodar de novo.

---

## Etapas (em `etapas/`)

### `01_tx_rend_bruto.parquet`
- **Dimensões:** 12.597 × 238
- **O que tem:** taxas de rendimento (aprovação, reprovação, abandono) para
  Roraima, 2007–2025, com as 3 gerações de layout do INEP empilhadas
  (2007–2011 `.xls`, 2012–2020 `tap_/tre_/tab_`, 2021–2025 `1_CAT_/2_CAT_/3_CAT_`).
- **Gerado por:** `01_tx_rend_bruto.py`
- **Uso:** auditoria. Não é consumido por modelos.

### `02a_tx_rend_selecionado.parquet`
- **Dimensões:** 12.597 × 19
- **O que tem:** 12 taxas (4 etapas × 3 tipos: FUN, FUN_AI, FUN_AF, MED) com
  nomes unificados + chaves (`ANO`, `CO_ENTIDADE`) + descrição (nome, município,
  localização, dependência).
- **Gerado por:** `02_tx_rend_selecionado_longitudinal.py`
- **Uso:** base mínima do modelo (só o alvo, sem features derivadas).

### `02b_tx_rend_longitudinal.parquet`
- **Dimensões:** 12.597 × 30
- **O que tem:** `02a` + `REDE_PUBLICA`, `DISP_REND` + `_LAG1` (valor do ano
  anterior), `_DELTA1` (variação anual) + `_T1` (valor do ano seguinte = alvo
  do modelo) + `ANO_ALVO`.
- **Gerado por:** `02_tx_rend_selecionado_longitudinal.py`
- **Uso:** base preditiva só com tx_rend. É a entrada do `04`.

### `03_censo_features.parquet`
- **Dimensões:** 16.449 × 21
- **O que tem:** as 18 variáveis de infraestrutura (Almeida & Mussato, 2023,
  Quadro 3) + `INFRA_FONTE_ARTIGO` + chaves (`ANO`, `CO_ENTIDADE`):
  - `IIB_*` (4): água potável, energia de rede, coleta de lixo, banheiro
  - `IDA_*` (5): despensa, refeitório, sala de diretoria, sala de professores, secretaria
  - `IDP_*` (5): biblioteca, lab. de informática, pátio coberto, pátio descoberto, quadra
  - `IEP_*` (4): computador, impressora, projetor, internet
- **Regra de fonte:** por ano, a primeira coluna realmente coletada (≥ 1 escola
  do Brasil com valor 1), começando pela do artigo; `NaN` se nenhuma foi
  coletada. Ver `relatorios/fontes_features_censo.csv` (variável × ano × coluna
  usada) e `relatorios/diagnostico_features_censo.txt`.
- `INFRA_FONTE_ARTIGO` = 1 nos anos em que as 18 vieram das colunas do artigo
  (2019–2025).
- **Gerado por:** `03_censo_features.py`
- **Uso:** enriquecimento. Não é consumido sozinho.

### `04_base_com_censo.parquet`
- **Dimensões:** 12.597 × 49
- **O que tem:** `02b` + as 18 variáveis + `INFRA_FONTE_ARTIGO` (merge `LEFT` por
  `ANO + CO_ENTIDADE`).
- **Gerado por:** `04_merge_features.py`
- **Uso:** modelo com `tx_rend` + infraestrutura (itens individuais).

### `05_base_com_indices.parquet`  (= `base_atual.parquet`)
- **Dimensões:** 12.597 × 55
- **O que tem:** `04` + 6 colunas derivadas, sem alterar nenhuma coluna do `04`:
  - `DIM_IIB_zano`, `DIM_IDA_zano`, `DIM_IDP_zano`, `DIM_IEP_zano` (`Float64`): soma
    dos itens **disponíveis no ano**, com z-score dentro de cada ano
  - `IIE_zano` (`Float64`): PC1 das 4 dimensões, pesos calculados no próprio ano
    (parâmetros e pesos por ano em `relatorios/indices_infra_parametros.json`)
  - `INFRA_ITENS_COMPLETOS` (`Int8`): 1 em 2012–2025 (as 4 dimensões com todos os
    itens do artigo), 0 em 2007–2011; marcador de período, não feature
- Cobertura de 100% das escolas em todos os anos. Em 2007–2011 IDA usa 2 itens e IDP
  3 itens (o Censo não coletava os outros 5); ver `docs/relatorio_05_...`, §5.
- `05_indices_infra.py --com-prop` acrescenta `DIM_*_prop` e `IIE_prop`.
- **Gerado por:** `05_indices_infra.py`
- **Uso:** base recomendada para o modelo. Na hora de treinar, escolha as colunas
  (18 itens, 4 dimensões de uma normalização, ou IIE).

---

## Por que o script `02` gera dois parquets (02a e 02b)

O script `02_tx_rend_selecionado_longitudinal.py` produz dois arquivos:

- **`02a`** — base limpa, sem features derivadas
- **`02b`** — `02a` + LAG1/DELTA1/T1 + ANO_ALVO

**Motivo de serem um só script:** a lógica de harmonização das 3 gerações de
layout do INEP (armadilha P009/P014) precisa ler o cache anual, aplicar a
trava com o rótulo humano do cabeçalho e só então montar o longitudinal.
Separar em dois scripts exigiria duplicar essa lógica ou gravar um parquet
intermediário que perderia a informação de posição — que é a única confiável
entre gerações.

**Uso prático:** se você quer só o alvo (sem lags), use `02a`. Se quer o
dataset preditivo, use `02b`.

---

## Relatórios (em `relatorios/`)

- `diagnostico_bruto.txt` — resumo do `01`: por ano, escolas únicas, colunas
- `validacao_longitudinal.txt` — validação do `02b` contra a base da Gabi (2019–2025)
- `diagnostico_features_censo.txt` — cobertura das 18 variáveis por ano e regra de fonte, no universo do Censo
- `fontes_features_censo.csv` — coluna do Censo usada por (variável, ano)
- `merge_features.txt` — cobertura do Censo no universo tx_rend (após o merge)
- `indices_infra.txt` e `indices_infra_parametros.json` — itens usados por ano, PCA por ano, cobertura
- `preenchimento_2007_2011.txt` — análise 02: custo de usar itens parciais em 2007–2011
- `escolha_metodo_infra.txt` e `_metricas.csv` — análise 01 (histórica): comparação de prop/zano/zref19
- `validacao_base.txt` — 45 checks de integridade da base
- `validacao_pos04.txt` — auditoria do parquet pós-04 (35 checks com `--completo` + tabelas de prevalência e ausência por ano)
- `validacao_indices.txt` — 41 checks dos índices (recálculo independente e teste de vazamento)

## Relatório de diagnóstico (na raiz de `saida/`)

- `relatorio_colunas_censo.csv` — inventário das colunas do Censo por ano,
  gerado pelo script `programas/diagnostico/explorar_colunas_censo.py`.
  Não faz parte do pipeline; é só material de investigação.

---

## Como reconstruir

```bash
# Reconstruir tudo (com cache quente: ~8 s)
python programas/99_pipeline.py

# Reconstruir tudo do zero (~10 min)
python programas/99_pipeline.py --force

# Só uma etapa (útil durante desenvolvimento)
python programas/04_merge_features.py

# Validar a base final
python testes/01_validar_base.py
python testes/02_validar_indices.py