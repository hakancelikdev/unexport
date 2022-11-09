## Add private name to `__all__`

You can add the private name to `__all__`  When you write 'unexport: public' as a comment.

```python
__all__ = ["public_variable"]

private_name = ... # unexport: public
```

## not-public

Removes privates from `__all__`

```python
class Test:...  # unexport: not-public

def _test():...  # unexport: not-public
```
