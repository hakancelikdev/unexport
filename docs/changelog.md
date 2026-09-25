# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Support Python3.14, including PEP 750 template strings and PEP 758 unparenthesized
  `except` expressions
- Support Python3.13, including PEP 696 type parameter defaults
- Support Python3.12, including PEP 695 `type` statements and generic functions/classes

### Changed

- Remove usage of `ast.Str`, which is deprecated since Python3.12
- Useful features documented
- Drop support for Python3.8 and Python3.9; Python3.10+ is now required
- Development status is now Beta
- `TypeVar`, `ParamSpec` and `TypeVarTuple` definitions are no longer added to `__all__`
- Refactoring replaces only the value of an existing `__all__`, so comments and other
  code on the same lines are kept
- Refactoring keeps the type of an existing `__all__` (list, tuple or set) and writes
  one name per line when `__all__` was already multi-line or would be longer than 88
  characters

### Fixed

- Comments after `__all__` were removed while refactoring
- A name defined both as a class/function and a variable is listed once in `__all__`
  [#43](https://github.com/hakancelikdev/unexport/issues/43)
- Names already listed in `__all__` that the module still binds (re-exported imports,
  dunders, lowercase variables) or that a star import may provide are kept instead of
  being removed [#39](https://github.com/hakancelikdev/unexport/issues/39)
- A stale `__all__` is rewritten to be empty when nothing is public anymore, and
  "Refactoring" is only printed when the file changed
  [#45](https://github.com/hakancelikdev/unexport/issues/45)
- A new `__all__` is inserted after the module docstring (and after a leading shebang or
  encoding line) instead of above it
  [#42](https://github.com/hakancelikdev/unexport/issues/42)
- Syntax errors and files that can't be read or decoded are reported with their path and
  make the exit code 1, instead of being skipped silently or crashing the run
  [#44](https://github.com/hakancelikdev/unexport/issues/44)
- Names that don't exist when the module is imported are no longer added to `__all__`:
  names deleted with `del`, defined only under `if TYPE_CHECKING:` or
  `if __name__ == "__main__":`, and comprehension variables
  [#40](https://github.com/hakancelikdev/unexport/issues/40)
- `__all__ +=`, annotated `__all__`, `extend` with a tuple and `__all__` inside
  functions are handled correctly; an `__all__` built from several statements is
  reported but not rewritten, and a dynamic `__all__` (e.g. `["a"] + sub.__all__`) is
  left alone [#41](https://github.com/hakancelikdev/unexport/issues/41)
- Crash on modules whose `__all__` is a set

## [0.4.0] - 2022-11-05

### Changed

- Change project name to `unexport` from `pyall`

## [0.3.5] - 2022-10-28

### Added

- Support Python3.11
- Support Python3.10
- Add py.typed
- Github Action

### Changed

- Single quotes to double quotes when refactoring
- Apply src layout
- Support tuple all

## [0.2.0] - 2021-04-11

### Changed

- Docs update by @hakancelikdev

### Fixed

- pyall: public by @hakancelikdev

## [0.1.0] - 2021-04-11

### Added

- pyall: not-public ( feature ) by @hakancelikdev
- pyall: public ( feature ) by @hakancelikdev
- refactor flag ( feature ) by @hakancelikdev
- diff flag ( feature ) by @hakancelikdev
- include flag ( feature ) by @hakancelikdev
- exclude flag ( feature ) by @hakancelikdev
