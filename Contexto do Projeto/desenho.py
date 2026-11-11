# -*- coding: utf-8 -*-
"""Caixas e setas para os diagramas dos notebooks desta pasta (fluxo, desenho t → t+1,
walk-forward). Só desenha: nenhuma função aqui calcula ou lê dado. As cores seguem o
abandono-escolar/src/figuras.py."""
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

AZUL = "#1f4e79"
AZUL_CLARO = "#dbe6f1"
CINZA = "#8c8c8c"
CINZA_CLARO = "#f1f1f1"
VERMELHO = "#b00000"
LARANJA_CLARO = "#fbe7d3"

ESTILOS = {
    "oficial": {"facecolor": AZUL_CLARO, "edgecolor": AZUL},
    "gustavo": {"facecolor": LARANJA_CLARO, "edgecolor": "#a0522d"},
    "externo": {"facecolor": "white", "edgecolor": CINZA},
    "avaliacao": {"facecolor": "#e3efe3", "edgecolor": "#2e6b2e"},
    "neutro": {"facecolor": CINZA_CLARO, "edgecolor": CINZA},
    "bloqueado": {"facecolor": "white", "edgecolor": VERMELHO},
    "decisao": {"facecolor": "#f3d9a4", "edgecolor": "#b8860b"},
    "livre": {"facecolor": "#cfe5cf", "edgecolor": "#2e6b2e"},
}


def tela(ax, largura=100, altura=60):
    """Eixo sem moldura, em coordenadas 0..largura × 0..altura."""
    ax.set_xlim(0, largura)
    ax.set_ylim(0, altura)
    ax.set_axis_off()


def caixa(ax, x, y, w, h, texto, estilo="neutro", tamanho=8, negrito_primeira=True, hachura=None):
    """Caixa com canto arredondado; (x, y) é o canto inferior esquerdo.
    A primeira linha do texto vai em negrito (título da caixa)."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                linewidth=1.1, hatch=hachura, **ESTILOS[estilo]))
    linhas = texto.split("\n")
    if negrito_primeira and len(linhas) > 1:
        ax.text(x + w / 2, y + h - 1.6, linhas[0], ha="center", va="top", fontsize=tamanho,
                fontweight="bold")
        ax.text(x + w / 2, y + h - 1.6 - tamanho * 0.42, "\n".join(linhas[1:]), ha="center",
                va="top", fontsize=tamanho - 1, linespacing=1.25)
    else:
        ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=tamanho,
                fontweight="bold" if negrito_primeira else "normal")
    return (x, y, w, h)


def centro(c, lado):
    """Ponto no meio de um lado da caixa: 'e', 'd', 'c' (cima), 'b' (baixo)."""
    x, y, w, h = c
    return {"e": (x, y + h / 2), "d": (x + w, y + h / 2), "c": (x + w / 2, y + h),
            "b": (x + w / 2, y)}[lado]


# Uma cor por família de estado, a mesma em todos os registros (notebooks 04 a 07)
VERDE = "#8fbf8f"
VERDE_CLARO = "#cfe5cf"
AMBAR = "#f3d9a4"
LARANJA = "#f6c9a0"
CINZA_ESTADO = "#e3e3e3"
COR_ESTADO = {
    # feito / vigente / respondido
    "feito": VERDE, "vigente": VERDE, "respondida": VERDE, "resolvido": VERDE, "adotada": VERDE,
    "coincide": VERDE, "citada nos documentos": VERDE, "feito (nulo)": VERDE,
    # feito de outro jeito / substituído
    "feito de outra forma": VERDE_CLARO, "substituída": VERDE_CLARO,
    # em parte
    "feito em parte": LARANJA, "em parte": LARANJA,
    # depende de decisão ou de conferência
    "aguarda decisão": AMBAR, "não decidida": AMBAR, "aberta": AMBAR, "aberto": AMBAR, "sugerida": AMBAR,
    "a conferir": "#f2b8b5",
    # informativo
    "informativo": AZUL_CLARO, "indireta": AZUL_CLARO,
    # não feito
    "não feito": CINZA_ESTADO, "não rodado": CINZA_ESTADO, "não implementada": CINZA_ESTADO,
    "não adotada": CINZA_ESTADO,
}


def grade_estados(ax, ids, estados, colunas=8, hachurar=None, notas=None, tamanho=8, legenda=True):
    """Uma célula por item (id + estado), na ordem dada, `colunas` por linha. Só desenha: os estados vêm
    prontos de um registro. `hachurar` marca células (ex.: linha proposta, fora da planilha); `notas`
    acrescenta uma terceira linha de texto."""
    import textwrap

    from matplotlib.patches import Patch, Rectangle
    n = len(ids)
    linhas = (n + colunas - 1) // colunas
    hachurar = list(hachurar) if hachurar is not None else [False] * n
    notas = list(notas) if notas is not None else [""] * n
    largura = max(10, int(120 / colunas))           # caracteres por linha que cabem numa célula
    for k, (i, e, h, nota) in enumerate(zip(ids, estados, hachurar, notas)):
        lin, col = divmod(k, colunas)
        y = linhas - 1 - lin
        ax.add_patch(Rectangle((col + 0.04, y + 0.06), 0.92, 0.88, facecolor=COR_ESTADO.get(e, "white"),
                               edgecolor="#555555" if h else "white", hatch="///" if h else None, linewidth=0.8))
        nota = textwrap.shorten(nota, width=3 * (largura + 4), placeholder=" …") if nota else ""
        texto = f"{i}\n{textwrap.fill(e, largura)}" + (f"\n{textwrap.fill(nota, largura + 4)}" if nota else "")
        fundo = {"facecolor": "white", "alpha": 0.85, "edgecolor": "none", "pad": 1.5} if h else None
        ax.text(col + 0.5, y + 0.5, texto, ha="center", va="center", fontsize=tamanho - (1 if nota else 0),
                linespacing=1.2, bbox=fundo)
    ax.set_xlim(0, colunas)
    ax.set_ylim(0, linhas)
    ax.set_axis_off()
    if legenda:
        vistos = list(dict.fromkeys(estados))
        alcas = [Patch(facecolor=COR_ESTADO.get(e, "white"), edgecolor="#bbbbbb", label=e) for e in vistos]
        if any(hachurar):
            alcas.append(Patch(facecolor="white", edgecolor="#555555", hatch="///", label="fora da planilha (proposta)"))
        ax.legend(handles=alcas, loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=8, frameon=False)


def seta(ax, origem, destino, texto=None, cor=AZUL, tracejada=False, curva=0.0, tamanho=7,
         deslocamento=(0, 1.2)):
    """Seta de `origem` para `destino` (pontos); `texto` vai no meio da seta."""
    ax.add_patch(FancyArrowPatch(origem, destino, arrowstyle="-|>", mutation_scale=10,
                                 color=cor, linewidth=1.1, linestyle="--" if tracejada else "-",
                                 connectionstyle=f"arc3,rad={curva}", shrinkA=2, shrinkB=2))
    if texto:
        xm = (origem[0] + destino[0]) / 2 + deslocamento[0]
        ym = (origem[1] + destino[1]) / 2 + deslocamento[1]
        ax.text(xm, ym, texto, ha="center", va="bottom", fontsize=tamanho, color=cor, style="italic")
