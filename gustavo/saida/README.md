# Saída do pipeline `gustavo/`

Cada arquivo aqui é uma etapa do pipeline de construção da base.
A ordem numérica reflete a sequência de execução.

Para reconstruir tudo: `python programas/99_pipeline.py --force`

---

## `base_atual.parquet`

**Cópia da última etapa pronta.** É o arquivo que o instrumento de avaliação
(`avaliacao/`) consome.

- Dimensões: 12.597 × 55
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
- `associacoes_descritivas.csv` — análise 03: associações descritivas registradas, reproduzidas por script
- `validacao_associacoes.txt` — teste 05: análise 03 contra os números registrados (36 checks)
- `funil_recorte.csv` — análise 04: funil de recorte da base avaliada, por ano e etapa
- `desfecho_por_ano.csv` e `cobertura_painel.csv` — análise 05: série do desfecho e cobertura dos
  indicadores no painel, por ano (números exibidos pelos notebooks do `abandono-escolar`)
- `validacao_descritivos.txt` — teste 06: análises 04–05 contra os números registrados (82 checks)
- `validacao_avaliacao.txt` — teste 04: instrumento de avaliação (65 checks)
- `validacao_sobreposicao.txt` — teste 07: rendimento 2019–2025 contra a base oficial (25 checks)
- `validacao_classificacao.txt` — teste 08: ferramenta de classificação de alto risco (65 checks)
- `verificacao_classificacao.txt` — verificação do treino da classificação (`avaliacao/03b_verificacao_classificacao.py`)
- `tempos_execucao.txt` — tempos de execução de 2026-11-02, cronometrados à mão (sem script)

## Resultados da avaliação (em `avaliacao/`)

Gerados pelos scripts de `gustavo/avaliacao/`; o prefixo do arquivo é o do script.
Classificação de alto risco (10/11/2026): `03_classificacao.csv` (métricas), `03_previsoes.csv` (uma linha por escola-ano de teste × nota), `03_testes.csv` (família F6 com Holm), `03_classificacao.md` (resumo) e `03b_controle_permutacao.csv` (sorteios da verificação).

- `01_baselines.csv` e `.md` — Etapa 1: B0, B1 e B1R por transição (`01_baselines.py`)
- `02_*` — Etapa 2: walk-forward, decisões por bloco e importância (`02_walkforward.py`)
- `02b_*` — robustez: células por ano, diferenças, decisões, padrão temporal (`02b_robustez.py`)
- `02c_*` — poder: largura dos intervalos, diferenças e importância agrupadas (`02c_poder.py`)
- `02d_testes.csv` e `02d_tdi_separado.md` — 228 linhas: os 152 testes primários (K de 10% e
  20%, correção de Holm por família) e 76 de K = 30%, fora da correção (`02d_tdi_separado.py`)
- `sintese_numeros.csv` — números de referência da síntese do projeto (`sintese_numeros.py`)

## Figuras (em `figuras/`)

Gravadas pelos notebooks `abandono-escolar/notebooks/02_descritivo.ipynb`, `03_avaliacao.ipynb` e `04_predicao.ipynb` (figuras `04_*`)
(PNG 300 dpi e PDF, com `src/figuras.py`); nenhuma calcula nada, todas exibem os CSV de `relatorios/`
e `avaliacao/`. Regenerar: executar o notebook (ver o README do `abandono-escolar`, limitações).

- `02_funil_base_avaliada_2023.*` — funil de recorte da base avaliada em t = 2023 (`funil_recorte.csv`)
- `02_desfecho_por_ano.*` — média, mediana e % de zeros do abandono, 2007–2025 (`desfecho_por_ano.csv`)
- `02_cobertura_painel.*` — escolas-ano do painel da Etapa 2 com cada grupo de preditores (`cobertura_painel.csv`)
- `03_etapa1_baselines.*` — Etapa 1: B1R − acaso e MAE B1 − MAE B0, alvos de 2009 a 2024 (`01_baselines.csv`)
- `03_resolucao_recall10.*` — Recall@10% com IC 95% dos modelos do Cenário B, por ano e agrupado (`02c_largura.csv`)
- `03_modelo_menos_baseline.*` — modelo − B1R_lag (F5) e modelo − B2 (F4), com Holm (`02d_testes.csv`)
- `03_importancia_grupos.*` — importância por grupo no bloco 4 (F1), com Holm (`02d_testes.csv`)

## Instantâneo anterior (em `_backup_2026-10-14/`)

Estado anterior à correção do relatório 04 e o 05 com 3 normalizações. Não é só histórico:
`testes/03_validar_censo_pos04.py` (seção I, antes × depois) e `analises/01_escolha_metodo_infra.py`
leem arquivos daqui. Mover a pasta exige mudar esses dois scripts.

## Relatório de diagnóstico (fora do pipeline)

- `relatorio_colunas_censo.csv` — inventário das colunas do Censo por ano, gerado em
  `saida/` pelo script `programas/diagnostico/explorar_colunas_censo.py`. Não faz parte do
  pipeline e não está no repositório hoje; uma versão anterior está em
  `old/pipeline_ate_2026-10-09/saida/` (na raiz do repositório).

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