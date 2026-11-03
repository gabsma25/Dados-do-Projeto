# -*- coding: utf-8 -*-
"""
02c — Aumentar o poder do instrumento antes de concluir (pedido de 2026-11-02).

  1. Bootstrap agrupado por escola com pooling dos 4 anos de teste
     (bootstrap.Agrupado): intervalo por ano e intervalo agrupado, lado a lado.
  2. Recall@K para K = 10%, 20% e 30%, com intervalo em cada um.
  3. Bootstrap da importância por bloco (modelo do bloco 4): 10 permutações
     fixas por bloco no conjunto de teste; em cada reamostragem de escolas,
     importância = Recall(modelo) − média dos Recall com o bloco permutado.
     Comparação central: TDI_ATU − rendimento.

Só Cenário B. 2025 continua bloqueado (D7). 1.000 reamostragens; IC 95% por
percentis; classe "vence"/"perde" só se o intervalo excluir zero.

Saída: gustavo/saida/avaliacao/02c_largura.csv, 02c_diferencas.csv,
       02c_importancia.csv, 02c_poder.md
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bootstrap as BS  # noqa: E402
import painel as P  # noqa: E402
import walkforward as W  # noqa: E402

SAIDA = Path(__file__).resolve().parent.parent / "saida" / "avaliacao"
ANOS = W.ANOS_TESTE
KS = BS.FRACOES_3K
N_PERM = 10
SEMENTE = 20261104
BASES = ["B1R_lag", "B1R", "B2"]


def ids_modelos():
    return [("B", m, k) for m in W.MODELOS for k in range(1, len(P.ORDEM_BLOCOS) + 1)]


def nome(pid):
    return pid[1] if pid[0] == "-" else f"{'Ridge' if pid[1] == 'ridge' else 'Árvore'} b{pid[2]}"


def md(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(out)


def ic_txt(v, lo, hi):
    return f"{v:+.2f} [{lo:+.2f}, {hi:+.2f}]"


def rodar(etapa, atual, oficial, rng):
    _, _, prev = W.rodar_etapa(P.montar(etapa, atual, oficial), etapa, ANOS, n_perm_boot=N_PERM)
    ag = BS.Agrupado(prev)
    pids = [("-", b, 0) for b in BASES] + ids_modelos()
    pred = {pid: np.concatenate([c["p"][pid] for c in prev]) for pid in pids}
    blocos = P.ORDEM_BLOCOS
    perm = {(mod, b, j): np.concatenate([c["perm"][("B", mod)][b][j] for c in prev])
            for mod in W.MODELOS for b in blocos for j in range(N_PERM)}
    y = ag.y
    todos = np.arange(len(y))

    def avaliar(idx):
        """{(pid|('imp',mod,bloco), K, ano|'agrupado'): valor} numa reamostragem."""
        sel = ag.por_ano(idx)
        out = {}
        for kn, f in KS.items():
            for pid in pids:
                v = [BS.recall_ano(y, pred[pid], sel[a], f) for a in ANOS]
                for a, x in zip(ANOS, v):
                    out[(pid, kn, a)] = x
                out[(pid, kn, "agrupado")] = float(np.mean(v))
            for mod in W.MODELOS:
                base = [out[(("B", mod, 4), kn, a)] for a in ANOS]
                for b in blocos:
                    v = [base[i] - np.mean([BS.recall_ano(y, perm[(mod, b, j)], sel[a], f)
                                            for j in range(N_PERM)]) for i, a in enumerate(ANOS)]
                    for a, x in zip(ANOS, v):
                        out[(("imp", mod, b), kn, a)] = x
                    out[(("imp", mod, b), kn, "agrupado")] = float(np.mean(v))
        return out

    ponto = avaliar(todos)
    dist = {}
    for idx in ag.sorteios(rng):
        for k, v in avaliar(idx).items():
            dist.setdefault(k, []).append(v)
    dist = {k: np.array(v) for k, v in dist.items()}
    return ponto, dist, len(ag.escolas), len(y)


def main():
    atual, oficial = pd.read_parquet(P.P_ATUAL), pd.read_parquet(P.P_OFICIAL)
    W.N_PERMUT = 1
    rng = np.random.default_rng(SEMENTE)
    larg, dif, imp, tam = [], [], [], []
    periodos = list(ANOS) + ["agrupado"]
    for etapa in ("AF", "EM"):
        ponto, dist, n_esc, n_lin = rodar(etapa, atual, oficial, rng)
        tam.append({"etapa": etapa, "escolas distintas": n_esc, "escolas-ano": n_lin})
        # 1. largura dos intervalos de cada célula (modelos do Cenário B)
        for pid in ids_modelos():
            for kn in KS:
                for per in periodos:
                    lo, hi = BS.intervalo(dist[(pid, kn, per)])
                    larg.append({"etapa": etapa, "id": nome(pid), "K": kn, "periodo": str(per),
                                 "valor": ponto[(pid, kn, per)], "lo": lo, "hi": hi, "largura": hi - lo})
        # diferenças pareadas
        for pid in ids_modelos():
            refs = {b: ("-", b, 0) for b in BASES}
            if pid[2] > 1:
                refs[f"bloco {pid[2] - 1}"] = (pid[0], pid[1], pid[2] - 1)
            for ref, rid in refs.items():
                for kn in KS:
                    for per in periodos:
                        d = dist[(pid, kn, per)] - dist[(rid, kn, per)]
                        lo, hi = BS.intervalo(d)
                        dif.append({"etapa": etapa, "modelo": pid[1], "bloco": pid[2], "referencia": ref,
                                    "K": kn, "periodo": str(per),
                                    "dif": ponto[(pid, kn, per)] - ponto[(rid, kn, per)],
                                    "lo": lo, "hi": hi, "classe": BS.classe(lo, hi)})
        # 3. importância por bloco e TDI_ATU − rendimento
        for mod in W.MODELOS:
            for kn in KS:
                for per in periodos:
                    for b in P.ORDEM_BLOCOS:
                        v = dist[(("imp", mod, b), kn, per)]
                        lo, hi = BS.intervalo(v)
                        imp.append({"etapa": etapa, "modelo": mod, "K": kn, "periodo": str(per),
                                    "comparacao": b, "valor": ponto[(("imp", mod, b), kn, per)],
                                    "lo": lo, "hi": hi, "classe": BS.classe(lo, hi)})
                    d = dist[(("imp", mod, "TDI_ATU"), kn, per)] - dist[(("imp", mod, "rendimento"), kn, per)]
                    lo, hi = BS.intervalo(d)
                    imp.append({"etapa": etapa, "modelo": mod, "K": kn, "periodo": str(per),
                                "comparacao": "TDI_ATU − rendimento",
                                "valor": ponto[(("imp", mod, "TDI_ATU"), kn, per)]
                                - ponto[(("imp", mod, "rendimento"), kn, per)],
                                "lo": lo, "hi": hi, "classe": BS.classe(lo, hi)})
    larg, dif, imp = pd.DataFrame(larg), pd.DataFrame(dif), pd.DataFrame(imp)
    for n_, df in (("02c_largura", larg), ("02c_diferencas", dif), ("02c_importancia", imp)):
        df.to_csv(SAIDA / f"{n_}.csv", index=False, encoding="utf-8")

    # ----- relatório -----
    larg["tipo"] = np.where(larg["periodo"] == "agrupado", "agrupado", "por ano")
    resumo = larg.groupby(["etapa", "K", "tipo"])["largura"].median().unstack("tipo").reset_index()
    resumo["queda"] = 1 - resumo["agrupado"] / resumo["por ano"]
    resumo = resumo.assign(**{c: resumo[c].map(lambda v: f"{v:.2f}") for c in ("por ano", "agrupado")},
                           queda=resumo["queda"].map(lambda v: f"{v:.0%}"))
    ag = dif[dif["periodo"] == "agrupado"]
    quando = ag.groupby(["etapa", "referencia", "K"]).agg(
        combinacoes=("classe", "size"), vence=("classe", lambda s: int((s == "vence").sum())),
        perde=("classe", lambda s: int((s == "perde").sum()))).reset_index()

    def tab_dif(etapa, ref):
        t = ag[(ag["etapa"] == etapa) & (ag["referencia"] == ref)].copy()
        t["id"] = t.apply(lambda r: f"{'Ridge' if r['modelo'] == 'ridge' else 'Árvore'} b{r['bloco']}", axis=1)
        t["txt"] = t.apply(lambda r: ic_txt(r["dif"], r["lo"], r["hi"]) + (" ✱" if r["classe"] != "indeterminado" else ""), axis=1)
        return md(t.pivot_table(index="id", columns="K", values="txt", aggfunc="first").reset_index())

    def tab_imp(etapa, mod):
        t = imp[(imp["etapa"] == etapa) & (imp["modelo"] == mod) & (imp["periodo"] == "agrupado")].copy()
        t["txt"] = t.apply(lambda r: ic_txt(r["valor"], r["lo"], r["hi"]) + (" ✱" if r["classe"] != "indeterminado" else ""), axis=1)
        return md(t.pivot_table(index="comparacao", columns="K", values="txt", aggfunc="first", sort=False).reset_index())

    txt = ["# Etapa 2 — poder do instrumento (bootstrap agrupado, K variável, importância)", "",
           f"Cenário B; testes {ANOS[0]}–{ANOS[-1]} (2025 bloqueado). {BS.N_BOOT} reamostragens de ESCOLAS",
           "com todos os anos de teste de cada escola; Recall@K calculado dentro do ano, agrupado = média",
           "das 4 transições. IC 95% por percentis. ✱ = intervalo exclui zero.", "",
           "## Tamanho", "", md(pd.DataFrame(tam)), "",
           "## 1. Largura mediana do IC 95% de uma célula (modelos do Cenário B)", "", md(resumo), "",
           "## 2. Em qual K alguma diferença agrupada exclui zero", "", md(quando), ""]
    for etapa in ("AF", "EM"):
        for ref in ["B1R_lag", "bloco 1", "bloco 2", "bloco 3", "B2", "B1R"]:
            txt += [f"### {etapa} — modelo − {ref} (agrupado)", "", tab_dif(etapa, ref), ""]
    txt += ["## 3. Importância por bloco com intervalo (modelo do bloco 4, agrupado)", ""]
    for etapa in ("AF", "EM"):
        for mod in W.MODELOS:
            txt += [f"### {etapa} — {mod}", "", tab_imp(etapa, mod), ""]
    (SAIDA / "02c_poder.md").write_text("\n".join(txt), encoding="utf-8")
    print("\n".join(txt))


if __name__ == "__main__":
    main()
