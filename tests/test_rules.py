"""
Um teste por regra, e cada um com o seu par limpo.

Um teste que so verifica que a regra dispara nao prova nada: prova que o
validador chumba sempre. Por isso cada caso partido tem ao lado a versao
correcta, e o teste exige que uma chumbe e a outra passe. E o mesmo principio
de correr um controlo, aplicado ao proprio validador.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from courselint.parse import ler_curso
from courselint.rules import validar

CURSO_OK = """\
title: A Course
description: A description long enough to be useful.
programming_language: python
difficulty_level: 2
from: datacamp
"""

CABECALHO = """\
---
title: 'A Chapter'
description: 'A chapter description.'
---
"""

NORMAL_OK = """
## Build the schema

```yaml
type: NormalExercise
key: aaaaaaaaaa
xp: 100
```

You will describe the shape you expect before anything else runs.

`@instructions`

- Import `pandera` as `pa`.

`@solution`

```{python}
import pandera as pa
```

`@sct`

```{python}
Ex().check_object("pa")
```
"""


def _escreve(raiz: Path, curso: str, capitulo: str) -> Path:
    (raiz / "course.yml").write_text(curso, encoding="utf-8")
    (raiz / "chapter1.md").write_text(capitulo, encoding="utf-8")
    return raiz


def _regras(raiz: Path) -> set[str]:
    return {a.regra for a in validar(ler_curso(raiz))}


def _caso(tmp_path: Path, curso: str, capitulo: str) -> set[str]:
    return _regras(_escreve(tmp_path, curso, capitulo))


# ------------------------------------------------------------- o controlo
def test_curso_correcto_nao_tem_achados(tmp_path):
    assert _caso(tmp_path, CURSO_OK, CABECALHO + NORMAL_OK) == set()


# ------------------------------------------------------------- estrutura
def test_campo_obrigatorio_em_falta(tmp_path):
    curso = CURSO_OK.replace("from: datacamp\n", "")
    assert "curso/campo-em-falta" in _caso(tmp_path, curso, CABECALHO + NORMAL_OK)


def test_dificuldade_fora_do_intervalo(tmp_path):
    curso = CURSO_OK.replace("difficulty_level: 2", "difficulty_level: 7")
    assert "curso/dificuldade" in _caso(tmp_path, curso, CABECALHO + NORMAL_OK)


def test_linguagem_invalida(tmp_path):
    curso = CURSO_OK.replace("programming_language: python", "programming_language: cobol")
    assert "curso/linguagem" in _caso(tmp_path, curso, CABECALHO + NORMAL_OK)


def test_capitulo_saltado(tmp_path):
    _escreve(tmp_path, CURSO_OK, CABECALHO + NORMAL_OK)
    (tmp_path / "chapter3.md").write_text(CABECALHO + NORMAL_OK, encoding="utf-8")
    assert "curso/capitulo-em-falta" in _regras(tmp_path)


def test_capitulo_sem_descricao(tmp_path):
    cab = "---\ntitle: 'A Chapter'\n---\n"
    assert "capitulo/campo-em-falta" in _caso(tmp_path, CURSO_OK, cab + NORMAL_OK)


# ---------------------------------------------------------------- blocos
def test_normal_sem_sct(tmp_path):
    cap = CABECALHO + NORMAL_OK.split("`@sct`")[0]
    assert "exercicio/bloco-em-falta" in _caso(tmp_path, CURSO_OK, cap)


def test_bloco_proibido_no_video(tmp_path):
    video = textwrap.dedent("""
        ## Watch this

        ```yaml
        type: VideoExercise
        key: bbbbbbbbbb
        xp: 50
        ```

        You will see how a schema behaves.

        `@video_link`
        https://example.com/v.mp4

        `@solution`

        ```{python}
        pass
        ```
        """)
    assert "exercicio/bloco-proibido" in _caso(tmp_path, CURSO_OK, CABECALHO + video)


def test_tipo_desconhecido(tmp_path):
    cap = CABECALHO + NORMAL_OK.replace("NormalExercise", "InventedExercise")
    assert "exercicio/tipo-desconhecido" in _caso(tmp_path, CURSO_OK, cap)


def test_exercicio_sem_xp(tmp_path):
    cap = CABECALHO + NORMAL_OK.replace("xp: 100\n", "")
    assert "exercicio/sem-xp" in _caso(tmp_path, CURSO_OK, cap)


def test_composto_e_declarado_nao_verificado(tmp_path):
    cap = CABECALHO + NORMAL_OK.replace("NormalExercise", "BulletExercise")
    assert "exercicio/nao-verificado" in _caso(tmp_path, CURSO_OK, cap)


# ------------------------------------------------------- escolha multipla
def _mcq(opcoes: str, extra: str = "", correct: int = 1) -> str:
    # Sem dedent: o texto interpolado ja vem encostado a esquerda e o dedent
    # calculava mal o prefixo comum, deixando o `##` indentado. Um cabecalho
    # indentado nao e cabecalho, e o parser via zero exercicios.
    return (
        "\n## Pick one\n\n"
        "```yaml\n"
        "type: PureMultipleChoiceExercise\n"
        "key: cccccccccc\n"
        "xp: 50\n"
        f"correct: {correct}\n"
        "```\n\n"
        "You will choose the statement that holds.\n\n"
        f"`@instructions`\n{opcoes}\n"
        f"`@possible_answers`\n{opcoes}\n"
        f"`@feedbacks`\n{extra or opcoes}\n"
    )


QUATRO = """
- The column exists.
- The column is typed.
- The column is named.
- The column is ordered.
"""


def test_mcq_correcto_nao_dispara(tmp_path):
    fb = """
- Close, but the name is separate from existence.
- Right, the type is part of the contract.
- The name alone does not constrain values.
- Ordering is not part of a schema contract.
"""
    regras = _caso(tmp_path, CURSO_OK, CABECALHO + _mcq(QUATRO, fb))
    assert not {r for r in regras if r.startswith("mcq/")}


def test_mcq_poucas_opcoes(tmp_path):
    tres = "\n- One.\n- Two.\n- Three.\n"
    assert "mcq/numero-de-opcoes" in _caso(tmp_path, CURSO_OK, CABECALHO + _mcq(tres))


def test_mcq_opcao_proibida(tmp_path):
    ops = QUATRO + "- All of the above.\n"
    assert "mcq/opcao-proibida" in _caso(tmp_path, CURSO_OK, CABECALHO + _mcq(ops))


def test_mcq_vies_de_comprimento(tmp_path):
    ops = ("\n- Yes.\n- No.\n- Maybe.\n"
           "- The column exists and is typed and is named and is ordered and was "
           "checked against the metrics table during the previous production run.\n")
    assert "mcq/viés-de-comprimento" in _caso(tmp_path, CURSO_OK, CABECALHO + _mcq(ops))


def test_mcq_feedback_vazio(tmp_path):
    fb = "\n- Try again.\n- Correct, the type is part of the contract.\n- Nope.\n- Wrong.\n"
    assert "mcq/feedback-vazio" in _caso(tmp_path, CURSO_OK, CABECALHO + _mcq(QUATRO, fb))


def test_chaves_concentradas(tmp_path):
    """
    O defeito que so existe ao nivel do banco.

    Oito perguntas, todas com a resposta certa na mesma posicao. Cada uma
    isolada esta impecavel, e e por isso que rever pergunta a pergunta nunca
    apanha isto.
    """
    cap = CABECALHO + "".join(_mcq(QUATRO, correct=1) for _ in range(8))
    assert "mcq/chaves-concentradas" in _regras(_escreve(tmp_path, CURSO_OK, cap))


def test_chaves_espalhadas_passam(tmp_path):
    cap = CABECALHO + "".join(_mcq(QUATRO, correct=i % 4) for i in range(8))
    assert "mcq/chaves-concentradas" not in _regras(_escreve(tmp_path, CURSO_OK, cap))


# ---------------------------------------------------------------- estilo
def test_ingles_britanico(tmp_path):
    cap = CABECALHO + NORMAL_OK.replace("describe the shape", "normalise the shape")
    assert "estilo/ingles-britanico" in _caso(tmp_path, CURSO_OK, cap)


def test_pronome_na_primeira_pessoa(tmp_path):
    cap = CABECALHO + NORMAL_OK.replace("You will describe", "We will describe")
    assert "estilo/pronome" in _caso(tmp_path, CURSO_OK, cap)


def test_comentario_sem_espaco(tmp_path):
    cap = CABECALHO + NORMAL_OK.replace("import pandera as pa",
                                        "#Validate first\nimport pandera as pa")
    assert "estilo/comentario-espaco" in _caso(tmp_path, CURSO_OK, cap)


def test_comentario_em_minuscula(tmp_path):
    cap = CABECALHO + NORMAL_OK.replace("import pandera as pa",
                                        "# validate first\nimport pandera as pa")
    assert "estilo/comentario-maiuscula" in _caso(tmp_path, CURSO_OK, cap)


# ---------------------------------------------------------------- parser
def test_yaml_partido_avisa_em_vez_de_rebentar(tmp_path):
    cap = CABECALHO + "\n## Broken\n\n```yaml\ntype: [unclosed\n```\n\nProse.\n"
    curso = ler_curso(_escreve(tmp_path, CURSO_OK, cap))
    assert any("invalido" in a for a in curso.avisos)


def test_cabecalho_sem_yaml_e_ignorado_com_aviso(tmp_path):
    cap = CABECALHO + "\n## Just prose, not an exercise\n\nSome words.\n"
    curso = ler_curso(_escreve(tmp_path, CURSO_OK, cap))
    assert any("ignorado" in a for a in curso.avisos)
    assert curso.exercicios == []


def test_curso_sem_course_yml(tmp_path):
    (tmp_path / "chapter1.md").write_text(CABECALHO + NORMAL_OK, encoding="utf-8")
    curso = ler_curso(tmp_path)
    assert any("course.yml" in a for a in curso.avisos)
