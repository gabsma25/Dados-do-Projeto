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
    out = {"n": n, "MAE": M.mae(y, p), "R2": M.r2(y, p)}
    for f in (.10, .20, .30):
        out[f"Rec@{int(f * 100)}"] = M.recall_at_k(y, p, M.k_de_fracao(n, f))
    return out


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


def previsoes_permutadas(pipe, X, blocos, n, rng):
    """n previsões com cada bloco permutado (mesma permutação nas colunas do bloco)."""
    out = {}
    for nome, cols in blocos.items():
        lst = []
        for _ in range(n):
            Xp = X.copy()
            Xp[cols] = X[cols].to_numpy()[rng.permutation(len(X))]
            lst.append(pipe.predict(Xp))
        out[nome] = lst
    return out


def rodar_etapa(painel, etapa, anos=ANOS_TESTE, n_perm_boot=0, grupos_perm=None):
    """Resultados (baselines + modelos × blocos × cenários), importâncias e
    previsões por ano (para o bootstrap de escolas).

    prev: lista de {"etapa", "ano_alvo", "y", "co", "p": {(cenario, modelo, bloco): ŷ},
                    "perm": {(cenario, modelo): {bloco: [ŷ permutado, ...]}}}
    "perm" só é preenchido para o bloco 4 do Cenário B e se n_perm_boot > 0;
    grupos_perm(etapa, cenario) define os grupos permutados (padrão: P.blocos).
    """
    res, imp, prev = [], [], []
    rng = np.random.default_rng(SEMENTE)
    rng_perm = np.random.default_rng(SEMENTE + 1)   # separado: não altera o rng da importância
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
        p_ano, perm = {}, {}
        for nome, p in base.items():
            res.append({**cab, "cenario": "-", "modelo": nome, "bloco": 0, **metricas(y, p)})
            p_ano[("-", nome, 0)] = p
        for cen in P.CENARIOS:
            blocos = P.blocos(etapa, cen)
            for k in range(1, len(P.ORDEM_BLOCOS) + 1):
                cols = P.colunas_bloco(etapa, cen, k)
                for mod in MODELOS:
                    pipe = modelo(mod).fit(tr[cols], ytr)
                    p = pipe.predict(te[cols])
                    res.append({**cab, "cenario": cen, "modelo": mod, "bloco": k, **metricas(y, p)})
                    p_ano[(cen, mod, k)] = p
                    if k == len(P.ORDEM_BLOCOS):
                        for lin in importancia_blocos(pipe, te[cols].copy(), y, blocos, rng):
                            imp.append({**cab, "cenario": cen, "modelo": mod, **lin})
                        if n_perm_boot and cen == "B":
                            grupos = (grupos_perm or P.blocos)(etapa, cen)
                            perm[(cen, mod)] = previsoes_permutadas(pipe, te[cols].copy(), grupos,
                                                                    n_perm_boot, rng_perm)
        prev.append({"etapa": etapa, "ano_alvo": ano, "y": y,
                     "co": te["CO_ENTIDADE"].astype(str).to_numpy(), "p": p_ano, "perm": perm})
    return pd.DataFrame(res), pd.DataFrame(imp), prev
