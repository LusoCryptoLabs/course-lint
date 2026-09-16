---
title: 'Why a Passing Test Is Not a Passing Pipeline'
description: 'Schemas, assertions, and the difference between valid and correct.'
---

## What validation actually buys you

```yaml
type: VideoExercise
key: 3f1a2b7c9d
xp: 50
```

In this video we'll look at what a schema can and cannot promise you.

`@projector_key`
3f1a2b7c9d

`@solution`

```{python}
print("this block should not exist on a video exercise")
```

---

## Writing your first schema

```yaml
type: NormalExercise
key: a91c3e5f27
xp: 100
```

A schema describes the shape you expect. It does not describe whether the
numbers are right. We normalise the column names first so the checks are
predictable.

`@instructions`

- Import `pandera` as `pa`.
- Build a schema that requires a non-null integer column named `reading`.

`@hint`

Use `pa.Column(int, nullable=False)`.

`@pre_exercise_code`

```{python}
import pandas as pd
readings = pd.DataFrame({"reading": [1, 2, 3]})
```

`@sample_code`

```{python}
#import pandera as pa

# ____ = pa.DataFrameSchema({"reading": ____})
```

`@solution`

```{python}
import pandera as pa

#validate the shape before anything else runs
schema = pa.DataFrameSchema({"reading": pa.Column(int, nullable=False)})
```

---

## Which check belongs in the schema?

```yaml
type: PureMultipleChoiceExercise
key: b4d8f0a613
xp: 50
correct: 1
```

A schema is a structural contract. Some checks belong in it and some do not.

`@instructions`

- The column exists and holds integers.
- The mean of the column is close to the mean we measured during the last production run, which we stored in the metrics table, provided that the run finished without any retries.
- The column is present.
- All of the above.

`@feedbacks`

- Not quite.
- Correct.
- Try again.
- Nope.
