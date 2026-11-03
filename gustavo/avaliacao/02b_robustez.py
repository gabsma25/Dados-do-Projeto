# -*- coding: utf-8 -*-
"""
02b — Correções de leitura da Etapa 2 (pedidas em 2026-11-02).

  1. Padrão temporal contra o B1R: o modelo vence nos anos de ruptura
     (2021, 2022) e perde nos estáveis (2023, 2024)? Verificado em AF e EM,
     Recall@10% e @20%, todos os blocos e modelos do Cenário B.
  2. B1R_lag (ordena pelo abandono de t−1) é o BASELINE PRINCIPAL; o B1R
     (abandono de t, publicado só depois do fim de t+1) é LIMITE SUPERIOR
     OTIMISTA. Decisões refeitas contra o B1R_lag.
  3. Bootstrap de escolas (bootstrap.py): intervalo para cada célula e para
     cada diferença. Decisão cuja diferença cruza zero vira "indeterminado".

Regras (fixadas antes de rodar):
  * superação de baseline: pontual = Rec@K maior em >= 3 de 4 anos;
    robusta = intervalo da diferença > 0 em >= 3 de 4 anos.
    "supera" = pontual e robusta, nas duas métricas; "indeterminado" =
    pontual sem robusta; "não supera" = sem pontual.
  * adoção de bloco: a mesma regra, aplicada a (bloco k) − (bloco k−1).

Entrada: base_atual + base oficial (via painel.py); 2025 continua bloqueado.
Saída:   gustavo/saida/avaliacao/02b_celulas.csv, 02b_diferencas.csv,
         02b_decisoes.csv, 02b_padrao_temporal.csv, 02b_robustez.md
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
RUPTURA, ESTAVEIS = (2021, 2022), (2023, 2024)
MAIORIA = len(ANOS) // 2 + 1
REFS = {"B1R_lag": ("-", "B1R_lag", 0), "B1R": ("-", "B1R", 0), "B2": ("-", "B2", 0)}
METS = list(BS.FRACOES)


def nome(pid):
    cen, mod, k = pid
    if cen == "-":
        return mod
    return f"{cen}/{'Ridge' if mod == 'ridge' else 'Árvore'} b{k}"


def md(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(out)


def main():
    atual, oficial = pd.read_parquet(P.P_ATUAL), pd.read_parquet(P.P_OFICIAL)
    W.N_PERMUT = 1                      # importância não é usada aqui
    rng = np.random.default_rng(BS.SEMENTE_BOOT)
    cel, dif, pont = [], [], []
    for etapa in ("AF", "EM"):
        res, _, prev = W.rodar_etapa(P.montar(etapa, atual, oficial), etapa, ANOS)
        pont.append(res)
        for c in prev:
            ano, d = c["ano_alvo"], BS.distribuicoes_ano(c, rng)
            ests = {(pid, m): W.metricas(c["y"], p)[m] for pid, p in c["p"].items() for m in METS}
            for (pid, m), v in d.items():
                lo, hi = BS.intervalo(v)
                cel.append({"etapa": etapa, "ano_alvo": ano, "id": nome(pid), "cenario": pid[0],
                            "modelo": pid[1], "bloco": pid[2], "metrica": m,
                            "valor": ests[(pid, m)], "lo": lo, "hi": hi})
            for pid in c["p"]:
                if pid[0] == "-":
                    continue
                comps = {r: REFS[r] for r in REFS}
                if pid[2] > 1:
                    comps[f"bloco {pid[2] - 1}"] = (pid[0], pid[1], pid[2] - 1)
                for ref, rid in comps.items():
                    for m in METS:
                        delta = d[(pid, m)] - d[(rid, m)]
                        lo, hi = BS.intervalo(delta)
                        dif.append({"etapa": etapa, "ano_alvo": ano, "cenario": pid[0],
                                    "modelo": pid[1], "bloco": pid[2], "referencia": ref,
                                    "metrica": m, "dif": ests[(pid, m)] - ests[(rid, m)],
                                    "lo": lo, "hi": hi, "classe": BS.classe(lo, hi)})
    cel, dif = pd.DataFrame(cel), pd.DataFrame(dif)

    # conferência: estimativas pontuais iguais às do 02_walkforward.csv
    p02 = pd.read_csv(SAIDA / "02_walkforward.csv")
    pt = pd.concat(pont, ignore_index=True)
    m = pt.merge(p02, on=["etapa", "ano_alvo", "cenario", "modelo", "bloco"], suffixes=("", "_02"))
    assert len(m) == len(p02) and np.allclose(m[["Rec@10", "Rec@20"]], m[["Rec@10_02", "Rec@20_02"]]), \
        "estimativas pontuais divergem do 02_walkforward.csv"

    # decisões
    dec = []
    for (cen, etapa, mod, k, ref), g in dif.groupby(["cenario", "etapa", "modelo", "bloco", "referencia"]):
        lin = {"cenario": cen, "etapa": etapa, "modelo": mod, "bloco": k, "referencia": ref}
        ok_p, ok_r = True, True
        for mt in METS:
            gm = g[g["metrica"] == mt]
            npont, nrob = int((gm["dif"] > 0).sum()), int((gm["classe"] == "vence").sum())
            nperde = int((gm["classe"] == "perde").sum())
            lin[f"{mt} pontual"] = f"{npont}/{len(ANOS)}"
            lin[f"{mt} IC>0"] = f"{nrob}/{len(ANOS)}"
            lin[f"{mt} IC<0"] = f"{nperde}/{len(ANOS)}"
            ok_p &= npont >= MAIORIA
            ok_r &= nrob >= MAIORIA
        lin["decisao"] = ("supera/adota" if ok_p and ok_r else "indeterminado" if ok_p else "não")
        dec.append(lin)
    dec = pd.DataFrame(dec)

    # padrão temporal contra o B1R (Cenário B)
    pad = []
    sub = dif[(dif["cenario"] == "B") & (dif["referencia"] == "B1R")]
    for (etapa, mod, k, mt), g in sub.groupby(["etapa", "modelo", "bloco", "metrica"]):
        g = g.set_index("ano_alvo")
        sinal = "".join("M" if g.loc[a, "dif"] > 0 else ("B" if g.loc[a, "dif"] < 0 else "=") for a in ANOS)
        rob = "".join({"vence": "M", "perde": "B", "indeterminado": "?"}[g.loc[a, "classe"]] for a in ANOS)
        pad.append({"etapa": etapa, "modelo": mod, "bloco": k, "metrica": mt,
                    "pontual 21-22-23-24": sinal, "bootstrap 21-22-23-24": rob,
                    "padrao_exato": sinal == "MMBB",
                    "ruptura>estavel": (sinal[:2].count("M") > sinal[2:].count("M"))})
    pad = pd.DataFrame(pad)

    for nomearq, df in (("02b_celulas", cel), ("02b_diferencas", dif),
                        ("02b_decisoes", dec), ("02b_padrao_temporal", pad)):
        df.to_csv(SAIDA / f"{nomearq}.csv", index=False, encoding="utf-8")

    # relatório
    def tab_celulas(cen, mt):
        t = cel[(cel["cenario"].isin(["-", cen])) & (cel["metrica"] == mt) & (cel["modelo"] != "B0")].copy()
        t["txt"] = t.apply(lambda r: f"{r['valor']:.2f} [{r['lo']:.2f}, {r['hi']:.2f}]", axis=1)
        t["col"] = t["etapa"] + " " + t["ano_alvo"].astype(str)
        pv = t.pivot_table(index="id", columns="col", values="txt", aggfunc="first", sort=False)
        return md(pv[[f"{e} {a}" for e in ("AF", "EM") for a in ANOS]].reset_index())

    largura = cel[cel["cenario"] == "B"].assign(larg=lambda d: d["hi"] - d["lo"]) \
        .groupby(["etapa", "metrica"])["larg"].median().round(2).reset_index()
    txt = ["# Etapa 2 — correções de leitura (bootstrap, B1R_lag, padrão temporal)", "",
           f"Bootstrap de escolas: {BS.N_BOOT} reamostragens pareadas por ano; intervalo 95% (percentis).",
           "B1R_lag = baseline principal (abandono de t−1, disponível na decisão).",
           "B1R = limite superior otimista (abandono de t, publicado depois do fim de t+1).",
           "2025 não avaliado (teste bloqueado, D7).", "",
           "## Largura mediana do intervalo 95% (Cenário B, modelos)", "", md(largura), ""]
    for mt in METS:
        txt += [f"## Cenário B — {mt} com intervalo 95%", "", tab_celulas("B", mt), ""]
    d_b = dec[dec["cenario"] == "B"].sort_values(["referencia", "etapa", "modelo", "bloco"])
    txt += ["## Decisões — Cenário B", "", md(d_b), "",
            "## Padrão temporal contra o B1R (M = modelo vence, B = B1R vence, ? = intervalo cruza zero)", "",
            md(pad), "",
            "## Decisões — Cenário A (referência)", "",
            md(dec[dec["cenario"] == "A"].sort_values(["referencia", "etapa", "modelo", "bloco"])), ""]
    (SAIDA / "02b_robustez.md").write_text("\n".join(txt), encoding="utf-8")
    print("\n".join(txt))


if __name__ == "__main__":
    main()
