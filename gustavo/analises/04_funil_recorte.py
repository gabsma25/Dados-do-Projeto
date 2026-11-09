# -*- coding: utf-8 -*-
"""
ANÁLISE 04 — Funil de recorte da base avaliada, com contagem por ano e etapa.
[FATO]: só contagem; o desfecho não é critério de nada.

A base avaliada é a base_atual (tx_rend de escolas de RR, 2007–2025), espinha
da Etapa 1 e do painel da Etapa 2. Ela NÃO é a base oficial do abandono-escolar
(6.054 linhas em 2019–2025, união de todos os indicadores): a base_atual tem
só as escolas com linha no tx_rend (4.733 linhas em 2019–2025).

Degraus (coluna `ordem`):
  1 Brasil ......... linhas da planilha tx_rend de escolas do ano, lidas de
                     abandono-escolar/docs/inventario_indicadores.csv
                     (n_linhas_dados). Só 2019–2025: os zips de 2007–2018 não
                     estão nesta máquina (verificado em 2026-11-03; SINTESE
                     §5.2), então nesses anos o funil começa em RR.
  2 RR ............. linhas da base_atual no ano (todas as redes)
  3 públicas ....... REDE_PUBLICA == 1
  4 com a etapa em t ............... públicas com taxa de abandono da etapa
  5 com a etapa em t e alvo em t+1 . encaixado no 4
  6 com alvo em t+1, sem a etapa em t (o `n_sem_t` da Etapa 1)
  7 universo da avaliação = 5 + 6 .. públicas com alvo em t+1
                                     (baselines.universo); NÃO é encaixado
                                     no 5
  8 painel da Etapa 2 .............. o universo, só ANO 2019–2024
                                     (painel.montar)

Os degraus 1–3 não dependem da etapa e se repetem em AF e EM. Ausência
estrutural fica vazia (nunca 0), com o motivo em `observacao`: Brasil em
2007–2018, alvo em t+1 no último ano (t+1 ainda não publicado), painel fora
de 2019–2024.

`tipo`, com o mesmo vocabulário do abandono-escolar/docs/funil_contagem.csv
(o notebook 02 desenha cada degrau por ele): "funil" para os degraus
encaixados (1–5 e 8, que é o 7 restrito a 2019–2024), "fora do funil" para o
6 (nunca somado a outro degrau) e "total" para o 7 (= 5 + 6).

Saída: gustavo/saida/relatorios/funil_recorte.csv
       (ano, etapa, ordem, degrau, tipo, n, fonte, observacao)
Uso:   python analises/04_funil_recorte.py
"""
import sys
from pathlib import Path

import pandas as pd

GUSTAVO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GUSTAVO / "avaliacao"))
import baselines as B  # noqa: E402
import painel as P  # noqa: E402

P_INV = GUSTAVO.parent / "abandono-escolar" / "docs" / "inventario_indicadores.csv"
SAIDA = GUSTAVO / "saida" / "relatorios" / "funil_recorte.csv"
F_ATUAL = "gustavo/saida/base_atual.parquet"
F_INV = "abandono-escolar/docs/inventario_indicadores.csv"
TIPO = {6: "fora do funil", 7: "total"}   # os demais degraus: "funil"


def brasil_por_ano():
    inv = pd.read_csv(P_INV)
    inv = inv[(inv["tipo"] == "tx_rend") & (inv["nivel"] == "escolas")]
    assert inv["ano"].is_unique, "inventário com mais de uma planilha tx_rend de escolas no mesmo ano"
    return dict(zip(inv["ano"].astype(int), inv["n_linhas_dados"].astype(int)))


def funil(atual, brasil):
    anos = sorted(atual["ANO"].astype(int).unique())
    ultimo = anos[-1]
    pub = atual["REDE_PUBLICA"].astype("Int8") == 1
    linhas = []

    def reg(ano, etapa, ordem, degrau, n, fonte, obs=""):
        linhas.append({"ano": ano, "etapa": etapa, "ordem": ordem, "degrau": degrau,
                       "tipo": TIPO.get(ordem, "funil"), "n": n, "fonte": fonte, "observacao": obs})

    for etapa, col in B.ETAPAS.items():
        u = B.universo(atual, etapa)
        painel = P.montar(etapa, atual)
        for ano in anos:
            a = (atual["ANO"] == ano).to_numpy()
            com_t = a & pub & atual[col].notna()
            com_t1 = a & pub & atual[f"{col}_T1"].notna()
            sem_t1 = ano == ultimo
            if ano in brasil:
                reg(ano, etapa, 1, "Brasil", brasil[ano], F_INV + " (n_linhas_dados)")
            else:
                reg(ano, etapa, 1, "Brasil", pd.NA, "",
                    "zip de tx_rend do ano não está nesta máquina; o funil começa em RR")
            reg(ano, etapa, 2, "RR", int(a.sum()), F_ATUAL)
            reg(ano, etapa, 3, "públicas", int((a & pub).sum()), F_ATUAL + " (REDE_PUBLICA = 1)")
            reg(ano, etapa, 4, "com a etapa em t", int(com_t.sum()), F_ATUAL + f" ({col} não nulo)")
            if sem_t1:
                obs = "t+1 ainda não publicado"
                for ordem, nome in ((5, "com a etapa em t e alvo em t+1"),
                                    (6, "com alvo em t+1, sem a etapa em t"),
                                    (7, "universo da avaliação"), (8, "painel da Etapa 2")):
                    reg(ano, etapa, ordem, nome, pd.NA, "", obs)
                continue
            reg(ano, etapa, 5, "com a etapa em t e alvo em t+1", int((com_t & com_t1).sum()),
                F_ATUAL + f" ({col} e {col}_T1 não nulos)")
            reg(ano, etapa, 6, "com alvo em t+1, sem a etapa em t", int((com_t1 & ~com_t).sum()),
                F_ATUAL + f" ({col}_T1 não nulo, {col} nulo)")
            reg(ano, etapa, 7, "universo da avaliação", int((u["ANO"] == ano).sum()), "baselines.universo")
            if ano in P.ANOS_FEATURES:
                reg(ano, etapa, 8, "painel da Etapa 2", int((painel["ANO"] == ano).sum()), "painel.montar")
            else:
                reg(ano, etapa, 8, "painel da Etapa 2", pd.NA, "", "ano fora do painel (ANO 2019–2024)")
    out = pd.DataFrame(linhas)
    out["n"] = out["n"].astype("Int64")
    return out


def main():
    atual = pd.read_parquet(P.P_ATUAL)
    out = funil(atual, brasil_por_ano())
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(SAIDA, index=False, encoding="utf-8")
    print(out.pivot_table(index=["etapa", "ano"], columns="ordem", values="n", aggfunc="first").to_string())
    print(f">>> {SAIDA}")


if __name__ == "__main__":
    main()
