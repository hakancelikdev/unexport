## Get Started

**Unexport is a linter that tries to keep the `__all__` in your Python modules always up
to date.**

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/hakancelikdev/unexport/main.svg)](https://results.pre-commit.ci/latest/github/hakancelikdev/unexport/main)
[![Test](https://github.com/hakancelikdev/unexport/actions/workflows/tests.yml/badge.svg)](https://github.com/hakancelikdev/unexport/actions/workflows/tests.yml)
[![Build Docs](https://github.com/hakancelikdev/unexport/actions/workflows/docs.yml/badge.svg)](https://github.com/hakancelikdev/unexport/actions/workflows/docs.yml)
[![Publish Package on Pypi](https://github.com/hakancelikdev/unexport/actions/workflows/pypi.yml/badge.svg)](https://github.com/hakancelikdev/unexport/actions/workflows/pypi.yml)

[![Pypi](https://img.shields.io/pypi/v/unexport)](https://pypi.org/project/unexport/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/unexport)
[![Downloads](https://static.pepy.tech/personalized-badge/unexport?period=total&units=none&left_color=grey&right_color=red&left_text=downloads)](https://pepy.tech/project/unexport)
[![License](https://img.shields.io/github/license/hakancelikdev/unexport.svg)](https://github.com/hakancelikdev/unexport/blob/main/LICENSE)

[![Forks](https://img.shields.io/github/forks/hakancelikdev/unexport)](https://github.com/hakancelikdev/unexport/fork)
[![Issues](https://img.shields.io/github/issues/hakancelikdev/unexport)](https://github.com/hakancelikdev/unexport/issues)
[![Stars](https://img.shields.io/github/stars/hakancelikdev/unexport)](https://github.com/hakancelikdev/unexport/stargazers)

[![Codecov](https://codecov.io/gh/hakancelikdev/unexport/branch/main/graph/badge.svg)](https://codecov.io/gh/hakancelikdev/unexport)
[![Contributors](https://img.shields.io/github/contributors/hakancelikdev/unexport)](https://github.com/hakancelikdev/unexport/graphs/contributors)
[![Last Commit](https://img.shields.io/github/last-commit/hakancelikdev/unexport.svg)](https://github.com/hakancelikdev/unexport/commits/main)

Try it out now using the Unexport Playground,
https://playground-unexport.hakancelik.dev/

## Installation

unexport requires Python 3.8+ and can be easily installed using most common Python
packaging tools. We recommend installing the latest stable release from PyPI with pip:

```shell
$ pip install unexport
```

## Sources

> (optional: default `the file directory you are in`) -> `Path(".")` You can give as
> many file or directory paths as you want.

**Usage**

- `$ unexport`
- `$ unexport example`
- `$ unexport example example1 example2 example/example.py`

## Include

> (optional: default '\\.(py)$') file include pattern

**Usage**

- `$ unexport --include mypackage`
- `$ unexport --include "mypackage|tests`

## Exclude

> (optional: default '^$') file exclude pattern

**Usage**

- `$ unexport --exclude __init__.py`
- `$ unexport --exclude "__init__.py|tests|.tox`

## Diff

> (optional: default `False`) Prints a diff of all the changes unexport would make to a
> file.

**Usage**

- `$ unexport -d`
- `$ unexport --diff`

## Refactor

> (optional: default `False`) refactor unexport automatically.

**Usage**

- `$ unexport -r`
- `$ unexport --refactor`

### Command line options

You can list many options by running unexport --help

```
usage: Unexport [-h] [-r] [-d] [--include include] [--exclude exclude] [-v] [sources [sources ...]]

Unexport is a linter that tries to keep the __all __ in your Python modules always up to date.

positional arguments:
  sources            Enter the directories and file paths you want to analyze.

optional arguments:
  -h, --help         show this help message and exit
  -r, --refactor     Auto-sync __all__ list in python modules automatically.
  -d, --diff         Prints a diff of all the changes Unexport would make to a file.
  --include include  File include pattern.
  --exclude exclude  File exclude pattern.
  -v, --version      Prints version of unexport
```

### Adding pre-commit plugins to your project

Once you have [pre-commit](https://pre-commit.com/)
[installed](https://pre-commit.com/#install), adding pre-commit plugins to your project
is done with the .pre-commit-config.yaml configuration file.

Add a file called .pre-commit-config.yaml to the root of your project. The pre-commit
config file describes what repositories and hooks are installed.

```yaml
repos:
  - repo: https://github.com/hakancelikdev/unexport
    rev: stable
    hooks:
      - id: unexport
        args: [--refactor]
```
