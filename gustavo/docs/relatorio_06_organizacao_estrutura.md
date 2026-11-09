# Relatório técnico 06 — Organização da estrutura de arquivos

**Projeto:** Risco de abandono escolar em Roraima (PIBIC/UERR + Mineração de Dados)
**Autora:** Gabriela (gabsma25), com Claude Code
**Data:** 2026-11-04
**Escopo:** arrumar a estrutura do repositório `Dados-do-Projeto` sem mudar nenhum caminho que
código, testes ou registros citam; refazer os três mapas da estrutura para o estado real.
**Documentos anteriores:** `relatorio_03_reorganizacao.md` (reorganização de 09/10/2026, que este
relatório segue como modelo)

---

## 0. Sumário

Quatro alterações, nenhuma em `programas/`, `analises/`, `avaliacao/`, `testes/` ou `saida/`
(fora o `saida/README.md`):

1. `old/old/` passou a se chamar `old/pipeline_ate_2026-10-09/`.
2. `.gitignore` novo na raiz (cache do Python e de ferramentas).
3. Os três mapas da estrutura foram refeitos: `README.md` da raiz, `gustavo/README.md` e
   `gustavo/saida/README.md`.
4. Este registro.

A opção de dividir `saida/relatorios/` por tipo e separar as funções dos scripts em
`avaliacao/` foi considerada e descartada por ora (§3).

## 1. Motivação

Os mapas descreviam a estrutura de antes de 02/11/2026. Quem chegasse pelo `README.md` da raiz
não encontraria `analises/`, `avaliacao/`, `saida/avaliacao/`, o passo `05_indices_infra.py`, os
testes 02–06, os notebooks nem `src/filtros.py`/`src/figuras.py`. E leria duas instruções
erradas: que o `gustavo/cache/` é "apagável (regenera dos zips)" — 2007–2018 só existe ali — e que
a `base_atual` sai do passo 04 — sai do 05.

## 2. Alterações

| Arquivo | Antes | Depois | Por quê |
|---|---|---|---|
| `old/old/` (57 arquivos) | `old/old/` | `old/pipeline_ate_2026-10-09/` | pasta `old` dentro de `old`; o nome novo diz o que é: o `gustavo/` antes da reorganização de 09/10 (criada no commit `fd96bc4`, "nova organização"). Nenhum arquivo citava `old/old`. |
| `.gitignore` (raiz) | não existia | `__pycache__/`, `*.pyc`, `.ruff_cache/`, `.pytest_cache/` | o `git status` listava cache do Python como arquivo novo |
| `README.md` (raiz) | árvore de 09/10 | árvore e fluxo conferidos contra os arquivos; notas sobre o gitlink do `abandono-escolar`, o cache versionado e os `Relatórios do Projeto/` | ver §4 |
| `gustavo/README.md` | estrutura com testes 01–03 e análises 01–02 | estrutura com `avaliacao/`, testes 01–06 e análises 01–05; estado dos testes 04–06; nota de que o "próximo passo" foi feito em `avaliacao/` | idem |
| `gustavo/saida/README.md` | sem `saida/avaliacao/` nem os relatórios de 03/11 | seções para os relatórios novos, `saida/avaliacao/` e `_backup_2026-10-14/` | idem |

O renome foi feito com `mv`, não com `git mv`, para não alterar o índice, que tinha um arquivo
preparado pela pesquisadora (`old/testes/teste.ipynb`). No commit, `git add -A old/` registra o
renome (o git o detecta pelo conteúdo).

## 3. O que não mudou, de propósito

| Item | Por que ficou |
|---|---|
| `saida/relatorios/`, `saida/avaliacao/`, `saida/etapas/` | são citados como evidência: 29, 13 e 11 arquivos citam esses caminhos, nos dois repositórios (contados em 2026-11-04, já com os mapas novos), entre eles o `abandono-escolar/docs/DECISOES.md`, a síntese, a metodologia, o `CLAUDE.md` e os relatórios 04 e 05. Mover quebraria as citações de registros que não se reescrevem. |
| `saida/_backup_2026-10-14/` | não é só histórico: `testes/03_validar_censo_pos04.py` (seção I) e `analises/01_escolha_metodo_infra.py` leem arquivos dali. |
| Funções e scripts juntos em `avaliacao/` | os scripts importam as funções pelo caminho atual; separar exige mudar todos e rodar os testes de novo. |
| 5 arquivos `.pyc` rastreados (`programas/__pycache__/`, `programas/diagnostico/__pycache__/`) | ficaram como estavam, por instrução da pesquisadora. O `.gitignore` não os tira do git; tirar exige `git rm --cached`. |
| `Artigos/desktop.ini` | arquivo de sistema do Windows; pode definir o ícone da pasta. Sem decisão, fica. |
| Conteúdo de `Relatórios do Projeto/` | é documento de planejamento de outro momento; o README da raiz agora avisa que não foi atualizado depois de 2026-11-02 e aponta a síntese, §4. |

## 4. Correções encontradas ao refazer os mapas

- **`README.md` da raiz:** a raiz se chamava "Projeto da Gabi/"; o passo 03 dava "17 features"
  (são 18); `04 → base_atual` (é o 05); só o teste 01 e os relatórios 01–03; `exploracao_colunas/`,
  que não existe no `abandono-escolar`; a nota "Caminhos em transição" (`src/abandono-escolar/…`),
  já resolvida — nenhum arquivo do `abandono-escolar` cita mais esse caminho.
- **`gustavo/README.md`:** "2012–2018: água e banheiro usam colunas substitutas" — são 2007–2018,
  e a biblioteca (2007–2008) e o projetor (2007–2011) também usam substitutas
  (`saida/relatorios/diagnostico_features_censo.txt`); "análises… não usam o alvo" — vale para
  01–02, não para 03–05.
- **`gustavo/saida/README.md`:** `base_atual` com "12.597 × 64" — são 55 colunas (o próprio README
  dizia 55 mais abaixo); `relatorio_colunas_censo.csv` "na raiz de `saida/`" — não está lá; há uma
  versão anterior em `old/pipeline_ate_2026-10-09/saida/`.

## 5. Verificação

- Antes do renome: nenhum arquivo do repositório nem do `abandono-escolar` citava `old/old`.
- Depois: os 57 arquivos estão em `old/pipeline_ate_2026-10-09/`; o índice do git não mudou.
- Todo caminho citado entre crases nos três README existe. Os que um verificador automático não
  achou são fragmentos (`.py`, `_metricas.csv`), nomes de repositório, caminhos relativos a
  outra pasta (conferidos um a um) ou ausências declaradas no texto (`relatorio_colunas_censo.csv`,
  `programas/06_modelo.py`, que nunca foi criado).
- Nenhum script, teste ou saída foi alterado; por isso os testes não foram rodados de novo.

## 6. Pendências (decisão da pesquisadora ou do Gustavo)

1. Tirar do git os 5 `.pyc` rastreados (`git rm --cached`).
2. `Artigos/desktop.ini`: manter ou tirar do git.
3. Dividir `saida/relatorios/` por tipo (pipeline, análises, validação): custo medido no §3.
4. Este repositório é do Gustavo e a pesquisadora não tem permissão de envio; estas alterações,
   como os commits locais anteriores, ficam nesta máquina até isso se resolver.
