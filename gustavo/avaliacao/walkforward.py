# -*- coding: utf-8 -*-
"""
Walk-forward da Etapa 2 (janela expansiva) — funções puras.

Para cada ano alvo Y: treino = ANO_ALVO < Y; teste = ANO_ALVO == Y.
Imputação (mediana + indicador de ausência) e padronização ficam DENTRO do
Pipeline e são ajustadas só no treino de cada dobra. Hiperparâmetros FIXOS,
escolhidos antes de ver resultado (nada é ajustado olhando o ano de teste):
  ridge   Ridge(alpha=1.0) sobre variáveis padronizadas
  arvore  DecisionTreeRegressor(max_depth=3, min_samples_leaf=20)

Importância: permutação de BLOCO inteiro (as colunas do bloco são
embaralhadas juntas, com a mesma permutação de linhas) no ano de teste,
medida como queda de Recall@10%, Recall@20% e aumento de MAE.
"""
import warnings

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

import baselines as B
import metricas as M
import painel as P

ANOS_TESTE = (2021, 2022, 2023, 2024)   # 2025 = teste bloqueado (D7)

# O IED só existe de 2021 em diante: nas dobras com teste em 2021 e 2022 o
# treino não tem nenhum valor de IED e o imputador descarta essas colunas
# (o bloco 3 vira, na prática, o bloco 2). É esperado; o aviso é silenciado.
warnings.filterwarnings("ignore", message="Skipping features without any observed values")
N_PERMUT = 100
SEMENTE = 20261102


def modelo(nome):
    imp = SimpleImputer(strategy="median", add_indicator=True)
    if nome == "ridge":
        return Pipeline([("imp", imp), ("pad", StandardScaler()), ("m", Ridge(alpha=1.0))])
    if nome == "arvore":
        return Pipeline([("imp", imp),
                         ("m", DecisionTreeRegressor(max_depth=3, min_samples_leaf=20,
                                                     random_state=0))])
    raise ValueError(nome)


MODELOS = ("ridge", "arvore")


def metricas(y, p):
    n = len(y)
    k10, k20 = M.k_de_fracao(n, .10), M.k_de_fracao(n, .20)
    return {"n": n, "MAE": M.mae(y, p), "R2": M.r2(y, p),
            "Rec@10": M.recall_at_k(y, p, k10), "Rec@20": M.recall_at_k(y, p, k20)}


def importancia_blocos(pipe, X, y, blocos, rng):
    base = metricas(y, pipe.predict(X))
    linhas = []
    for nome, cols in blocos.items():
        d10, d20, dmae = [], [], []
        for _ in range(N_PERMUT):
            Xp = X.copy()
            Xp[cols] = X[cols].to_numpy()[rng.permutation(len(X))]
            m = metricas(y, pipe.predict(Xp))
            d10.append(base["Rec@10"] - m["Rec@10"])
            d20.append(base["Rec@20"] - m["Rec@20"])
            dmae.append(m["MAE"] - base["MAE"])
        linhas.append({"bloco": nome, "dRec@10": float(np.mean(d10)),
                       "dRec@20": float(np.mean(d20)), "dMAE": float(np.mean(dmae))})
    return linhas


def rodar_etapa(painel, etapa, anos=ANOS_TESTE):
    """Resultados (baselines + modelos × blocos × cenários) e importâncias."""
    res, imp = [], []
    rng = np.random.default_rng(SEMENTE)
    s = P.SUF[etapa]
    for ano in anos:
        tr = painel[painel["ANO_ALVO"] < ano]
        te = painel[painel["ANO_ALVO"] == ano]
        y, ytr = te["y_t1"].to_numpy(), tr["y_t1"].to_numpy()
        mu = float(ytr.mean())
        cab = {"etapa": etapa, "ano_alvo": ano,
               "anos_treino": f"{int(tr['ANO_ALVO'].min())}-{int(tr['ANO_ALVO'].max())}",
               "n_treino": len(tr)}
        base = {
            "B0": np.full(len(te), mu),
            "B1R": B.b1_persistencia(te, mu, "y_t"),                     # ordena por y_t
            "B1R_lag": B.b1_persistencia(te, mu, f"ABANDONO_{s}_L1"),    # ordena por y_{t−1}
            "B2": B.b2_mediana_estrato(tr, te),
        }
        for nome, p in base.items():
            res.append({**cab, "cenario": "-", "modelo": nome, "bloco": 0, **metricas(y, p)})
        for cen in P.CENARIOS:
            blocos = P.blocos(etapa, cen)
            for k in range(1, len(P.ORDEM_BLOCOS) + 1):
                cols = P.colunas_bloco(etapa, cen, k)
                for mod in MODELOS:
                    pipe = modelo(mod).fit(tr[cols], ytr)
                    res.append({**cab, "cenario": cen, "modelo": mod, "bloco": k,
                                **metricas(y, pipe.predict(te[cols]))})
                    if k == len(P.ORDEM_BLOCOS):
                        for lin in importancia_blocos(pipe, te[cols].copy(), y, blocos, rng):
                            imp.append({**cab, "cenario": cen, "modelo": mod, **lin})
    return pd.DataFrame(res), pd.DataFrame(imp)
