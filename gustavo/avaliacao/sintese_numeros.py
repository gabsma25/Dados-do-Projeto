# -*- coding: utf-8 -*-
"""
Números de referência para a síntese do projeto (regra 9 do CLAUDE.md: toda
contagem publicada sai de código). Só lê; não altera base nem saída de etapa.

Saída: gustavo/saida/avaliacao/sintese_numeros.csv  (grupo, item, valor, fonte)
Uso:   python avaliacao/sintese_numeros.py
"""
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import baselines as B  # noqa: E402
import painel as P  # noqa: E402

G = Path(__file__).resolve().parent.parent
AV = G / "saida" / "avaliacao"
DADOS = G.parent / "abandono-escolar" / "dados"
linhas = []


def reg(grupo, item, valor, fonte):
    linhas.append({"grupo": grupo, "item": item, "valor": valor, "fonte": fonte})


# ---- bases ----
for nome, p in [("base_atual", G / "saida" / "base_atual.parquet"),
                ("base oficial", P.P_OFICIAL),
                ("03_censo_features", G / "saida" / "etapas" / "03_censo_features.parquet")]:
    d = pd.read_parquet(p)
    reg("bases", f"{nome}: linhas × colunas", f"{d.shape[0]} × {d.shape[1]}", str(p.relative_to(G.parent)))
    reg("bases", f"{nome}: anos", f"{int(d['ANO'].min())}–{int(d['ANO'].max())}", str(p.relative_to(G.parent)))
    reg("bases", f"{nome}: escolas distintas", d["CO_ENTIDADE"].nunique(), str(p.relative_to(G.parent)))
atual = pd.read_parquet(P.P_ATUAL)

# ---- universo e abandono médio por ano (públicas com taxa na etapa) ----
pub = atual[atual["REDE_PUBLICA"].astype("Int8") == 1]
for etapa, col in B.ETAPAS.items():
    s = pub[["ANO", col]].dropna()
    g = s.groupby("ANO")[col].agg(["size", "mean"])
    for ano, r in g.iterrows():
        reg(f"abandono médio {etapa} (públicas com taxa)", int(ano),
            f"{r['mean']:.2f} (n={int(r['size'])})", "base_atual.parquet")
    u = B.universo(atual, etapa)
    reg("universo Etapa 1", f"{etapa}: escolas-ano (pública + alvo t+1)", len(u), "baselines.universo")
    pn = P.montar(etapa, atual)
    reg("painel Etapa 2", f"{etapa}: escolas-ano (ANO 2019–2024)", len(pn), "painel.montar")
    te = pn[pn["ANO_ALVO"].between(2021, 2024)]
    reg("painel Etapa 2", f"{etapa}: teste agrupado 2021–2024, escolas-ano / escolas",
        f"{len(te)} / {te['CO_ENTIDADE'].nunique()}", "painel.montar")

# ---- larguras de intervalo ----
c = pd.read_csv(AV / "02b_celulas.csv")
c = c[c["cenario"] == "B"]
for (etapa, m), g in c.groupby(["etapa", "metrica"]):
    reg("largura IC 95% por ano (02b, modelos B)", f"{etapa} {m}", f"{(g['hi'] - g['lo']).median():.2f}",
        "02b_celulas.csv (mediana)")
lg = pd.read_csv(AV / "02c_largura.csv")
lg["tipo"] = lg["periodo"].where(lg["periodo"] == "agrupado", "por ano")
for (etapa, k, t), g in lg.groupby(["etapa", "K", "tipo"]):
    reg("largura IC 95% (02c, modelos B)", f"{etapa} {k} {t}", f"{g['largura'].median():.2f}",
        "02c_largura.csv (mediana)")
w = pd.read_csv(AV / "02_walkforward.csv")
wb = w[w["cenario"] == "B"]
for etapa, g in wb.groupby("etapa"):
    reg("Recall@10% observado", f"{etapa} modelos Cenário B (mín–máx)",
        f"{g['Rec@10'].min():.2f}–{g['Rec@10'].max():.2f}", "02_walkforward.csv")

# ---- Etapa 1 (baselines, 2009–2025) ----
e1 = pd.read_csv(AV / "01_baselines.csv")
for etapa, g in e1.groupby("etapa"):
    reg("Etapa 1", f"{etapa}: transições avaliadas", f"{len(g)} ({g['ano_alvo'].min()}–{g['ano_alvo'].max()})", "01_baselines.csv")
    reg("Etapa 1", f"{etapa}: anos com MAE B1 < MAE B0", f"{int((g['B1_MAE'] < g['B0_MAE']).sum())} de {len(g)}", "01_baselines.csv")
    reg("Etapa 1", f"{etapa}: anos com R² B1 > 0", f"{int((g['B1_R2'] > 0).sum())} de {len(g)}", "01_baselines.csv")
    for k in ("10", "20"):
        r = g[f"B1R_Rec@{k}"]
        reg("Etapa 1", f"{etapa}: B1R Recall@{k}% mín / mediana / máx",
            f"{r.min():.2f} / {r.median():.2f} / {r.max():.2f}", "01_baselines.csv")
        reg("Etapa 1", f"{etapa}: anos com B1R Recall@{k}% > aleatório",
            f"{int((r > g[f'B0_Rec@{k}']).sum())} de {len(g)}", "01_baselines.csv")

# ---- contagens de testes ----
d02b = pd.read_csv(AV / "02b_diferencas.csv")
d02b = d02b[d02b["cenario"] == "B"]
reg("testes", "02b: diferenças por ano (Cenário B), IC exclui zero, sem correção",
    f"{int((d02b['classe'] != 'indeterminado').sum())} de {len(d02b)}", "02b_diferencas.csv")
d02c = pd.read_csv(AV / "02c_diferencas.csv")
a = d02c[(d02c["periodo"] == "agrupado") & d02c["referencia"].isin(["B1R_lag", "bloco 1", "bloco 2", "bloco 3"])]
reg("testes", "02c: modelo − B1R_lag e entre blocos (agrupado, 3 K), IC exclui zero, sem correção",
    f"{int((a['classe'] != 'indeterminado').sum())} de {len(a)}", "02c_diferencas.csv")
t = pd.read_csv(AV / "02d_testes.csv")
for fam, g in t[t["primario"]].groupby("familia"):
    reg("testes 02d (Holm, K primário)", fam, f"{int(g['rejeita_holm'].sum())} de {len(g)}", "02d_testes.csv")
for item in ["TDI", "ATU", "rendimento", "IED", "infraestrutura"]:
    g = t[(t["familia"] == "F1") & (t["item"] == item)]
    reg("testes 02d F1 por grupo", item,
        f"IC>0 sem correção {int(g['ic_exclui_zero'].sum())}/{len(g)}; Holm {int(g['rejeita_holm'].sum())}/{int(g['primario'].sum())}",
        "02d_testes.csv")

# ---- dados em disco ----
for sub in ["origem", "bruto", "interim", "processado", "externo"]:
    p = DADOS / sub
    if p.exists():
        tam = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        reg("dados em disco", f"dados/{sub}", f"{tam / 1e9:.2f} GB" if tam >= 1e8 else f"{tam / 1e6:.1f} MB", "soma dos arquivos")
man = pd.read_csv(DADOS / "MANIFEST.csv")
reg("dados em disco", "MANIFEST.csv: linhas por estágio", man["estagio"].value_counts().to_dict(), "dados/MANIFEST.csv")
cache = G / "cache"
reg("dados em disco", "gustavo/cache", f"{sum(f.stat().st_size for f in cache.rglob('*') if f.is_file()) / 1e6:.1f} MB",
    "soma dos arquivos")
n_testes = subprocess.run([str(G.parent / "abandono-escolar" / ".venv" / "Scripts" / "python.exe"),
                           "-m", "pytest", "--collect-only", "-q"],
                          cwd=G.parent / "abandono-escolar", capture_output=True, text=True).stdout.strip().splitlines()
reg("testes", "abandono-escolar: testes pytest coletados", n_testes[-1] if n_testes else "?", "pytest --collect-only")

out = pd.DataFrame(linhas)
out["valor"] = out["valor"].astype(str)
out.to_csv(AV / "sintese_numeros.csv", index=False, encoding="utf-8")
print(out.to_string(index=False))
