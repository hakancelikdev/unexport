## Get Started

![pyall](https://raw.githubusercontent.com/hakancelik96/pyall/master/images/logo/pyall.png ":size=60%")

**Pyall is a linter that tries to keep the **all ** in your Python modules always up to
date.**

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/hakancelik96/pyall/master.svg)](https://results.pre-commit.ci/latest/github/hakancelik96/pyall/master)
![test](https://github.com/hakancelik96/pyall/workflows/Test/badge.svg)

[![Pypi](https://img.shields.io/pypi/v/pyall)](https://pypi.org/project/pyall/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyall)
[![Downloads](https://static.pepy.tech/personalized-badge/pyall?period=total&units=none&left_color=grey&right_color=red&left_text=downloads)](https://pepy.tech/project/pyall)
[![License](https://img.shields.io/github/license/hakancelik96/pyall.svg)](https://github.com/hakancelik96/pyall/blob/master/LICENSE)

[![Forks](https://img.shields.io/github/forks/hakancelik96/pyall)](https://github.com/hakancelik96/pyall/fork)
[![Issues](https://img.shields.io/github/issues/hakancelik96/pyall)](https://github.com/hakancelik96/pyall/issues)
[![Stars](https://img.shields.io/github/stars/hakancelik96/pyall)](https://github.com/hakancelik96/pyall/stargazers)

[![Codecov](https://codecov.io/gh/hakancelik96/pyall/branch/master/graph/badge.svg)](https://codecov.io/gh/hakancelik96/pyall)
[![Contributors](https://img.shields.io/github/contributors/hakancelik96/pyall)](https://github.com/hakancelik96/pyall/graphs/contributors)
[![Last Commit](https://img.shields.io/github/last-commit/hakancelik96/pyall.svg)](https://github.com/hakancelik96/pyall/commits/master)

## Installation

pyall requires Python 3.8+ and can be easily installed using most common Python
packaging tools. We recommend installing the latest stable release from PyPI with pip:

```shell
$ pip install pyall
```

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
  - repo: https://github.com/hakancelik96/pyall
    rev: stable
    hooks:
      - id: pyall
        args: [--refactor]
```
