from importlib.resources import files
from pathlib import Path
from platformdirs import user_cache_dir

# The code under test directory
CUT_DIR = files("dxbench.cut")

# The directory where the LLM generated tests will be stored
LLM_GEN_DIR = Path(user_cache_dir("dxbench")) / "llm_gen_tests"
LLM_GEN_DIR.mkdir(parents=True, exist_ok=True)

init_file = LLM_GEN_DIR / "__init__.py"
if not init_file.exists():
    init_file.write_text("", encoding="utf-8")

print("Note: We will be caching the LLM generated tests in:", LLM_GEN_DIR)


from .bot import *
from .runner import *
from .registry import *
