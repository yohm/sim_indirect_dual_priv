from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
FIGURES_DIR = SCRIPT_DIR / "figures"
OUTPUT_DIR = SCRIPT_DIR / "output"


def resolve_build_exe(exe_name: str, build_dir: str = "cmake-build-release") -> Path:
    return ROOT / build_dir / exe_name


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def figure_path(filename: str) -> Path:
    ensure_dir(FIGURES_DIR)
    return FIGURES_DIR / filename


def output_path(filename: str) -> Path:
    ensure_dir(OUTPUT_DIR)
    return OUTPUT_DIR / filename


def load_json_arg(value: str) -> str:
    path = Path(value)
    if path.exists():
        return path.read_text()
    return value


def dumps_json_arg(params: dict[str, Any]) -> str:
    return json.dumps(params, separators=(",", ":"))


def parse_json_stdout(text: str) -> dict[str, Any]:
    return json.loads(text)


def print_build_hint() -> None:
    print("[INFO] Please build the project first:", file=sys.stderr)
    print("  cmake -S . -B cmake-build-release -DCMAKE_BUILD_TYPE=Release", file=sys.stderr)
    print("  cmake --build cmake-build-release -j", file=sys.stderr)


def run_command(cmd: list[str], *, check: bool = True, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, capture_output=True, text=True, check=check)


def run_json_command(exe: Path | str, args: list[str]) -> dict[str, Any]:
    cmd = [str(exe)] + args
    try:
        result = run_command(cmd, check=True)
    except FileNotFoundError as exc:
        print(f"[ERROR] Executable not found: {exe}", file=sys.stderr)
        print_build_hint()
        raise RuntimeError(f"Executable not found: {exe}") from exc
    except subprocess.CalledProcessError as exc:
        print(f"[ERROR] Execution failed: {' '.join(cmd)}", file=sys.stderr)
        if exc.stdout:
            print(exc.stdout, file=sys.stderr)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        raise RuntimeError(f"Execution failed: {' '.join(cmd)}") from exc

    try:
        return parse_json_stdout(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"[ERROR] Failed to parse JSON output from {' '.join(cmd)}", file=sys.stderr)
        raise RuntimeError(f"Invalid JSON from {' '.join(cmd)}") from exc
