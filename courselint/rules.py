"""
As verificacoes.

Cada uma devolve Achados e cada Achado traz a fonte da regra. Isso e
deliberado: quem discorda de um achado discorda com a DataCamp, nao comigo, e
consegue ir ler o documento sem me perguntar nada.

Nenhuma verificacao chama modelo nenhum. Um validador que precisa de um modelo
para decidir se a saida do modelo esta boa nao resolve o problema, so o adia.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass

from . import spec
from .parse import Curso, Exercicio


@dataclass
class Achado:
    regra: str
    onde: str
    mensagem: str
    fonte: str

    def __str__(self) -> str:
        return f"{self.regra:22s} {self.onde:24s} {self.mensagem}"


# --------------------------------------------------------------- estrutura
FONTE_ESTRUTURA = "docs/courses/repo-structure.md"


def estrutura(curso: Curso) -> list[Achado]:
    out: list[Achado] = []
    m = curso.meta

    for campo in spec.COURSE_YML_OBRIGATORIO:
        if not m.get(campo):
            out.append(Achado("curso/campo-em-falta", "course.yml",
                              f"falta o campo obrigatorio '{campo}'", FONTE_ESTRUTURA))

    lingua = str(m.get("programming_language", "")).lower()
    if lingua and lingua not in spec.LINGUAGENS:
        out.append(Achado("curso/linguagem", "course.yml",
                          f"'{lingua}' nao e uma de {', '.join(spec.LINGUAGENS)}",
                          FONTE_ESTRUTURA))

    dif = m.get("difficulty_level")
    if dif is not None and dif not in spec.DIFICULDADE:
        out.append(Achado("curso/dificuldade", "course.yml",
                          f"difficulty_level e {dif!r}, tem de ser 1, 2 ou 3",
                          FONTE_ESTRUTURA))

    # "The chapter files cannot skip numbers, so having chapter1.md and
    # chapter3.md but not chapter2.md will lead to a failed build."
    numeros = [c.numero for c in curso.capitulos]
    if numeros:
        esperado = list(range(1, max(numeros) + 1))
        for n in sorted(set(esperado) - set(numeros)):
            out.append(Achado("curso/capitulo-em-falta", f"chapter{n}.md",
                              f"existe chapter{max(numeros)}.md mas falta este, o build chumba",
                              FONTE_ESTRUTURA))

    for cap in curso.capitulos:
        for campo in spec.CAPITULO_YML_OBRIGATORIO:
            if not cap.meta.get(campo):
                out.append(Achado("capitulo/campo-em-falta", cap.ficheiro,
                                  f"falta '{campo}' no cabecalho", FONTE_ESTRUTURA))
        if not cap.exercicios:
            out.append(Achado("capitulo/vazio", cap.ficheiro,
                              "nenhum exercicio reconhecido", FONTE_ESTRUTURA))
    return out


# ------------------------------------------------------------------ blocos
FONTE_BLOCOS = "docs/courses/exercises/technical-details/exercise-blocks.md"


def blocos(curso: Curso) -> list[Achado]:
    out: list[Achado] = []
    for ex in curso.exercicios:
        if ex.tipo in spec.TIPOS_COMPOSTOS:
            out.append(Achado("exercicio/nao-verificado", ex.onde,
                              f"{ex.tipo} e composto e a documentacao nao o detalha, nao verifiquei",
                              FONTE_BLOCOS))
            continue

        regra = spec.BLOCOS.get(ex.tipo)
        if regra is None:
            out.append(Achado("exercicio/tipo-desconhecido", ex.onde,
                              f"type '{ex.tipo or '(vazio)'}' nao existe na matriz",
                              FONTE_BLOCOS))
            continue

        presentes = set(ex.blocos)
        # title e assignment vem do cabecalho e do corpo, nao de um `@bloco`.
        presentes |= {"title"} if ex.titulo else set()
        if ex.blocos.get("assignment") or _tem_prosa(ex):
            presentes.add("assignment")

        for falta in sorted(regra["obrigatorios"] - presentes):
            out.append(Achado("exercicio/bloco-em-falta", ex.onde,
                              f"{ex.tipo} exige @{falta}", FONTE_BLOCOS))

        for extra in sorted(set(ex.blocos) - regra["permitidos"]):
            out.append(Achado("exercicio/bloco-proibido", ex.onde,
                              f"@{extra} nao existe para {ex.tipo}", FONTE_BLOCOS))

        if not ex.meta.get("xp"):
            out.append(Achado("exercicio/sem-xp", ex.onde,
                              "sem xp definido", FONTE_BLOCOS))
    return out


def _tem_prosa(ex: Exercicio) -> bool:
    """O assignment e a prosa entre o yaml e o primeiro `@bloco`."""
    return bool(ex.blocos) or bool(ex.titulo)


# --------------------------------------------------------- escolha multipla
FONTE_MCQ = "docs/courses/exercises/multiple-choice-exercises/responses.md"
_OPCAO = re.compile(r"^\s*[-*]\s+(.+?)\s*$", re.M)


def _opcoes(ex: Exercicio) -> list[str]:
    fonte = ex.blocos.get("possible_answers") or ex.blocos.get("instructions", "")
    return [o.strip() for o in _OPCAO.findall(fonte) if o.strip()]


def escolha_multipla(curso: Curso) -> list[Achado]:
    out: list[Achado] = []
    mcq = [e for e in curso.exercicios
           if e.tipo in ("MultipleChoiceExercise", "PureMultipleChoiceExercise")]

    for ex in mcq:
        ops = _opcoes(ex)
        if not ops:
            out.append(Achado("mcq/sem-opcoes", ex.onde,
                              "nao consegui encontrar opcoes", FONTE_MCQ))
            continue

        if not spec.OPCOES_MIN <= len(ops) <= spec.OPCOES_MAX:
            out.append(Achado("mcq/numero-de-opcoes", ex.onde,
                              f"{len(ops)} opcoes, a regra sao {spec.OPCOES_MIN} ou {spec.OPCOES_MAX}",
                              FONTE_MCQ))

        for o in ops:
            limpo = re.sub(r"[`*_.]", "", o).strip().lower()
            if limpo in spec.RESPOSTAS_PROIBIDAS:
                out.append(Achado("mcq/opcao-proibida", ex.onde,
                                  f"'{o}' nunca deve ser usada", FONTE_MCQ))

        # "Answers that are significantly longer or shorter than others create
        # visual bias." Quem escreve a resposta certa tende a qualifica-la, e
        # e por isso que a mais comprida e tantas vezes a certa.
        if len(ops) > 2:
            comprimentos = [len(o) for o in ops]
            media = statistics.mean(comprimentos)
            for o, c in zip(ops, comprimentos):
                if media and c > media * spec.DESVIO_COMPRIMENTO:
                    out.append(Achado("mcq/viés-de-comprimento", ex.onde,
                                      f"uma opcao tem {c} caracteres contra uma media de {media:.0f}",
                                      FONTE_MCQ))
                    break

        fb = ex.blocos.get("feedbacks", "")
        if fb:
            for linha in _OPCAO.findall(fb):
                if linha.strip().lower().rstrip("!.") in spec.FEEDBACK_VAZIO:
                    out.append(Achado("mcq/feedback-vazio", ex.onde,
                                      f"'{linha.strip()}' nao explica nada", FONTE_MCQ))

    out.extend(_posicao_da_chave(mcq))
    return out


def _posicao_da_chave(mcq: list[Exercicio]) -> list[Achado]:
    """
    Nao documentado pela DataCamp. Esta aqui por experiencia propria.

    Publiquei quatro cursos com trinta e duas perguntas cujas respostas certas
    estavam todas na primeira posicao. Clicar oito vezes na primeira passava o
    curso e emitia certificado. Nenhuma pergunta estava errada isoladamente,
    portanto rever pergunta a pergunta nunca ia apanhar: o defeito so existe ao
    nivel do banco.
    """
    posicoes: list[int] = []
    for ex in mcq:
        chave = ex.meta.get("correct") or ex.meta.get("correct_answer")
        if isinstance(chave, int):
            posicoes.append(chave)

    if len(posicoes) < spec.KEY_CHECK_MINIMO:
        return []

    mais_comum = max(set(posicoes), key=posicoes.count)
    fatia = posicoes.count(mais_comum) / len(posicoes)
    if fatia > spec.KEY_CONCENTRATION_LIMIT:
        return [Achado("mcq/chaves-concentradas", "curso",
                       f"{fatia:.0%} das respostas certas na posicao {mais_comum}, "
                       f"em {len(posicoes)} perguntas",
                       "nao documentado, ver docstring")]
    return []


# ------------------------------------------------------------------- estilo
FONTE_ESTILO = "docs/courses/guidelines/style.md"
_PALAVRA = re.compile(r"[A-Za-z']+")
_PROSA = ("assignment", "instructions", "hint")


def estilo(curso: Curso) -> list[Achado]:
    out: list[Achado] = []
    for ex in curso.exercicios:
        texto = " ".join(ex.blocos.get(b, "") for b in _PROSA)
        texto = f"{ex.titulo} {texto}"
        baixo = texto.lower()

        for palavra in _PALAVRA.findall(baixo):
            if palavra in spec.BRITANICO:
                out.append(Achado("estilo/ingles-britanico", ex.onde,
                                  f"'{palavra}' deve ser '{spec.BRITANICO[palavra]}'",
                                  FONTE_ESTILO))
                break

        for p in spec.PRONOME_PROIBIDO:
            if p in baixo:
                out.append(Achado("estilo/pronome", ex.onde,
                                  f"'{p.strip()}' em vez de falar com o aluno por 'you'",
                                  FONTE_ESTILO))
                break

        out.extend(_comentarios(ex))
    return out


_COMENTARIO = re.compile(r"^\s*#(\s*)(.*)$")


def _comentarios(ex: Exercicio) -> list[Achado]:
    """Regras de comentario do guia de estilo, so para codigo Python."""
    out: list[Achado] = []
    codigo = ex.blocos.get("sample_code", "") + "\n" + ex.blocos.get("solution", "")
    for linha in codigo.splitlines():
        m = _COMENTARIO.match(linha)
        if not m:
            continue
        espaco, texto = m.group(1), m.group(2).strip()
        if not texto:
            continue
        if espaco != " ":
            out.append(Achado("estilo/comentario-espaco", ex.onde,
                              "exactamente um espaco depois do cardinal", FONTE_ESTILO))
        if texto[0].isalpha() and not texto[0].isupper():
            out.append(Achado("estilo/comentario-maiuscula", ex.onde,
                              f"'{texto[:30]}' devia comecar por maiuscula", FONTE_ESTILO))
        if "`" in texto or '"' in texto:
            out.append(Achado("estilo/comentario-aspas", ex.onde,
                              "sem plicas nem aspas a volta de nomes em comentarios",
                              FONTE_ESTILO))
        break  # um achado por exercicio chega para a pessoa ir la ver
    return out


TODAS = (estrutura, blocos, escolha_multipla, estilo)


def validar(curso: Curso) -> list[Achado]:
    return [a for regra in TODAS for a in regra(curso)]
