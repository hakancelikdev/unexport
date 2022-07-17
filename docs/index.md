## Get Started

**Pyall is a linter that tries to keep the `__all__` in your Python modules always up to
date.**

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/hakancelikdev/pyall/main.svg)](https://results.pre-commit.ci/latest/github/hakancelikdev/pyall/main)
[![test](https://github.com/hakancelikdev/pyall/actions/workflows/tests.yml/badge.svg)](https://github.com/hakancelikdev/pyall/actions/workflows/tests.yml)

[![Pypi](https://img.shields.io/pypi/v/pyall)](https://pypi.org/project/pyall/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyall)
[![Downloads](https://static.pepy.tech/personalized-badge/pyall?period=total&units=none&left_color=grey&right_color=red&left_text=downloads)](https://pepy.tech/project/pyall)
[![License](https://img.shields.io/github/license/hakancelikdev/pyall.svg)](https://github.com/hakancelikdev/pyall/blob/main/LICENSE)

[![Forks](https://img.shields.io/github/forks/hakancelikdev/pyall)](https://github.com/hakancelikdev/pyall/fork)
[![Issues](https://img.shields.io/github/issues/hakancelikdev/pyall)](https://github.com/hakancelikdev/pyall/issues)
[![Stars](https://img.shields.io/github/stars/hakancelikdev/pyall)](https://github.com/hakancelikdev/pyall/stargazers)

[![Codecov](https://codecov.io/gh/hakancelikdev/pyall/branch/main/graph/badge.svg)](https://codecov.io/gh/hakancelikdev/pyall)
[![Contributors](https://img.shields.io/github/contributors/hakancelikdev/pyall)](https://github.com/hakancelikdev/pyall/graphs/contributors)
[![Last Commit](https://img.shields.io/github/last-commit/hakancelikdev/pyall.svg)](https://github.com/hakancelikdev/pyall/commits/main)

## Installation

pyall requires Python 3.8+ and can be easily installed using most common Python
packaging tools. We recommend installing the latest stable release from PyPI with pip:

```shell
$ pip install pyall
```

## Sources

> (optional: default `the file directory you are in`) -> `Path(".")` You can give as
> many file or directory paths as you want.

**Usage**

- `$ pyall`
- `$ pyall example`
- `$ pyall example example1 example2 example/example.py`

## Include

> (optional: default '\\.(py)$') file include pattern

**Usage**

- `$ pyall --include mypackage`
- `$ pyall --include "mypackage|tests`

## Exclude

> (optional: default '^$') file exclude pattern

**Usage**

- `$ pyall --exclude __init__.py`
- `$ pyall --exclude "__init__.py|tests|.tox`

## Diff

> (optional: default `False`) Prints a diff of all the changes pyall would make to a
> file.

**Usage**

- `$ pyall -d`
- `$ pyall --diff`

## Refactor

> (optional: default `False`) refactor pyall automatically.

**Usage**

- `$ pyall -r`
- `$ pyall --refactor`

### Command line options

You can list many options by running pyall --help

```
usage: Pyall [-h] [-r] [-d] [--include include] [--exclude exclude] [-v] [sources [sources ...]]

Pyall is a linter that tries to keep the __all __ in your Python modules always up to date.

positional arguments:
  sources            Enter the directories and file paths you want to analyze.

optional arguments:
  -h, --help         show this help message and exit
  -r, --refactor     Auto-sync __all__ list in python modules automatically.
  -d, --diff         Prints a diff of all the changes Pyall would make to a file.
  --include include  File include pattern.
  --exclude exclude  File exclude pattern.
  -v, --version      Prints version of pyall
```

### Adding pre-commit plugins to your project

Once you have [pre-commit](https://pre-commit.com/)
[installed](https://pre-commit.com/#install), adding pre-commit plugins to your project
is done with the .pre-commit-config.yaml configuration file.

Add a file called .pre-commit-config.yaml to the root of your project. The pre-commit
config file describes what repositories and hooks are installed.

```yaml
repos:
  - repo: https://github.com/hakancelikdev/pyall
    rev: stable
    hooks:
      - id: pyall
        args: [--refactor]
```
