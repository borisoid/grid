import subprocess
import sys
from pathlib import Path


def test_mypy() -> None:
    import mypy.api

    stdout, stderr, code = mypy.api.run([str(Path.cwd())])
    print(stdout)
    print(stderr)
    assert code == 0


def test_pyright() -> None:
    subprocess.check_call(["pyright", ".", "--pythonpath", sys.executable])
