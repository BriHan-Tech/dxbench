from pathlib import Path

from dxbench import Bot, LLM_GEN_DIR
from dxbench.internal.prompts import get_prompt


def generate_test(bot: Bot, path: Path) -> Path:
    test_filename = f"test_{path.name}"
    output_path = LLM_GEN_DIR / test_filename
    generated_test = bot.get_response(get_prompt(path))
    output_path.write_text(generated_test, encoding="utf-8")
    print(f"Generated tests for {path} at {output_path} successfully.")
    return output_path
