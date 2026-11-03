# -*- coding: utf-8 -*-
"""
02 — Etapa 2 do protocolo: walk-forward, Cenário B (principal) e A (teto).

Entrada: base_atual.parquet + base oficial 2019–2025 (merge só em memória)
Saída:   gustavo/saida/avaliacao/02_walkforward.csv    (métricas por ano)
         gustavo/saida/avaliacao/02_importancia.csv    (permutação por bloco)
         gustavo/saida/avaliacao/02_walkforward.md     (tabelas + decisões)
Uso:     python avaliacao/02_walkforward.py [--incluir-2025]

--incluir-2025 avalia também a transição 2024→2025, que pela D7 do orientador
é o teste bloqueado (uma única avaliação, depois de congelar tudo).

Critérios (fixados antes de ver resultado):
  * primário: Recall@10% e Recall@20%, ano a ano; R² e MAE são secundários
  * modelo "supera" o baseline se tiver Recall@K maior na maioria dos anos
  * bloco k+1 é adotado só se melhorar Recall@10% E Recall@20% na maioria
    dos anos em relação ao bloco k (empate não conta como melhora)
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import painel as P  # noqa: E402
import walkforward as W  # noqa: E402

SAIDA = Path(__file__).resolve().parent.parent / "saida" / "avaliacao"
ROTULO = {"B0": "B0 média", "B1R": "B1R limite otimista (y_t)", "B1R_lag": "B1R_lag BASELINE (y_t−1)",
          "B2": "B2 mediana loc×dep"}


def rotulo(r):
    if r["modelo"] in ROTULO:
        return ROTULO[r["modelo"]]
    return f"{'Ridge' if r['modelo'] == 'ridge' else 'Árvore'} bloco {r['bloco']}"


def lado_a_lado(res, metrica, cenario, anos):
    """Linhas = baselines + modelos; colunas = AF anos | EM anos."""
    sel = res[res["cenario"].isin(["-", cenario])].copy()
    sel["linha"] = sel.apply(rotulo, axis=1)
    sel["col"] = sel["etapa"] + " " + sel["ano_alvo"].astype(str)
    t = sel.pivot_table(index="linha", columns="col", values=metrica, sort=False)
    t = t[[f"{e} {a}" for e in ("AF", "EM") for a in anos]]
    return md(t.reset_index(), 2)


def md(df, casas=2):
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(f"{v:.{casas}f}" if isinstance(v, float) else str(v)
                                     for v in r) + " |")
    return "\n".join(out)


def contagens(res, anos):
    """Decisões calculadas por código: superação dos baselines e adoção de blocos."""
    linhas = []
    maioria = len(anos) // 2 + 1
    for (cen, etapa, mod), g in res[res["cenario"] != "-"].groupby(["cenario", "etapa", "modelo"]):
        bl = res[(res["cenario"] == "-") & (res["etapa"] == etapa)].set_index(["modelo", "ano_alvo"])
        for k in range(1, len(P.ORDEM_BLOCOS) + 1):
            gk = g[g["bloco"] == k].set_index("ano_alvo")
            lin = {"cenario": cen, "etapa": etapa, "modelo": mod, "bloco": k}
            for kk in ("Rec@10", "Rec@20"):
                for b in ("B1R", "B1R_lag", "B2"):
                    lin[f"{kk}>{b}"] = int(sum(gk.loc[a, kk] > bl.loc[(b, a), kk] for a in anos))
                if k > 1:
                    gp = g[g["bloco"] == k - 1].set_index("ano_alvo")
                    lin[f"{kk} melhora vs bloco {k - 1}"] = int(sum(gk.loc[a, kk] > gp.loc[a, kk] for a in anos))
            if k > 1:
                ok = all(lin[f"{kk} melhora vs bloco {k - 1}"] >= maioria for kk in ("Rec@10", "Rec@20"))
                lin["adota bloco"] = "sim" if ok else "não"
            linhas.append(lin)
    return pd.DataFrame(linhas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--incluir-2025", action="store_true")
    args = ap.parse_args()
    anos = W.ANOS_TESTE + ((2025,) if args.incluir_2025 else ())

    atual = pd.read_parquet(P.P_ATUAL)
    oficial = pd.read_parquet(P.P_OFICIAL)
    res, imp = [], []
    for etapa in ("AF", "EM"):
        painel = P.montar(etapa, atual, oficial)
        r, i, _ = W.rodar_etapa(painel, etapa, anos)
        res.append(r); imp.append(i)
    res, imp = pd.concat(res, ignore_index=True), pd.concat(imp, ignore_index=True)
    SAIDA.mkdir(parents=True, exist_ok=True)
    res.to_csv(SAIDA / "02_walkforward.csv", index=False, encoding="utf-8")
    imp.to_csv(SAIDA / "02_importancia.csv", index=False, encoding="utf-8")
    cont = contagens(res, anos)
    cont.to_csv(SAIDA / "02_decisoes.csv", index=False, encoding="utf-8")

    n = res[res["modelo"] == "B0"][["etapa", "ano_alvo", "anos_treino", "n_treino", "n"]]
    txt = ["# Etapa 2 — Walk-forward", "",
           f"Anos de teste: {', '.join(map(str, anos))} (2025 = teste bloqueado pela D7"
           f"{', INCLUÍDO' if args.incluir_2025 else ', não avaliado'}).",
           "Cenário B = principal (sem rendimento de t). Cenário A = teto otimista.", "",
           "## Tamanho das dobras", "", md(n, 0), ""]
    for cen in ("B", "A"):
        titulo = "Cenário B (principal)" if cen == "B" else "Cenário A (teto otimista — usa rendimento de t)"
        txt += [f"## {titulo}", ""]
        for met in ("Rec@10", "Rec@20", "MAE", "R2"):
            sec = "primário" if met.startswith("Rec") else "secundário"
            txt += [f"### {met} ({sec})", "", lado_a_lado(res, met, cen, anos), ""]
        ic = imp[imp["cenario"] == cen].copy()
        ic["col"] = ic["etapa"] + " " + ic["ano_alvo"].astype(str)
        for mod in W.MODELOS:
            for met in ("dRec@10", "dRec@20"):
                t = ic[ic["modelo"] == mod].pivot_table(index="bloco", columns="col", values=met, sort=False)
                t = t[[f"{e} {a}" for e in ("AF", "EM") for a in anos]].reset_index()
                txt += [f"### Importância por bloco — {mod}, bloco 4, queda de {met[1:]} ao permutar", "",
                        md(t, 3), ""]
    txt += ["## Contagens para decisão (anos em que o modelo supera / o bloco melhora)", "",
            md(cont, 0), ""]
    s = "\n".join(txt)
    (SAIDA / "02_walkforward.md").write_text(s, encoding="utf-8")
    print(s)


if __name__ == "__main__":
    main()
