"""
Linha de comandos.

Sai com codigo 1 quando ha achados, para poder viver num hook de commit ou num
passo de integracao continua. Um validador que informa mas nao trava e um
relatorio, nao e um portao.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from .parse import ler_curso
from .rules import validar

VERDE, VERMELHO, AMARELO, CINZA, FIM = "\033[32m", "\033[31m", "\033[33m", "\033[90m", "\033[0m"


def _cor(ativa: bool):
    return (lambda c, t: f"{c}{t}{FIM}") if ativa else (lambda c, t: t)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="course-lint",
        description="Valida um curso no formato de autoria da DataCamp contra as regras publicadas.")
    p.add_argument("caminho", nargs="?", default=".", help="raiz do repositorio do curso")
    p.add_argument("--sem-cor", action="store_true")
    p.add_argument("--fonte", action="store_true", help="mostrar o documento que justifica cada achado")
    args = p.parse_args(argv)

    raiz = Path(args.caminho)
    if not raiz.is_dir():
        print(f"{raiz} nao e uma pasta", file=sys.stderr)
        return 2

    pinta = _cor(not args.sem_cor and sys.stdout.isatty())

    curso = ler_curso(raiz)
    achados = validar(curso)

    titulo = curso.meta.get("title") or raiz.name
    print(f"\n{pinta(CINZA, 'curso')}  {titulo}")
    print(f"{pinta(CINZA, 'lido ')}  {len(curso.capitulos)} capitulos, "
          f"{len(curso.exercicios)} exercicios\n")

    for aviso in curso.avisos:
        print(f"  {pinta(CINZA, 'nota')}  {aviso}")
    if curso.avisos:
        print()

    if not achados:
        print(f"  {pinta(VERDE, 'sem achados')}\n")
        return 0

    por_regra = Counter(a.regra.split("/")[0] for a in achados)
    for grupo in sorted(por_regra):
        print(f"  {pinta(AMARELO, grupo.upper())}")
        for a in [x for x in achados if x.regra.startswith(grupo + "/")]:
            print(f"    {pinta(VERMELHO, a.regra):<32} {pinta(CINZA, a.onde)}  {a.mensagem}")
            if args.fonte:
                print(f"    {' ':<22} {pinta(CINZA, a.fonte)}")
        print()

    print(f"  {pinta(VERMELHO, str(len(achados)) + ' achados')} em "
          f"{len(set(a.onde for a in achados))} sitios\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
