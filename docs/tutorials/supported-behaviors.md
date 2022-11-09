## Add private name to `__all__`

You can add the private name to `__all__`  When you write 'unexport: public' as a comment.

```python
__all__ = ["private_name"]

private_name = ... # unexport: public
```

## Remove public name from `__all__`

You can remove the public name from `__all__`  When you write 'unexport: not-public' as a comment.

```python
class Test:...  # unexport: not-public

def _test():...  # unexport: not-public
```
