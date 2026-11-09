# -*- coding: utf-8 -*-
"""
05 — Confere a saída da análise 03 (associações descritivas) contra os
números registrados em abandono-escolar/docs/DECISOES.md (entrada "Correção
de hipóteses", 2026-11-02) e docs/problemas.csv (P026).

Os valores registrados estão abaixo, com a casa decimal com que foram
registrados; a tolerância é meia unidade dessa casa. A decomposição entre /
dentro da escola (bloco D) foi registrada no DECISOES.md em 2026-11-03, a
partir deste mesmo script, e é conferida contra esse registro (com o n).

Saída: gustavo/saida/relatorios/validacao_associacoes.txt
Uso:   python analises/03_associacoes_descritivas.py && python testes/05_validar_associacoes.py
"""
import sys
from pathlib import Path

import pandas as pd

GUSTAVO = Path(__file__).resolve().parent.parent
P_SAIDA = GUSTAVO / "saida" / "relatorios" / "associacoes_descritivas.csv"
REPORT = GUSTAVO / "saida" / "relatorios" / "validacao_associacoes.txt"

# (bloco, etapa, medida, metodo): (valor registrado, casas decimais) — DECISOES.md 2026-11-02
REGISTRADO = {
    ("A", "AF", "TDI(t) x REPROVACAO(t-1)", "pearson"): (0.226, 3),
    ("A", "AF", "TDI(t) x REPROVACAO(t-1)", "spearman"): (0.150, 3),
    ("A", "EM", "TDI(t) x REPROVACAO(t-1)", "pearson"): (-0.012, 3),
    ("A", "EM", "TDI(t) x REPROVACAO(t-1)", "spearman"): (-0.137, 3),
    ("A", "AF", "TDI(t) x ABANDONO(t-1)", "pearson"): (0.361, 3),
    ("A", "AF", "TDI(t) x ABANDONO(t-1)", "spearman"): (0.271, 3),
    ("A", "EM", "TDI(t) x ABANDONO(t-1)", "pearson"): (0.212, 3),
    ("A", "EM", "TDI(t) x ABANDONO(t-1)", "spearman"): (0.162, 3),
    ("A", "AF", "TDI(t) x TDI(t-1)", "pearson"): (0.882, 3),
    ("A", "AF", "TDI(t) x TDI(t-1)", "spearman"): (0.858, 3),
    ("A", "EM", "TDI(t) x TDI(t-1)", "pearson"): (0.860, 3),
    ("A", "EM", "TDI(t) x TDI(t-1)", "spearman"): (0.829, 3),
    ("A", "AF", "ABANDONO(t) x ABANDONO(t-1)", "pearson"): (0.250, 3),
    ("A", "EM", "ABANDONO(t) x ABANDONO(t-1)", "pearson"): (0.226, 3),
    ("A", "escola", "IIE_zano(t) x IIE_zano(t-1)", "spearman"): (0.98, 2),
    ("B", "AF", "TDI x alvo(t+1)", "spearman"): (0.287, 3),
    ("B", "AF", "abandono(t) x alvo(t+1)", "spearman"): (0.233, 3),
    ("B", "AF", "abandono(t-1) x alvo(t+1)", "spearman"): (0.183, 3),
    ("B", "AF", "ATU x alvo(t+1)", "spearman"): (0.032, 3),
    ("B", "EM", "TDI x alvo(t+1)", "spearman"): (0.233, 3),
    ("B", "EM", "abandono(t) x alvo(t+1)", "spearman"): (0.207, 3),
    ("B", "EM", "IED_ALTO x alvo(t+1)", "spearman"): (0.184, 3),
    ("B", "EM", "ATU x alvo(t+1)", "spearman"): (-0.048, 3),
    ("B", "EM", "abandono(t-1) x alvo(t+1)", "spearman"): (0.023, 3),
}
# bloco D — DECISOES.md, decomposição recalculada em 2026-11-03: (valor, casas, n)
DECOMPOSICAO = {
    ("AF", "TDI(t) x abandono(t+1): entre escolas (médias por escola)"): (0.601, 3, 252),
    ("AF", "TDI(t) x abandono(t+1): dentro da escola (desvios da média)"): (0.033, 3, 1382),
    ("AF", "TDI(t) x abandono(t+1): total (sem decompor)"): (0.346, 3, 1395),
    ("EM", "TDI(t) x abandono(t+1): entre escolas (médias por escola)"): (0.432, 3, 169),
    ("EM", "TDI(t) x abandono(t+1): dentro da escola (desvios da média)"): (0.046, 3, 960),
    ("EM", "TDI(t) x abandono(t+1): total (sem decompor)"): (0.264, 3, 963),
}
# faixas registradas (mín, máx) com 2 casas — dimensões e P026 (rendimento: 0,17–0,20,
# corrigida no registro em 2026-11-03; estava 0,18–0,20)
FAIXAS = {
    "dimensões da infraestrutura, persistência (Spearman)": (
        lambda d: d[(d["bloco"] == "A") & d["medida"].str.startswith("DIM_")], (0.80, 0.96)),
    "P026: MDI do trio somado (3 sementes)": (
        lambda d: d[d["medida"].str.startswith("MDI com trio: trio somado")], (0.41, 0.42)),
    "P026: MDI do TDI com trio (3 sementes)": (
        lambda d: d[d["medida"].str.startswith("MDI com trio: TDI")], (0.33, 0.34)),
    "P026: permutação de bloco, TDI (3 sementes)": (
        lambda d: d[d["medida"].str.startswith("permutação de bloco: TDI")], (0.25, 0.35)),
    "P026: permutação de bloco, rendimento (3 sementes)": (
        lambda d: d[d["medida"].str.startswith("permutação de bloco: rendimento")], (0.17, 0.20)),
}

log, cont = [], {"ok": 0, "fail": 0}


def ok(m):
    cont["ok"] += 1; log.append(f"  ✅ {m}")


def fail(m):
    cont["fail"] += 1; log.append(f"  ❌ {m}")


d = pd.read_csv(P_SAIDA)
log.append("Valores pontuais registrados no DECISOES.md")
for (bloco, etapa, medida, metodo), (reg, casas) in REGISTRADO.items():
    sel = d[(d["bloco"] == bloco) & (d["etapa"] == etapa) & (d["medida"] == medida) & (d["metodo"] == metodo)]
    if len(sel) != 1:
        fail(f"{etapa} {medida} {metodo}: {len(sel)} linhas na saída")
        continue
    v = float(sel["valor"].iloc[0])
    msg = f"{etapa} {medida} ({metodo}): obtido {v:+.{casas + 1}f}, registrado {reg:+.{casas}f}"
    (ok if abs(v - reg) <= 0.5 * 10 ** -casas + 1e-12 else fail)(msg)
log.append("")
log.append("Faixas registradas (mín–máx, 2 casas)")
for nome, (filtro, (lo, hi)) in FAIXAS.items():
    v = filtro(d)["valor"]
    vmin, vmax = round(float(v.min()), 2), round(float(v.max()), 2)
    msg = f"{nome}: obtido {vmin:.2f}–{vmax:.2f}, registrado {lo:.2f}–{hi:.2f} (n={len(v)})"
    (ok if (vmin == lo and vmax == hi) else fail)(msg)
log.append("")
log.append("Decomposição entre / dentro da escola (bloco D), registrada no DECISOES.md")
for (etapa, medida), (reg, casas, n_reg) in DECOMPOSICAO.items():
    sel = d[(d["bloco"] == "D") & (d["etapa"] == etapa) & (d["medida"] == medida)]
    if len(sel) != 1:
        fail(f"{etapa} {medida}: {len(sel)} linhas na saída")
        continue
    v, n = float(sel["valor"].iloc[0]), int(sel["n"].iloc[0])
    msg = f"{etapa} {medida}: obtido {v:+.{casas + 1}f} (n={n}), registrado {reg:+.{casas}f} (n={n_reg})"
    (ok if abs(v - reg) <= 0.5 * 10 ** -casas + 1e-12 and n == n_reg else fail)(msg)
n_rf = d[d["bloco"] == "C"]["n"]
(ok if int(n_rf[d["medida"].str.startswith("MDI")].iloc[0]) == 1390 else fail)(
    f"P026: n do Random Forest = {int(n_rf[d['medida'].str.startswith('MDI')].iloc[0])} (registrado 1.390)")
log.append("")
log.append(f"RESUMO: {cont['ok']} OK, {cont['fail']} falhas")
txt = "\n".join(log)
print(txt)
REPORT.write_text(txt, encoding="utf-8")
sys.exit(1 if cont["fail"] else 0)
