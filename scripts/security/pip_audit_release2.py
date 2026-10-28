from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ALL_ROOTS = (
    Path("ai-services"),
    Path("student-1"),
    Path("student-2"),
    Path("student-3"),
    Path("student-4"),
    Path("student-5"),
)

IGNORED_PARTS = {
    ".venv",
    "venv",
    "__pycache__",
}

STUDENT_PATTERN = re.compile(r"^student-[1-5]$")


def dependency_scope(file_name: str) -> Path | None:
    path = Path(file_name)
    parts = path.parts

    if not parts:
        return None

    if (
        parts[0] == "ai-services"
        and len(parts) >= 2
    ):
        return Path("ai-services") / parts[1]

    if STUDENT_PATTERN.fullmatch(parts[0]):
        return Path(parts[0])

    return None


def discover_requirement_files(
    roots: set[Path] | tuple[Path, ...],
) -> tuple[Path, ...]:
    requirement_files: set[Path] = set()

    for root in roots:
        if not root.is_dir():
            continue

        for requirement_file in root.rglob(
            "requirements.txt"
        ):
            if any(
                part in IGNORED_PARTS
                for part in requirement_file.parts
            ):
                continue

            requirement_files.add(requirement_file)

    return tuple(
        sorted(
            requirement_files,
            key=lambda path: path.as_posix(),
        )
    )


def main() -> int:
    supplied_files = sys.argv[1:]

    if supplied_files:
        selected_roots = {
            scope
            for file_name in supplied_files
            if (
                scope := dependency_scope(file_name)
            )
            is not None
        }

        if not selected_roots:
            print(
                "pip-audit: no Python dependency "
                "scope affected by this commit."
            )
            return 0

        print("Dependency scopes affected by commit:")

        for root in sorted(
            selected_roots,
            key=lambda path: path.as_posix(),
        ):
            print(f" - {root.as_posix()}")

        requirement_files = (
            discover_requirement_files(
                selected_roots
            )
        )
    else:
        print(
            "No filenames supplied; running full "
            "Release 2 dependency audit."
        )

        requirement_files = (
            discover_requirement_files(
                ALL_ROOTS
            )
        )

    if not requirement_files:
        print(
            "No dependency manifests found in "
            "the selected scope."
        )
        return 0

    failures: list[str] = []

    print(
        f"Auditing {len(requirement_files)} "
        "dependency manifest(s)."
    )

    for requirement_file in requirement_files:
        print(
            f"\n===== pip-audit: "
            f"{requirement_file.as_posix()} ====="
        )

        # Safe S603 exception: the executable and command are fixed,
        # and requirement_file is discovered only from repository paths.
        result = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-m",
                "pip_audit",
                "-r",
                str(requirement_file),
            ],
            check=False,
        )

        if result.returncode != 0:
            failures.append(
                requirement_file.as_posix()
            )

    if failures:
        print("\nDependency audit failed for:")

        for failure in failures:
            print(f" - {failure}")

        return 1

    print(
        "\nSelected Release 2 dependency "
        "manifests passed pip-audit."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
