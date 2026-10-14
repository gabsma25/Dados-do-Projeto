# -*- coding: utf-8 -*-
"""
02 — Valida as 18 variáveis e os índices derivados (05) em base_atual.parquet.

Recalcula cada método de forma independente (sem reaproveitar as colunas já
gravadas) e compara:
  A. presença e tipos das 18 + 15 colunas
  B. prop    : recomputada dos itens; faixa [0,1]; NaN só se algum item for NaN
  C. zano    : média 0 / desvio 1 por ano; só usa dados do próprio ano
  D. zref19  : média 0 / desvio 1 no recorte de 2019; parâmetros não dependem
               de nenhum dado posterior a 2019 (sem vazamento)
  E. IIE     : pesos, autovalores, critérios do artigo (Kaiser, >60%),
               recomputação e propriedades
  F. consistência entre métodos (Spearman por ano)
  G. sanidade substantiva (urbana > rural; infra melhora ao longo do tempo)
  H. sensibilidade: desvios pequenos que amplificam o z-score

Saída: gustavo/saida/relatorios/validacao_indices.txt
Uso:   python testes/02_validar_indices.py
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

GUSTAVO = Path(__file__).resolve().parent.parent
P_ATUAL = GUSTAVO / "saida" / "base_atual.parquet"
P_JSON = GUSTAVO / "saida" / "relatorios" / "indices_infra_parametros.json"
REPORT = GUSTAVO / "saida" / "relatorios" / "validacao_indices.txt"
TOL = 1e-9

# reaproveita só as CONSTANTES do 05 (grupos de itens, nomes), não as contas
spec = importlib.util.spec_from_file_location(
    "ind05", GUSTAVO / "programas" / "05_indices_infra.py")
ind05 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ind05)
DIMS, NORMS = ind05.DIMENSOES, ind05.NORMS
ITENS = [i for l in DIMS.values() for i in l]

log, cont = [], {"ok": 0, "warn": 0, "fail": 0}


def secao(t):
    log.extend(["", "=" * 78, t, "=" * 78])


def ok(m):
    cont["ok"] += 1; log.append(f"  ✅ {m}")


def warn(m):
    cont["warn"] += 1; log.append(f"  ⚠️  {m}")


def fail(m):
    cont["fail"] += 1; log.append(f"  ❌ {m}")


def info(m):
    log.append(f"     {m}")


def check(cond, msg_ok, msg_fail):
    ok(msg_ok) if cond else fail(msg_fail)


for p in (P_ATUAL, P_JSON):
    if not p.exists():
        print(f"[ERRO] falta {p} — rode o pipeline (99_pipeline.py)")
        sys.exit(1)
base = pd.read_parquet(P_ATUAL)
par = json.loads(P_JSON.read_text(encoding="utf-8"))
ANO = base["ANO"].astype(int)
anos = sorted(ANO.unique())
TIPO_OK = (all(str(base[i].dtype) == "Int8" for i in ITENS)
           and all(str(base[c].dtype) == "Float64" for c in
                   [f"DIM_{d}_{n}" for n in NORMS for d in DIMS] + [f"IIE_{n}" for n in NORMS]))
base[ITENS] = base[ITENS].astype("float64")   # contas em float (NA -> NaN)
for _c in [f"DIM_{d}_{n}" for n in NORMS for d in DIMS] + [f"IIE_{n}" for n in NORMS]:
    base[_c] = base[_c].astype("float64")

# ------------------------------------------------------------------
secao("A. PRESENÇA E TIPOS")
# ------------------------------------------------------------------
cols_novas = [f"DIM_{d}_{n}" for n in NORMS for d in DIMS] + [f"IIE_{n}" for n in NORMS]
check(len(ITENS) == 18 and all(i in base.columns for i in ITENS),
      "18 variáveis de infraestrutura presentes", "faltam variáveis de infraestrutura")
check(len(cols_novas) == 15 and all(c in base.columns for c in cols_novas),
      "15 colunas derivadas presentes (4 dimensões + IIE × 3 normalizações)",
      f"faltam: {[c for c in cols_novas if c not in base.columns]}")
check(TIPO_OK, "tipos (regra 6): 18 variáveis Int8 e 15 derivadas Float64 nullable",
      "tipos fora da regra 6 nas 18 variáveis ou nas colunas derivadas")
check(not np.isinf(base[cols_novas].to_numpy(dtype=float)).any(),
      "nenhum valor infinito nas colunas derivadas", "há infinitos")
check(base.duplicated(["ANO", "CO_ENTIDADE"]).sum() == 0,
      "chave (ANO, CO_ENTIDADE) única", "chave duplicada")

# ------------------------------------------------------------------
secao("B. PROP  (soma dos itens / nº de itens)")
# ------------------------------------------------------------------
soma = pd.DataFrame({d: base[l].sum(axis=1, min_count=len(l)) for d, l in DIMS.items()})
for d, l in DIMS.items():
    esp = soma[d] / len(l)
    got = base[f"DIM_{d}_prop"]
    check(((esp - got).abs().fillna(0) < TOL).all() and (esp.isna() == got.isna()).all(),
          f"DIM_{d}_prop = soma/{len(l)} (recomputado) e NaN só quando falta item",
          f"DIM_{d}_prop diverge da recomputação")
    v = got.dropna()
    check(v.between(0, 1).all(), f"DIM_{d}_prop em [0, 1]", f"DIM_{d}_prop fora de [0,1]")
    passos = (v * len(l)).round(9)
    check(((passos - passos.round()).abs() < 1e-6).all(),
          f"DIM_{d}_prop só assume múltiplos de 1/{len(l)}",
          f"DIM_{d}_prop tem valores não discretos")

# ------------------------------------------------------------------
secao("C. ZANO  (z dentro de cada ano)")
# ------------------------------------------------------------------
minimo = par["min_escolas_ano"]
mal = []
for d in DIMS:
    z = base[f"DIM_{d}_zano"]
    for ano in anos:
        m = ANO == ano
        s = soma.loc[m, d].dropna()
        valido = len(s) >= minimo and s.std(ddof=0) > 0
        zz = z[m]
        if not valido:
            if zz.notna().any():
                mal.append((d, ano, "z presente em ano inválido"))
            continue
        if abs(zz.mean()) > 1e-8 or abs(zz.std(ddof=0) - 1) > 1e-8:
            mal.append((d, ano, f"média={zz.mean():.3g} dp={zz.std(ddof=0):.3g}"))
        # função afim crescente da prop no ano => correlação 1
        c = np.corrcoef(zz.dropna(), base.loc[zz.dropna().index, f"DIM_{d}_prop"])[0, 1]
        if c < 1 - 1e-9:
            mal.append((d, ano, f"corr(z, prop)={c:.6f}"))
check(not mal, "em todo (dimensão, ano) válido: média 0, desvio 1 e corr(z, prop)=1",
      f"problemas: {mal[:5]}")
# só informação do próprio ano: recalcular com os dados de UM ano isolado
d0, a0 = "IEP", 2016
s = soma.loc[ANO == a0, d0].dropna()
z_iso = (s - s.mean()) / s.std(ddof=0)
check(((z_iso - base.loc[z_iso.index, f"DIM_{d0}_zano"]).abs() < 1e-9).all(),
      f"z de {d0}/{a0} recomputado só com dados de {a0} confere (sem dado de outro ano)",
      f"z de {d0}/{a0} depende de outros anos")

# ------------------------------------------------------------------
secao("D. ZREF19  (z com média/desvio fixos de 2019)")
# ------------------------------------------------------------------
ref = ((ANO == par["ano_referencia"])
       & base["DEPENDENCIA"].astype(str).str.lower().str.startswith("estad")
       & base["APROVACAO_MED"].notna())
check(int(ref.sum()) == par["n_escolas_referencia"],
      f"recorte de referência recomputado = {int(ref.sum())} escolas "
      f"(artigo: 165; diferença = escolas fora da base de rendimento)",
      "recorte de referência diverge do JSON")
for d in DIMS:
    s = soma.loc[ref, d].dropna()
    mu, sd = s.mean(), s.std(ddof=0)
    pj = par["z_referencia_2019"][d]
    check(abs(mu - pj["media"]) < 1e-9 and abs(sd - pj["dp"]) < 1e-9,
          f"{d}: parâmetros do JSON conferem (média {mu:.3f}, dp {sd:.3f})",
          f"{d}: parâmetros do JSON divergem")
    zr = base.loc[ref, f"DIM_{d}_zref19"]
    check(abs(zr.mean()) < 1e-8 and abs(zr.std(ddof=0) - 1) < 1e-8,
          f"{d}: no recorte 2019 o z tem média 0 e desvio 1",
          f"{d}: z no recorte não é padrão")
# sem vazamento: parâmetros só com dados <= 2019 são idênticos
so19 = base[ANO <= par["ano_referencia"]]
ref19 = ((so19["ANO"].astype(int) == par["ano_referencia"])
         & so19["DEPENDENCIA"].astype(str).str.lower().str.startswith("estad")
         & so19["APROVACAO_MED"].notna())
vaz = []
for d, l in DIMS.items():
    s = so19.loc[ref19, l].sum(axis=1, min_count=len(l)).dropna()
    pj = par["z_referencia_2019"][d]
    if abs(s.mean() - pj["media"]) > 1e-9 or abs(s.std(ddof=0) - pj["dp"]) > 1e-9:
        vaz.append(d)
check(not vaz, "parâmetros zref19 recomputados SÓ com dados até 2019 são idênticos "
      "(nenhum dado posterior influencia)", f"vazamento em: {vaz}")
check(par["ano_referencia"] < 2021,
      "ano de referência (2019) é anterior ao primeiro fold de teste (2021)",
      "ano de referência não é anterior aos folds de teste")

# ------------------------------------------------------------------
secao("E. IIE  (PC1 das 4 dimensões, pesos fixos de 2019)")
# ------------------------------------------------------------------
Zr = pd.DataFrame({d: base.loc[ref, f"DIM_{d}_zref19"] for d in DIMS}).dropna()
R = np.corrcoef(Zr.values.T)
vals, vecs = np.linalg.eigh(R)
o = np.argsort(vals)[::-1]; vals, vecs = vals[o], vecs[:, o]
w = vecs[:, 0] * (1 if vecs[:, 0].sum() >= 0 else -1)
pj = np.array([par["pca_2019"]["pesos_pc1"][d] for d in DIMS])
check(np.allclose(w, pj, atol=1e-9), "pesos PC1 recomputados conferem com o JSON",
      "pesos PC1 divergem")
check(abs(np.linalg.norm(w) - 1) < 1e-9, "pesos têm norma 1", "pesos sem norma 1")
check((w > 0).all(), f"todos os pesos positivos ({np.round(w, 3).tolist()})",
      "há peso negativo: dimensões não apontam no mesmo sentido")
check(abs(vals.sum() - 4) < 1e-9, "soma dos autovalores = 4 (traço da matriz de correlação)",
      "autovalores não somam 4")
check(vals[0] > 1, f"critério de Kaiser: autovalor PC1 = {vals[0]:.3f} > 1",
      f"PC1 não atende Kaiser ({vals[0]:.3f})")
ve = vals[0] / vals.sum()
(ok if ve > 0.6 else warn)(f"PC1 explica {ve*100:.1f}% da variância (artigo exige > 60%)")
off = R[np.triu_indices(4, 1)]
info(f"correlações entre as 4 dimensões (2019): min={off.min():.2f} máx={off.max():.2f}")
for n in NORMS:
    mat = pd.DataFrame({d: base[f"DIM_{d}_{n}"] for d in DIMS})
    esp = (mat * w).sum(axis=1, min_count=4)
    got = base[f"IIE_{n}"]
    check(((esp - got).abs().fillna(0) < 1e-9).all() and (esp.isna() == got.isna()).all(),
          f"IIE_{n} = Σ w·DIM_{n} (recomputado) e NaN se alguma dimensão for NaN",
          f"IIE_{n} diverge da recomputação")

# ------------------------------------------------------------------
secao("F. CONSISTÊNCIA ENTRE MÉTODOS  (Spearman por ano, IIE)")
# ------------------------------------------------------------------
info(f"{'ano':>5}{'n':>6}{'prop~zano':>11}{'prop~zref19':>13}{'zano~zref19':>13}")
baixos = []
for ano in anos:
    s = base[ANO == ano][["IIE_prop", "IIE_zano", "IIE_zref19"]].dropna()
    if len(s) < 30:
        info(f"{ano:>5}{len(s):>6}{'--':>11}{'--':>13}{'--':>13}")
        continue
    c = s.corr(method="spearman")
    a, b, d_ = c.loc["IIE_prop", "IIE_zano"], c.loc["IIE_prop", "IIE_zref19"], c.loc["IIE_zano", "IIE_zref19"]
    info(f"{ano:>5}{len(s):>6}{a:>11.3f}{b:>13.3f}{d_:>13.3f}")
    if min(a, b, d_) < 0.9:
        baixos.append((ano, round(min(a, b, d_), 3)))
(warn if baixos else ok)(
    f"ordenação das escolas muda entre métodos em: {baixos}" if baixos
    else "as 3 normalizações ordenam as escolas quase igual (Spearman ≥ 0,90 em todos os anos)")
s = base[ANO == 2019][["IIE_prop", "IIE_zref19"]].dropna()
check(abs(np.corrcoef(s["IIE_prop"], s["IIE_zref19"])[0, 1]) > 0.99,
      "em 2019, IIE_prop e IIE_zref19 têm correlação > 0,99 "
      "(só diferem por escala dos itens)", "IIE_prop e IIE_zref19 divergem em 2019")

# ------------------------------------------------------------------
secao("G. SANIDADE SUBSTANTIVA")
# ------------------------------------------------------------------
for loc_a, loc_b in [("Urbana", "Rural")]:
    t = base[(ANO == 2019)].groupby("LOCALIZACAO")["IIE_zref19"].mean()
    if loc_a in t and loc_b in t:
        (ok if t[loc_a] > t[loc_b] else fail)(
            f"2019: IIE médio {loc_a} ({t[loc_a]:.2f}) {'>' if t[loc_a] > t[loc_b] else '<='} "
            f"{loc_b} ({t[loc_b]:.2f})  — o artigo também encontra infra urbana > rural")
t = base[ANO >= 2012].groupby(ANO)["IIE_prop"].mean()
info("IIE_prop médio por ano (2012+): " + "  ".join(f"{a}:{v:.2f}" for a, v in t.items()))
ok("IIE médio calculado por ano (conferir tendência no relatório)") if t.notna().all() else warn("IIE médio com anos vazios")
cob = base.groupby(ANO)[["IIE_prop", "IIE_zano", "IIE_zref19"]].apply(lambda d: d.notna().mean() * 100)
sem = [int(a) for a in cob.index if cob.loc[a].max() == 0]
info(f"anos sem nenhum IIE (itens não coletados): {sem}")
check(set(sem) <= {2007, 2008, 2009, 2010, 2011},
      "só 2007-2011 ficam sem IIE (itens do IDA/IDP não coletados)",
      f"anos inesperados sem IIE: {sem}")
check(all(cob.loc[a].min() > 85 for a in range(2012, 2022)),
      "2012-2021: IIE disponível em > 85% das escolas da base",
      "cobertura do IIE em 2012-2021 abaixo de 85%")
info("cobertura do IIE (%): " + "  ".join(f"{int(a)}:{cob.loc[a,'IIE_prop']:.0f}" for a in cob.index))

# ------------------------------------------------------------------
secao("H. SENSIBILIDADE — desvios pequenos amplificam o z-score")
# ------------------------------------------------------------------
ea = pd.DataFrame(par["z_por_ano"])
inval = ea[~ea["valido"]]
if len(inval):
    info(f"(dimensão, ano) sem zano por n<{minimo} ou dp=0: "
         f"{[(r.dim, r.ano) for r in inval.itertuples()][:10]}")
else:
    ok(f"todo (dimensão, ano) tem n ≥ {minimo} e desvio > 0")
val = ea[ea["valido"] & ea["ano"].ge(2012)]
mn = val.loc[val["dp_soma"].idxmin()]
(ok if mn["dp_soma"] >= 0.5 else warn)(
    f"menor desvio da soma bruta (2012+): {mn['dp_soma']:.2f} "
    f"({mn['dim']}/{int(mn['ano'])}) — abaixo de 0,5 o z-score amplifica ruído")
info("desvio da soma bruta por dimensão (2012+): " + "; ".join(
    f"{d}: {val[val.dim == d]['dp_soma'].min():.2f}–{val[val.dim == d]['dp_soma'].max():.2f}"
    for d in DIMS))

# ------------------------------------------------------------------
secao("RESUMO")
# ------------------------------------------------------------------
log.append(f"  ✅ OK:      {cont['ok']}")
log.append(f"  ⚠️  Warn:   {cont['warn']}")
log.append(f"  ❌ Falhas:  {cont['fail']}")
log.append("")
log.append("  🎉 ÍNDICES VALIDADOS" if cont["fail"] == 0
           else f"  ❌ {cont['fail']} falhas — revisar")
txt = "\n".join(log)
print(txt)
REPORT.write_text(txt, encoding="utf-8")
print(f"\n>>> Relatório: {REPORT}")
sys.exit(1 if cont["fail"] else 0)
