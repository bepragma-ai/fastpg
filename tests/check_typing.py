"""Build and check FastPG as an installed library: python tests/check_typing.py."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="fastpg-typing-") as temporary:
        work = Path(temporary)
        dist = work / "dist"
        subprocess.run(
            [sys.executable, "-m", "build", "--outdir", str(dist)],
            cwd=ROOT, check=True,
        )
        wheel = next(dist.glob("*.whl"))
        with zipfile.ZipFile(wheel) as archive:
            assert "fastpg/py.typed" in archive.namelist()
        with tarfile.open(next(dist.glob("*.tar.gz"))) as archive:
            assert any(name.endswith("/src/fastpg/py.typed") for name in archive.getnames())

        environment = work / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        bin_dir = environment / ("Scripts" if os.name == "nt" else "bin")
        python = bin_dir / ("python.exe" if os.name == "nt" else "python")
        subprocess.run(
            [str(python), "-m", "pip", "install", str(wheel), "pyright>=1.1.400"],
            cwd=work, check=True,
        )
        consumer = work / "consumer"
        shutil.copytree(ROOT / "tests" / "typing", consumer)
        env = {**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", "")}
        env.pop("PYTHONPATH", None)
        # Running outside the checkout prevents src/ or an editable install from
        # masking missing annotations in the published artifact.
        command = [str(python), "-m", "pyright"]
        subprocess.run(command + ["--project", str(consumer)], cwd=consumer, env=env, check=True)
        result = subprocess.run(
            command + ["--verifytypes", "fastpg", "--ignoreexternal", "--outputjson"],
            cwd=consumer, env=env, check=True, stdout=subprocess.PIPE, text=True,
        )
        report = json.loads(result.stdout)
        assert report["typeCompleteness"]["completenessScore"] == 1, result.stdout
        print("Public type completeness: 100%")
        subprocess.run(
            [str(python), str(consumer / "queries.py")],
            cwd=consumer, env=env, check=True,
        )
    print("Installed-wheel typing checks passed.")


if __name__ == "__main__":
    main()
