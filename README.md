# course-lint

Valida um curso escrito no formato de autoria da DataCamp contra as regras que
a própria DataCamp publica em
[github.com/datacamp/authoring](https://github.com/datacamp/authoring).

```sh
pip install pyyaml
python -m courselint.cli exemplo
```

```
curso  Validating Data Pipelines in Python
lido   2 capitulos, 4 exercicios

  CURSO
    curso/campo-em-falta       course.yml      falta o campo obrigatorio 'from'
    curso/dificuldade          course.yml      difficulty_level e 5, tem de ser 1, 2 ou 3
    curso/capitulo-em-falta    chapter2.md     existe chapter3.md mas falta este, o build chumba

  EXERCICIO
    exercicio/bloco-proibido   chapter1.md:6   @solution nao existe para VideoExercise
    exercicio/bloco-em-falta   chapter1.md:27  NormalExercise exige @sct

  MCQ
    mcq/opcao-proibida         chapter1.md:74  'All of the above.' nunca deve ser usada
    mcq/vies-de-comprimento    chapter1.md:74  uma opcao tem 177 caracteres contra uma media de 63

  22 achados em 7 sitios
```

Sai com código 1 quando há achados, para poder viver num hook de commit ou num
passo de integração contínua. Um validador que informa mas não trava é um
relatório, não é um portão.

## Porque existe

Conteúdo escrito por um modelo respeita o esquema quase sempre. O quase é o
problema. Um prompt não garante estrutura, e a única coisa que garante é código
que recusa o que está mal antes de chegar a alguém.

Isto é a metade determinística desse par: o modelo escreve, e isto decide se
publica.

## O que verifica, e de onde vem cada regra

Nenhuma regra aqui é gosto meu. Cada achado traz o documento que o justifica, e
`--fonte` mostra-o na linha seguinte, para que quem discorde discorde com a
fonte em vez de comigo.

| Grupo | Verifica | Fonte |
|---|---|---|
| `curso/` | Campos obrigatórios do `course.yml`, linguagem válida, dificuldade de 1 a 3, e capítulos sem saltos de numeração | `docs/courses/repo-structure.md` |
| `capitulo/` | Cabeçalho com título e descrição, capítulo não vazio | `docs/courses/repo-structure.md` |
| `exercicio/` | A matriz de blocos por tipo de exercício: o que é obrigatório, o que é proibido, e XP definido | `docs/courses/exercises/technical-details/exercise-blocks.md` |
| `mcq/` | Quatro ou cinco opções, nunca "All of the above" nem "None of the above", sem viés de comprimento, feedback que explique alguma coisa | `docs/courses/exercises/multiple-choice-exercises/responses.md` |
| `estilo/` | Inglês americano, falar ao aluno por "you", e as regras de comentário do guia | `docs/courses/guidelines/style.md` |

### A matriz de blocos

É a parte que apanha mais erros, porque é literal e não admite julgamento. Um
`@solution` num `VideoExercise` não é discutível, é um bloco que não existe
para aquele tipo.

| Bloco | Video | Normal | MultipleChoice | PureMultipleChoice |
|---|:---:|:---:|:---:|:---:|
| `instructions` | | sim | sim | sim |
| `sample_code` | | sim | | |
| `solution` | | sim | | |
| `sct` | | sim | sim | |
| `possible_answers` | | | | sim |
| `feedbacks` | | | | sim |

### A regra que eles não documentam

`mcq/chaves-concentradas` verifica a distribuição da posição da resposta certa
ao longo do banco inteiro. Não vem da documentação da DataCamp, vem de um erro
meu.

Publiquei quatro cursos com trinta e duas perguntas em que a resposta certa
estava sempre na primeira posição. Clicar oito vezes na primeira passava o
curso e emitia certificado.

O que interessa neste caso não é o erro, é a forma dele: **nenhuma pergunta
estava errada isoladamente.** Rever pergunta a pergunta, com todo o cuidado do
mundo, nunca ia apanhar aquilo, porque o defeito só existe ao nível do banco.
Por isso é que a verificação tem de ser de tipo diferente da construção.

## O que não verifica, e diz que não verifica

`TabExercise` e `BulletExercise` são composições de outros tipos e a
documentação não os detalha. O validador marca-os como não verificados em vez
de os aprovar em silêncio. Aprovar por omissão é pior do que admitir a lacuna.

## Testes

```sh
python -m pytest tests/ -q
```

Vinte e cinco testes, um por regra, e cada caso partido tem ao lado a versão
correcta. Um teste que só verifica que a regra dispara não prova nada, prova
que o validador chumba sempre. É o mesmo princípio de correr um controlo,
aplicado ao próprio validador.

## Limites

O parser ancora em cabeçalho de nível 2 seguido de bloco YAML, e não no
separador horizontal, porque os exemplos publicados usam `***` dentro de
exercícios compostos e `---` entre exercícios de topo e eu não tenho a certeza
de que seja sempre assim. Quando não percebe uma secção, avisa em vez de a
saltar.

A lista de inglês britânico é curta de propósito: só entram pares onde a forma
é inequívoca. `analyse` fica de fora porque é nome de variável em metade dos
cursos de dados.
