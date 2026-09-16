---
title: 'Failing Closed'
---

## What to do when the check fails

```yaml
type: NormalExercise
key: c72e19b408
xp: 100
```

`@instructions`

- Raise instead of returning a partial frame.

`@sample_code`

```{python}
def load(path):
    frame = read(path)
    # return frame even when invalid
    return frame
```
