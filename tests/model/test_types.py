import subprocess
from pathlib import Path


def test_mypy() -> None:
    subprocess.check_call(["mypy", Path.cwd()])


# def test_pyright() -> None:
#     subprocess.check_call(["pyright", "."])
