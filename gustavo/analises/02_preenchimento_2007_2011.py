# -*- coding: utf-8 -*-
"""
ANÁLISE 02 — Como tratar IDA, IDP e IIE em 2007-2011 (itens não coletados).

Contexto: 5 dos 18 itens (despensa, refeitório, secretaria, pátio coberto e pátio
descoberto) só existem a partir de 2012. Logo IDA (3 de 5 itens) e IDP (2 de 5)
não podem ser calculados como no artigo em 2007-2011, e o IIE depende das 4
dimensões. Esta análise compara três formas de lidar com isso e mede o custo da
escolhida (decisão de 14/10/2026: usar os itens disponíveis em cada ano).

Opções para o IIE (todas com z por ano; IIE = média dos z das dimensões,
re-padronizada por ano — só para comparar as opções em escala igual):
  A. só IIB + IEP em todos os anos          (descarta IDA e IDP)
  B. itens disponíveis em cada ano          (ESCOLHIDA: IDA 2 itens e IDP 3 itens até 2011)
  C. núcleo fixo: os 13 itens de todos os anos em todos os anos (IDA 2, IDP 3 sempre)

Não usa o desfecho. Entrada: gustavo/saida/base_atual.parquet (18 itens + ids) e,
para os pesos reais, indices_infra_parametros.json.
Saída:  gustavo/saida/relatorios/preenchimento_2007_2011.txt
Uso:    python analises/02_preenchimento_2007_2011.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

GUSTAVO = Path(__file__).resolve().parent.parent
P_BASE = GUSTAVO / "saida" / "base_atual.parquet"
P_JSON = GUSTAVO / "saida" / "relatorios" / "indices_infra_parametros.json"
REPORT = GUSTAVO / "saida" / "relatorios" / "preenchimento_2007_2011.txt"

DIMS = {
    "IIB": ["IIB_agua_potavel", "IIB_energia_rede", "IIB_coleta_lixo", "IIB_banheiro"],
    "IDA": ["IDA_despensa", "IDA_refeitorio", "IDA_sala_diretoria", "IDA_sala_professor", "IDA_secretaria"],
    "IDP": ["IDP_biblioteca", "IDP_lab_informatica", "IDP_patio_coberto", "IDP_patio_descoberto", "IDP_quadra_esportes"],
    "IEP": ["IEP_computador", "IEP_impressora", "IEP_projetor", "IEP_internet"],
}
ITENS = [i for l in DIMS.values() for i in l]
NUCLEO = {"IDA": ["IDA_sala_diretoria", "IDA_sala_professor"],
          "IDP": ["IDP_biblioteca", "IDP_lab_informatica", "IDP_quadra_esportes"]}

if not P_BASE.exists():
    print(f"[ERRO] não achei {P_BASE} — rode o pipeline (99_pipeline.py)")
    sys.exit(1)
b = pd.read_parquet(P_BASE)
ano = b["ANO"].astype(int).to_numpy()
anos = sorted(set(ano.tolist()))
F = b[ITENS].astype("float64")
CO = b["CO_ENTIDADE"].astype(str).to_numpy()
chave = pd.Series(np.arange(len(b)), index=pd.Index([f"{c}_{a}" for c, a in zip(CO, ano)]))

L = []


def sec(t):
    L.extend(["", "=" * 78, t, "=" * 78])


def zano(v):
    v = np.asarray(v, float)
    out = np.full(len(v), np.nan)
    for a in anos:
        m = ano == a
        x = v[m]
        ok = ~np.isnan(x)
        if ok.sum() >= 30 and x[ok].std() > 0:
            out[m] = (x - x[ok].mean()) / x[ok].std()
    return out


def soma(cols):
    X = F[cols].to_numpy()
    return np.where(np.isnan(X).any(axis=1), np.nan, X.sum(axis=1))


def disponiveis(lista):
    """Fração dos itens disponíveis em cada ano (NaN se faltar algum item do ano) e nº de itens por ano."""
    prop = np.full(len(b), np.nan)
    nitens = {}
    for a in anos:
        m = ano == a
        av = [i for i in lista if F.loc[m, i].notna().any()]
        nitens[a] = len(av)
        X = F.loc[m, av].to_numpy()
        prop[m] = np.where(np.isnan(X).any(axis=1), np.nan, X.mean(axis=1))
    return prop, nitens


def persist(v, a):
    cur = np.flatnonzero(ano == a)
    k = [f"{CO[i]}_{a + 1}" for i in cur]
    ok = np.array([x in chave.index for x in k])
    x = v[cur[ok]]
    y = v[chave.loc[[kk for kk, o in zip(k, ok) if o]].to_numpy()]
    m = ~(np.isnan(x) | np.isnan(y))
    return float(pd.Series(x[m]).rank().corr(pd.Series(y[m]).rank()))


def delta_dp(v, a):
    """Δ médio (a+1 menos a) da mesma escola, em desvios-padrão entre escolas do ano a."""
    cur = np.flatnonzero(ano == a + 1)
    k = [f"{CO[i]}_{a}" for i in cur]
    ok = np.array([x in chave.index for x in k])
    d = v[cur[ok]] - v[chave.loc[[kk for kk, o in zip(k, ok) if o]].to_numpy()]
    return float(np.nanmean(d) / np.nanstd(v[ano == a]))


def spear_ano(x, y, a):
    m = (ano == a)
    return float(pd.Series(x[m]).rank().corr(pd.Series(y[m]).rank()))


# ----- séries
s_iib, s_iep = soma(DIMS["IIB"]), soma(DIMS["IEP"])
z_iib, z_iep = zano(s_iib), zano(s_iep)
p_ida, n_ida = disponiveis(DIMS["IDA"])
p_idp, n_idp = disponiveis(DIMS["IDP"])
p_ida_n, _ = disponiveis(NUCLEO["IDA"])
p_idp_n, _ = disponiveis(NUCLEO["IDP"])
z_ida_b, z_idp_b = zano(p_ida), zano(p_idp)          # B: itens disponíveis
z_ida_c, z_idp_c = zano(p_ida_n), zano(p_idp_n)      # C: núcleo fixo
completo_ida = np.where(ano >= 2012, p_ida, np.nan)
completo_idp = np.where(ano >= 2012, p_idp, np.nan)


def rz(M):
    return zano(np.mean(M, axis=1))


iie_a = rz(np.column_stack([z_iib, z_iep]))
iie_b = rz(np.column_stack([z_iib, z_ida_b, z_idp_b, z_iep]))
iie_c = rz(np.column_stack([z_iib, z_ida_c, z_idp_c, z_iep]))
iie_full = np.where(ano >= 2012, iie_b, np.nan)       # em 2012+, B = IIE com os itens do artigo

L.append("PREENCHIMENTO DE IDA, IDP E IIE EM 2007-2011")
L.append("=" * 78)
L.append(f"Base: {P_BASE.name} ({len(b)} linhas, {anos[0]}-{anos[-1]})")

sec("1. ITENS DISPONÍVEIS POR ANO")
L.append("  Itens existentes em todos os anos: " + ", ".join(
    i for i in ITENS if all(F.loc[ano == a, i].notna().any() for a in anos)))
L.append("  Itens só de 2012 em diante:        " + ", ".join(
    i for i in ITENS if not any(F.loc[ano == a, i].notna().any() for a in range(2007, 2012))))
L.append(f"  Itens usados por ano — IDA: 2007-2011 = {n_ida[2007]} de 5; 2012+ = {n_ida[2012]} de 5   "
         f"IDP: 2007-2011 = {n_idp[2007]} de 5; 2012+ = {n_idp[2012]} de 5   IIB e IEP: 4 de 4 sempre")

sec("2. PERSISTÊNCIA DA POSIÇÃO DA MESMA ESCOLA EM VOLTA DE 2011→2012 (IIE, Spearman t→t+1)")
L.append("  A = só IIB+IEP | B = itens disponíveis (escolhida) | C = núcleo fixo | IIE_zano = coluna gravada pelo 05")
iie_05 = b["IIE_zano"].astype("float64").to_numpy()
L.append(f"  {'transição':>10}{'A':>8}{'B':>8}{'C':>8}{'IIE_zano':>10}")
for a in range(2009, 2015):
    L.append(f"  {a}→{a + 1:>4}{persist(iie_a, a):>8.3f}{persist(iie_b, a):>8.3f}{persist(iie_c, a):>8.3f}"
             f"{persist(iie_05, a):>10.3f}" + ("   <- virada de itens" if a == 2011 else ""))
L.append("  Δ médio da mesma escola (dp):")
L.append(f"  {'transição':>10}{'A':>8}{'B':>8}{'C':>8}")
for a in range(2009, 2015):
    L.append(f"  {a}→{a + 1:>4}{delta_dp(iie_a, a):>+8.3f}{delta_dp(iie_b, a):>+8.3f}{delta_dp(iie_c, a):>+8.3f}")

sec("3. DIMENSÕES IDA E IDP: itens disponíveis (B) x núcleo fixo (C)")
L.append(f"  {'dim':>4}{'transição':>12}{'B':>8}{'C':>8}")
for nome, zb, zc in (("IDA", z_ida_b, z_ida_c), ("IDP", z_idp_b, z_idp_c)):
    for a in (2009, 2010, 2011, 2012, 2013):
        L.append(f"  {nome:>4}{a:>7}→{a + 1}{persist(zb, a):>8.3f}{persist(zc, a):>8.3f}"
                 + ("   <- virada de itens" if a == 2011 else ""))

sec("4. O QUE O prop TERIA FEITO NO NÍVEL (fração dos itens disponíveis, sem z)")
for nome, pv, pn in (("IDA", p_ida, p_ida_n), ("IDP", p_idp, p_idp_n)):
    L.append(f"  {nome}: Δ médio 2011→2012 da mesma escola = {delta_dp(pv, 2011):+.3f} dp com itens "
             f"disponíveis; {delta_dp(pn, 2011):+.3f} dp com núcleo fixo")
L.append("  (com z por ano o nível comum é removido; o prop deixaria esse salto na série)")

sec("5. RESOLUÇÃO DAS DIMENSÕES PARCIAIS")
for nome, v, a in (("IDA com 2 itens (2011)", p_ida, 2011), ("IDP com 3 itens (2011)", p_idp, 2011),
                   ("IDA com 5 itens (2019)", p_ida, 2019), ("IDP com 5 itens (2019)", p_idp, 2019)):
    s = pd.Series(v[ano == a]).dropna()
    L.append(f"  {nome}: {s.nunique()} valores distintos; maior grupo empatado = "
             f"{s.value_counts(normalize=True).iloc[0] * 100:.0f}% das escolas")

sec("6. QUANTO FICA IMPERFEITO: versão parcial x completa, medido em 2012-2025")
for nome, parcial, completo in (("IDA (2 itens x 5 itens)", p_ida_n, completo_ida),
                                ("IDP (3 itens x 5 itens)", p_idp_n, completo_idp)):
    r = [spear_ano(parcial, completo, a) for a in range(2012, 2026)]
    L.append(f"  {nome}: Spearman dentro do ano — mínimo {min(r):.3f}, média {np.mean(r):.3f}")
r = [spear_ano(iie_c, iie_full, a) for a in range(2012, 2026)]
L.append(f"  IIE (núcleo x completo): Spearman dentro do ano — mínimo {min(r):.3f}, média {np.mean(r):.3f}")
r = [spear_ano(iie_a, iie_full, a) for a in range(2012, 2026)]
L.append(f"  IIE (só IIB+IEP x completo): mínimo {min(r):.3f}, média {np.mean(r):.3f}")

sec("7. PESOS REAIS DO PC1 (normalizados para somar 1) COM A OPÇÃO ESCOLHIDA")
if P_JSON.exists():
    par = json.loads(P_JSON.read_text(encoding="utf-8"))
    rows = []
    for a in anos:
        p = par["pca_por_ano"][str(a)]
        w = np.array(list(p["pesos_pc1"].values()))
        rows.append((a, w / w.sum(), p["variancia_explicada"][0]))
    L.append(f"  {'ano':>5}   {'IIB':>6}{'IDA':>6}{'IDP':>6}{'IEP':>6}   var.PC1")
    for a, w, v in rows:
        L.append(f"  {a:>5}   " + "".join(f"{x:>6.3f}" for x in w) + f"   {v * 100:.1f}%")
    W = np.array([r_[1] for r_ in rows])
    L.append("  mín–máx por dimensão: " + "; ".join(f"{d} {W[:, k].min():.3f}–{W[:, k].max():.3f}"
                                                  for k, d in enumerate(DIMS)))
else:
    L.append("  (sem indices_infra_parametros.json — rode o 05)")

txt = "\n".join(L)
print(txt)
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(txt, encoding="utf-8")
print(f"\n>>> Relatório: {REPORT}")
