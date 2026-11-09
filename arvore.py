"""Imprime a árvore de arquivos do projeto (mapa simples, só leitura).

Uso (na raiz do Dados-do-Projeto):
    python arvore.py                        # árvore completa na tela
    python arvore.py --nivel 2              # só até 2 níveis de pasta
    python arvore.py gustavo                # a partir de outra pasta
    python arvore.py --saida mapa.txt       # grava em arquivo em vez da tela

Pastas OCULTAS não aparecem; pastas RESUMIDAS aparecem numa linha, com o número de
arquivos (são grandes ou cópias antigas). Segue a junção abandono-escolar/.
"""
import argparse
import os
import sys
from pathlib import Path

OCULTAS = {".git", ".venv", "__pycache__", ".ruff_cache", ".pytest_cache", ".ipynb_checkpoints", ".claude"}
RESUMIDAS = {"dados", "cache", "etapas", "fixtures", "pipeline_ate_2026-10-09", "diagnosticos_saida",
             "certificados"}


def contar(pasta: Path) -> int:
    return sum(len(arquivos) for _, _, arquivos in os.walk(pasta))


def arvore(pasta: Path, prefixo: str, nivel: int, max_nivel: int | None, linhas: list[str]) -> None:
    try:
        itens = sorted(pasta.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except OSError as erro:
        linhas.append(f"{prefixo}└── [sem acesso: {erro.strerror}]")
        return
    itens = [p for p in itens if p.name not in OCULTAS]
    for i, p in enumerate(itens):
        ultimo = i == len(itens) - 1
        ramo, recuo = ("└── ", "    ") if ultimo else ("├── ", "│   ")
        if not p.is_dir():
            linhas.append(f"{prefixo}{ramo}{p.name}")
        elif p.name in RESUMIDAS:
            linhas.append(f"{prefixo}{ramo}{p.name}/  [{contar(p)} arquivos, resumida]")
        elif max_nivel is not None and nivel >= max_nivel:
            linhas.append(f"{prefixo}{ramo}{p.name}/  [{contar(p)} arquivos]")
        else:
            linhas.append(f"{prefixo}{ramo}{p.name}/")
            arvore(p, prefixo + recuo, nivel + 1, max_nivel, linhas)


def main() -> None:
    ap = argparse.ArgumentParser(description="Árvore de arquivos do projeto.")
    ap.add_argument("pasta", nargs="?", default=".", help="pasta de partida (padrão: a atual)")
    ap.add_argument("--nivel", type=int, default=None, help="profundidade máxima de pastas")
    ap.add_argument("--saida", default=None, help="grava a árvore neste arquivo .txt")
    args = ap.parse_args()

    raiz = Path(args.pasta)
    linhas = [f"{raiz.resolve().name}/"]
    arvore(raiz, "", 1, args.nivel, linhas)
    texto = "\n".join(linhas) + "\n"
    if args.saida:
        Path(args.saida).write_text(texto, encoding="utf-8")
        print(f"{len(linhas) - 1} itens → {args.saida}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(texto)


if __name__ == "__main__":
    main()
