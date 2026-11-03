# -*- coding: utf-8 -*-
"""
02d — TDI e ATU em grupos de permutação separados, IED nos anos com treino,
e a regra de testes múltiplos aplicada (pedido de 2026-11-02).

O modelo NÃO muda: é o do bloco 4 do Cenário B (mesmas colunas, mesmos
hiperparâmetros). Muda só a medida de importância: o grupo TDI_ATU vira dois
grupos, TDI e ATU (painel.blocos_importancia). Bootstrap agrupado por escola
com pooling das transições (bootstrap.Agrupado), 10 permutações fixas por
grupo, Recall@K calculado dentro do ano e agregado pela média das transições.

REGRA (DECISOES.md, 2026-11-02), declarada antes de rodar:
  * K primário = 10% e 20% (fixados nas Etapas 1–2). K = 30% é só
    sensibilidade: reportado, sem correção e sem peso de decisão.
  * Cada pergunta é uma FAMÍLIA; p-valor bootstrap bilateral e Holm dentro da
    família, α = 0,05. "Rejeita" = p ajustado ≤ 0,05.
Famílias (K primário, 2 etapas × 2 modelos salvo indicação):
  F1  importância > 0 de cada grupo (rendimento, TDI, ATU, IED, infra),
      transições 2021–2024 ........................................ 40 testes
  F2  TDI separável: (TDI − rendimento) e (TDI − ATU), 2021–2024 ..... 16 testes
  F3  IED só nas transições em que o treino tinha IED (2023–2024) .... 8 testes
  F4  modelo − B2, 8 modelos, 2021–2024 ............................. 32 testes
  F5  modelo − B1R_lag (8) e bloco k − bloco k−1 (6), 2021–2024 ...... 56 testes
Com B reamostragens o menor p é 2/(B+1); o primeiro passo de Holm na maior
família exige p ≤ 0,05/56 ≈ 0,0009, por isso B = 5.000.

Saída: gustavo/saida/avaliacao/02d_testes.csv, 02d_tdi_separado.md
Uso:   python avaliacao/02d_tdi_separado.py [--n-boot 5000]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bootstrap as BS  # noqa: E402
import metricas as M  # noqa: E402
import painel as P  # noqa: E402
import walkforward as W  # noqa: E402

SAIDA = Path(__file__).resolve().parent.parent / "saida" / "avaliacao"
ANOS = W.ANOS_TESTE
KS = BS.FRACOES_3K
K_PRIMARIO = ("Rec@10", "Rec@20")
N_PERM = 10
SEMENTE = 20261105
GRUPOS = P.GRUPOS_IMPORTANCIA
PERIODOS = {"2021–2024": ANOS, "2023–2024": (2023, 2024)}
BASES = ["B1R_lag", "B2"]
ALFA = 0.05


def ids_modelos():
    return [("B", m, k) for m in W.MODELOS for k in range(1, len(P.ORDEM_BLOCOS) + 1)]


def nome_mod(m):
    return "Ridge" if m == "ridge" else "Árvore"


def rodar(etapa, atual, oficial, rng, n_boot):
    _, _, prev = W.rodar_etapa(P.montar(etapa, atual, oficial), etapa, ANOS,
                               n_perm_boot=N_PERM, grupos_perm=P.blocos_importancia)
    ag = BS.Agrupado(prev)
    pids = [("-", b, 0) for b in BASES] + ids_modelos()
    pred = {pid: np.concatenate([c["p"][pid] for c in prev]) for pid in pids}
    perm = {(m, g, j): np.concatenate([c["perm"][("B", m)][g][j] for c in prev])
            for m in W.MODELOS for g in GRUPOS for j in range(N_PERM)}
    y = ag.y

    def avaliar(idx):
        sel = ag.por_ano(idx)
        out = {}
        for kn, f in KS.items():
            for a in ANOS:
                s = sel[a]
                k = M.k_de_fracao(len(s), f)
                py = M.prob_topk(y[s], k)          # P(escola no TopK real): uma vez por ano e K

                def rec(p):
                    return float(np.dot(M.prob_topk(p[s], k), py) / k)
                for pid in pids:
                    out[(pid, kn, a)] = rec(pred[pid])
                for m in W.MODELOS:
                    base = out[(("B", m, 4), kn, a)]
                    for g in GRUPOS:
                        out[(("imp", m, g), kn, a)] = base - np.mean([rec(perm[(m, g, j)])
                                                                      for j in range(N_PERM)])
        return out

    ponto = avaliar(np.arange(len(y)))
    dist = {k: np.empty(n_boot) for k in ponto}
    for b, idx in enumerate(ag.sorteios(rng, n_boot)):
        for k, v in avaliar(idx).items():
            dist[k][b] = v

    def agreg(src, chave, kn, per):
        anos = PERIODOS[per]
        return np.mean([src[(chave, kn, a)] for a in anos], axis=0)
    return ponto, dist, agreg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-boot", type=int, default=5000)
    args = ap.parse_args()
    atual, oficial = pd.read_parquet(P.P_ATUAL), pd.read_parquet(P.P_OFICIAL)
    W.N_PERMUT = 1
    rng = np.random.default_rng(SEMENTE)
    linhas = []

    def teste(familia, etapa, modelo, item, kn, per, v, d):
        lo, hi = BS.intervalo(d)
        linhas.append({"familia": familia, "etapa": etapa, "modelo": modelo, "item": item,
                       "K": kn, "periodo": per, "valor": float(v), "lo": lo, "hi": hi,
                       "p": BS.p_bootstrap(d), "ic_exclui_zero": lo > 0 or hi < 0})

    for etapa in ("AF", "EM"):
        ponto, dist, agreg = rodar(etapa, atual, oficial, rng, args.n_boot)
        for kn in KS:
            for m in W.MODELOS:
                for g in GRUPOS:                                         # F1
                    c = ("imp", m, g)
                    teste("F1", etapa, m, g, kn, "2021–2024", agreg(ponto, c, kn, "2021–2024"),
                          agreg(dist, c, kn, "2021–2024"))
                for outro in ("rendimento", "ATU"):                      # F2
                    a_, b_ = ("imp", m, "TDI"), ("imp", m, outro)
                    teste("F2", etapa, m, f"TDI − {outro}", kn, "2021–2024",
                          agreg(ponto, a_, kn, "2021–2024") - agreg(ponto, b_, kn, "2021–2024"),
                          agreg(dist, a_, kn, "2021–2024") - agreg(dist, b_, kn, "2021–2024"))
                c = ("imp", m, "IED")                                    # F3
                teste("F3", etapa, m, "IED", kn, "2023–2024", agreg(ponto, c, kn, "2023–2024"),
                      agreg(dist, c, kn, "2023–2024"))
            for pid in ids_modelos():
                mlabel = f"{nome_mod(pid[1])} b{pid[2]}"
                refs = {"B2": ("F4", ("-", "B2", 0)), "B1R_lag": ("F5", ("-", "B1R_lag", 0))}
                if pid[2] > 1:
                    refs[f"bloco {pid[2] - 1}"] = ("F5", (pid[0], pid[1], pid[2] - 1))
                for ref, (fam, rid) in refs.items():
                    teste(fam, etapa, mlabel, f"− {ref}", kn, "2021–2024",
                          agreg(ponto, pid, kn, "2021–2024") - agreg(ponto, rid, kn, "2021–2024"),
                          agreg(dist, pid, kn, "2021–2024") - agreg(dist, rid, kn, "2021–2024"))
    df = pd.DataFrame(linhas)
    df["primario"] = df["K"].isin(K_PRIMARIO)
    df["p_holm"] = np.nan
    for fam, g in df[df["primario"]].groupby("familia"):
        df.loc[g.index, "p_holm"] = BS.holm(g["p"].to_numpy())
    df["rejeita_holm"] = df["p_holm"] <= ALFA
    df["n_familia"] = df["familia"].map(df[df["primario"]].groupby("familia").size())
    df.to_csv(SAIDA / "02d_testes.csv", index=False, encoding="utf-8")

    # ----- relatório -----
    def cel(r):
        s = f"{r['valor']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}]"
        if r["primario"]:
            s += f" p_H={r['p_holm']:.3f}" + (" ✱" if r["rejeita_holm"] else "")
        else:
            s += " †" if r["ic_exclui_zero"] else ""
        return s

    def tab(t, linha, colunas="K"):
        t = t.copy()
        t["txt"] = t.apply(cel, axis=1)
        pv = t.pivot_table(index=linha, columns=colunas, values="txt", aggfunc="first", sort=False)
        cols = [linha] + list(pv.columns)
        out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        for i, r in pv.iterrows():
            out.append("| " + " | ".join([str(i)] + [str(v) for v in r]) + " |")
        return "\n".join(out)

    def contagem(t):
        return (f"IC exclui zero (sem correção, 3 K): {int(t['ic_exclui_zero'].sum())} de {len(t)}; "
                f"Holm (K primário): {int(t['rejeita_holm'].sum())} de {int(t['primario'].sum())}")

    txt = ["# TDI e ATU separados, IED nos anos com treino, e correção para testes múltiplos", "",
           f"Modelo do bloco 4 do Cenário B (inalterado). Bootstrap agrupado por escola, {args.n_boot}",
           "reamostragens; IC 95% por percentis; p bilateral bootstrap; Holm dentro de cada família no K",
           "primário (10% e 20%). ✱ = rejeita com Holm (α = 0,05). † = K 30% (sensibilidade), IC exclui zero,",
           "sem correção. Famílias declaradas no cabeçalho do script antes de rodar.", "",
           "## Famílias", "",
           "| família | pergunta | testes | rejeitados (Holm) |", "|---|---|---|---|"]
    perg = {"F1": "grupo carrega sinal (importância > 0), 2021–2024",
            "F2": "TDI separável do rendimento e do ATU, 2021–2024",
            "F3": "IED > 0 nos anos com IED no treino (2023–2024)",
            "F4": "modelo supera o B2 (território × rede), 2021–2024",
            "F5": "modelo supera o B1R_lag / bloco supera o anterior, 2021–2024"}
    for fam in ("F1", "F2", "F3", "F4", "F5"):
        g = df[(df["familia"] == fam) & df["primario"]]
        txt.append(f"| {fam} | {perg[fam]} | {len(g)} | {int(g['rejeita_holm'].sum())} |")
    txt.append("")
    tdi = df[(df["familia"] == "F1") & (df["item"] == "TDI")]
    atu = df[(df["familia"] == "F1") & (df["item"] == "ATU")]
    txt += ["## O TDI sozinho mantém os 12 de 12?", "",
            f"- TDI: {contagem(tdi)}", f"- ATU: {contagem(atu)}",
            f"- TDI − rendimento: {contagem(df[(df['familia'] == 'F2') & (df['item'] == 'TDI − rendimento')])}",
            f"- TDI − ATU: {contagem(df[(df['familia'] == 'F2') & (df['item'] == 'TDI − ATU')])}", ""]
    for etapa in ("AF", "EM"):
        for m in W.MODELOS:
            t = df[(df["etapa"] == etapa) & (df["modelo"] == m) & df["familia"].isin(["F1", "F2"])]
            txt += [f"### F1/F2 — {etapa}, {nome_mod(m)} (queda de Recall@K ao permutar o grupo)", "",
                    tab(t, "item"), ""]
    txt += ["## F3 — IED nas transições em que o treino tinha IED (2023–2024)", "",
            "Em 2021 e 2022 o treino não tem nenhum valor de IED e o modelo não usa o grupo; a média",
            "de 2021–2024 do F1 dilui o IED com dois zeros estruturais.", ""]
    t = df[df["familia"] == "F3"].assign(linha=lambda d: d["etapa"] + " " + d["modelo"].map(nome_mod))
    txt += [tab(t, "linha"), ""]
    for fam, titulo in (("F4", "modelo − B2"), ("F5", "modelo − B1R_lag e bloco − bloco anterior")):
        for etapa in ("AF", "EM"):
            t = df[(df["familia"] == fam) & (df["etapa"] == etapa)].assign(
                linha=lambda d: d["modelo"] + " " + d["item"])
            txt += [f"## {fam} — {titulo}, {etapa}", "", tab(t, "linha"), ""]
    (SAIDA / "02d_tdi_separado.md").write_text("\n".join(txt), encoding="utf-8")
    print("\n".join(txt))


if __name__ == "__main__":
    main()
