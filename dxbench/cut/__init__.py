import importlib
from pathlib import Path

_this_dir = Path(__file__).parent

for _py_file in _this_dir.glob("*.py"):
    if _py_file.name == "__init__.py":
        continue

    _module_name = _py_file.stem
    _module = importlib.import_module(f".{_module_name}", package=__name__)

    for _name in dir(_module):
        if not _name.startswith("_"):
            globals()[_name] = getattr(_module, _name)
