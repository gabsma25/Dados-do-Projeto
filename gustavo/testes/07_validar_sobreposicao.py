# -*- coding: utf-8 -*-
"""
07 — Confere, célula por célula, o rendimento de 2019–2025 nas duas bases que a
avaliação junta (avaliacao/painel.py): saida/base_atual.parquet, de onde vem o
rendimento, e a base longitudinal oficial, de onde vêm TDI, ATU e IED
(abandono-escolar/dados/processado/base_longitudinal_rr_2019_2025.parquet).

As duas harmonizam o tx_rend do INEP com códigos diferentes, mas em 2019–2025
leem as mesmas planilhas: os valores têm de ser iguais. O
programas/02_tx_rend_selecionado_longitudinal.py faz a mesma comparação com o
02b (relatorios/validacao_longitudinal.txt); este teste confere a base final,
depois das etapas 03–05.

  A. Chaves, anos e colunas
       ANO + CO_ENTIDADE único nas duas bases; os 7 anos nas duas; as mesmas
       colunas de rendimento (APROVACAO_, REPROVACAO_, ABANDONO_) dos dois lados.
  B. Linhas
       toda escola-ano do gustavo tem par na oficial. A oficial tem escolas-ano
       a mais, porque o universo dela é a união das chaves das planilhas de
       indicadores (src/base_longitudinal.py, etapa 2): quase todas são escolas
       só de educação infantil, que estão na planilha de ATU e não nas de
       rendimento. Confere-se que nenhuma tem taxa de rendimento.
  C. Valores, coluna a coluna
       mesma ausência e mesmo valor (tolerância 1e-9). _LAG1 e _DELTA1 são
       comparados de 2020 em diante: em 2019 dependem de 2018, que só o gustavo
       tem; confere-se que a oficial está vazia ali (ausência estrutural).

Saída: gustavo/saida/relatorios/validacao_sobreposicao.txt
Uso:   python testes/07_validar_sobreposicao.py
       (depois do programas/05_indices_infra.py, que grava a base_atual; a base
       oficial é a do `python -m src.base_longitudinal`, no abandono-escolar)
"""
import sys
from pathlib import Path

import pandas as pd

GUSTAVO = Path(__file__).resolve().parent.parent
P_ATUAL = GUSTAVO / "saida" / "base_atual.parquet"
P_OFICIAL = (GUSTAVO.parent / "abandono-escolar" / "dados" / "processado"
             / "base_longitudinal_rr_2019_2025.parquet")
REPORT = GUSTAVO / "saida" / "relatorios" / "validacao_sobreposicao.txt"
CHAVE = ["ANO", "CO_ENTIDADE"]
ANOS = list(range(2019, 2026))
PREFIXOS = ("APROVACAO_", "REPROVACAO_", "ABANDONO_")
PASSADO = ("_LAG1", "_DELTA1")   # em 2019 dependem de 2018
DERIVADAS = PASSADO + ("_T1",)
TOLERANCIA = 1e-9                # a mesma da comparação com a v1.0 (DECISOES, 2026-09-30)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")   # ✅/❌ não existem em cp1252 (saída redirecionada no Windows)

log, cont = [], {"ok": 0, "fail": 0}


def ok(m):
    cont["ok"] += 1; log.append(f"  ✅ {m}")


def fail(m):
    cont["fail"] += 1; log.append(f"  ❌ {m}")


def check(cond, m):
    (ok if cond else fail)(m)


for p in (P_ATUAL, P_OFICIAL):
    if not p.exists():
        raise SystemExit(f"[ERRO] não achei {p}")
g = pd.read_parquet(P_ATUAL)
o = pd.read_parquet(P_OFICIAL)
g = g[g["ANO"].between(ANOS[0], ANOS[-1])].copy()
for d in (g, o):
    d["CO_ENTIDADE"] = d["CO_ENTIDADE"].astype("string")
    d["ANO"] = d["ANO"].astype("Int16")

# ------------------------------------------------- A. chaves, anos e colunas
log.append("A. Chaves, anos e colunas")
dup_g, dup_o = int(g.duplicated(CHAVE).sum()), int(o.duplicated(CHAVE).sum())
check(dup_g == 0 and dup_o == 0,
      f"ANO + CO_ENTIDADE único nas duas bases (gustavo 2019–2025: {len(g)} linhas, oficial: {len(o)}; "
      f"repetidos: {dup_g} e {dup_o})")
anos_g = sorted(int(a) for a in g["ANO"].unique())
anos_o = sorted(int(a) for a in o["ANO"].unique())
anos_ok = anos_g == ANOS and anos_o == ANOS
check(anos_ok, "2019–2025, ano a ano, nas duas bases"
      + ("" if anos_ok else f" (gustavo {anos_g}; oficial {anos_o})"))
rend_g = {c for c in g.columns if c.startswith(PREFIXOS)}
rend_o = {c for c in o.columns if c.startswith(PREFIXOS)}
cols = sorted(rend_g & rend_o)
taxas = [c for c in cols if not c.endswith(DERIVADAS)]
de_um_lado = sorted(rend_g ^ rend_o)
check(bool(cols) and not de_um_lado,
      f"as mesmas {len(cols)} colunas de rendimento nas duas bases ({len(taxas)} taxas do ano e "
      f"{len(cols) - len(taxas)} derivadas)" + (f"; só de um lado: {', '.join(de_um_lado)}" if de_um_lado else ""))

# ------------------------------------------------------------- B. linhas
log.append("")
log.append("B. Linhas")
m = g[CHAVE + cols].merge(o[CHAVE + cols], on=CHAVE, how="outer", suffixes=("_g", "_o"), indicator=True)
sem_par = int((m["_merge"] == "left_only").sum())
dica = "; nenhuma casou: confira o tipo de CO_ENTIDADE" if len(g) and sem_par == len(g) else ""
check(sem_par == 0, f"toda escola-ano do gustavo tem par na oficial ({len(g) - sem_par} de {len(g)}){dica}")
so_oficial = m[m["_merge"] == "right_only"]
com_taxa = int(so_oficial[[f"{c}_o" for c in taxas]].notna().any(axis=1).sum())
check(bool(taxas) and com_taxa == 0,
      f"as {len(so_oficial)} escolas-ano só da oficial não têm nenhuma das {len(taxas)} taxas do ano "
      f"(com alguma: {com_taxa})")

# ------------------------------------------------- C. valores, coluna a coluna
log.append("")
log.append(f"C. Valores, coluna a coluna (tolerância {TOLERANCIA:.0e}; _LAG1 e _DELTA1 de 2020 em diante)")
m = m[m["_merge"] == "both"]
em_2019 = (m["ANO"] == 2019).to_numpy(dtype=bool)
for c in cols:
    a, b = m[f"{c}_g"].astype("Float64"), m[f"{c}_o"].astype("Float64")
    nota, vazia_2019 = "", True
    if c.endswith(PASSADO):
        n_o19, n_g19 = int(b[em_2019].notna().sum()), int(a[em_2019].notna().sum())
        vazia_2019 = n_o19 == 0
        estado = "vazia" if vazia_2019 else f"com {n_o19} valores (esperado: vazia)"
        nota = f"; 2019: oficial {estado}, gustavo com {n_g19} (vêm de 2018)"
        a, b = a[~em_2019], b[~em_2019]
    aus = int((a.isna() != b.isna()).sum())
    ambos = a.notna() & b.notna()
    dif = (a[ambos] - b[ambos]).abs()
    n_ambos, n_dif = int(ambos.sum()), int((dif > TOLERANCIA).sum())
    maior = float(dif.max()) if n_ambos else 0.0
    check(n_ambos > 0 and aus == 0 and n_dif == 0 and vazia_2019,
          f"{c}: {n_ambos} valores nas duas, {n_dif} diferentes (maior dif. {maior:.1e}); "
          f"ausência difere em {aus}{nota}")

log.append("")
log.append(f"RESUMO: {cont['ok']} OK, {cont['fail']} falhas")
txt = "\n".join(log)
print(txt)
REPORT.write_text(txt, encoding="utf-8")
sys.exit(1 if cont["fail"] else 0)
