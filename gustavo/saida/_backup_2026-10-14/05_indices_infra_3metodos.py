# -*- coding: utf-8 -*-
"""
05 — Índices de infraestrutura (Almeida & Mussato, 2023) em 3 normalizações.

Entrada:  gustavo/saida/etapas/04_base_com_censo.parquet   (18 variáveis 0/1)
Saída:    gustavo/saida/etapas/05_base_com_indices.parquet (+15 colunas)
          gustavo/saida/base_atual.parquet                 (cópia deste)
          gustavo/saida/relatorios/indices_infra.txt
          gustavo/saida/relatorios/indices_infra_parametros.json

As 18 variáveis ORIGINAIS ficam na base. As colunas novas são derivadas e podem
ser descartadas livremente na hora de montar o modelo (nível 18 -> 4 -> 1).

Dimensões do artigo (Quadro 3): IIB (4 itens), IDA (5), IDP (5), IEP (4).
Soma bruta da dimensão = quantos itens a escola tem. Uma dimensão só existe
quando TODOS os seus itens estão presentes (senão NaN) — assim 2007-2011, anos
em que alguns itens não foram coletados, ficam sem IDA/IDP/IIE em vez de
receber um número que significa outra coisa.

Normalizações (sufixo da coluna):
  _prop    : soma / nº de itens da dimensão (0 a 1). Sem parâmetros ajustados.
  _zano    : z-score DENTRO de cada ano (média e desvio de todas as escolas da
             base naquele ano). Usa só informação do próprio ano. NaN se
             n < 30 ou desvio = 0.
  _zref19  : z-score com média e desvio FIXOS de 2019, calculados nas escolas
             estaduais com taxa de ensino médio (aproximação do recorte do
             artigo: 165 escolas; aqui o número é reportado no relatório).

IIE (índice final) = primeiro componente principal das 4 dimensões, com os
PESOS FIXOS calculados em 2019 (correlação das 4 dimensões _zref19 no recorte
de referência; sinal ajustado para pesos somarem > 0). Os mesmos pesos são
aplicados às 4 dimensões de cada normalização:  IIE_<norm> = soma(w_i * DIM_i).
A escala do IIE_prop, IIE_zano e IIE_zref19 é, portanto, diferente entre si;
compare só dentro da mesma normalização.

Tipagem (regra 6): colunas derivadas Float64 nullable; as 18 originais seguem Int8.

Colunas criadas (15):
  DIM_IIB_prop DIM_IDA_prop DIM_IDP_prop DIM_IEP_prop IIE_prop
  DIM_IIB_zano DIM_IDA_zano DIM_IDP_zano DIM_IEP_zano IIE_zano
  DIM_IIB_zref19 DIM_IDA_zref19 DIM_IDP_zref19 DIM_IEP_zref19 IIE_zref19

Uso:  python programas/05_indices_infra.py
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

GUSTAVO = Path(__file__).resolve().parent.parent
SAIDA_ETAPAS = GUSTAVO / "saida" / "etapas"
SAIDA_REL = GUSTAVO / "saida" / "relatorios"
SAIDA_BASE = GUSTAVO / "saida" / "base_atual.parquet"
IN_BASE = SAIDA_ETAPAS / "04_base_com_censo.parquet"
OUT = SAIDA_ETAPAS / "05_base_com_indices.parquet"
OUT_REL = SAIDA_REL / "indices_infra.txt"
OUT_JSON = SAIDA_REL / "indices_infra_parametros.json"

DIMENSOES = {
    "IIB": ["IIB_agua_potavel", "IIB_energia_rede", "IIB_coleta_lixo", "IIB_banheiro"],
    "IDA": ["IDA_despensa", "IDA_refeitorio", "IDA_sala_diretoria",
            "IDA_sala_professor", "IDA_secretaria"],
    "IDP": ["IDP_biblioteca", "IDP_lab_informatica", "IDP_patio_coberto",
            "IDP_patio_descoberto", "IDP_quadra_esportes"],
    "IEP": ["IEP_computador", "IEP_impressora", "IEP_projetor", "IEP_internet"],
}
NORMS = ["prop", "zano", "zref19"]
ANO_REF = 2019
MIN_ESCOLAS_ANO = 30


def somas_brutas(base):
    """Soma de itens por dimensão; NaN se algum item da dimensão for NaN."""
    out = {}
    for d, itens in DIMENSOES.items():
        out[d] = base[itens].sum(axis=1, min_count=len(itens))
    return pd.DataFrame(out, index=base.index)


def recorte_referencia(base):
    """Escolas estaduais, ANO_REF, com taxa de ensino médio (proxy do recorte)."""
    m = ((base["ANO"].astype(int) == ANO_REF)
         & base["DEPENDENCIA"].astype(str).str.lower().str.startswith("estad")
         & base["APROVACAO_MED"].notna())
    return m


def main():
    print("=" * 78)
    print("05 — ÍNDICES DE INFRAESTRUTURA (3 normalizações)")
    print("=" * 78)
    if not IN_BASE.exists():
        print(f"[ERRO] não achei {IN_BASE} — rode 04 antes")
        sys.exit(1)

    base = pd.read_parquet(IN_BASE)
    itens = [i for l in DIMENSOES.values() for i in l]
    faltam = [i for i in itens if i not in base.columns]
    if faltam:
        print(f"[ERRO] faltam colunas: {faltam} — rode 03 e 04")
        sys.exit(1)
    base_f = base.copy()
    base_f[itens] = base_f[itens].astype("float64")   # contas em float; saída volta a Int8/Float64
    soma = somas_brutas(base_f)
    n_itens = {d: len(l) for d, l in DIMENSOES.items()}

    novas = {}
    # ---- prop
    for d in DIMENSOES:
        novas[f"DIM_{d}_prop"] = soma[d] / n_itens[d]

    # ---- z por ano
    est_ano = []
    for d in DIMENSOES:
        col = pd.Series(np.nan, index=base.index)
        for ano, idx in base.groupby("ANO").groups.items():
            s = soma.loc[idx, d]
            v = s.dropna()
            media, dp = (v.mean(), v.std(ddof=0)) if len(v) else (np.nan, np.nan)
            valido = len(v) >= MIN_ESCOLAS_ANO and dp > 0
            est_ano.append({"ano": int(ano), "dim": d, "n": int(len(v)),
                            "media_soma": None if np.isnan(media) else float(media),
                            "dp_soma": None if np.isnan(dp) else float(dp),
                            "valido": bool(valido)})
            if valido:
                col.loc[idx] = (s - media) / dp
        novas[f"DIM_{d}_zano"] = col

    # ---- z com referência fixa 2019
    ref = recorte_referencia(base)
    params_ref = {}
    for d in DIMENSOES:
        v = soma.loc[ref, d].dropna()
        params_ref[d] = {"media": float(v.mean()), "dp": float(v.std(ddof=0)),
                         "n": int(len(v))}
        novas[f"DIM_{d}_zref19"] = (soma[d] - params_ref[d]["media"]) / params_ref[d]["dp"]

    # ---- pesos do IIE (PC1 da correlação das 4 dimensões z de 2019)
    Z = pd.DataFrame({d: novas[f"DIM_{d}_zref19"] for d in DIMENSOES}).loc[ref].dropna()
    R = np.corrcoef(Z.values.T)
    vals, vecs = np.linalg.eigh(R)
    ordem = np.argsort(vals)[::-1]
    vals, vecs = vals[ordem], vecs[:, ordem]
    w = vecs[:, 0]
    if w.sum() < 0:
        w = -w
    var_exp = vals / vals.sum()
    pesos = dict(zip(DIMENSOES.keys(), [float(x) for x in w]))

    for nm in NORMS:
        mat = pd.DataFrame({d: novas[f"DIM_{d}_{nm}"] for d in DIMENSOES})
        novas[f"IIE_{nm}"] = (mat * w).sum(axis=1, min_count=len(DIMENSOES))

    novas_df = pd.DataFrame(novas, index=base.index).astype("Float64")
    ordem_cols = []
    for nm in NORMS:
        ordem_cols += [f"DIM_{d}_{nm}" for d in DIMENSOES] + [f"IIE_{nm}"]
    base = pd.concat([base, novas_df[ordem_cols]], axis=1)

    base.to_parquet(OUT, index=False)
    shutil.copy2(OUT, SAIDA_BASE)
    print(f">>> {OUT}  ({base.shape[0]} × {base.shape[1]})")
    print(f">>> {SAIDA_BASE} (cópia)")

    # ---- relatórios
    params = {
        "ano_referencia": ANO_REF,
        "n_escolas_referencia": int(ref.sum()),
        "n_escolas_artigo": 165,
        "recorte": "DEPENDENCIA=Estadual & APROVACAO_MED não nulo (proxy de 'oferta ensino médio')",
        "z_referencia_2019": params_ref,
        "pca_2019": {"autovalores": [float(x) for x in vals],
                     "variancia_explicada": [float(x) for x in var_exp],
                     "pesos_pc1": pesos,
                     "matriz_correlacao": R.round(4).tolist()},
        "z_por_ano": est_ano,
        "min_escolas_ano": MIN_ESCOLAS_ANO,
    }
    OUT_JSON.write_text(json.dumps(params, indent=2, ensure_ascii=False),
                        encoding="utf-8")

    L = ["ÍNDICES DE INFRAESTRUTURA — 05", "=" * 70,
         f"Base: {base.shape[0]} × {base.shape[1]} (15 colunas novas)", "",
         f"Referência 2019: {int(ref.sum())} escolas (artigo: 165; recorte aproximado)",
         "Parâmetros z fixos (soma bruta):",
         f"{'dim':>5}{'n':>6}{'media':>9}{'dp':>8}"]
    for d, p in params_ref.items():
        L.append(f"{d:>5}{p['n']:>6}{p['media']:>9.3f}{p['dp']:>8.3f}")
    L += ["", "PCA das 4 dimensões (2019, correlação):",
          "  autovalores:        " + "  ".join(f"{x:.3f}" for x in vals),
          "  variância explicada: " + "  ".join(f"{x*100:.1f}%" for x in var_exp),
          f"  Kaiser (autovalor PC1 > 1): {'sim' if vals[0] > 1 else 'NÃO'}   "
          f"PC1 > 60% da variância: {'sim' if var_exp[0] > 0.6 else 'NÃO'}",
          "  pesos PC1:           " + "  ".join(f"{d}={x:.3f}" for d, x in pesos.items()),
          "", "Cobertura (% de escolas com valor) por ano:",
          f"{'ano':>5}{'n':>6}" + "".join(f"{c:>13}" for c in
                                          ["IIE_prop", "IIE_zano", "IIE_zref19"])]
    for ano in sorted(base["ANO"].unique()):
        sub = base[base["ANO"] == ano]
        L.append(f"{ano:>5}{len(sub):>6}" + "".join(
            f"{sub[c].notna().mean()*100:>12.1f}%" for c in
            ["IIE_prop", "IIE_zano", "IIE_zref19"]))
    L += ["", "z por ano — média e desvio das somas brutas (IIB / IDA / IDP / IEP):"]
    ea = pd.DataFrame(est_ano)
    for ano in sorted(ea["ano"].unique()):
        sub = ea[ea["ano"] == ano].set_index("dim")
        L.append(f"  {ano}: " + " | ".join(
            f"{d} dp={sub.loc[d,'dp_soma']:.2f}" if sub.loc[d, 'valido']
            else f"{d} --" for d in DIMENSOES))
    OUT_REL.write_text("\n".join(L), encoding="utf-8")
    print(f">>> {OUT_REL}\n>>> {OUT_JSON}")
    print("\n".join(L[:22]))


if __name__ == "__main__":
    main()
