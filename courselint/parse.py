"""
Le um repositorio de curso no formato da DataCamp e devolve objectos.

Uma decisao importante: o parser separa exercicios por cabecalho de nivel 2
seguido de um bloco yaml, e nao pelo separador horizontal. Os exemplos
publicados usam `***` dentro de exercicios compostos e `---` entre exercicios
de topo, e eu nao tenho a certeza de que seja sempre assim. Ancorar no que e
inequivoco (o cabecalho mais o yaml) e mais fiavel do que adivinhar o
separador, e quando o parser nao percebe uma seccao, diz, em vez de a saltar.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    raise SystemExit("falta o pyyaml: pip install pyyaml")


@dataclass
class Exercicio:
    titulo: str
    tipo: str
    meta: dict
    blocos: dict[str, str]
    ficheiro: str
    linha: int

    @property
    def onde(self) -> str:
        return f"{self.ficheiro}:{self.linha}"


@dataclass
class Capitulo:
    ficheiro: str
    numero: int
    meta: dict
    exercicios: list[Exercicio] = field(default_factory=list)


@dataclass
class Curso:
    raiz: Path
    meta: dict
    capitulos: list[Capitulo] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def exercicios(self) -> list[Exercicio]:
        return [e for c in self.capitulos for e in c.exercicios]


_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
_CABECALHO = re.compile(r"^##\s+(.+?)\s*$", re.M)
_YAML_FENCE = re.compile(r"\A\s*```(?:yaml|yml)?\n(.*?)```", re.S)
_BLOCO = re.compile(r"^`@([a-z_]+)`\s*$", re.M)


def _frontmatter(texto: str, ficheiro: str, avisos: list[str]) -> tuple[dict, str]:
    m = _FRONTMATTER.match(texto)
    if not m:
        avisos.append(f"{ficheiro}: sem cabecalho yaml no topo do capitulo")
        return {}, texto
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as exc:
        avisos.append(f"{ficheiro}: cabecalho yaml invalido ({exc.__class__.__name__})")
        meta = {}
    return meta, texto[m.end():]


def _blocos(corpo: str) -> dict[str, str]:
    """
    Parte o corpo de um exercicio nos seus blocos `@nome`.

    O assignment nao tem marcador: e a prosa entre o bloco yaml e o primeiro
    `@`. Apanhado ao testar, porque sem isto as regras de estilo nunca liam o
    texto onde o autor escreve a maior parte da prosa.
    """
    marcas = list(_BLOCO.finditer(corpo))
    out: dict[str, str] = {}
    cabeca = corpo[:marcas[0].start()] if marcas else corpo
    if cabeca.strip():
        out["assignment"] = cabeca.strip()
    if not marcas:
        return out
    for i, m in enumerate(marcas):
        fim = marcas[i + 1].start() if i + 1 < len(marcas) else len(corpo)
        out[m.group(1)] = corpo[m.end():fim].strip()
    return out


def _exercicios(corpo: str, ficheiro: str, deslocamento: int,
                avisos: list[str]) -> list[Exercicio]:
    cabecalhos = list(_CABECALHO.finditer(corpo))
    out: list[Exercicio] = []
    for i, h in enumerate(cabecalhos):
        fim = cabecalhos[i + 1].start() if i + 1 < len(cabecalhos) else len(corpo)
        bloco = corpo[h.end():fim]
        linha = deslocamento + corpo[:h.start()].count("\n") + 1

        fence = _YAML_FENCE.match(bloco)
        if not fence:
            # Um cabecalho sem yaml nao e um exercicio: pode ser prosa do
            # capitulo. Nao e erro, mas fica registado para nao desaparecer.
            avisos.append(f"{ficheiro}:{linha}: '{h.group(1)}' nao tem bloco yaml, ignorado")
            continue
        try:
            meta = yaml.safe_load(fence.group(1)) or {}
        except yaml.YAMLError:
            avisos.append(f"{ficheiro}:{linha}: yaml do exercicio invalido")
            meta = {}

        out.append(Exercicio(
            titulo=h.group(1),
            tipo=str(meta.get("type", "")),
            meta=meta,
            blocos=_blocos(bloco[fence.end():]),
            ficheiro=ficheiro,
            linha=linha,
        ))
    return out


def ler_curso(raiz: str | Path) -> Curso:
    raiz = Path(raiz)
    avisos: list[str] = []

    ficheiro_curso = raiz / "course.yml"
    if ficheiro_curso.exists():
        try:
            meta = yaml.safe_load(ficheiro_curso.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            avisos.append(f"course.yml: yaml invalido ({exc.__class__.__name__})")
            meta = {}
    else:
        avisos.append("course.yml: nao existe")
        meta = {}

    curso = Curso(raiz=raiz, meta=meta, avisos=avisos)

    for caminho in sorted(raiz.glob("chapter*.md")) + sorted(raiz.glob("chapter*.Rmd")):
        m = re.match(r"chapter(\d+)\.(md|Rmd)$", caminho.name)
        if not m:
            avisos.append(f"{caminho.name}: nome fora do padrao chapterN.md, ignorado")
            continue
        texto = caminho.read_text(encoding="utf-8")
        cab, corpo = _frontmatter(texto, caminho.name, avisos)
        deslocamento = texto[:len(texto) - len(corpo)].count("\n")
        curso.capitulos.append(Capitulo(
            ficheiro=caminho.name,
            numero=int(m.group(1)),
            meta=cab,
            exercicios=_exercicios(corpo, caminho.name, deslocamento, avisos),
        ))

    curso.capitulos.sort(key=lambda c: c.numero)
    return curso
