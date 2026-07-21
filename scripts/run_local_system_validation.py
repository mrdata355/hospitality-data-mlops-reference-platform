from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    print(f"\n$ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=ROOT, check=True, env=env)


def _git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short=12", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "local-validation"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build, start, validate, and stop the local system stack."
    )
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--keep-running", action="store_true")
    parser.add_argument("--skip-pipeline", action="store_true")
    args = parser.parse_args()

    if shutil.which("docker") is None:
        raise RuntimeError("Docker is required for local system validation.")

    if not args.skip_pipeline:
        _run([sys.executable, "scripts/run_all.py"])
        _run([sys.executable, "scripts/run_backtests.py"])

    environment = os.environ.copy()
    environment.update(
        {
            "APP_ENV": "system-validation",
            "BUILD_DATE": datetime.now(timezone.utc).isoformat(),
            "BUILD_SHA": _git_sha(),
            "SERVICE_VERSION": environment.get("SERVICE_VERSION", "1.1.0"),
        }
    )

    _run(["docker", "compose", "up", "--build", "--detach"], env=environment)
    try:
        _run(
            [
                sys.executable,
                "scripts/run_system_validation.py",
                "--base-url",
                args.base_url,
            ],
            env=environment,
        )
    finally:
        if not args.keep_running:
            _run(["docker", "compose", "down"], env=environment)


if __name__ == "__main__":
    main()
