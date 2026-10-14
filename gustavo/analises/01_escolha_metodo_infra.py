# -*- coding: utf-8 -*-
"""
ANÁLISE 01 — Escolha do método de normalização dos índices de infraestrutura.

STATUS: ANÁLISE HISTÓRICA DE DECISÃO (14/10/2026). O 05 atual só gera o método
escolhido (zano, ano a ano); as colunas prop e zref19 comparadas aqui existem
apenas no instantâneo saida/_backup_2026-10-14/05_base_com_indices_3metodos.parquet,
que é a entrada padrão deste script. Os resultados estão em docs/relatorio_05.

NÃO é um teste de validação do pipeline (isso é testes/02_validar_indices.py).
Esta análise serviu para ESCOLHER entre as três versões geradas pelo 05 antigo:
    prop    soma / nº de itens                      (sem parâmetros)
    zano    z-score dentro de cada ano              (parâmetros do próprio ano)
    zref19  z-score com média/dp fixos de 2019      (parâmetros de 2019)
para as 5 colunas de cada método: DIM_IIB, DIM_IDA, DIM_IDP, DIM_IEP e IIE.

REGRA DO PROJETO (CLAUDE.md, regra 3): variável NUNCA é escolhida pela
correlação com o desfecho. Por isso esta análise não lê nenhuma coluna de
alvo (ABANDONO_*, REPROVACAO_*). A única leitura de taxa é a PRESENÇA de
APROVACAO_MED, usada como filtro "a escola tem ensino médio" para reconstruir o
recorte de referência do 05. Os critérios são só estruturais:

  1. Cobertura por ano e ausências estruturais (2007-2011 não têm IDA/IDP/IIE)
  2. Equivalência da ordenação dentro do ano entre os 3 métodos
  3. Nível e tendência ao longo dos anos (quanto da variância é "efeito ano")
  4. Quebras de nível na MESMA escola entre anos consecutivos
  5. Persistência da posição da escola (t -> t+1 e t -> t+3)
  6. Estacionariedade treino -> teste em validação walk-forward
  7. Robustez do IIE aos pesos (fixos de 2019 x do ano x acumulados até t x iguais)
  8. Sensibilidade do zref19 ao recorte de referência (152 escolas x artigo 165)
  9. Dependências de dados externos ao ano t (vazamento temporal, regra 4)
 10. Resumo dos critérios

Os limites de leitura (✅/⚠️/❌) são regras práticas declaradas no topo do
arquivo, não testes estatísticos. A decisão final é humana.

Entrada: gustavo/saida/_backup_2026-10-14/05_base_com_indices_3metodos.parquet
Saída:   gustavo/saida/relatorios/escolha_metodo_infra.txt
         gustavo/saida/relatorios/escolha_metodo_infra_metricas.csv
Uso:     python analises/01_escolha_metodo_infra.py [--base caminho.parquet]
         (a base precisa ter as 18 variáveis e as 15 colunas DIM_/IIE_ dos 3 métodos)
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

GUSTAVO = Path(__file__).resolve().parent.parent
P_ATUAL = GUSTAVO / "saida" / "_backup_2026-10-14" / "05_base_com_indices_3metodos.parquet"
REPORT = GUSTAVO / "saida" / "relatorios" / "escolha_metodo_infra.txt"
CSV = GUSTAVO / "saida" / "relatorios" / "escolha_metodo_infra_metricas.csv"

# ---------------------------------------------------------------- limites
LIM_ESTAC_OK, LIM_ESTAC_ATENCAO = 0.25, 0.50   # |deslocamento treino->teste| em dp do treino
LIM_QUEBRA_OK, LIM_QUEBRA_ATENCAO = 0.10, 0.20  # |Δ médio da mesma escola| em dp entre escolas
LIM_TENDENCIA_OK, LIM_TENDENCIA_ATENCAO = 0.05, 0.15  # eta² do ano (fração da variância)
LIM_PESOS_OK, LIM_PESOS_ATENCAO = 0.995, 0.98   # Spearman IIE(pesos fixos) x IIE(outros pesos)
LIM_RECORTE_OK, LIM_RECORTE_ATENCAO = 0.10, 0.25  # |deslocamento de nível| em dp do IIE
ANO_MIN_IIE = 2012

ap = argparse.ArgumentParser()
ap.add_argument("--base", default=str(P_ATUAL))
args = ap.parse_args()
P_BASE = Path(args.base)
if not P_BASE.exists():
    print(f"[ERRO] não achei {P_BASE} — o instantâneo de 3 métodos fica em saida/_backup_2026-10-14/")
    sys.exit(1)

# constantes próprias (esta análise não depende do 05 atual)
DIMS = {
    "IIB": ["IIB_agua_potavel", "IIB_energia_rede", "IIB_coleta_lixo", "IIB_banheiro"],
    "IDA": ["IDA_despensa", "IDA_refeitorio", "IDA_sala_diretoria", "IDA_sala_professor", "IDA_secretaria"],
    "IDP": ["IDP_biblioteca", "IDP_lab_informatica", "IDP_patio_coberto", "IDP_patio_descoberto", "IDP_quadra_esportes"],
    "IEP": ["IEP_computador", "IEP_impressora", "IEP_projetor", "IEP_internet"],
}
NORMS = ["prop", "zano", "zref19"]
ANO_REF = 2019
ITENS = [i for l in DIMS.values() for i in l]
DN = list(DIMS)                                  # IIB, IDA, IDP, IEP

log, met = [], []
cont = {"ok": 0, "warn": 0, "fail": 0}


def secao(t):
    log.extend(["", "=" * 78, t, "=" * 78])


def info(m=""):
    log.append(f"     {m}" if m else "")


def flag(nivel, msg):
    cont[nivel] += 1
    log.append({"ok": "  ✅ ", "warn": "  ⚠️  ", "fail": "  ❌ "}[nivel] + msg)


def reg(secao_, metodo, variavel, ano, nome, valor):
    met.append((secao_, metodo, variavel, "" if ano is None else int(ano), nome,
                None if valor is None or (isinstance(valor, float) and np.isnan(valor)) else float(valor)))


def fl(s):
    """Série -> float64 com NaN (aceita Int8/Float64 nullable, pandas 2 e 3)."""
    return pd.to_numeric(s, errors="coerce").astype("float64")


def sp(a, b):
    """Spearman entre dois arrays com NaN (usa só pares completos)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = ~(np.isnan(a) | np.isnan(b))
    if m.sum() < 5:
        return np.nan
    ra, rb = pd.Series(a[m]).rank().to_numpy(), pd.Series(b[m]).rank().to_numpy()
    if ra.std() == 0 or rb.std() == 0:
        return np.nan
    return float(np.corrcoef(ra, rb)[0, 1])


def pr(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = ~(np.isnan(a) | np.isnan(b))
    if m.sum() < 5 or a[m].std() == 0 or b[m].std() == 0:
        return np.nan
    return float(np.corrcoef(a[m], b[m])[0, 1])


def ks(a, b):
    a, b = np.sort(a[~np.isnan(a)]), np.sort(b[~np.isnan(b)])
    if len(a) == 0 or len(b) == 0:
        return np.nan
    xs = np.concatenate([a, b])
    return float(np.max(np.abs(np.searchsorted(a, xs, side="right") / len(a)
                               - np.searchsorted(b, xs, side="right") / len(b))))


def pc1(R):
    """Pesos do 1º componente (matriz de correlação), norma 1, soma > 0."""
    w, v = np.linalg.eigh(R)
    i = int(np.argmax(w))
    vec = v[:, i]
    if vec.sum() < 0:
        vec = -vec
    return vec, w[i], w[::-1] / w.sum()


def faixa(v, ok, atencao):
    return "ok" if v <= ok else ("warn" if v <= atencao else "fail")


# ---------------------------------------------------------------- dados
b = pd.read_parquet(P_BASE)
b = b.copy()
b["ANO"] = b["ANO"].astype(int)
b["CO"] = b["CO_ENTIDADE"].astype(str)
anos = sorted(b["ANO"].unique())
COLS = {n: [f"DIM_{d}_{n}" for d in DN] + [f"IIE_{n}"] for n in NORMS}
faltam = [c for n in NORMS for c in COLS[n] if c not in b.columns] + \
         [i for i in ITENS if i not in b.columns]
if faltam:
    print(f"[ERRO] faltam colunas {faltam[:6]}... — rode o 05")
    sys.exit(1)
V = {}                                           # V[(var, norma)] -> float64
for n in NORMS:
    for d in DN:
        V[(d, n)] = fl(b[f"DIM_{d}_{n}"])
    V[("IIE", n)] = fl(b[f"IIE_{n}"])
VARS = DN + ["IIE"]
dummy_alvo = [c for c in b.columns if c.startswith(("ABANDONO", "APROVACAO", "REPROVACAO"))]

log.append("ESCOLHA DO MÉTODO DE NORMALIZAÇÃO — índices de infraestrutura (pós-05)")
log.append("=" * 78)
log.append(f"Base: {P_BASE.name}  ({len(b)} linhas × {b.shape[1]} colunas, "
           f"{anos[0]}–{anos[-1]})")
log.append(f"Colunas analisadas: 15 (4 dimensões + IIE) × 3 métodos ({', '.join(NORMS)})")
log.append(f"Colunas de desfecho na base ({len(dummy_alvo)}): esta análise não as usa como "
           "critério. Única leitura: se APROVACAO_MED é não-nulo, para saber se a escola tem")
log.append("ensino médio e reconstruir o recorte de referência do 05 (seção 8) — é um filtro, "
           "não um preditor.")
log.append("")
log.append("Como ler: a análise compara os métodos em critérios que NÃO usam o alvo.")
log.append("Dentro de um mesmo ano, prop/zano/zref19 de cada DIMENSÃO são transformações")
log.append("afins da mesma soma (mesma ordenação). As diferenças reais estão em (a) como o")
log.append("nível se comporta ENTRE anos, (b) de onde vêm os parâmetros e (c) como o IIE")
log.append("agrega as dimensões.")

# ================================================================
secao("1. COBERTURA E AUSÊNCIAS ESTRUTURAIS")
# ================================================================
cob = pd.DataFrame({(v, n): V[(v, n)].groupby(b["ANO"]).apply(lambda s: s.notna().mean() * 100)
                    for v in VARS for n in NORMS})
tam = b.groupby("ANO").size()
for v in VARS:
    for n in NORMS:
        for a in anos:
            reg("cobertura", n, v, a, "pct_com_valor", cob.loc[a, (v, n)])
sem = {v: [int(a) for a in anos if cob.loc[a, (v, "prop")] == 0] for v in VARS}
info("Anos SEM valor, por coluna (igual nos 3 métodos):")
for v in VARS:
    s = sem[v]
    info(f"  {v:4s}: " + (f"{s[0]}–{s[-1]} ({len(s)} anos)" if s else "nenhum"))
info("")
info("Motivo: a pergunta do Censo não existia em 2007-2011 para despensa, refeitório,")
info("secretaria, pátio coberto e pátio descoberto. Uma dimensão só existe quando TODOS os")
info("itens existem; logo IDA (despensa, refeitório, secretaria) e IDP (os dois pátios) ficam")
info("vazias nesses anos, e o IIE, que usa as 4 dimensões, também. IIB e IEP cobrem 2007-2025.")
diff_cob = max(abs(cob[(v, n)] - cob[(v, "prop")]).max() for v in VARS for n in NORMS)
(flag("ok", "cobertura idêntica nos 3 métodos (nenhum método perde linhas por n<30 ou dp=0)")
 if diff_cob == 0 else
 flag("warn", f"cobertura difere entre métodos (até {diff_cob:.1f} p.p.)"))
n_iie = int(V[("IIE", "prop")].notna().sum())
info(f"Linhas com IIE: {n_iie} de {len(b)} ({n_iie / len(b) * 100:.1f}%); "
     f"anos com IIE: {ANO_MIN_IIE}–{anos[-1]}")
info("")
info("Composição da base por ano (referencial do zano = todas as escolas da base no ano):")
comp = pd.DataFrame({
    "n": tam,
    "%estadual": b["DEPENDENCIA"].astype(str).str.lower().str.startswith("estad").groupby(b["ANO"]).mean() * 100,
    "%rural": b["LOCALIZACAO"].astype(str).str.lower().str.startswith("rural").groupby(b["ANO"]).mean() * 100,
})
info("  ano     n  %estadual  %rural")
for a in anos:
    info(f"  {a}  {int(comp.loc[a, 'n']):4d}   {comp.loc[a, '%estadual']:5.1f}    {comp.loc[a, '%rural']:5.1f}")

# ================================================================
secao("2. EQUIVALÊNCIA DA ORDENAÇÃO DENTRO DO ANO (Spearman entre métodos)")
# ================================================================
pares = [("prop", "zano"), ("prop", "zref19"), ("zano", "zref19")]
tab2 = {}
for v in VARS:
    for (m1, m2) in pares:
        rs = []
        for a in anos:
            msk = (b["ANO"] == a).to_numpy()
            r = sp(V[(v, m1)].to_numpy()[msk], V[(v, m2)].to_numpy()[msk])
            if not np.isnan(r):
                rs.append(r); reg("equivalencia", f"{m1}x{m2}", v, a, "spearman", r)
        tab2[(v, m1, m2)] = (min(rs), np.mean(rs)) if rs else (np.nan, np.nan)
info("Mínimo (e média) do Spearman por ano:")
info("  coluna  prop×zano        prop×zref19      zano×zref19")
for v in VARS:
    cel = [f"{tab2[(v, a, b_)][0]:.4f} ({tab2[(v, a, b_)][1]:.4f})" for a, b_ in pares]
    info(f"  {v:5s}   " + "   ".join(cel))
dim_min = min(tab2[(d, a, b_)][0] for d in DN for a, b_ in pares if not np.isnan(tab2[(d, a, b_)][0]))
iie_min = min(tab2[("IIE", a, b_)][0] for a, b_ in pares)
(flag("ok", f"dimensões: ordenação idêntica nos 3 métodos (mínimo {dim_min:.4f}) — "
            "o método só importa para o nível ENTRE anos e para o IIE")
 if dim_min > 0.9999 else flag("warn", f"dimensões diferem entre métodos (mínimo {dim_min:.4f})"))
(flag("ok", f"IIE: ordenação dentro do ano praticamente igual (mínimo {iie_min:.4f})")
 if iie_min >= 0.99 else flag("warn", f"IIE: ordenação dentro do ano difere (mínimo {iie_min:.4f})"))
info("")
info("Consequência: se o modelo é treinado ano a ano, ou se o objetivo é ranquear escolas")
info("DENTRO de um ano (lista top-K), os três métodos entregam a mesma informação.")
info("A escolha só pesa quando os anos são empilhados no mesmo modelo.")

# ================================================================
secao("3. NÍVEL E TENDÊNCIA ENTRE ANOS (quanto é 'efeito ano')")
# ================================================================
info("Média anual (e desvio entre escolas) — IIE:")
info("  ano   prop           zano           zref19")
for a in anos:
    if a < ANO_MIN_IIE:
        continue
    msk = (b["ANO"] == a).to_numpy()
    cel = []
    for n in NORMS:
        x = V[("IIE", n)].to_numpy()[msk]
        cel.append(f"{np.nanmean(x):6.3f} ({np.nanstd(x):.3f})")
        reg("nivel", n, "IIE", a, "media", np.nanmean(x)); reg("nivel", n, "IIE", a, "dp", np.nanstd(x))
    info(f"  {a}  " + "  ".join(cel))
info("")
info("eta² do ano = fração da variância total que é só diferença de média entre anos:")
info("  coluna   anos          prop    zano   zref19")
eta = {}
for v in VARS:
    for n in NORMS:
        x = V[(v, n)]
        m = x.notna()
        xs, ys = x[m], b.loc[m, "ANO"]
        sst = ((xs - xs.mean()) ** 2).sum()
        ssb = (xs.groupby(ys).transform("mean").sub(xs.mean()) ** 2).sum()
        eta[(v, n)] = float(ssb / sst) if sst > 0 else np.nan
        reg("tendencia", n, v, None, "eta2_ano", eta[(v, n)])
    a0 = anos[0] if v in ("IIB", "IEP") else ANO_MIN_IIE
    info(f"  {v:5s}   {a0}–{anos[-1]}   " + "   ".join(f"{eta[(v, n)]:.3f}" for n in NORMS))
info("")
info("Leitura: zano zera o efeito ano POR CONSTRUÇÃO. Se prop/zref19 têm eta² alto, a feature")
info("carrega uma tendência temporal (a infraestrutura melhora com os anos) que pode se")
info("confundir com qualquer outra variável que também tenha tendência (ex.: o próprio")
info("desfecho) quando os anos são empilhados. Se for baixo, zano descarta pouca informação.")
for n in ("prop", "zref19"):
    e = eta[("IIE", n)]
    nivel = faixa(e, LIM_TENDENCIA_OK, LIM_TENDENCIA_ATENCAO)
    msg = (f"IIE_{n}: {e * 100:.1f}% da variância é diferença de média entre anos "
           f"(limites: ≤{LIM_TENDENCIA_OK * 100:.0f}% ok, ≤{LIM_TENDENCIA_ATENCAO * 100:.0f}% atenção)")
    flag(nivel, msg)
flag("ok", f"IIE_zano: eta² = {eta[('IIE', 'zano')]:.3f} (zero por construção)")
# tendência anual em dp-entre-escolas
info("")
info("Tendência linear da média anual, em desvios-padrão entre escolas por ano (IIE):")
for n in NORMS:
    mm = V[("IIE", n)].groupby(b["ANO"]).mean()
    ss = V[("IIE", n)].groupby(b["ANO"]).std(ddof=0)
    ok_ = [a for a in anos if a >= ANO_MIN_IIE]
    sl = np.polyfit(ok_, mm.loc[ok_].to_numpy(), 1)[0] / np.nanmean(ss.loc[ok_].to_numpy())
    reg("tendencia", n, "IIE", None, "inclinacao_dp_por_ano", sl)
    info(f"  {n:7s}: {sl:+.3f} dp/ano")

# ================================================================
secao("4. QUEBRAS DE NÍVEL NA MESMA ESCOLA (Δ médio entre t-1 e t, em dp entre escolas)")
# ================================================================
key = b["CO"] + "_" + b["ANO"].astype(str)
idx = pd.Series(np.arange(len(b)), index=key.to_numpy())


def delta_medio(vec, a):
    """Δ médio (t - t-1) das escolas presentes nos dois anos, / dp entre escolas em t-1."""
    cur = b.index[(b["ANO"] == a).to_numpy()]
    ant_key = b.loc[cur, "CO"] + "_" + str(a - 1)
    ok = ant_key.isin(idx.index).to_numpy()
    if ok.sum() < 20:
        return np.nan, 0
    i_cur = np.arange(len(b))[(b["ANO"] == a).to_numpy()][ok]
    i_ant = idx.loc[ant_key[ok]].to_numpy()
    d = vec[i_cur] - vec[i_ant]
    d = d[~np.isnan(d)]
    if len(d) < 20:
        return np.nan, 0
    base_dp = np.nanstd(vec[(b["ANO"] == a - 1).to_numpy()])
    return (float(np.mean(d) / base_dp) if base_dp > 0 else np.nan), len(d)


qb = {}
for v in ("IIB", "IEP", "IIE"):
    for n in NORMS:
        vec = V[(v, n)].to_numpy()
        for a in anos[1:]:
            dm, nn = delta_medio(vec, a)
            if not np.isnan(dm):
                qb[(v, n, a)] = dm
                reg("quebras", n, v, a, "delta_medio_em_dp", dm)
info("Δ médio da mesma escola (em dp entre escolas do ano anterior). Valores positivos")
info("grandes em um único ano, e não nos vizinhos, indicam mudança de questionário.")
for v in ("IIB", "IEP", "IIE"):
    info("")
    info(f"  {v}: transição   prop     zano    zref19")
    for a in anos[1:]:
        if (v, "prop", a) in qb:
            info(f"        {a-1}→{a}  " + "  ".join(f"{qb[(v, n, a)]:+7.3f}" for n in NORMS))
info("")
info("Resumo (|Δ| médio por transição, pior transição):")
info("  coluna  método    |Δ| médio   pior |Δ|   transição")
resumo_q = {}
for v in ("IIB", "IEP", "IIE"):
    for n in NORMS:
        ds = {a: qb[(v, n, a)] for a in anos[1:] if (v, n, a) in qb}
        am = float(np.mean(np.abs(list(ds.values()))))
        pior_a = max(ds, key=lambda k: abs(ds[k]))
        resumo_q[(v, n)] = (am, abs(ds[pior_a]), pior_a)
        reg("quebras", n, v, None, "abs_delta_medio", am)
        reg("quebras", n, v, None, "pior_abs_delta", abs(ds[pior_a]))
        info(f"  {v:5s}   {n:7s}   {am:7.3f}    {abs(ds[pior_a]):7.3f}    {pior_a-1}→{pior_a}")
info("")
info("Quebras conhecidas (documentadas no relatório 04):")
for (v, a, rot) in (("IEP", 2012, "projetor: EQUIP_RETROPROJETOR → EQUIP_MULTIMIDIA"),
                    ("IIB", 2019, "água e banheiro: colunas do artigo passam a existir")):
    if all((v, n, a) in qb for n in NORMS):
        info(f"  {v} {a-1}→{a} ({rot}): " + "  ".join(f"{n}={qb[(v, n, a)]:+.3f}" for n in NORMS))
for n in NORMS:
    am, pior, pa = resumo_q[("IIE", n)]
    flag(faixa(pior, LIM_QUEBRA_OK, LIM_QUEBRA_ATENCAO),
         f"IIE_{n}: pior salto da mesma escola = {pior:.3f} dp ({pa-1}→{pa}); "
         f"limites ≤{LIM_QUEBRA_OK} ok, ≤{LIM_QUEBRA_ATENCAO} atenção")
for n in NORMS:
    am, pior, pa = resumo_q[("IIB", n)]
    flag(faixa(pior, LIM_QUEBRA_OK, LIM_QUEBRA_ATENCAO),
         f"IIB_{n} (2007-2025): pior salto = {pior:.3f} dp ({pa-1}→{pa})")
for n in NORMS:
    am, pior, pa = resumo_q[("IEP", n)]
    flag(faixa(pior, LIM_QUEBRA_OK, LIM_QUEBRA_ATENCAO),
         f"IEP_{n} (2007-2025): pior salto = {pior:.3f} dp ({pa-1}→{pa})")
info("")
info("Atenção: parte desses saltos é melhora REAL da infraestrutura, não quebra. O zano")
info("remove os dois (quebra e tendência comum a todas as escolas). Ele NÃO remove melhora")
info("que atinge só algumas escolas — essa continua aparecendo como mudança de posição.")

# ================================================================
secao("5. PERSISTÊNCIA DA POSIÇÃO DA ESCOLA")
# ================================================================
info("Spearman entre o valor da escola em t e em t+h (média sobre os pares de anos).")
info("'pooled' = Pearson sobre todos os pares empilhados (inclui diferenças de nível entre anos).")
info("")
info("  coluna  h   prop    zano    zref19      | pooled: prop   zano   zref19")
pers = {}
for v in VARS:
    for h in (1, 3):
        rs = {n: [] for n in NORMS}
        pool = {n: ([], []) for n in NORMS}
        for a in anos:
            if a + h > anos[-1]:
                continue
            ia = (b["ANO"] == a).to_numpy()
            ka = b.loc[ia, "CO"].to_numpy()
            ib = (b["ANO"] == a + h).to_numpy()
            kb = b.loc[ib, "CO"]
            pos = pd.Series(np.flatnonzero(ib), index=kb.to_numpy())
            comum = [k for k in ka if k in pos.index]
            if len(comum) < 20:
                continue
            sa = pd.Series(np.flatnonzero(ia), index=ka).loc[comum].to_numpy()
            sb = pos.loc[comum].to_numpy()
            for n in NORMS:
                x = V[(v, n)].to_numpy()
                r = sp(x[sa], x[sb])
                if not np.isnan(r):
                    rs[n].append(r); reg("persistencia", n, v, a, f"spearman_h{h}", r)
                pool[n][0].append(x[sa]); pool[n][1].append(x[sb])
        if not rs["prop"]:
            continue
        pp = {n: pr(np.concatenate(pool[n][0]), np.concatenate(pool[n][1])) for n in NORMS}
        for n in NORMS:
            pers[(v, h, n)] = (np.mean(rs[n]), pp[n])
            reg("persistencia", n, v, None, f"spearman_medio_h{h}", np.mean(rs[n]))
            reg("persistencia", n, v, None, f"pearson_pooled_h{h}", pp[n])
        info(f"  {v:5s}   {h}   " + "  ".join(f"{np.mean(rs[n]):.3f}" for n in NORMS)
             + "    |        " + "  ".join(f"{pp[n]:.3f}" for n in NORMS))
sp1 = {n: pers[("IIE", 1, n)][0] for n in NORMS}
spread = max(sp1.values()) - min(sp1.values())
(flag("ok", f"persistência t→t+1 do IIE praticamente igual entre métodos (amplitude {spread:.4f})")
 if spread < 0.01 else flag("warn", f"persistência do IIE difere entre métodos (amplitude {spread:.4f})"))
info("Leitura: a posição relativa da escola é estável (a escola \"carrega\" sua infraestrutura);")
info("o que o zano muda é só o nível comum a todas as escolas em cada ano.")

# ================================================================
secao("6. ESTACIONARIEDADE TREINO → TESTE (walk-forward)")
# ================================================================
info("Para cada ano de teste Y, o treino é todo ano anterior com a coluna disponível")
info("(mínimo 2 anos). d = (média_teste − média_treino) / dp_treino.  KS = distância de")
info("Kolmogorov-Smirnov entre as distribuições de treino e teste.")
est = {}
for v in ("IIB", "IEP", "IIE"):
    anos_v = [a for a in anos if (V[(v, "prop")][(b["ANO"] == a).to_numpy()].notna().sum() > 0)]
    info("")
    info(f"  {v}: teste    d_prop   d_zano  d_zref19 |  KS_prop  KS_zano  KS_zref19")
    for Y in anos_v[2:]:
        tr = (b["ANO"].isin([a for a in anos_v if a < Y])).to_numpy()
        te = (b["ANO"] == Y).to_numpy()
        ds, kss = [], []
        for n in NORMS:
            x = V[(v, n)].to_numpy()
            dsd = np.nanstd(x[tr])
            d = (np.nanmean(x[te]) - np.nanmean(x[tr])) / dsd if dsd > 0 else np.nan
            k = ks(x[tr], x[te])
            est[(v, n, Y)] = (d, k)
            reg("estacionariedade", n, v, Y, "d_treino_teste", d)
            reg("estacionariedade", n, v, Y, "ks", k)
            ds.append(d); kss.append(k)
        info(f"       {Y}   " + " ".join(f"{d:+7.3f}" for d in ds) + "  | "
             + " ".join(f"{k:8.3f}" for k in kss))
info("")
info("Resumo (máximo |d| e máximo KS sobre os folds):")
info("  coluna  método    máx |d|   máx KS")
for v in ("IIB", "IEP", "IIE"):
    for n in NORMS:
        ys = [Y for (vv, nn, Y) in est if vv == v and nn == n]
        md = max(abs(est[(v, n, Y)][0]) for Y in ys)
        mk = max(est[(v, n, Y)][1] for Y in ys)
        info(f"  {v:5s}   {n:7s}   {md:6.3f}   {mk:6.3f}")
        reg("estacionariedade", n, v, None, "max_abs_d", md); reg("estacionariedade", n, v, None, "max_ks", mk)
for n in NORMS:
    ys = [Y for (vv, nn, Y) in est if vv == "IIE" and nn == n]
    md = max(abs(est[("IIE", n, Y)][0]) for Y in ys)
    flag(faixa(md, LIM_ESTAC_OK, LIM_ESTAC_ATENCAO),
         f"IIE_{n}: no pior fold a média do teste fica a {md:.2f} dp do treino "
         f"(limites ≤{LIM_ESTAC_OK} ok, ≤{LIM_ESTAC_ATENCAO} atenção)")
info("")
info("Nota sobre o KS do zano: as dimensões são somas discretas; a cada ano o z leva cada soma")
info("para uma posição diferente (média e dp do ano), então treino e teste ficam com 'degraus'")
info("em lugares distintos e o KS sobe sem que a forma tenha mudado. Leia o KS do zano com")
info("cautela; o d (deslocamento de média) é a medida principal.")
info("")
info("Leitura: zano é estacionário em média e dp por construção; o KS mostra o que sobra")
info("(mudança de forma). Para prop/zref19, d alto significa que o teste cai numa região")
info("de valores que o treino quase não viu — risco para árvores, que não extrapolam, e")
info("para qualquer modelo que aprenda 'infra alta = ano recente' em vez de 'infra alta = escola melhor'.")

# ================================================================
secao("7. ROBUSTEZ DO IIE AOS PESOS")
# ================================================================
info("O IIE usa pesos do 1º componente principal calculados em 2019 (iguais nos 3 métodos).")
info("Aqui: pesos recalculados por ano, pesos acumulados até t (sem olhar o futuro) e pesos iguais.")
ok4 = {a: (b["ANO"] == a).to_numpy() for a in anos}
W = {}
info("")
info("  ano    autovalor  var.PC1   pesos PC1 (IIB IDA IDP IEP)")
for a in [x for x in anos if x >= ANO_MIN_IIE]:
    X = np.column_stack([V[(d, "zano")].to_numpy()[ok4[a]] for d in DN])
    X = X[~np.isnan(X).any(axis=1)]
    R = np.corrcoef(X.T)
    w, lam, frac = pc1(R)
    W[a] = w
    reg("pesos", "todos", "IIE", a, "autovalor_pc1", lam); reg("pesos", "todos", "IIE", a, "var_pc1", frac[0])
    for d, wi in zip(DN, w):
        reg("pesos", "todos", d, a, "peso_pc1", wi)
    info(f"  {a}   {lam:6.3f}    {frac[0] * 100:5.1f}%    " + " ".join(f"{x:.3f}" for x in w))
w19 = W[ANO_REF]
dmax = max(np.abs(W[a] - w19).max() for a in W)
info(f"  desvio máximo de qualquer peso anual em relação a 2019: {dmax:.3f}")

info("")
info("Spearman, dentro do ano, entre o IIE atual (pesos de 2019) e variantes (mín. e média sobre os anos):")
info("  método    anual          acumulado até t     pesos iguais")
pesos_res = {}
for n in NORMS:
    X = np.column_stack([V[(d, n)].to_numpy() for d in DN])
    atual = V[("IIE", n)].to_numpy()
    r_ano, r_exp, r_eq = [], [], []
    for a in [x for x in anos if x >= ANO_MIN_IIE]:
        m = ok4[a]
        r_ano.append(sp(atual[m], X[m] @ W[a]))
        pool = np.concatenate([np.flatnonzero(ok4[y]) for y in anos if ANO_MIN_IIE <= y <= a])
        Xp = X[pool]
        Xp = Xp[~np.isnan(Xp).any(axis=1)]
        wexp, _, _ = pc1(np.corrcoef(Xp.T))
        r_exp.append(sp(atual[m], X[m] @ wexp))
        r_eq.append(sp(atual[m], np.nanmean(X[m], axis=1)))
    pesos_res[n] = (min(r_ano), np.mean(r_ano), min(r_exp), np.mean(r_exp), min(r_eq), np.mean(r_eq))
    p = pesos_res[n]
    for nm, vals in (("anual", r_ano), ("acumulado", r_exp), ("iguais", r_eq)):
        reg("pesos", n, "IIE", None, f"spearman_min_{nm}", min(vals))
    info(f"  {n:7s}   {p[0]:.4f} ({p[1]:.4f})  {p[2]:.4f} ({p[3]:.4f})    {p[4]:.4f} ({p[5]:.4f})")
pior_pesos = min(min(pesos_res[n][0], pesos_res[n][2], pesos_res[n][4]) for n in NORMS)
flag(faixa(1 - pior_pesos, 1 - LIM_PESOS_OK, 1 - LIM_PESOS_ATENCAO),
     f"mudar a forma de ponderar o IIE altera a ordenação no máximo a {pior_pesos:.4f} de Spearman "
     f"(limites ≥{LIM_PESOS_OK} ok, ≥{LIM_PESOS_ATENCAO} atenção)")
info("")
info("Leitura: se esse valor é próximo de 1, a dependência dos pesos de 2019 é inofensiva para")
info("a ordenação — e trocar para pesos acumulados (sem vazamento) ou iguais é uma opção barata.")
info("IIE_prop aplica pesos pensados para dimensões padronizadas a dimensões em escala 0–1;")
info("essa é uma diferença do artigo (que padroniza antes) — ver Spearman prop×zano na seção 2.")

# ================================================================
secao("8. SENSIBILIDADE DO zref19 AO RECORTE DE REFERÊNCIA")
# ================================================================
base_f = b.copy()
for i in ITENS:
    base_f[i] = fl(base_f[i])
soma = pd.DataFrame({d: base_f[l].sum(axis=1, min_count=len(l)) for d, l in DIMS.items()})
est19 = base_f["DEPENDENCIA"].astype(str).str.lower().str.startswith("estad")
recortes = {
    "atual (estadual, 2019, com taxa EM)": (b["ANO"] == ANO_REF) & est19 & base_f["APROVACAO_MED"].notna(),
    "estadual, 2019 (sem filtro de EM)": (b["ANO"] == ANO_REF) & est19,
    "todas as escolas, 2019": (b["ANO"] == ANO_REF),
}
# nota: APROVACAO_MED só é usado para reconstruir o recorte do 05 (filtro de oferta de EM), não como preditor
cur = V[("IIE", "zref19")].to_numpy()
info("Parâmetros (média ± dp da soma bruta) e efeito no IIE_zref19, 2012–2025:")
info("  recorte                                  n     IIB          IDA          IDP          IEP        Δnível(dp)  Spearman")
rec_res = {}
for nome, msk in recortes.items():
    m = msk.to_numpy() & soma.notna().all(axis=1).to_numpy()
    mu, sd = soma[m].mean(), soma[m].std(ddof=0)
    Z = (soma - mu) / sd
    w, _, _ = pc1(np.corrcoef(Z[m].to_numpy().T))
    alt = (Z.to_numpy() @ w)
    sel = ~np.isnan(alt) & ~np.isnan(cur)
    dif = alt[sel] - cur[sel]
    desl = abs(dif.mean()) / np.nanstd(cur[sel])
    r = sp(alt[sel], cur[sel])
    rec_res[nome] = (int(m.sum()), desl, r)
    reg("recorte", "zref19", "IIE", None, f"deslocamento_dp__{nome}", desl)
    reg("recorte", "zref19", "IIE", None, f"spearman__{nome}", r)
    cel = "  ".join(f"{mu[d]:.2f}±{sd[d]:.2f}" for d in DN)
    info(f"  {nome:38s} {int(m.sum()):4d}  {cel}   {desl:6.3f}     {r:.4f}")
# autoconferência: o recorte atual reproduz a coluna gravada pelo 05
nome0 = list(recortes)[0]
m0 = recortes[nome0].to_numpy() & soma.notna().all(axis=1).to_numpy()
mu, sd = soma[m0].mean(), soma[m0].std(ddof=0)
w0, _, _ = pc1(np.corrcoef(((soma - mu) / sd)[m0].to_numpy().T))
rep = ((soma - mu) / sd).to_numpy() @ w0
sel = ~np.isnan(rep) & ~np.isnan(cur)
err = np.abs(rep[sel] - cur[sel]).max()
(flag("ok", f"autoconferência: reproduzi o IIE_zref19 do 05 (erro máximo {err:.1e})")
 if err < 1e-8 else flag("fail", f"NÃO reproduzi o IIE_zref19 do 05 (erro máximo {err:.2e}) — rever esta análise"))
info("")
info("As duas linhas alternativas são OUTRAS POPULAÇÕES de referência (373 e 667 escolas), não")
info("variações do recorte do artigo: mostram que o nível do zref19 é relativo à população")
info("escolhida (propriedade do método, não erro). O que importa para a incerteza do 152 x 165 é a")
info("reamostragem abaixo.")
rng = np.random.default_rng(20190101)
ref_idx = np.flatnonzero(m0)
Z_all_src = soma.to_numpy()
desl_bs, rho_bs = [], []
sel2 = ~np.isnan(cur)
for _ in range(300):
    pick = rng.choice(ref_idx, size=len(ref_idx), replace=True)
    mu_b, sd_b = Z_all_src[pick].mean(axis=0), Z_all_src[pick].std(axis=0)
    wb, _, _ = pc1(np.corrcoef(((Z_all_src[pick] - mu_b) / sd_b).T))
    alt = ((Z_all_src - mu_b) / sd_b) @ wb
    s_ = sel2 & ~np.isnan(alt)
    desl_bs.append(abs((alt[s_] - cur[s_]).mean()) / np.nanstd(cur[s_]))
    rho_bs.append(sp(alt[s_], cur[s_]))
p95 = float(np.percentile(desl_bs, 95))
reg("recorte", "zref19", "IIE", None, "bootstrap_desloc_p95_dp", p95)
reg("recorte", "zref19", "IIE", None, "bootstrap_spearman_min", float(np.min(rho_bs)))
info(f"Reamostragem (300×) das {len(ref_idx)} escolas de referência: deslocamento do nível do")
info(f"IIE_zref19 — mediana {np.median(desl_bs):.3f} dp, percentil 95 {p95:.3f} dp; Spearman mínimo {np.min(rho_bs):.4f}.")
flag(faixa(p95, LIM_RECORTE_OK, LIM_RECORTE_ATENCAO),
     f"incerteza amostral do recorte de 152 escolas: nível do IIE_zref19 muda ≤ {p95:.2f} dp (p95) "
     f"(limites ≤{LIM_RECORTE_OK} ok, ≤{LIM_RECORTE_ATENCAO} atenção)")
info("")
info("Leitura: o recorte do artigo (165 escolas estaduais de EM) não está replicado (aqui 152).")
info("Só o zref19 depende de uma população de referência fixa; prop não tem parâmetros e o")
info("zano usa as próprias escolas de cada ano.")

# ================================================================
secao("9. DEPENDÊNCIAS E VAZAMENTO TEMPORAL (regra 4 do CLAUDE.md)")
# ================================================================
dep = [
    ("prop",   "nenhum parâmetro nas dimensões",
     "pesos do IIE de 2019", "não", "0–1 (fração de itens)"),
    ("zano",   "média/dp das escolas do PRÓPRIO ano t",
     "pesos do IIE de 2019", "não (só usa o ano t)", "relativa: posição entre as escolas do ano"),
    ("zref19", "média/dp fixos de 2019 (recorte de 152 escolas)",
     "pesos do IIE de 2019", "SIM em folds com teste < 2019", "absoluta: distância ao padrão de 2019"),
]
for n, p1, p2, vz, esc in dep:
    info(f"  {n}:")
    info(f"      parâmetros das dimensões : {p1}")
    info(f"      pesos do IIE             : {p2}")
    info(f"      usa dado futuro em folds com teste antes de 2019? {vz}")
    info(f"      escala/interpretação     : {esc}")
info("")
info("Os pesos do IIE (2019) são comuns aos 3 métodos e, estritamente, também usam dado de")
info("2019 em folds anteriores. A seção 7 mede quanto isso importa para a ordenação.")
info("Fidelidade ao artigo (z-score das dimensões sobre as escolas estaduais de EM de 2019):")
info("zref19 é o mais próximo para 2019; zano repete o procedimento do artigo a cada ano,")
info("sobre todas as escolas da base; prop é uma simplificação sem equivalente no artigo.")

# ================================================================
secao("10. RESUMO DOS CRITÉRIOS")
# ================================================================
SIM = {"ok": "✅", "warn": "⚠️ ", "fail": "❌"}
ORD = {"ok": 0, "warn": 1, "fail": 2}
crit = {}   # (critério, método) -> nivel


def pior(*ns):
    return max(ns, key=lambda k: ORD[k])


L_COB = "Cobertura (2012+ completa)"
L_FUT = "Parâmetros das dimensões sem dado futuro"
L_PES = "Pesos do IIE (2019) sem dado futuro"
L_TIE = "Tendência de nível entre anos — IIE"
L_TID = "Tendência de nível entre anos — dimensões"
L_QIE = "Quebra de questionário — IIE"
L_QID = "Quebra de questionário — dimensões"
L_EIE = "Estacionariedade treino→teste — IIE"
L_EID = "Estacionariedade treino→teste — dimensões"
L_REC = "Independência da população de referência"
L_ORD = "Ordenação dentro do ano"
linhas = [L_COB, L_FUT, L_PES, L_TIE, L_TID, L_QIE, L_QID, L_EIE, L_EID, L_REC, L_ORD]
for n in NORMS:
    crit[(L_COB, n)] = "ok"
    crit[(L_FUT, n)] = "fail" if n == "zref19" else "ok"
    crit[(L_PES, n)] = faixa(1 - pesos_res[n][2], 1 - LIM_PESOS_OK, 1 - LIM_PESOS_ATENCAO)
    crit[(L_PES, n)] = pior("warn", crit[(L_PES, n)])   # vazamento estrito em folds < 2019, nos 3
    crit[(L_TIE, n)] = faixa(eta[("IIE", n)], LIM_TENDENCIA_OK, LIM_TENDENCIA_ATENCAO)
    crit[(L_TID, n)] = faixa(max(eta[(d, n)] for d in DN), LIM_TENDENCIA_OK, LIM_TENDENCIA_ATENCAO)
    crit[(L_QIE, n)] = faixa(resumo_q[("IIE", n)][1], LIM_QUEBRA_OK, LIM_QUEBRA_ATENCAO)
    crit[(L_QID, n)] = faixa(max(resumo_q[(d, n)][1] for d in ("IIB", "IEP")), LIM_QUEBRA_OK, LIM_QUEBRA_ATENCAO)
    ysI = [Y for (vv, nn, Y) in est if vv == "IIE" and nn == n]
    crit[(L_EIE, n)] = faixa(max(abs(est[("IIE", n, Y)][0]) for Y in ysI), LIM_ESTAC_OK, LIM_ESTAC_ATENCAO)
    crit[(L_EID, n)] = faixa(max(abs(est[(d, n, Y)][0]) for d in ("IIB", "IEP")
                                 for Y in [y for (vv, nn, y) in est if vv == d and nn == n]),
                             LIM_ESTAC_OK, LIM_ESTAC_ATENCAO)
    crit[(L_REC, n)] = pior("warn", faixa(p95, LIM_RECORTE_OK, LIM_RECORTE_ATENCAO)) if n == "zref19" else "ok"
    crit[(L_ORD, n)] = "ok"
info(f"  {'critério':46s} {'prop':>6s} {'zano':>6s} {'zref19':>7s}")
for c in linhas:
    info(f"  {c:46s} " + " ".join(f"{SIM[crit[(c, n)]]:>6s}" for n in NORMS))
info("")
for n in NORMS:
    cnt = {k: sum(1 for c in linhas if crit[(c, n)] == k) for k in ("ok", "warn", "fail")}
    info(f"  {n:7s}: ✅ {cnt['ok']}   ⚠️  {cnt['warn']}   ❌ {cnt['fail']}")
    for c in linhas:
        reg("resumo", n, c, None, "nivel(0=ok,1=atencao,2=falha)", ORD[crit[(c, n)]])
info("")
info("Notas:")
info("  • 'Pesos do IIE (2019)': os 3 métodos herdam o mesmo problema (folds com teste < 2019 usam")
info("    pesos estimados em 2019). Marcado ⚠️ nos 3 por rigor; a seção 7 mostra que trocar por pesos")
info("    acumulados até t muda a ordenação do IIE em no máximo ~0,002 de Spearman.")
info("  • 'Parâmetros das dimensões sem dado futuro': só o zref19 falha (média/dp de 2019).")
info("  • 'Independência da população de referência': zref19 é relativo a uma população fixa,")
info("    que ainda não replica o recorte do artigo (152 x 165).")
info("  • ⚠️ nas linhas de 'dimensões' para prop/zref19 refletem a quebra de água/banheiro em 2019")
info("    (IIB) e o crescimento de IEP; o IIE agregado dilui esses efeitos.")
info("")
info("O QUE ESTA ANÁLISE NÃO DECIDE: se o desempenho preditivo melhora com um método ou outro.")
info("Isso não pode ser escolhido pela correlação com o alvo (regra 3). A comparação preditiva")
info("só entra na fase de modelagem, com o método tratado como hiperparâmetro dentro do")
info("walk-forward, com a especificação congelada antes de olhar o fold final.")

# ================================================================
secao("RESUMO DA EXECUÇÃO")
# ================================================================
log.append(f"  ✅ Leituras OK:       {cont['ok']}")
log.append(f"  ⚠️  Atenção:          {cont['warn']}")
log.append(f"  ❌ Falhas/limitações: {cont['fail']}")
log.append("  (as marcas de ⚠️/❌ são sinais para a decisão, não erros do pipeline;")
log.append("   só o ❌ da autoconferência da seção 8 indicaria erro desta análise)")
txt = "\n".join(log)
print(txt)
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(txt, encoding="utf-8")
pd.DataFrame(met, columns=["secao", "metodo", "variavel", "ano", "metrica", "valor"]).to_csv(
    CSV, index=False, encoding="utf-8-sig")
print(f"\n>>> Relatório: {REPORT}\n>>> Métricas:  {CSV}")
sys.exit(0)
