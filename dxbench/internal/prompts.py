from pathlib import Path

PROMPT = """
Help me write tests for the following function:

{code}

The code is written in Python. Please use Pytest to test it.

The tests should import the function through:
    
{import_statement}

Please give your code exactly.
Do not include any explanations or comments.
Do not include any other text, just the code.
Ensure that your response is runnable, without any prior cleaning.
"""


def get_code(filepath: str) -> str:
    return Path(filepath).read_text(encoding="utf-8")


def get_prompt(filepath: Path) -> str:
    return PROMPT.format(
        code=filepath.read_text(encoding="utf-8"),
        import_statement=f"from code.{filepath.stem} import {filepath.stem}",
    )
