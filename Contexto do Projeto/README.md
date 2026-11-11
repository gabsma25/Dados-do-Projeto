# Contexto do Projeto

Esta pasta apresenta o projeto **Risco de abandono escolar em Roraima** em oito notebooks: o fluxo dos dados,
as figuras, os pilares (ferramentas e decisões), o histórico dos experimentos, as referências, as decisões e
os planos. Estado de referência: 10/11/2026.

Os notebooks atualizam os relatórios 00 a 07 de `../Relatórios do Projeto/`, escritos até 14/10/2026, com o que
foi decidido e descoberto depois. Os relatórios antigos não foram alterados e ficam como histórico.

| Arquivo | Substitui | Conteúdo |
|---|---|---|
| `00_leia_primeiro.ipynb` | `00_LEIA_PRIMEIRO.md` | fluxo dos dados, pilares, ferramentas, testes, linha do tempo das decisões, ordem de leitura |
| `01_projeto.ipynb` | `01_PROJETO.md` | pergunta (antes e agora), escopo, cobertura temporal, pessoas, estado atual, resultados, pendências, glossário |
| `02_dados.ipynb` | `02_DADOS.md` | fontes do INEP, manifesto e procedência, universo, papéis e ausência, comparação com a v1.0, base estendida, desfecho e persistência, enriquecimento |
| `03_metodologia.ipynb` | `03_METODOLOGIA.md` | painéis, Cenário B e blocos, regras, walk-forward, baselines, modelos, Recall@K, bootstrap e Holm |
| `04_experimentos.ipynb` | `04_EXPERIMENTOS.md` | o que já tocou a transição 2024→2025, os experimentos de outubro, a Etapa 2 ano a ano, o padrão temporal refutado, o TDI separável, as análises descritivas, a matriz E0–E9, os 13 itens refutados |
| `05_referencias.ipynb` | `05_REFERENCIAS.md` | Almeida & Mussato (2023) anotado, proposta do orientador, fontes de dados, método, contexto (a conferir) |
| `06_decisoes_problemas_perguntas.ipynb` | `06_DECISOES_PROBLEMAS_PERGUNTAS.md` | as três numerações "D", decisões vigentes e revertidas, **divergências nos documentos oficiais**, decisões em aberto e quem decide, problemas, perguntas |
| `07_planos.ipynb` | `07_PLANOS.md` | plano de outubro, estratégia do orientador, critérios da fase 1, Plano avançado de 07/10, caminhos que dependem de decisão |
| `gerar_tabelas.py` | — | gera `tabelas/*.csv`: as contagens que os notebooks exibem e que ainda não existiam em CSV |
| `desenho.py` | — | caixas, setas e grades de estado dos diagramas |
| `registros/` | — | **classificação escrita à mão** (estado de cada decisão, pergunta, experimento, passo de plano e referência), uma linha por item, cada uma com a fonte |
| `tabelas/` | — | CSVs gerados por `gerar_tabelas.py` |
| `figuras/` | — | figuras desta pasta em PNG (300 dpi) e PDF, gravadas pelos notebooks |

## Regras que os notebooks seguem

- **Exibem, não calculam** (`abandono-escolar/CLAUDE.md` §4). Os números vêm de três lugares, todos gerados
  por código:
  - `abandono-escolar/docs/*.csv`;
  - `gustavo/saida/` (relatórios, avaliação e figuras);
  - `tabelas/`, gerada por `gerar_tabelas.py`.

  As células só leem, filtram e desenham.
- **Os registros são classificação, não medida.** `registros/*.csv` foi escrito à mão em 10/11/2026 a partir
  das fontes citadas em cada linha. O `gerar_tabelas.py` só conta e para se algum estado estiver fora do
  vocabulário do registro. Revise antes de citar.
- **Nível de evidência** da síntese no título de cada figura: FATO, MEDIDO, PONTUAL, EXPLORATÓRIO,
  INTERPRETAÇÃO ou REFUTADO.
- **Nenhum modelo é avaliado aqui.** A transição 2024→2025 continua bloqueada (D7). As figuras que usam o
  desfecho de 2025 já tabulado (persistência, decomposição) são marcadas como EXPLORATÓRIO.
- **Figuras de outros notebooks** (`abandono-escolar/notebooks/01–03`) são mostradas a partir dos PNGs que
  eles gravaram, sem recalcular.
- **Nenhum documento oficial foi alterado.** As divergências encontradas estão no notebook 06, §5, com a
  correção proposta, e a decisão é da pesquisadora (`CLAUDE.md` §6).

## Como rodar

Da pasta `Dados-do-Projeto`, com o `.venv` do `abandono-escolar` ativado. O kernel `python3` usa o `python`
do PATH, e cada notebook confere as versões contra o `requirements.txt`.

```bash
abandono-escolar\.venv\Scripts\activate
python "Contexto do Projeto/gerar_tabelas.py"
cd "Contexto do Projeto"
jupyter nbconvert --to notebook --execute --inplace 0*.ipynb
```

**O que precisa existir:**

- `Dados-do-Projeto/abandono-escolar` (junction para a cópia oficial), com `dados/processado/`,
  `dados/MANIFEST.csv` e `docs/`;
- `Dados-do-Projeto/gustavo/saida/`, com a `base_atual.parquet`, os relatórios, a avaliação e as figuras.

Nada aqui baixa dados, regrava base ou roda modelo.

## Para exportar (NotebookLM, orientador)

```bash
jupyter nbconvert --to html 0*.ipynb
```

Junto com os oito HTML, suba o `SINTESE_DO_PROJETO.md` e o `DECISOES.md` do `abandono-escolar`. Com espaço,
acrescente o `metodologia_variaveis.md` e o `CLAUDE.md`.
