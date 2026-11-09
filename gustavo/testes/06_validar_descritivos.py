# -*- coding: utf-8 -*-
"""
06 — Confere os números gerados para os notebooks (N1–N4, 2026-11-03) contra
o que já estava registrado, por fontes independentes sempre que possível.

  A. funil_recorte.csv (analises/04)
       RR × abandono-escolar/docs/inventario_indicadores.csv (2019–2025) e
       × saida/relatorios/diagnostico_bruto.txt (2007–2025); com a etapa em t
       e universo × abandono-escolar/docs/desfechos_cobertura.csv; somas ×
       universo da Etapa 1 e painel da Etapa 2 em sintese_numeros.csv; sem a
       etapa em t × n_sem_t do 01_baselines.csv; encaixe dos degraus e
       ausência estrutural vazia (nunca 0).
  B. desfecho_por_ano.csv (analises/05)
       2019–2025 × abandono-escolar/docs/desfechos_distribuicao.csv (na casa
       decimal registrada); 2007–2025 × "abandono médio" do sintese_numeros.
  C. cobertura_painel.csv (analises/05)
       linhas do painel × painel da Etapa 2; IED vazio em 2019–2020 e presente
       a partir de 2021 (P019); HAD sem contagem.
  D. 01_baselines.csv e sintese_numeros.csv (N4)
       diferenças = diferença dos níveis; contagens da Etapa 1 com 2025
       inalteradas; contagens sem 2025 batem com as linhas até 2024.

Saída: gustavo/saida/relatorios/validacao_descritivos.txt
Uso:   python analises/04_funil_recorte.py && python analises/05_descritivo_por_ano.py
       && python avaliacao/01_baselines.py && python avaliacao/sintese_numeros.py
       && python testes/06_validar_descritivos.py
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

GUSTAVO = Path(__file__).resolve().parent.parent
REL = GUSTAVO / "saida" / "relatorios"
AV = GUSTAVO / "saida" / "avaliacao"
DOCS = GUSTAVO.parent / "abandono-escolar" / "docs"
REPORT = REL / "validacao_descritivos.txt"

# Etapa 1 com 2024→2025, como registrada antes de 2026-11-03 (sintese_numeros.csv)
ETAPA1_REGISTRADA = {
    "AF: transições avaliadas": "17 (2009–2025)", "AF: anos com MAE B1 < MAE B0": "11 de 17",
    "AF: anos com R² B1 > 0": "1 de 17", "AF: anos com B1R Recall@10% > aleatório": "17 de 17",
    "AF: anos com B1R Recall@20% > aleatório": "17 de 17",
    "EM: transições avaliadas": "17 (2009–2025)", "EM: anos com MAE B1 < MAE B0": "6 de 17",
    "EM: anos com R² B1 > 0": "1 de 17", "EM: anos com B1R Recall@10% > aleatório": "15 de 17",
    "EM: anos com B1R Recall@20% > aleatório": "16 de 17",
}
ETAPA_COL = {"AF": "AF", "EM": "EM"}

log, cont = [], {"ok": 0, "fail": 0}


def ok(m):
    cont["ok"] += 1; log.append(f"  ✅ {m}")


def fail(m):
    cont["fail"] += 1; log.append(f"  ❌ {m}")


def check(cond, m):
    (ok if cond else fail)(m)


def perto(v, reg, casas):
    return abs(float(v) - float(reg)) <= 0.5 * 10 ** -casas + 1e-9


fu = pd.read_csv(REL / "funil_recorte.csv")
fu["n"] = fu["n"].astype("Int64")
d = pd.read_csv(REL / "desfecho_por_ano.csv")
cob = pd.read_csv(REL / "cobertura_painel.csv")
e1 = pd.read_csv(AV / "01_baselines.csv")
sn = pd.read_csv(AV / "sintese_numeros.csv")
inv = pd.read_csv(DOCS / "inventario_indicadores.csv")
inv = inv[(inv["tipo"] == "tx_rend") & (inv["nivel"] == "escolas")].set_index("ano")
cobert = pd.read_csv(DOCS / "desfechos_cobertura.csv").set_index("ANO")
dist = pd.read_csv(DOCS / "desfechos_distribuicao.csv")


def degrau(etapa, ordem):
    return fu[(fu["etapa"] == etapa) & (fu["ordem"] == ordem)].set_index("ano")["n"]


def sn_valor(grupo, item):
    v = sn[(sn["grupo"] == grupo) & (sn["item"] == item)]["valor"]
    return v.iloc[0] if len(v) == 1 else None


# ---------------------------------------------------------------- A. funil
log.append("A. Funil de recorte (funil_recorte.csv)")
rr = degrau("AF", 2)
rr_inv = inv["n_linhas_rr"]
check(all(int(rr[a]) == int(rr_inv[a]) for a in rr_inv.index),
      f"RR 2019–2025 = n_linhas_rr do inventário de indicadores ({ {int(k): int(v) for k, v in rr_inv.items()} })")
diag = {int(a): int(n) for a, n in
        re.findall(r"^\s+(\d{4}):\s+(\d+) linhas", (REL / "diagnostico_bruto.txt").read_text(encoding="utf-8"), re.MULTILINE)}
check(len(diag) == 19 and all(int(rr[a]) == n for a, n in diag.items()),
      f"RR 2007–2025 = diagnostico_bruto.txt ({len(diag)} anos)")
check(degrau("AF", 2).equals(degrau("EM", 2)) and degrau("AF", 3).equals(degrau("EM", 3)),
      "degraus 2 e 3 iguais em AF e EM (não dependem da etapa)")
for etapa in ("AF", "EM"):
    c4, c7 = degrau(etapa, 4), degrau(etapa, 7)
    reg4 = cobert[f"com_{etapa}"]
    check(all(int(c4[a]) == int(reg4[a]) for a in reg4.index),
          f"{etapa}: com a etapa em t, 2019–2025 = desfechos_cobertura.com_{etapa}")
    reg7 = cobert[f"com_alvo_{etapa}_t1"].loc[2019:2024]
    check(all(int(c7[a]) == int(reg7[a]) for a in reg7.index),
          f"{etapa}: universo, ANO 2019–2024 = desfechos_cobertura.com_alvo_{etapa}_t1")
    soma7 = int(c7.dropna().sum())
    reg_u = sn_valor("universo Etapa 1", f"{etapa}: escolas-ano (pública + alvo t+1)")
    check(reg_u is not None and soma7 == int(reg_u), f"{etapa}: soma do universo = {soma7} (registrado {reg_u})")
    soma8 = int(degrau(etapa, 8).dropna().sum())
    reg_p = sn_valor("painel Etapa 2", f"{etapa}: escolas-ano (ANO 2019–2024)")
    check(reg_p is not None and soma8 == int(reg_p), f"{etapa}: soma do painel da Etapa 2 = {soma8} (registrado {reg_p})")
    c6 = degrau(etapa, 6)
    st = e1[e1["etapa"] == etapa].set_index("ano_alvo")["n_sem_t"]
    check(all(int(c6[a - 1]) == int(st[a]) for a in st.index),
          f"{etapa}: sem a etapa em t = n_sem_t do 01_baselines.csv ({len(st)} transições)")
    largo = fu[fu["etapa"] == etapa].pivot(index="ano", columns="ordem", values="n")
    cheio = largo.dropna(subset=[2, 3, 4, 5, 6, 7])
    enc = ((cheio[2] >= cheio[3]) & (cheio[3] >= cheio[4]) & (cheio[4] >= cheio[5])).all()
    enc_b = (largo[1].dropna() >= largo[2][largo[1].notna()]).all()
    check(bool(enc and enc_b), f"{etapa}: encaixe Brasil ≥ RR ≥ públicas ≥ com a etapa ≥ com a etapa e alvo")
    check(bool((cheio[7] == cheio[5] + cheio[6]).all()), f"{etapa}: universo = (com a etapa e alvo) + (sem a etapa)")
    vazio1 = sorted(largo.index[largo[1].isna()])
    check(vazio1 == list(range(2007, 2019)), f"{etapa}: Brasil vazio exatamente em 2007–2018 (zips fora desta máquina)")
    check(bool(largo.loc[2025, [5, 6, 7, 8]].isna().all()), f"{etapa}: degraus 5–8 vazios em 2025 (t+1 não publicado)")
    fora = largo.loc[[a for a in largo.index if a not in range(2019, 2025)], 8]
    check(bool(fora.isna().all()), f"{etapa}: painel vazio fora de 2019–2024")
    check(not (fu[fu["etapa"] == etapa]["n"] == 0).any(), f"{etapa}: nenhuma contagem 0 no funil")

# ---------------------------------------------------- B. desfecho por ano
log.append("")
log.append("B. Desfecho por ano (desfecho_por_ano.csv)")
casas = {"media": 2, "mediana": 2, "p75": 1, "p90": 1, "max": 1, "pct_zero": 1}
for _, r in dist.iterrows():
    g = d[(d["ano"] == r["ANO"]) & (d["etapa"] == r["etapa"])]
    if len(g) != 1:
        fail(f"{r['etapa']} {r['ANO']}: {len(g)} linhas"); continue
    g = g.iloc[0]
    difs = [c for c, k in casas.items() if not perto(g[c], r[c], k)]
    check(int(g["n"]) == int(r["n"]) and not difs,
          f"{r['etapa']} {r['ANO']}: n={int(g['n'])}, média {g['media']:.2f}, p90 {g['p90']:.1f}, "
          f"% zeros {g['pct_zero']:.1f} = desfechos_distribuicao" + (f" (difere: {difs})" if difs else ""))
for etapa in ("AF", "EM"):
    s = sn[sn["grupo"] == f"abandono médio {etapa} (públicas com taxa)"]
    erros = []
    for _, r in s.iterrows():
        media, n = re.match(r"([\d.]+) \(n=(\d+)\)", r["valor"]).groups()
        g = d[(d["ano"] == int(r["item"])) & (d["etapa"] == etapa)].iloc[0]
        if not (perto(g["media"], media, 2) and int(g["n"]) == int(n)):
            erros.append(r["item"])
    check(len(s) == 19 and not erros, f"{etapa}: média e n de 2007–2025 = sintese_numeros ({len(s)} anos)"
          + (f"; diferem {erros}" if erros else ""))

# ---------------------------------------------------- C. cobertura do painel
log.append("")
log.append("C. Cobertura do painel (cobertura_painel.csv)")
for etapa in ("AF", "EM"):
    c = cob[cob["etapa"] == etapa]
    n_painel = int(c.drop_duplicates("ano")["n_painel"].sum())
    reg_p = sn_valor("painel Etapa 2", f"{etapa}: escolas-ano (ANO 2019–2024)")
    check(n_painel == int(reg_p), f"{etapa}: linhas do painel = {n_painel} (registrado {reg_p})")
    ied = c[c["indicador"] == "IED (N1 a N5)"].set_index("ano")["n_com"]
    check(int(ied.loc[2019]) == 0 and int(ied.loc[2020]) == 0 and (ied.loc[2021:2024] > 0).all(),
          f"{etapa}: IED vazio em 2019–2020 e presente em 2021–2024 (P019)")
    had = c[c["indicador"] == "HAD"]
    check(had["n_com"].isna().all() and len(had) == 6, f"{etapa}: HAD sem contagem nos 6 anos (não entra no painel)")
    p = c["pct_com"].dropna()
    check(bool(((p >= 0) & (p <= 100)).all()), f"{etapa}: % entre 0 e 100")

# ---------------------------------------------------- D. Etapa 1 (N4)
log.append("")
log.append("D. Etapa 1: diferenças e contagens sem 2025")
for k in ("10", "20"):
    check(np.allclose(e1[f"B1R-B0_Rec@{k}"], e1[f"B1R_Rec@{k}"] - e1[f"B0_Rec@{k}"], atol=1e-12),
          f"B1R-B0_Rec@{k} = B1R_Rec@{k} − B0_Rec@{k}")
check(np.allclose(e1["B1-B0_MAE"], e1["B1_MAE"] - e1["B0_MAE"], atol=1e-12), "B1-B0_MAE = B1_MAE − B0_MAE")
for item, reg in ETAPA1_REGISTRADA.items():
    v = sn_valor("Etapa 1", item)
    check(v == reg, f"com 2025: {item} = {v} (registrado {reg})")
ate = e1[e1["ano_alvo"] <= 2024]
for etapa, g in ate.groupby("etapa"):
    esperado = {
        f"{etapa}: transições avaliadas": f"{len(g)} ({g['ano_alvo'].min()}–{g['ano_alvo'].max()})",
        f"{etapa}: anos com MAE B1 < MAE B0": f"{int((g['B1_MAE'] < g['B0_MAE']).sum())} de {len(g)}",
        f"{etapa}: anos com R² B1 > 0": f"{int((g['B1_R2'] > 0).sum())} de {len(g)}",
    }
    for k in ("10", "20"):
        esperado[f"{etapa}: anos com B1R Recall@{k}% > aleatório"] = \
            f"{int((g[f'B1R_Rec@{k}'] > g[f'B0_Rec@{k}']).sum())} de {len(g)}"
    for item, esp in esperado.items():
        v = sn_valor("Etapa 1 até 2024 (sem 2024→2025, D7)", item)
        check(v == esp, f"sem 2025: {item} = {v}")
check(int(ate["ano_alvo"].max()) == 2024 and len(ate) == 32, "sem 2025: 16 transições por etapa (2009–2024)")
GRUPO_POS = "Etapa 1: posição de 2024→2025 (1ª = mais favorável à persistência)"
for etapa, g in e1.groupby("etapa"):
    g = g.set_index("ano_alvo")
    for nome, col, maior_melhor in (("R² do B1", "B1_R2", True), ("MAE do B1 − MAE do B0", "B1-B0_MAE", False),
                                    ("Recall@10% do B1R", "B1R_Rec@10", True), ("Recall@20% do B1R", "B1R_Rec@20", True)):
        v = g[col]
        melhores = int((v > v[2025]).sum()) if maior_melhor else int((v < v[2025]).sum())
        reg = sn_valor(GRUPO_POS, f"{etapa}: {nome}")
        check(reg is not None and reg.startswith(f"{melhores + 1}ª de {len(g)}"),
              f"posição de 2024→2025, {etapa} {nome}: {reg}")
r2_com = sn_valor("Etapa 1", "AF: anos com R² B1 > 0")
r2_sem = sn_valor("Etapa 1 até 2024 (sem 2024→2025, D7)", "AF: anos com R² B1 > 0")
check(r2_com == "1 de 17" and r2_sem == "0 de 16" and sn_valor(GRUPO_POS, "AF: R² do B1").startswith("1ª"),
      "AF: o único R² do B1 > 0 é o de 2024→2025 (1 de 17 com, 0 de 16 sem, e 1ª posição)")

log.append("")
log.append(f"RESUMO: {cont['ok']} OK, {cont['fail']} falhas")
txt = "\n".join(log)
print(txt)
REPORT.write_text(txt, encoding="utf-8")
sys.exit(1 if cont["fail"] else 0)
