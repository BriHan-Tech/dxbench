import docker
import json

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Mapping, Literal, Dict, Tuple

IMAGE_NAME = "dxbench-sandbox"

DOCKERFILE = """\
FROM python:3.12-slim
WORKDIR /work
RUN pip install --no-cache-dir pytest pytest-timeout pytest-json-report
# optional: block network/subprocess inside tests
RUN python - <<'PY'\nimport sys\n"".__class__.__mro__[1].__dict__\nPY
CMD ["python", "-q"]
"""


@dataclass(frozen=True)
class TestCaseResult:
    outcome: Literal["passed", "failed", "error"]
    duration: float
    message: str


def _parse_json_report(path: Path) -> Dict[str, TestCaseResult]:
    out: Dict[str, TestCaseResult] = {}

    if not path.exists():
        return out

    try:
        with path.open() as f:
            report = json.load(f)

        for test in report.get("tests", []):
            nodeid = test.get("nodeid", "")
            outcome = test.get("outcome", "")
            duration = test.get("duration", 0.0)

            message = ""
            if outcome != "passed":
                call_info = test.get("call", {})
                message = call_info.get("longrepr", "")
                if not message:
                    setup_info = test.get("setup", {})
                    teardown_info = test.get("teardown", {})
                    message = setup_info.get("longrepr", "") or teardown_info.get("longrepr", "")

                message = str(message)[:800] if message else ""

            out[nodeid] = TestCaseResult(
                outcome=outcome,
                duration=float(duration),
                message=message,
            )

    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing JSON report: {e}")

    return out


def build_sandbox(image_name: str = IMAGE_NAME) -> None:
    """
    Creates a Sandbox environment for running LLM-generated tests.

    Args:
        image (str): The name of the image.
    """

    client = docker.from_env()
    with TemporaryDirectory() as td:
        ctx = Path(td)
        (ctx / "Dockerfile").write_text(DOCKERFILE, encoding="utf-8")

        print("Building docker image")
        _, logs = client.images.build(path=str(ctx), tag=image_name, rm=True, pull=False)

        print("Built Docker Image with Logs:")
        for rec in logs:
            if isinstance(rec, Mapping):
                s = rec.get("stream")
                if isinstance(s, str):
                    s = s.strip()
                    if s:
                        print(s)


def run_in_sandbox(cut_dir: Path, tests_dir: Path) -> Tuple[int, Dict[str, bool]]:
    client = docker.from_env()

    with TemporaryDirectory() as outd:
        out = Path(outd)

        debug_cmd = "echo 'Files in /code:' && find /code -type f -name '*.py' && echo 'Files in /tests:' && find /tests -type f -name '*.py'"

        print("=== DEBUG INFO ===")
        c_debug = client.containers.run(
            image=IMAGE_NAME,
            command=["bash", "-lc", debug_cmd],
            volumes={
                str(cut_dir.resolve()): {"bind": "/code", "mode": "ro"},
                str(tests_dir.resolve()): {"bind": "/tests", "mode": "ro"},
            },
            remove=True,
        )
        print(c_debug.decode("utf-8"))

        import_test_cmd = 'cd /tests && python -c \'import sys; sys.path.insert(0, "/"); from code.add import add; print("Import successful")\''
        print("=== IMPORT TEST ===")
        try:
            c_import = client.containers.run(
                image=IMAGE_NAME,
                command=["bash", "-lc", import_test_cmd],
                volumes={
                    str(cut_dir.resolve()): {"bind": "/code", "mode": "ro"},
                    str(tests_dir.resolve()): {"bind": "/tests", "mode": "ro"},
                },
                remove=True,
            )
            print(c_import.decode("utf-8"))
        except Exception as e:
            print(f"Import test failed: {e}")

        syntax_test_cmd = 'cd /tests && python -c \'import sys; sys.path.insert(0, "/"); exec(open("test_add.py").read()); print("Syntax check passed")\''
        print("=== SYNTAX TEST ===")
        try:
            c_syntax = client.containers.run(
                image=IMAGE_NAME,
                command=["bash", "-lc", syntax_test_cmd],
                volumes={
                    str(cut_dir.resolve()): {"bind": "/code", "mode": "ro"},
                    str(tests_dir.resolve()): {"bind": "/tests", "mode": "ro"},
                },
                remove=True,
            )
            print(c_syntax.decode("utf-8"))
        except Exception as e:
            print(f"Syntax test failed: {e}")

        collect_test_cmd = "cd /tests && PYTHONPATH=/ python -m pytest --collect-only -v"
        print("=== PYTEST COLLECT TEST ===")
        c_collect = client.containers.run(
            image=IMAGE_NAME,
            command=["bash", "-lc", collect_test_cmd],
            volumes={
                str(cut_dir.resolve()): {"bind": "/code", "mode": "ro"},
                str(tests_dir.resolve()): {"bind": "/tests", "mode": "ro"},
            },
            detach=True,
        )

        try:
            for chunk in c_collect.logs(stream=True):
                print(chunk.decode("utf-8"), end="")
            collect_exit_code = int(c_collect.wait().get("StatusCode", 1))
            print(f"Collection exit code: {collect_exit_code}")
        finally:
            try:
                c_collect.remove(force=True)
            except Exception:
                pass

        cat_test_cmd = "cat /tests/test_add.py"
        print("=== GENERATED TEST CONTENT ===")
        try:
            c_cat = client.containers.run(
                image=IMAGE_NAME,
                command=["bash", "-lc", cat_test_cmd],
                volumes={
                    str(cut_dir.resolve()): {"bind": "/code", "mode": "ro"},
                    str(tests_dir.resolve()): {"bind": "/tests", "mode": "ro"},
                },
                remove=True,
            )
            print(c_cat.decode("utf-8"))
        except Exception as e:
            print(f"Cat test failed: {e}")
        print("=== END DEBUG ===")

        cmd = (
            "PYTHONPATH=/ "
            "pytest -v /tests --timeout=5 --tb=short --cache-clear "
            "--json-report --json-report-file=/out/pytest-report.json"
        )

        c = client.containers.run(
            image=IMAGE_NAME,
            command=["bash", "-lc", cmd],
            volumes={
                str(cut_dir.resolve()): {"bind": "/code", "mode": "ro"},
                str(tests_dir.resolve()): {"bind": "/tests", "mode": "ro"},
                str(out.resolve()): {"bind": "/out", "mode": "rw"},
            },
            network_mode="none",
            detach=True,
        )

        try:
            for chunk in c.logs(stream=True):
                print(chunk.decode("utf-8"), end="")
            exit_code = int(c.wait().get("StatusCode", 1))
        finally:
            try:
                c.remove(force=True)
            except Exception:
                pass

        per_test = _parse_json_report(out / "pytest-report.json")

        per_file: Dict[str, bool] = {}
        for nodeid, r in per_test.items():
            file_path = nodeid.split("::", 1)[0]
            filename = Path(file_path).name

            if filename not in per_file:
                per_file[filename] = True

            if r.outcome != "passed":
                per_file[filename] = False

        return exit_code, per_file
