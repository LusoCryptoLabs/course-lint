"""
As regras publicadas pela DataCamp, como dados.

Nada aqui e opiniao minha. Cada constante cita o documento de onde saiu, em
github.com/datacamp/authoring, para que qualquer regra possa ser contestada
contra a fonte em vez de contra o meu gosto.

A unica excepcao esta assinalada como tal: KEY_CONCENTRATION_LIMIT, que eles
nao documentam e que eu acrescentei depois de publicar 32 perguntas com a
resposta certa sempre na mesma posicao.
"""

from __future__ import annotations

# ---------------------------------------------------------------- estrutura
# docs/courses/repo-structure.md
COURSE_YML_OBRIGATORIO = ("title", "description", "programming_language",
                          "difficulty_level", "from")
LINGUAGENS = ("r", "python", "sql", "shell")
DIFICULDADE = (1, 2, 3)
CAPITULO_YML_OBRIGATORIO = ("title", "description")

# ------------------------------------------------------------------ blocos
# docs/courses/exercises/technical-details/exercise-blocks.md
# A matriz e literal: um visto quer dizer que o bloco existe para aquele tipo,
# uma cruz quer dizer que nao existe. Um bloco fora da coluna e erro, nao e
# estilo, e e por isso que isto valida sem julgamento nenhum pelo meio.
BLOCOS = {
    "VideoExercise": {
        "obrigatorios": {"title", "assignment", "video_link"},
        "permitidos": {"title", "assignment", "video_link", "aspect_ratio",
                       "projector_key"},
    },
    "NormalExercise": {
        "obrigatorios": {"title", "assignment", "instructions", "solution", "sct"},
        "permitidos": {"title", "assignment", "instructions", "hint",
                       "pre_exercise_code", "sample_code", "solution", "sct"},
    },
    "MultipleChoiceExercise": {
        "obrigatorios": {"title", "assignment", "instructions", "sct"},
        "permitidos": {"title", "assignment", "instructions", "hint",
                       "pre_exercise_code", "sct"},
    },
    "PureMultipleChoiceExercise": {
        "obrigatorios": {"title", "assignment", "instructions",
                         "possible_answers", "feedbacks"},
        "permitidos": {"title", "assignment", "instructions", "hint",
                       "pre_exercise_code", "possible_answers", "feedbacks"},
    },
    # TabExercise e BulletExercise sao composicoes dos outros. A documentacao
    # nao os detalha, por isso nao invento uma matriz para eles: o parser
    # reconhece-os e o validador diz que nao os verifica, em vez de os aprovar
    # em silencio. Aprovar por omissao e pior do que admitir a lacuna.
}
TIPOS_COMPOSTOS = ("TabExercise", "BulletExercise")

# --------------------------------------------------------------- escolha multipla
# docs/courses/exercises/multiple-choice-exercises/responses.md
OPCOES_MIN = 4
OPCOES_MAX = 5
RESPOSTAS_PROIBIDAS = ("all of the above", "none of the above",
                       "todas as anteriores", "nenhuma das anteriores")
# "Answers that are significantly longer or shorter than others create visual
# bias." Eles dizem a regra e nao dao numero. O numero e meu, e esta aqui em
# vez de espalhado pelo codigo para poder ser discutido.
DESVIO_COMPRIMENTO = 2.5
FEEDBACK_VAZIO = ("try again", "tenta outra vez", "incorrect", "wrong",
                  "errado", "nope", "not quite")

# Nao documentado por eles. Ver o docstring do modulo.
KEY_CONCENTRATION_LIMIT = 0.45
KEY_CHECK_MINIMO = 8

# ------------------------------------------------------------------- estilo
# docs/courses/guidelines/style.md
# So entram aqui pares onde a forma britanica e inequivoca. "analyse" fica de
# fora de proposito: e nome de variavel em metade dos cursos de dados.
BRITANICO = {
    "standardise": "standardize", "standardised": "standardized",
    "normalise": "normalize", "normalised": "normalized",
    "optimise": "optimize", "optimised": "optimized",
    "visualise": "visualize", "visualised": "visualized",
    "initialise": "initialize", "initialised": "initialized",
    "serialise": "serialize", "behaviour": "behavior",
    "colour": "color", "centre": "center", "labelled": "labeled",
    "modelling": "modeling", "licence": "license",
}
PRONOME_PROIBIDO = ("we ", "we'll", "we've", "we're", "our ", "us ", "let's")
