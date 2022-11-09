## public

Adds public variables to `__all__`

```python
__all__ = ["public_variable"]

public_variable = ... # unexport: public
```

## not-public

Removes privates from `__all__`

```python
class Test:...  # unexport: not-public

def _test():...  # unexport: not-public
```
