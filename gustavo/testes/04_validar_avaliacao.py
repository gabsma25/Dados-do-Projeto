# -*- coding: utf-8 -*-
"""
04 — Valida o instrumento de avaliação (avaliacao/metricas.py e baselines.py).

  A. métricas de regressão contra contas feitas à mão
  B. Recall@K: casos à mão, desempate exato (enumeração de todas as ordens),
     previsão constante = K/n, previsão perfeita = 1
  C. baselines: B1 = coluna de abandono em t; fallback só onde falta y_t;
     B0 sem vazamento (perturbar o ano avaliado e os seguintes não muda o B0)
  D. universo: só pública, só com alvo, chave única por ano
  E. conferência cruzada: MAE do B1 (pares completos) contra
     abandono-escolar/docs/desfechos_persistencia.csv (código independente)
  F. B2: mediana do treino por estrato, conta à mão
  G. painel da Etapa 2: lags conferidos linha a linha; Cenário B sem nada de
     rendimento de t; nenhuma composição completa (trio de rendimento, IED N6/ALTO)
  H. walk-forward sem vazamento: perturbar alvo e preditores do ano de teste e
     dos seguintes não muda o modelo ajustado

Saída: gustavo/saida/relatorios/validacao_avaliacao.txt
Uso:   python testes/04_validar_avaliacao.py
"""
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

GUSTAVO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GUSTAVO / "avaliacao"))
import baselines as B  # noqa: E402
import metricas as M  # noqa: E402
import painel as P  # noqa: E402
import walkforward as W  # noqa: E402

P_BASE = GUSTAVO / "saida" / "base_atual.parquet"
P_REF = GUSTAVO.parent / "abandono-escolar" / "docs" / "desfechos_persistencia.csv"
REPORT = GUSTAVO / "saida" / "relatorios" / "validacao_avaliacao.txt"
TOL = 1e-12

log, cont = [], {"ok": 0, "warn": 0, "fail": 0}


def secao(t):
    log.extend(["", "=" * 78, t, "=" * 78])


def ok(m):
    cont["ok"] += 1; log.append(f"  ✅ {m}")


def warn(m):
    cont["warn"] += 1; log.append(f"  ⚠️  {m}")


def fail(m):
    cont["fail"] += 1; log.append(f"  ❌ {m}")


def check(cond, msg_ok, msg_fail):
    ok(msg_ok) if cond else fail(msg_fail)


def recall_enumerado(y, yhat, k):
    """Média exata sobre todas as ordens de desempate (força bruta)."""
    n = len(y)
    tot, cnt = 0.0, 0
    for p1 in itertools.permutations(range(n)):
        top_hat = set(sorted(range(n), key=lambda i: (-yhat[i], p1.index(i)))[:k])
        for p2 in itertools.permutations(range(n)):
            top_y = set(sorted(range(n), key=lambda i: (-y[i], p2.index(i)))[:k])
            tot += len(top_hat & top_y); cnt += 1
    return tot / cnt / k


# ------------------------------------------------------------------
secao("A. Métricas de regressão (contas à mão)")
# ------------------------------------------------------------------
y, p = [0, 2, 4], [1, 2, 7]
check(abs(M.mae(y, p) - 4 / 3) < TOL, "MAE([0,2,4],[1,2,7]) = 4/3", f"MAE = {M.mae(y, p)}")
check(abs(M.rmse(y, p) - np.sqrt(10 / 3)) < TOL, "RMSE = sqrt(10/3)", f"RMSE = {M.rmse(y, p)}")
check(abs(M.r2(y, p) - (1 - 10 / 8)) < TOL, "R² = 1 - 10/8 = -0,25 (negativo permitido)", f"R² = {M.r2(y, p)}")
check(abs(M.r2(y, [2, 2, 2])) < TOL, "R² da média do próprio conjunto = 0", "R² da média ≠ 0")
check(M.k_de_fracao(233, .10) == 23 and M.k_de_fracao(165, .10) == 17 and M.k_de_fracao(5, .10) == 1,
      "K = round(f·n), mínimo 1 (233→23, 165→17 [16,5↑], 5→1)", "K incorreto")

# ------------------------------------------------------------------
secao("B. Recall@K")
# ------------------------------------------------------------------
check(M.recall_at_k([5, 4, 3, 2, 1], [9, 8, 1, 1, 1], 2) == 1.0, "ordem perfeita no topo → 1", "perfeito ≠ 1")
check(M.recall_at_k([5, 4, 3, 2, 1], [1, 1, 1, 8, 9], 2) == 0.0, "ordem invertida → 0", "invertido ≠ 0")
check(abs(M.recall_at_k([5, 4, 3, 2, 1], [9, 1, 8, 1, 1], 2) - 0.5) < TOL, "1 de 2 acertos → 0,5", "caso 0,5 falhou")
rng = np.random.default_rng(0)
yy = rng.integers(0, 5, 40).astype(float)
for k in (1, 4, 8, 20):
    check(abs(M.recall_at_k(yy, np.full(40, 3.3), k) - k / 40) < TOL,
          f"previsão constante → K/n (k={k})", f"constante ≠ K/n (k={k})")
pior = 0.0
for _ in range(25):
    n = 5
    y5 = rng.integers(0, 3, n).astype(float)
    p5 = rng.integers(0, 3, n).astype(float)
    k = int(rng.integers(1, n + 1))
    pior = max(pior, abs(M.recall_at_k(y5, p5, k) - recall_enumerado(y5, p5, k)))
check(pior < 1e-12, f"empates: valor esperado = média sobre todas as ordens (25 casos, erro máx {pior:.1e})",
      f"empates divergem da enumeração ({pior:.2e})")

# ------------------------------------------------------------------
secao("C. Baselines")
# ------------------------------------------------------------------
base = pd.read_parquet(P_BASE)
for etapa, col in B.ETAPAS.items():
    u = B.universo(base, etapa)
    for ano in (2015, 2021, 2025):
        te = u[u["ANO_ALVO"] == ano]
        mu = B.b0_media(u[u["ANO_ALVO"] < ano])
        p1 = B.b1_persistencia(te, mu)
        tem = te["y_t"].notna().to_numpy()
        check(np.array_equal(p1[tem], te["y_t"].to_numpy()[tem]) and np.all(p1[~tem] == mu),
              f"{etapa} {ano}: B1 = y_t; B0 do treino só nas {int((~tem).sum())} sem y_t",
              f"{etapa} {ano}: B1 incorreto")
    # vazamento: bagunçar alvo do ano avaliado e dos seguintes não muda B0
    a = 2016
    u2 = u.copy()
    fut = u2["ANO_ALVO"] >= a
    u2.loc[fut, "y_t1"] = rng.uniform(0, 100, int(fut.sum()))
    check(B.avaliar_ano(u, a)["media_treino"] == B.avaliar_ano(u2, a)["media_treino"],
          f"{etapa}: B0 de {a} não muda com alvos de {a}+ perturbados (sem vazamento)",
          f"{etapa}: B0 usa dado do ano avaliado ou futuro")

# ------------------------------------------------------------------
secao("D. Universo")
# ------------------------------------------------------------------
for etapa, col in B.ETAPAS.items():
    u = B.universo(base, etapa)
    m = base.merge(u[["ANO", "CO_ENTIDADE"]], on=["ANO", "CO_ENTIDADE"], how="inner", validate="1:1")
    check((m["REDE_PUBLICA"].astype("Int8") == 1).all(), f"{etapa}: só escolas públicas", f"{etapa}: entrou privada")
    check(u["y_t1"].notna().all(), f"{etapa}: todas com alvo (oferecem a etapa em t+1)", f"{etapa}: alvo nulo")
    check(not u.duplicated(["ANO", "CO_ENTIDADE"]).any(), f"{etapa}: chave (ANO, CO_ENTIDADE) única",
          f"{etapa}: chave duplicada")
    check(((u["ANO_ALVO"] - u["ANO"]) == 1).all(), f"{etapa}: ANO_ALVO = ANO + 1", f"{etapa}: defasagem errada")
    esperado = int(((base["REDE_PUBLICA"].astype("Int8") == 1) & base[f"{col}_T1"].notna()).sum())
    check(len(u) == esperado, f"{etapa}: {len(u)} escolas-ano no universo", f"{etapa}: contagem diverge")

# ------------------------------------------------------------------
secao("E. Conferência cruzada com o projeto oficial (B1, pares completos)")
# ------------------------------------------------------------------
if not P_REF.exists():
    warn(f"referência ausente: {P_REF}")
else:
    ref = pd.read_csv(P_REF)
    res = pd.concat([B.avaliar(base, e) for e in B.ETAPAS], ignore_index=True)
    dif = []
    for _, r in ref.iterrows():
        alvo = int(r["transicao"].split("->")[1])
        lin = res[(res["etapa"] == r["etapa"]) & (res["ano_alvo"] == alvo)]
        dif.append(abs(float(lin["B1_MAE_pares"].iloc[0]) - r["mae_b1_persistencia"]))
    pior = max(dif)
    # a referência vem da base v1.0 do orientador e é arredondada a 2 casas
    if pior <= 0.005 + 1e-9:
        ok(f"MAE do B1 bate com desfechos_persistencia.csv nas {len(dif)} transições (dif. máx {pior:.3f})")
    elif pior <= 0.10:
        warn(f"MAE do B1 próximo da referência (dif. máx {pior:.3f}; bases de origem diferentes)")
    else:
        fail(f"MAE do B1 diverge da referência (dif. máx {pior:.3f})")

# ------------------------------------------------------------------
secao("F. B2 (mediana do treino por localização × dependência)")
# ------------------------------------------------------------------
tr = pd.DataFrame({"LOCALIZACAO": ["U", "U", "U", "R", "R"], "DEPENDENCIA": ["E"] * 5,
                   "y_t1": [1.0, 3.0, 10.0, 0.0, 4.0]})
te = pd.DataFrame({"LOCALIZACAO": ["U", "R", "X"], "DEPENDENCIA": ["E", "E", "E"]})
p2 = B.b2_mediana_estrato(tr, te)
check(np.allclose(p2, [3.0, 2.0, 3.0]), "B2: U→3, R→2, célula nova → mediana geral 3",
      f"B2 incorreto: {p2}")

# ------------------------------------------------------------------
secao("G. Painel da Etapa 2")
# ------------------------------------------------------------------
oficial = pd.read_parquet(P.P_OFICIAL)
for etapa in ("AF", "EM"):
    pn = P.montar(etapa, base, oficial)
    s = P.SUF[etapa]
    idx = base.set_index(["ANO", "CO_ENTIDADE"])[f"ABANDONO_{s}"].astype("Float64").astype("float64")
    amostra = pn.sample(200, random_state=1)
    erro = 0
    for _, r in amostra.iterrows():
        for lag, col in ((1, f"ABANDONO_{s}_L1"), (2, f"ABANDONO_{s}_L2"), (0, f"ABANDONO_{s}_T0")):
            v = idx.get((r["ANO"] - lag, r["CO_ENTIDADE"]), np.nan)
            erro += not ((np.isnan(v) and np.isnan(r[col])) or v == r[col])
    check(erro == 0, f"{etapa}: lags t, t−1, t−2 conferidos em 200 linhas sorteadas",
          f"{etapa}: {erro} lags errados")
    check(np.allclose(pn["y_t"].to_numpy(), pn[f"ABANDONO_{s}_T0"].to_numpy(), equal_nan=True),
          f"{etapa}: ABANDONO_T0 = y_t do universo", f"{etapa}: T0 diverge de y_t")
    dl = pn[f"ABANDONO_{s}_L1"] - pn[f"ABANDONO_{s}_L2"]
    check(np.allclose(pn[f"ABANDONO_{s}_DLAG"], dl, equal_nan=True),
          f"{etapa}: DLAG = abandono(t−1) − abandono(t−2)", f"{etapa}: DLAG incorreto")
    cols_b = P.colunas_bloco(etapa, "B", 4)
    check(not any(c.endswith(("_T0", "_D1")) for c in cols_b) and not any(c.startswith("APROVACAO") for c in cols_b),
          f"{etapa}: Cenário B sem rendimento de t, sem DELTA1 e sem APROVACAO",
          f"{etapa}: Cenário B contém informação de t")
    cols_a = P.colunas_bloco(etapa, "A", 4)
    check(not any(c.startswith("APROVACAO") for c in cols_a)
          and not any(c.endswith(("_N6", "_ALTO")) for c in cols_a + cols_b),
          f"{etapa}: nenhuma composição completa (sem APROVACAO, sem IED N6/ALTO)",
          f"{etapa}: composição completa presente")
    check(len(pn) == len(B.universo(base, etapa).query("ANO >= 2019 and ANO <= 2024")),
          f"{etapa}: painel = universo da Etapa 1 em 2019–2024 ({len(pn)} linhas)",
          f"{etapa}: painel perdeu ou duplicou linhas")
    check(pn["ANO"].between(2019, 2024).all() and (pn["ANO_ALVO"] == pn["ANO"] + 1).all(),
          f"{etapa}: ANO 2019–2024 e ANO_ALVO = ANO + 1", f"{etapa}: anos fora do esperado")

# ------------------------------------------------------------------
secao("H. Walk-forward sem vazamento")
# ------------------------------------------------------------------
# Executa o rodar_etapa de verdade. Perturbar os anos POSTERIORES ao avaliado
# (alvo e preditores) não pode mudar nada no ano avaliado; perturbar o ALVO do
# próprio ano avaliado não pode mudar as previsões (só as métricas).
W.N_PERMUT = 5   # a importância não é o objeto deste teste
pn = P.montar("EM", base, oficial)
cols_todas = sorted({c for cen in P.CENARIOS for c in P.colunas_bloco("EM", cen, 4)})
ano = 2022
pert = pn.copy()
fut = pert["ANO_ALVO"] > ano
pert.loc[fut, "y_t1"] = rng.uniform(0, 100, int(fut.sum()))
pert.loc[fut, cols_todas] = rng.normal(0, 50, (int(fut.sum()), len(cols_todas)))
r1, _ = W.rodar_etapa(pn, "EM", anos=(ano,))
r2, _ = W.rodar_etapa(pert, "EM", anos=(ano,))
met = ["MAE", "R2", "Rec@10", "Rec@20"]
check(np.allclose(r1[met].to_numpy(), r2[met].to_numpy()),
      f"rodar_etapa: perturbar os anos após {ano} não muda nenhuma métrica de {ano} ({len(r1)} linhas)",
      f"rodar_etapa: o ano {ano} depende de anos futuros")
check(int(r1.loc[r1["modelo"] == "B0", "n_treino"].iloc[0]) == int((pn["ANO_ALVO"] < ano).sum()),
      f"rodar_etapa: treino de {ano} = só ANO_ALVO < {ano}", "rodar_etapa: treino incorreto")
pert2 = pn.copy()
hoje = pert2["ANO_ALVO"] == ano
pert2.loc[hoje, "y_t1"] = rng.uniform(0, 100, int(hoje.sum()))
tr = pn[pn["ANO_ALVO"] < ano]
for mod in W.MODELOS:
    c = P.colunas_bloco("EM", "B", 4)
    m1 = W.modelo(mod).fit(tr[c], tr["y_t1"])
    tr2 = pert2[pert2["ANO_ALVO"] < ano]
    m2 = W.modelo(mod).fit(tr2[c], tr2["y_t1"])
    x = pn.loc[hoje, c]
    check(np.allclose(m1.predict(x), m2.predict(x)),
          f"{mod}: o alvo do ano de teste não entra no ajuste",
          f"{mod}: o alvo do ano de teste vazou para o ajuste")

# ------------------------------------------------------------------
secao("RESUMO")
# ------------------------------------------------------------------
log.append(f"  ✅ OK:      {cont['ok']}")
log.append(f"  ⚠️  Warn:   {cont['warn']}")
log.append(f"  ❌ Falhas:  {cont['fail']}")
log.append("")
log.append("  🎉 INSTRUMENTO VALIDADO" if cont["fail"] == 0 else f"  ❌ {cont['fail']} falhas — revisar")
txt = "\n".join(log)
print(txt)
REPORT.write_text(txt, encoding="utf-8")
print(f"\n>>> Relatório: {REPORT}")
sys.exit(1 if cont["fail"] else 0)
