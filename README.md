# Dados-do-Projeto

Risco de abandono escolar em Roraima (PIBIC/UERR + disciplina de mineração de dados).
Esta pasta é a raiz do repositório e reúne três frentes: o pipeline oficial do projeto
(`abandono-escolar/`), a extensão da série histórica e das features do Censo
(`gustavo/`) e a documentação de planejamento (`Relatórios do Projeto/`).

- Regras de trabalho do projeto: [`abandono-escolar/CLAUDE.md`](abandono-escolar/CLAUDE.md)
- Instalação e bootstrap do pipeline oficial: [`abandono-escolar/README.md`](abandono-escolar/README.md)
- Pipeline estendido (2007–2025): [`gustavo/README.md`](gustavo/README.md) e [`gustavo/COMO_RODAR.md`](gustavo/COMO_RODAR.md)

## Arquitetura de pastas

Mapa conferido contra os arquivos em 2026-11-04 (`gustavo/docs/relatorio_06_organizacao_estrutura.md`).

```
Dados-do-Projeto/                      raiz do repositório
├── README.md                          este arquivo
├── VISAO_GERAL_DO_PROJETO.md          visão geral para decisões futuras
├── requirements.txt                   ambiente comum (inclui o do abandono-escolar; fixa scikit-learn 1.8.0)
├── .gitignore                         cache do Python e de ferramentas
├── Artigos/                           referências em PDF (ex.: Almeida & Mussato, 2023)
├── Relatórios do Projeto/             planejamento (00_LEIA_PRIMEIRO … 07_PLANOS), anterior à avaliação
│                                      de 2026-11-02; o que foi superado está na síntese, §4
│
├── abandono-escolar/                  pipeline oficial (repositório git próprio; ver Notas)
│   ├── CLAUDE.md                      fonte de verdade: contexto, dados e regras invioláveis
│   ├── README.md                      pré-requisitos, bootstrap, fontes e limitações
│   ├── requirements.txt · pytest.ini  dependências e configuração de testes
│   ├── src/                           módulos Python (python -m src.<módulo>)
│   │   ├── config.py · leitura.py     caminhos, constantes e leitura de CSV/planilhas
│   │   ├── aquisicao.py · fontes_inep.csv · certificados/   download do INEP e verificação TLS
│   │   ├── extrair_brutos_inep.py     extrai os .xlsx dos zips de indicadores
│   │   ├── integridade.py · manifesto.py                    sha256 e MANIFEST.csv
│   │   ├── indicadores_inep.py        detecção de cabeçalho e inventário das planilhas
│   │   ├── indicadores_rr.py          recorte de Roraima (um parquet por indicador e ano)
│   │   ├── base_longitudinal.py       regera a base escola-ano e compara com a v1.0
│   │   ├── analise_base_longitudinal.py · tabelas_metodologia.py   tabelas descritivas
│   │   ├── catalogo_microdados.py · relatorio_catalogo.py · relatorio_catalogo.html
│   │   ├── filtros.py                 funil de recorte da base oficial → docs/funil_contagem.csv
│   │   ├── figuras.py                 padrão das figuras dos notebooks (matplotlib)
│   │   ├── bootstrap.py               orquestra todas as etapas
│   │   └── migracao_estrutura.py      migração única para a estrutura de dados por estágio
│   ├── dados/                         fora do git, exceto MANIFEST.csv
│   │   ├── MANIFEST.csv               estágio, origem, arquivo e sha256 de cada arquivo
│   │   ├── origem/                    zips do INEP como vieram (somente leitura)
│   │   │   ├── censo/                 microdados do Censo Escolar 2019–2025
│   │   │   ├── indicadores/           indicadores educacionais (tx_rend, TDI, ATU, IED, HAD)
│   │   │   └── doc/                   PDFs de documentação
│   │   ├── bruto/                     extraído dos zips, nome original (somente leitura)
│   │   ├── interim/indicadores_rr/    recorte de RR em parquet ({tipo}_{ano}.parquet)
│   │   ├── processado/                base longitudinal regerada (.parquet + .csv)
│   │   ├── externo/                   base v1.0 do orientador (somente leitura)
│   │   └── cache_download/            downloads em andamento, páginas do INEP, certificado
│   ├── docs/                          tabelas geradas por código, método, decisões, síntese
│   │   ├── DECISOES.md · metodologia_variaveis.md · SINTESE_DO_PROJETO.md
│   │   ├── problemas.csv              mantido à mão pela pesquisadora
│   │   ├── *.csv                      inventários, catálogo, desfechos, funil (gerados por código)
│   │   └── figuras/                   figuras dos notebooks (PNG + PDF)
│   ├── notebooks/                     01_leitura_e_recorte · 02_descritivo (lê gustavo/) · 03 a fazer
│   └── tests/                         pytest: sem rede, sem tocar em dados/; fixtures
│
├── gustavo/                           pipeline estendido (2007–2025) e instrumento de avaliação
│   ├── README.md                      visão geral, estado atual, validações e pendências
│   ├── COMO_RODAR.md                  ordem de execução, ambiente, flags e testes
│   ├── programas/                     construção da base, na ordem de execução
│   │   ├── 01_tx_rend_bruto.py                    zips do INEP → parquet bruto (RR, 3 gerações de layout)
│   │   ├── 02_tx_rend_selecionado_longitudinal.py bruto → 12 taxas harmonizadas → LAG1/DELTA1/T1
│   │   ├── 03_censo_features.py                   18 itens de infraestrutura (Almeida & Mussato, 2023)
│   │   ├── 04_merge_features.py                   longitudinal + Censo (ANO + CO_ENTIDADE)
│   │   ├── 05_indices_infra.py                    4 dimensões + IIE, ano a ano → base_atual.parquet
│   │   ├── 99_pipeline.py                         roda 01 → 05 (--force, --from)
│   │   └── diagnostico/                           scripts pontuais, fora do pipeline
│   ├── analises/                      fora do pipeline: 01–02 método dos índices; 03 associações
│   │                                  descritivas; 04 funil e 05 descritivos (números dos notebooks)
│   ├── avaliacao/                     protocolo de avaliação
│   │   ├── baselines.py · bootstrap.py · metricas.py · painel.py · walkforward.py   funções
│   │   ├── 01_baselines.py            Etapa 1: B0, B1 e B1R, transições 2008→2009 a 2024→2025
│   │   ├── 02_walkforward.py · 02b_robustez.py · 02c_poder.py · 02d_tdi_separado.py   Etapa 2
│   │   └── sintese_numeros.py         números de referência da síntese
│   ├── testes/                        01 base · 02 índices · 03 Censo pós-04 · 04 avaliação ·
│   │                                  05 associações · 06 descritivos
│   ├── cache/                         recorte de RR por ano: tx_rend/ e censo/ ({ano}.parquet);
│   │                                  NÃO APAGAR — 2007–2018 só existe aqui (os zips não estão nesta máquina)
│   ├── docs/                          relatórios técnicos 01–06
│   └── saida/
│       ├── README.md                  descrição de cada arquivo
│       ├── base_atual.parquet         base consumida pela avaliação (cópia da etapa 05; 12.597 × 55)
│       ├── etapas/                    01 · 02a · 02b · 03 · 04 · 05
│       ├── relatorios/                diagnósticos do pipeline, saídas das análises, resultados dos testes
│       ├── avaliacao/                 resultados do protocolo de avaliação (CSV + MD)
│       ├── figuras/                   figuras do notebook 02 do abandono-escolar (PNG 300 dpi + PDF)
│       └── _backup_2026-10-14/        estado anterior ao relatório 04; ainda é entrada do teste 03
│                                      e da análise 01 (por isso fica aqui)
│
└── old/                               material antigo, mantido só como histórico
    ├── v1.ipynb · v1_corrigido.ipynb  notebooks de análise anteriores
    ├── diagnosticos_plano.py · diagnosticos_saida/
    ├── testes/                        notebooks e scripts de teste descartados
    └── pipeline_ate_2026-10-09/       gustavo/ antes da reorganização de 09/10/2026
                                       (programas/, saida/, testes/); até 2026-11-04 se chamava old/old/
```

## Fluxo dos dados

```
Pipeline oficial (abandono-escolar/)
  origem/ (zips) → bruto/ (planilhas) → interim/ (recorte RR) → processado/ (base 2019–2025)
                                                               → docs/ (tabelas, funil) → notebooks/

Pipeline estendido (gustavo/)
  zips tx_rend (origem/indicadores) ou cache/tx_rend ──▶ 01 ─▶ 02 ─┐
                                                                   ├─▶ 04 ─▶ 05 ─▶ saida/base_atual.parquet
  Censo (bruto/censo, origem/censo) ou cache/censo ────▶ 03 ───────┘                       │
                                                                                          ▼
                                avaliacao/ (01 baselines; 02–02d walk-forward) ─▶ saida/avaliacao/
```

## Notas

- **`origem/`, `bruto/` e `externo/` são somente leitura** (regra 1 do CLAUDE.md). O `gustavo/`
  lê de `abandono-escolar/dados/` e escreve só dentro de `gustavo/`; não altera o pipeline oficial.
- **Como o `gustavo/` acha os dados:** os scripts sobem a árvore de pastas procurando
  `abandono-escolar/dados/`; podem ser rodados de qualquer pasta, mas o jeito canônico é
  `cd gustavo && python programas/99_pipeline.py`.
- **Dependências e ambiente:** `requirements.txt` desta raiz (inclui o
  `abandono-escolar/requirements.txt` e fixa scikit-learn, xlrd e dependências). O `gustavo/`
  roda no `.venv` do `abandono-escolar`, nunca no Python global (`gustavo/COMO_RODAR.md`).
- **Dois repositórios git:** a raiz (`GustavoGGI/Dados-do-Projeto`) e `abandono-escolar/`
  (`gabsma25/abandono-escolar`) têm `.git` próprio. A raiz guarda só o commit de referência do
  `abandono-escolar` (gitlink, sem `.gitmodules`): um clone da raiz traz a pasta vazia, e o
  `abandono-escolar` precisa ser clonado à parte, lado a lado com `gustavo/`. Nesta máquina,
  `abandono-escolar/` é uma junção para o clone oficial.
- **Dados não vão para o git:** `abandono-escolar/dados/` fica fora do versionamento (exceto
  `MANIFEST.csv`); os zips são obtidos pelo bootstrap ou colocados em `dados/origem/` manualmente.
  O `gustavo/cache/` é versionado de propósito: é a única cópia de 2007–2018 nesta máquina.
- **`Relatórios do Projeto/` não foi atualizado depois de 2026-11-02.** Afirmações dele que foram
  refutadas ou superadas estão em `abandono-escolar/docs/SINTESE_DO_PROJETO.md`, §4.
