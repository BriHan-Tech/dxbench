from dataclasses import dataclass
from pathlib import Path


@dataclass
class CutAndResult:
    cut_file: Path
    should_pass: bool

    @property
    def test_filename(self) -> str:
        return f"test_{self.cut_file.name}"


cut_result_registry = [
    CutAndResult(cut_file=Path("dxbench/cut/add.py"), should_pass=True),
]
