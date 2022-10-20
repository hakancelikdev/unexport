import ast

__all__ = (
    "ADD_COMMENTS_REGEX_PATTERN",
    "ALL_NODE",
    "EXCLUDE_REGEX_PATTERN",
    "GLOB_PATTERN",
    "INCLUDE_REGEX_PATTERN",
    "SKIP_COMMENTS_REGEX_PATTERN",
)

# TUPLE
ALL_NODE = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Name)

# REGEX
INCLUDE_REGEX_PATTERN = r"\.(py)$"
EXCLUDE_REGEX_PATTERN = r"^$"
GLOB_PATTERN = r"**/*.py"
SKIP_COMMENTS_REGEX_PATTERN = r"#.*(pyall: {0,1}not-public)"
ADD_COMMENTS_REGEX_PATTERN = r"#.*(pyall: {0,1}public)"
