# -*- coding: utf-8 -*-
"""
ANÁLISE 03 — Associações descritivas que rodaram em código descartável em
2026-11-02 e cujos números estão em abandono-escolar/docs/DECISOES.md
("Correção de hipóteses") e em docs/problemas.csv (P026).

Níveis (os da docs/SINTESE_DO_PROJETO.md):
  [FATO]         associação entre preditores, ou do desfecho com ele mesmo
                 como descrição; reexecutável, sem inferência
  [EXPLORATÓRIO] associação de preditor com o desfecho calculada fora do
                 walk-forward, sobre todos os anos (inclui os de teste e o
                 alvo de 2025): serve para hipótese, nunca para decidir

Blocos:
  A. [FATO] persistência e correlações entre preditores (base oficial, públicas,
     lag dentro da própria base → pares 2020–2025); persistência da
     infraestrutura (base_atual, públicas, ANO ≥ 2019)
  B. [EXPLORATÓRIO] ρ de Spearman de cada preditor com o alvo (_T1), anos
     empilhados, públicas, alvo não nulo
  C. [EXPLORATÓRIO] Random Forest da P026: Cenário A, AF, sem divisão
     temporal; importância por impureza com o trio e com 2 das 3 taxas
     (3 sementes) e queda de R² por permutação de bloco em holdout aleatório
     de 30% (3 sementes, 30 repetições). Parâmetros idênticos aos de 2026-11-02.
  D. [EXPLORATÓRIO] decomposição entre escolas / dentro da escola da
     correlação do TDI(t) com o abandono. NÃO há número registrado para ela
     (não está no DECISOES.md); a definição é a deste script: Pearson nas
     médias por escola (entre) e nos desvios em relação à média da própria
     escola (dentro, só escolas com ≥ 2 anos), base oficial, públicas,
     alvo não nulo. Calculada contra o alvo (abandono em t+1) e, como
     referência, contra o abandono em t.

Saída: gustavo/saida/relatorios/associacoes_descritivas.csv
       (bloco, nivel, etapa, medida, metodo, n, valor)
Uso:   python analises/03_associacoes_descritivas.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

GUSTAVO = Path(__file__).resolve().parent.parent
P_OFICIAL = (GUSTAVO.parent / "abandono-escolar" / "dados" / "processado"
             / "base_longitudinal_rr_2019_2025.parquet")
P_ATUAL = GUSTAVO / "saida" / "base_atual.parquet"
SAIDA = GUSTAVO / "saida" / "relatorios" / "associacoes_descritivas.csv"
K = ["ANO", "CO_ENTIDADE"]
CFG = {
    "AF": dict(tdi="TDI_FUN_AF", rep="REPROVACAO_FUN_AF", ab="ABANDONO_FUN_AF", apr="APROVACAO_FUN_AF",
               atu="ATU_FUN_AF", ied="IED_FUN_ALTO", t1="ABANDONO_FUN_AF_T1"),
    "EM": dict(tdi="TDI_MED_TOTAL", rep="REPROVACAO_MED", ab="ABANDONO_MED", apr="APROVACAO_MED",
               atu="ATU_MED_TOTAL", ied="IED_MED_ALTO", t1="ABANDONO_MED_T1"),
}
INFRA = ["IIE_zano", "DIM_IIB_zano", "DIM_IDA_zano", "DIM_IDP_zano", "DIM_IEP_zano"]
SEMENTES = (0, 1, 2)
linhas = []


def f(s):
    return s.astype("Float64").astype("float64")


def publicas(df):
    return df[df["REDE_PUBLICA"].astype("Int8") == 1].copy()


def com_lag(df, cols):
    lag = df[K + cols].copy()
    lag["ANO"] = lag["ANO"] + 1
    lag = lag.rename(columns={c: c + "_L1" for c in cols})
    return df.merge(lag, on=K, how="left", validate="1:1")


def reg(bloco, nivel, etapa, medida, metodo, n, valor):
    linhas.append({"bloco": bloco, "nivel": nivel, "etapa": etapa, "medida": medida,
                   "metodo": metodo, "n": int(n), "valor": float(valor)})


def correl(bloco, nivel, etapa, medida, x, y, metodos=("pearson", "spearman")):
    m = x.notna() & y.notna()
    for met in metodos:
        reg(bloco, nivel, etapa, medida, met, m.sum(), x[m].corr(y[m], method=met))


def main():
    oficial = publicas(pd.read_parquet(P_OFICIAL))
    atual = publicas(pd.read_parquet(P_ATUAL))

    # A. [FATO]
    for e, c in CFG.items():
        d = com_lag(oficial, [c["tdi"], c["rep"], c["ab"]])
        for nome, x, y in [("TDI(t) x REPROVACAO(t-1)", c["tdi"], c["rep"] + "_L1"),
                           ("TDI(t) x ABANDONO(t-1)", c["tdi"], c["ab"] + "_L1"),
                           ("TDI(t) x TDI(t-1)", c["tdi"], c["tdi"] + "_L1"),
                           ("ABANDONO(t) x ABANDONO(t-1)", c["ab"], c["ab"] + "_L1")]:
            correl("A", "FATO", e, nome, f(d[x]), f(d[y]))
    a = com_lag(atual[atual["ANO"] >= 2019], INFRA)
    for col in INFRA:
        correl("A", "FATO", "escola", f"{col}(t) x {col}(t-1)", f(a[col]), f(a[col + "_L1"]), ("spearman",))

    # B. [EXPLORATÓRIO] ρ com o alvo
    for e, c in CFG.items():
        d = com_lag(oficial, [c["ab"]])
        d = d[d[c["t1"]].notna()]
        for nome, col in [("TDI", c["tdi"]), ("abandono(t)", c["ab"]), ("abandono(t-1)", c["ab"] + "_L1"),
                          ("ATU", c["atu"]), ("IED_ALTO", c["ied"])]:
            correl("B", "EXPLORATÓRIO", e, f"{nome} x alvo(t+1)", f(d[col]), f(d[c["t1"]]), ("spearman",))

    # C. [EXPLORATÓRIO] Random Forest da P026 (AF, Cenário A, sem divisão temporal)
    c = CFG["AF"]
    trio = [c["ab"], c["apr"], c["rep"]]
    outras = [c["tdi"], c["atu"]]
    x = oficial[trio + outras + [c["t1"]]].astype("float64").dropna()
    y = x.pop(c["t1"])
    rotulo = {c["ab"]: "ABANDONO", c["apr"]: "APROVACAO", c["rep"]: "REPROVACAO",
              c["tdi"]: "TDI", c["atu"]: "ATU"}

    def mdi(cols, s):
        rf = RandomForestRegressor(n_estimators=500, random_state=s, n_jobs=-1).fit(x[cols], y)
        return pd.Series(rf.feature_importances_, cols)
    for s in SEMENTES:
        i = mdi(trio + outras, s)
        for col, v in i.items():
            reg("C", "EXPLORATÓRIO", "AF", f"MDI com trio: {rotulo[col]} (semente {s})", "impureza", len(x), v)
        reg("C", "EXPLORATÓRIO", "AF", f"MDI com trio: trio somado (semente {s})", "impureza", len(x), i[trio].sum())
        dois = [c["ab"], c["rep"]] + outras
        i2 = mdi(dois, s)
        for col, v in i2.items():
            reg("C", "EXPLORATÓRIO", "AF", f"MDI com 2 das 3: {rotulo[col]} (semente {s})", "impureza", len(x), v)
        reg("C", "EXPLORATÓRIO", "AF", f"MDI com 2 das 3: rendimento somado (semente {s})", "impureza",
            len(x), i2[[c["ab"], c["rep"]]].sum())
    blocos = {"rendimento (trio)": trio, "TDI": [c["tdi"]], "ATU": [c["atu"]]}
    for s in SEMENTES:
        xtr, xte, ytr, yte = train_test_split(x[trio + outras], y, test_size=.3, random_state=s)
        rf = RandomForestRegressor(n_estimators=500, random_state=s, n_jobs=-1).fit(xtr, ytr)
        base = rf.score(xte, yte)
        rng = np.random.default_rng(s)
        reg("C", "EXPLORATÓRIO", "AF", f"R² holdout (semente {s})", "R2", len(xte), base)
        for b, cols in blocos.items():
            q = []
            for _ in range(30):
                xp = xte.copy()
                xp[cols] = xte[cols].to_numpy()[rng.permutation(len(xp))]
                q.append(base - rf.score(xp, yte))
            reg("C", "EXPLORATÓRIO", "AF", f"permutação de bloco: {b} (semente {s})", "queda de R2",
                len(xte), np.mean(q))

    # D. [EXPLORATÓRIO] decomposição entre / dentro da escola
    for e, c in CFG.items():
        d = oficial[oficial[c["t1"]].notna()][["CO_ENTIDADE", c["tdi"], c["t1"], c["ab"]]].copy()
        for col in (c["tdi"], c["t1"], c["ab"]):
            d[col] = f(d[col])
        for alvo, rot in ((c["t1"], "abandono(t+1)"), (c["ab"], "abandono(t)")):
            z = d[["CO_ENTIDADE", c["tdi"], alvo]].dropna()
            med = z.groupby("CO_ENTIDADE")[[c["tdi"], alvo]].mean()
            reg("D", "EXPLORATÓRIO", e, f"TDI(t) x {rot}: entre escolas (médias por escola)", "pearson",
                len(med), med[c["tdi"]].corr(med[alvo]))
            n_anos = z.groupby("CO_ENTIDADE")[alvo].transform("size")
            w = z[n_anos >= 2].copy()
            for col in (c["tdi"], alvo):
                w[col] = w[col] - w.groupby("CO_ENTIDADE")[col].transform("mean")
            reg("D", "EXPLORATÓRIO", e, f"TDI(t) x {rot}: dentro da escola (desvios da média)", "pearson",
                len(w), w[c["tdi"]].corr(w[alvo]))
            reg("D", "EXPLORATÓRIO", e, f"TDI(t) x {rot}: total (sem decompor)", "pearson",
                len(z), z[c["tdi"]].corr(z[alvo]))

    out = pd.DataFrame(linhas)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(SAIDA, index=False, encoding="utf-8")
    with pd.option_context("display.width", 200, "display.max_rows", 200):
        print(out.assign(valor=out["valor"].round(3)).to_string(index=False))
    print(f"\n>>> {SAIDA}")


if __name__ == "__main__":
    main()
