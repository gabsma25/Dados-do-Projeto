# -*- coding: utf-8 -*-
"""
Gera as tabelas que os notebooks desta pasta exibem e que ainda não existiam em
CSV (regra 9 do abandono-escolar/CLAUDE.md: todo número publicado é gerado por
código). Os notebooks só leem, filtram e desenham: não calculam.

Só lê. Entradas:
  abandono-escolar/dados/processado/base_longitudinal_rr_2019_2025.parquet
  abandono-escolar/dados/MANIFEST.csv            (+ tamanho dos arquivos em disco)
  abandono-escolar/docs/dicionario_anotado.csv, problemas.csv,
                        comparacao_base_v1.csv, DECISOES.md
  gustavo/saida/base_atual.parquet
  gustavo/saida/avaliacao/02d_testes.csv
  gustavo/saida/relatorios/validacao_*.txt
  Contexto do Projeto/registros/*.csv            (classificação escrita à mão, linha a linha, cada uma
                                                  com a fonte; revisar antes de citar. O código só conta
                                                  e confere que o estado está no vocabulário de cada registro)

Saída: Contexto do Projeto/tabelas/*.csv (lista no fim da execução).
Uso (da pasta Dados-do-Projeto):
  abandono-escolar\\.venv\\Scripts\\python.exe "Contexto do Projeto\\gerar_tabelas.py"
"""
import re
import sys
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
DADOS_DO_PROJETO = AQUI.parent
OFICIAL = DADOS_DO_PROJETO / "abandono-escolar"
GUSTAVO = DADOS_DO_PROJETO / "gustavo"
SAIDA = AQUI / "tabelas"

P_BASE = OFICIAL / "dados" / "processado" / "base_longitudinal_rr_2019_2025.parquet"
P_ATUAL = GUSTAVO / "saida" / "base_atual.parquet"
P_MANIFESTO = OFICIAL / "dados" / "MANIFEST.csv"
DOCS = OFICIAL / "docs"
P_TESTES_02D = GUSTAVO / "saida" / "avaliacao" / "02d_testes.csv"
RELATORIOS = GUSTAVO / "saida" / "relatorios"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ENTRADAS = [P_BASE, P_ATUAL, P_MANIFESTO, DOCS / "dicionario_anotado.csv", DOCS / "problemas.csv",
            DOCS / "comparacao_base_v1.csv", DOCS / "DECISOES.md", P_TESTES_02D]
faltam = [str(p) for p in ENTRADAS if not p.exists()]
if faltam:
    raise SystemExit("[ERRO] faltam entradas:\n  " + "\n  ".join(faltam))

SAIDA.mkdir(exist_ok=True)
gravados = []


def gravar(df, nome):
    caminho = SAIDA / nome
    df.to_csv(caminho, index=False, encoding="utf-8", lineterminator="\n")
    gravados.append((nome, len(df)))


RENDIMENTO = ("APROVACAO_", "REPROVACAO_", "ABANDONO_")
DERIVADAS = ("_LAG1", "_DELTA1", "_T1")
base = pd.read_parquet(P_BASE)
atual = pd.read_parquet(P_ATUAL)

# ------------------------------------------------------------------ universo
# Composição da base oficial por ano: quem está no universo (união das chaves das
# quatro planilhas de indicadores) e quanto dele tem cada fonte.
taxas = [c for c in base.columns if c.startswith(RENDIMENTO) and not c.endswith(DERIVADAS)]
disp = ["DISP_REND", "DISP_TDI", "DISP_ATU", "DISP_IED"]
b = base.assign(
    publica=base["REDE_PUBLICA"].astype("Int8") == 1,
    com_rendimento=base[taxas].notna().any(axis=1),
    sem_valor=(base[disp].astype("Int8") == 0).all(axis=1),
)
universo = (b.groupby("ANO")
            .agg(linhas=("CO_ENTIDADE", "size"),
                 escolas=("CO_ENTIDADE", "nunique"),
                 publicas=("publica", "sum"),
                 com_rendimento=("com_rendimento", "sum"),
                 publicas_com_rendimento=("publica", lambda s: int((s & b.loc[s.index, "com_rendimento"]).sum())),
                 sem_valor_nas_colunas_mantidas=("sem_valor", "sum"),
                 **{f"com_{d.split('_')[1]}": (d, lambda s: int((s.astype("Int8") == 1).sum())) for d in disp})
            .reset_index())
universo["privadas"] = universo["linhas"] - universo["publicas"]
universo["publicas_sem_rendimento"] = universo["publicas"] - universo["publicas_com_rendimento"]
total = {"ANO": "total", "linhas": len(b), "escolas": b["CO_ENTIDADE"].nunique()}
total.update({c: int(universo[c].sum()) for c in universo.columns if c not in total})
universo = pd.concat([universo.astype({"ANO": "string"}), pd.DataFrame([total])], ignore_index=True)
gravar(universo, "universo_por_ano.csv")

composicao = (b.groupby(["ANO", "DEPENDENCIA", "LOCALIZACAO"], observed=True).size()
              .rename("linhas").reset_index())
gravar(composicao, "universo_rede_localizacao.csv")

# ------------------------------------------------------------------ colunas
def grupo(coluna):
    regras = [("TDI_", "TDI"), ("ATU_", "ATU"), ("IED_", "IED"), ("DISP_", "disponibilidade (DISP_*)"),
              ("APROVACAO_", "rendimento"), ("REPROVACAO_", "rendimento"), ("ABANDONO_", "rendimento"),
              ("IIB_", "infraestrutura: itens"), ("IDA_", "infraestrutura: itens"),
              ("IDP_", "infraestrutura: itens"), ("IEP_", "infraestrutura: itens"),
              ("DIM_", "infraestrutura: índices"), ("IIE_", "infraestrutura: índices"),
              ("INFRA_", "infraestrutura: marcadores")]
    for prefixo, nome in regras:
        if coluna.startswith(prefixo):
            return nome
    return "identificação e contexto"


todas = sorted(set(base.columns) | set(atual.columns))
colunas = pd.DataFrame({"coluna": todas})
colunas["grupo"] = colunas["coluna"].map(grupo)
colunas["na_base_oficial"] = colunas["coluna"].isin(base.columns)
colunas["na_base_atual"] = colunas["coluna"].isin(atual.columns)
colunas["onde"] = colunas.apply(
    lambda r: "nas duas" if r.na_base_oficial and r.na_base_atual
    else ("só na oficial" if r.na_base_oficial else "só na base_atual (gustavo)"), axis=1)
gravar(colunas, "colunas_das_bases.csv")
gravar(colunas.groupby(["grupo", "onde"]).size().rename("colunas").reset_index(), "colunas_por_grupo.csv")

bases = pd.DataFrame([
    {"base": "oficial (abandono-escolar)", "linhas": len(base), "colunas": base.shape[1],
     "ano_min": int(base["ANO"].min()), "ano_max": int(base["ANO"].max()),
     "escolas": base["CO_ENTIDADE"].nunique()},
    {"base": "base_atual (gustavo)", "linhas": len(atual), "colunas": atual.shape[1],
     "ano_min": int(atual["ANO"].min()), "ano_max": int(atual["ANO"].max()),
     "escolas": atual["CO_ENTIDADE"].nunique()},
])
gravar(bases, "bases_dimensoes.csv")

# ------------------------------------------------------------------ manifesto
man = pd.read_csv(P_MANIFESTO, dtype=str)
man["bytes"] = [(OFICIAL / "dados" / a).stat().st_size if (OFICIAL / "dados" / a).exists() else pd.NA
                for a in man["arquivo"]]
man["no_disco"] = man["bytes"].notna()
man["bytes"] = man["bytes"].astype("Int64")
por_estagio = (man.groupby(["estagio", "origem"])
               .agg(arquivos=("arquivo", "size"), no_disco=("no_disco", "sum"),
                    bytes=("bytes", lambda s: s.sum(min_count=1)))
               .reset_index())
por_estagio["gb"] = (por_estagio["bytes"].astype("Float64") / 1e9).round(3)
gravar(por_estagio, "manifesto_por_estagio.csv")

# ------------------------------------------------------------------ papéis e problemas
dic = pd.read_csv(DOCS / "dicionario_anotado.csv", dtype=str, keep_default_na=False)
gravar(dic.groupby(["papel", "status"]).size().rename("variaveis").reset_index(), "papeis_variaveis.csv")

prob = pd.read_csv(DOCS / "problemas.csv", dtype=str, keep_default_na=False)
gravar(prob.groupby(["tipo", "status"]).size().rename("problemas").reset_index(), "problemas_por_tipo.csv")

comp = pd.read_csv(DOCS / "comparacao_base_v1.csv")
gravar(comp.groupby("classificacao").agg(colunas=("coluna", "size"),
                                         maior_diferenca=("max_diferenca_abs", "max")).reset_index(),
       "comparacao_v1_resumo.csv")

# ------------------------------------------------------------------ testes com correção (02d)
t = pd.read_csv(P_TESTES_02D)
t = t[t["primario"]]
familias = (t.groupby(["familia", "etapa"])
            .agg(testes=("rejeita_holm", "size"), sobrevivem=("rejeita_holm", "sum"),
                 ic_exclui_zero_sem_correcao=("ic_exclui_zero", "sum"))
            .reset_index())
gravar(familias, "familias_holm.csv")

# ------------------------------------------------------------------ checks dos testes
linhas = []
for txt in sorted(RELATORIOS.glob("validacao_*.txt")):
    conteudo = txt.read_text(encoding="utf-8")
    m = re.search(r"RESUMO:\s*(\d+)\s*OK,\s*(\d+)\s*falhas", conteudo)
    if m:
        ok, falhas = int(m.group(1)), int(m.group(2))
    else:
        mo = re.search(r"OK:\s*(\d+)", conteudo)
        mf = re.search(r"Falhas:\s*(\d+)", conteudo)
        if not (mo and mf):
            continue                       # relatório sem contagem de checks (ex.: validacao_longitudinal)
        ok, falhas = int(mo.group(1)), int(mf.group(1))
    linhas.append({"relatorio": txt.name, "ok": ok, "falhas": falhas})
gravar(pd.DataFrame(linhas), "checks_gustavo.csv")

# ------------------------------------------------------------------ linha do tempo das decisões
def categoria(data, titulo):
    if re.match(r"D\d+ ", titulo):
        return "desenho (orientador, 17/09)"
    if data >= "2026-11-02":
        return "avaliação e objetivo"
    return "dados e procedência"


entradas = re.findall(r"^## (\d{4}-\d{2}-\d{2}) — (.+)$", (DOCS / "DECISOES.md").read_text(encoding="utf-8"),
                      flags=re.M)
tempo = pd.DataFrame(entradas, columns=["data", "titulo"])
tempo["categoria"] = [categoria(d, ti) for d, ti in zip(tempo["data"], tempo["titulo"])]
tempo["substituida"] = tempo["titulo"].str.contains("SUBSTITUÍDA", regex=False)
gravar(tempo, "linha_do_tempo_decisoes.csv")

# ------------------------------------------------------------------ registros (escritos à mão, com fonte)
# Os estados de cada registro têm vocabulário fechado: um estado fora dele para a execução, para que um
# erro de digitação não vire uma categoria nova numa figura.
REGISTROS = AQUI / "registros"
VOCABULARIO = {
    "decisoes_doc06.csv": ("estado", None, {"vigente", "feito", "substituída", "aguarda decisão", "não implementada"}),
    "perguntas_doc06.csv": ("estado", None, {"respondida", "em parte", "aberta"}),
    "plano_outubro.csv": ("estado", "fase", {"feito", "feito de outra forma", "feito em parte", "aguarda decisão",
                                             "não feito"}),
    "estrategia_orientador.csv": ("estado", None, {"feito", "feito em parte", "não feito"}),
    "criterios_fase1.csv": ("estado", None, {"feito", "feito em parte", "não feito"}),
    "plano_avancado.csv": ("estado", None, {"adotada", "coincide", "em parte", "não decidida", "não adotada"}),
    "matriz_experimentos.csv": ("estado", None, {"feito", "feito (nulo)", "feito de outra forma", "feito em parte",
                                                 "não rodado"}),
    "referencias.csv": ("estado", "grupo", {"citada nos documentos", "sugerida", "indireta", "a conferir"}),
    "problemas_fora_do_csv.csv": ("estado", None, {"aberto", "em parte", "resolvido", "informativo"}),
    "experimentos_historico.csv": ("avaliou_modelo_2024_2025", None, {"sim", "não", "em parte", "não (só baselines)"}),
}
faltam = [n for n in VOCABULARIO if not (REGISTROS / n).exists()]
if faltam:
    raise SystemExit("[ERRO] faltam registros em " + str(REGISTROS) + ": " + ", ".join(faltam))
registro = {n: pd.read_csv(REGISTROS / n, dtype=str, keep_default_na=False) for n in VOCABULARIO}
fora = [(n, v) for n, (col, _, ok) in VOCABULARIO.items() for v in set(registro[n][col]) - ok]
fora += [("experimentos_historico.csv", v) for v in set(registro["experimentos_historico.csv"]["olhou_desfecho_2025"])
         - {"sim", "não"}]
if fora:
    raise SystemExit("[ERRO] estado fora do vocabulário: " + "; ".join(f"{n}: '{v}'" for n, v in fora))

resumos = []
for nome, (col, grupo, _) in VOCABULARIO.items():
    r = registro[nome]
    chaves = ([grupo] if grupo else []) + [col]
    c = r.groupby(chaves, sort=False).size().rename("n").reset_index()
    c = c.rename(columns={col: "estado", **({grupo: "grupo"} if grupo else {})})
    if not grupo:
        c["grupo"] = ""
    c.insert(0, "registro", nome.removesuffix(".csv"))
    resumos.append(c[["registro", "grupo", "estado", "n"]])
gravar(pd.concat(resumos, ignore_index=True), "registros_resumo.csv")

refs = registro["referencias.csv"]
gravar(refs.groupby(["grupo", "parte"], sort=False).size().rename("referencias").reset_index(),
       "referencias_por_parte.csv")

# Problemas: a planilha oficial (mantida à mão pela pesquisadora) mais as linhas propostas e os M do doc 06
oficiais = prob[["id", "tipo", "objeto_afetado", "status"]].rename(columns={"objeto_afetado": "objeto",
                                                                             "status": "estado"})
oficiais["na_planilha"] = "sim"
extras = registro["problemas_fora_do_csv.csv"][["id", "tipo", "objeto", "estado"]].copy()
extras["na_planilha"] = "não"
# Linha proposta para um id que já está na planilha (P006) é correção da linha, não problema novo:
# fica um só registro, com o estado da planilha e a correção anotada.
correcao = extras[extras["id"].isin(oficiais["id"])].set_index("id")["estado"]
oficiais["correcao_proposta"] = oficiais["id"].map(lambda i: f"estado proposto: {correcao[i]}" if i in correcao else "")
extras = extras[~extras["id"].isin(oficiais["id"])].assign(correcao_proposta="")
todos = pd.concat([oficiais, extras], ignore_index=True)
todos["serie"] = todos["id"].str[0]
todos["numero"] = todos["id"].str[1:].astype(int)
todos = todos.sort_values(["serie", "numero"], ascending=[False, True]).drop(columns="numero")
gravar(todos, "problemas_todos.csv")
gravar(todos.groupby(["serie", "na_planilha", "estado"]).size().rename("problemas").reset_index(),
       "problemas_resumo.csv")

print("Gravado em", SAIDA)
for nome, n in gravados:
    print(f"  {nome:34s} {n:4d} linhas")
