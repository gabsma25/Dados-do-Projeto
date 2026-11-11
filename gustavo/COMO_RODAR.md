# Como rodar o pipeline

Tudo é rodado da pasta `gustavo/`. Os scripts funcionam de qualquer CWD
(auto-discovery de pasta), mas rodar daqui é o "jeito canônico".

## Ambiente (desde 2026-11-03)

O `gustavo/` roda no **mesmo `.venv` do `abandono-escolar`, nunca no Python
global**. Dependências em `Dados-do-Projeto/requirements.txt`, que inclui o
`requirements.txt` do pipeline oficial e fixa o que só o `gustavo/` usa
(scikit-learn, xlrd e dependências):

```bash
..\abandono-escolar\.venv\Scripts\python.exe -m pip install -r ..\requirements.txt
..\abandono-escolar\.venv\Scripts\python.exe programas/99_pipeline.py
```

Nos comandos abaixo, `python` significa esse interpretador.

**scikit-learn fixado em 1.8.0** (decisão da pesquisadora, 2026-11-03). Os
resultados registrados até 2026-11-03 vieram do Python global (numpy 2.1.1,
pandas 3.0.3, pyarrow 24.0.0, scikit-learn 1.8.0). Com o scikit-learn 1.9.1 que
estava no `.venv`, o Random Forest da P026 (`analises/03`, bloco C) mudava até
0,0036 e o `testes/05_validar_associacoes.py` acusava 2 faixas (TDI 0,25–0,34 e
rendimento 0,17–0,21 contra 0,25–0,35 e 0,17–0,20 registradas).

Verificação no `.venv` com o scikit-learn 1.8.0 (numpy 2.5.3, pandas 3.0.5,
pyarrow 25.0.1), contra as saídas do Python global:

- avaliação (`02`, `02b`, `02c`, `02d`): saídas idênticas byte a byte;
- `testes/04`: 65 OK, 0 falhas; `testes/05`: 30 OK, 0 falhas (36 desde que passou a
  conferir também a decomposição, rodado de novo no `.venv`);
- `analises/03`: diferença máxima de 3e-16;
- bases do pipeline (verificadas antes, com o scikit-learn 1.9.1; o pipeline não
  usa scikit-learn): conteúdo idêntico, só os metadados do Parquet mudam.

As saídas versionadas são as do Python global.

---

## Pipeline completo (reconstruir tudo)

```bash
python programas/99_pipeline.py
```

Roda os 5 scripts em ordem:

1. `01_tx_rend_bruto.py`                    → `etapas/01_tx_rend_bruto.parquet`
2. `02_tx_rend_selecionado_longitudinal.py` → `etapas/02a_*.parquet` e `etapas/02b_*.parquet`
3. `03_censo_features.py`                   → `etapas/03_censo_features.parquet`
4. `04_merge_features.py`                   → `etapas/04_base_com_censo.parquet`
5. `05_indices_infra.py`                    → `etapas/05_base_com_indices.parquet` + `base_atual.parquet`

**Tempo:** ~17 s com cache quente. ~10 min do zero (primeira vez, ou após
apagar cache).

**Flags:**

```bash
# Ignorar todo o cache (reprocessa dos zips originais)
python programas/99_pipeline.py --force
# (o 03 passou a gravar também {ano}_nacional.json no cache; cache antigo sem
#  o .json é reprocessado automaticamente)

# Começar de uma etapa específica (útil quando 01 e 02 já estão ok)
python programas/99_pipeline.py --from 03

# Combinar
python programas/99_pipeline.py --force --from 03
```

---

## Rodar uma etapa só

### Etapas 01 e 03 (aceitam `--force`)

```bash
# 01 — reprocessa dos zips (ignora cache dos anos)
python programas/01_tx_rend_bruto.py --force

# 01 — só um ano específico (reprocessa só aquele, útil para debug)
python programas/01_tx_rend_bruto.py --force-year 2010

# 03 — reprocessa dos zips do Censo (ignora cache dos anos)
python programas/03_censo_features.py --force
```

### Etapas 02, 04 e 05 (não aceitam flag)

```bash
# 02 — lê cache quente de 01, sempre regenera 02a e 02b (rápido: ~3 s)
python programas/02_tx_rend_selecionado_longitudinal.py

# 04 — lê 02b + 03, sempre regenera o 04 (rápido: ~2 s)
python programas/04_merge_features.py

# 05 — lê o 04, gera as 4 dimensões z + IIE + marcador e atualiza base_atual (rápido: ~3 s)
python programas/05_indices_infra.py

# 05 — opcional: acrescenta também DIM_*_prop e IIE_prop (fora do padrão)
python programas/05_indices_infra.py --com-prop
```

**Por que 02 e 04 não têm `--force`:**

- **02** — só trabalha em cima do cache, que já é o produto final do 01.
  Não existe "versão antiga" do 02 para descartar; regenerar é sempre barato.
- **04** e **05** — só fazem merge/contas; não têm cache próprio. Se 02b ou 03
  estiverem desatualizados, refletem isso. Para forçar, refaça 02b e/ou 03 antes.

**Quando o 02 não acha o cache do 01:** ele para com erro claro
("cache não encontrado"). Rode o 01 antes.

---

## Testes

```bash
# Integridade da base, todos os estágios (45 checks)
python testes/01_validar_base.py

# Índices (05): recalcula tudo de forma independente e testa vazamento (41 checks; 44 com --com-prop)
python testes/02_validar_indices.py

# Auditoria do parquet PÓS-04: tipos, ausências, zeros estruturais, recomputo
# da regra, comparação com o CSV original do INEP, antes x depois (35 checks com --completo)
python testes/03_validar_censo_pos04.py          # --sem-bruto pula a leitura do CSV do INEP
python testes/03_validar_censo_pos04.py --completo # confere também os zips 2007-2018 (mais lento)
```

Saídas em `saida/relatorios/validacao_base.txt`, `validacao_indices.txt` e `validacao_pos04.txt`. Se algum check falhar,
o relatório aponta qual.

```bash
# Avaliação e associações (65 e 36 checks)
python testes/04_validar_avaliacao.py
python testes/05_validar_associacoes.py      # depois de analises/03

# Números dos notebooks: funil, desfecho por ano, cobertura do painel, Etapa 1 sem 2025 (82 checks)
python analises/04_funil_recorte.py
python analises/05_descritivo_por_ano.py
python testes/06_validar_descritivos.py      # depois de 01_baselines e sintese_numeros
```

Saídas em `validacao_avaliacao.txt`, `validacao_associacoes.txt` e `validacao_descritivos.txt`.

```bash
# Rendimento 2019–2025 da base_atual contra a base oficial, célula por célula (25 checks)
python testes/07_validar_sobreposicao.py      # depois do 05_indices_infra; saída em validacao_sobreposicao.txt
```

---

## Análises de decisão (não são testes)

```bash
# Como tratar IDA/IDP/IIE em 2007-2011 (lê saida/base_atual.parquet, ~10 s)
python analises/02_preenchimento_2007_2011.py

# Escolha do método de normalização (HISTÓRICA: lê o instantâneo de 3 métodos em
# saida/_backup_2026-10-14/05_base_com_indices_3metodos.parquet, ~15 s)
python analises/01_escolha_metodo_infra.py
```

Saídas: `saida/relatorios/preenchimento_2007_2011.txt`, `escolha_metodo_infra.txt` e
`escolha_metodo_infra_metricas.csv`. Nenhuma usa o desfecho como critério (regra 3).

---

## Scripts de diagnóstico (não entram no pipeline)

Ficam em `programas/diagnostico/`. Não são chamados pelo 99_pipeline.

```bash
# Ver quais colunas do Censo existem em RR por ano
python programas/diagnostico/explorar_colunas_censo.py

# Filtrar por ano ou por padrão de coluna
python programas/diagnostico/explorar_colunas_censo.py --anos 2019 2020
python programas/diagnostico/explorar_colunas_censo.py --buscar AGUA BIBLIOTECA

# Inspecionar o conteúdo bruto dos zips antigos do INEP (para debug de layout)
python programas/diagnostico/inspecionar_zips_antigos.py
```

---

## Limpar cache

Cache é só otimização. Apagar é seguro:

```bash
Remove-Item cache\tx_rend\* -Force
Remove-Item cache\censo\* -Force
```

Depois de apagar, a próxima execução reprocessa os zips (~10 min).

---

## Dependências

- `pandas`, `pyarrow` (parquets)
- `openpyxl` (xlsx do INEP)
- `xlrd` (xls antigos de 2007–2011)
- `numpy`

Já estão no ambiente. Se algum der ImportError, avise antes de instalar
(fora da política do CLAUDE.md).