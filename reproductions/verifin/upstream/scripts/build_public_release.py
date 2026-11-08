#!/usr/bin/env python3
"""Build and validate a compact, anonymous publication snapshot.

This tool is deliberately source-preserving: it never changes or deletes files
in the working repository and refuses to overwrite an existing destination.
The embedded artifact builder deterministically generates per-run manifests.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Iterable


# Validation must not mutate a finished release by creating __pycache__ files.
sys.dont_write_bytecode = True


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "publication_manifest.json"

TEXT_SUFFIXES = {
    "",
    ".cff",
    ".csv",
    ".gitignore",
    ".gitattributes",
    ".html",
    ".ipynb",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".sh",
    ".smt2",
    ".svg",
    ".tex",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

FORBIDDEN_TOP_LEVEL_PATHS = {
    "artifacts",
    "data",
    "datasets",
    "results",
    "runs",
}

FORBIDDEN_PATH_PARTS = {
    ".claude",
    ".codex",
    ".git",
    ".ipynb_checkpoints",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
}

CONTENT_RULES = {
    "absolute macOS home path": re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    "absolute Linux home path": re.compile(r"/home/[A-Za-z0-9._-]+/"),
    "Anthropic-style credential": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "OpenAI-style credential": re.compile(
        r"(?<![A-Za-z0-9])sk-(?!ant-)[A-Za-z0-9_-]{20,}"
    ),
    "Hugging Face-style credential": re.compile(r"hf_[A-Za-z0-9]{20,}"),
    "GitHub-style credential": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "AWS access-key identifier": re.compile(r"AKIA[0-9A-Z]{16}"),
    "Slack-style credential": re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    "Google API credential": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}

EMAIL_RE = re.compile(
    r"(?<![A-Za-z0-9._%+-])([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})(?![A-Za-z0-9.-])"
)
SAFE_EXAMPLE_DOMAINS = {"example.com", "example.org", "example.net"}

# These directories are ignored in the private research worktree because they
# contain large, generated, or locally acquired state.  The publication builder
# copies only a hash-locked allowlist from them, so the corresponding top-level
# ignore rules must not survive in a fresh release: otherwise ``git add .``
# silently omits the paper datasets and results.
PRIVATE_ONLY_IGNORE_RULES = {"/data/", "/results/"}


class ReleaseError(RuntimeError):
    """A publication safety check failed."""


def _artifact_api() -> Any:
    """Import the sibling artifact builder in script and module contexts."""

    try:
        from scripts import build_publication_artifacts as artifact_api
    except ModuleNotFoundError:
        import build_publication_artifacts as artifact_api
    return artifact_api


def _load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ReleaseError("manifest root must be a JSON object")
    if not isinstance(data.get("include"), list) or not data["include"]:
        raise ReleaseError("manifest 'include' must be a non-empty list")
    if not isinstance(data.get("exclude_globs", []), list):
        raise ReleaseError("manifest 'exclude_globs' must be a list")
    return data


def _matches_any(path: Path, patterns: Iterable[str]) -> bool:
    normalized = path.as_posix()
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)


def _iter_source_files(source: Path, relative: Path, excludes: list[str]) -> Iterable[tuple[Path, Path]]:
    target = source / relative
    if not target.exists():
        raise ReleaseError(f"manifest entry does not exist: {relative}")
    if target.is_symlink():
        raise ReleaseError(f"symlinks are not allowed in the release: {relative}")
    if target.is_file():
        if not _matches_any(relative, excludes):
            yield target, relative
        return
    for candidate in sorted(target.rglob("*")):
        if candidate.is_dir():
            continue
        destination = candidate.relative_to(source)
        if candidate.is_symlink():
            raise ReleaseError(f"symlinks are not allowed in the release: {destination}")
        if not _matches_any(destination, excludes):
            yield candidate, destination


def _sanitize_notebook(source: Path, destination: Path) -> None:
    notebook = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(notebook, dict) or not isinstance(notebook.get("cells"), list):
        raise ReleaseError(f"notebook has an invalid structure: {source}")
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
            cell_metadata = cell.get("metadata")
            if isinstance(cell_metadata, dict):
                for key in ("execution", "ExecuteTime", "executionInfo"):
                    cell_metadata.pop(key, None)
    metadata = notebook.setdefault("metadata", {})
    metadata.pop("widgets", None)
    kernelspec = metadata.get("kernelspec")
    if isinstance(kernelspec, dict):
        kernelspec["display_name"] = "Python 3"
        kernelspec["name"] = "python3"
    destination.write_text(
        json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )


def _sanitize_release_gitignore(path: Path) -> None:
    """Remove private-worktree rules that hide locked release artifacts."""

    lines = path.read_text(encoding="utf-8").splitlines()
    kept = [line for line in lines if line.strip() not in PRIVATE_ONLY_IGNORE_RULES]
    marker = (
        "# data/ and results/ are intentionally commit-visible in this public "
        "snapshot; only hash-locked files are exported."
    )
    if marker not in kept:
        kept.extend(["", marker])
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")


def build_release(source: Path, destination: Path, manifest: dict[str, Any]) -> int:
    source = source.resolve()
    destination = destination.resolve()
    if destination.exists():
        raise ReleaseError(f"destination already exists; refusing to overwrite: {destination}")
    if destination == source or source in destination.parents:
        raise ReleaseError("destination cannot be inside the working repository")

    excludes = [str(item) for item in manifest.get("exclude_globs", [])]
    selected: dict[Path, Path] = {}
    for raw_entry in manifest["include"]:
        relative = Path(str(raw_entry))
        if relative.is_absolute() or ".." in relative.parts:
            raise ReleaseError(f"manifest entry must be repository-relative: {raw_entry}")
        for original, output_relative in _iter_source_files(source, relative, excludes):
            selected[output_relative] = original

    destination.mkdir(parents=True)
    try:
        for output_relative, original in sorted(selected.items()):
            output = destination / output_relative
            output.parent.mkdir(parents=True, exist_ok=True)
            if output.suffix == ".ipynb" and manifest.get("clear_notebook_outputs", True):
                _sanitize_notebook(original, output)
            else:
                shutil.copy2(original, output)
        release_gitignore = destination / ".gitignore"
        if release_gitignore.is_file():
            _sanitize_release_gitignore(release_gitignore)
        artifact_manifest = manifest.get("publication_artifacts")
        if artifact_manifest is not None:
            artifact_relative = Path(str(artifact_manifest))
            if artifact_relative.is_absolute() or ".." in artifact_relative.parts:
                raise ReleaseError(
                    "publication_artifacts must be a repository-relative path"
                )
            artifact_lock_path = (source / artifact_relative).resolve(strict=True)
            if source not in artifact_lock_path.parents:
                raise ReleaseError("publication_artifacts escapes the source repository")
            artifact_api = _artifact_api()
            artifact_lock = artifact_api._load_lock(artifact_lock_path)
            prepared = artifact_api.prepare_source(
                source, artifact_lock_path, artifact_lock
            )
            artifact_api.add_bundle(source, destination, prepared)
    except Exception:
        # Preserve the partial copy for inspection; never delete user data.
        raise

    issues = check_release(destination, manifest)
    if issues:
        formatted = "\n".join(f"- {issue}" for issue in issues)
        raise ReleaseError(f"release scan failed:\n{formatted}")
    return len(selected)


def _looks_textual(path: Path) -> bool:
    return path.name in {".gitignore", ".gitattributes"} or path.suffix.lower() in TEXT_SUFFIXES


def check_release(root: Path, manifest: dict[str, Any]) -> list[str]:
    root = root.resolve()
    if not root.is_dir():
        return [f"not a directory: {root}"]
    issues: list[str] = []
    max_bytes = int(manifest.get("max_file_bytes", 50_000_000))
    max_files = int(manifest.get("max_release_files", 10_000))
    max_total_bytes = int(manifest.get("max_release_bytes", 250_000_000))
    managed_artifact_paths: set[str] = set()
    gitignore_path = root / ".gitignore"
    if gitignore_path.is_file():
        release_ignore_rules = {
            line.strip()
            for line in gitignore_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        hidden_artifact_rules = sorted(
            PRIVATE_ONLY_IGNORE_RULES & release_ignore_rules
        )
        if hidden_artifact_rules:
            issues.append(
                "release .gitignore hides publication artifacts: "
                + ", ".join(hidden_artifact_rules)
            )
    artifact_manifest_path = root / "ARTIFACT_MANIFEST.json"
    if artifact_manifest_path.is_file():
        try:
            artifact_api = _artifact_api()
            artifact_api.check_bundle(root, allow_other_files=True)
            artifact_manifest = json.loads(
                artifact_manifest_path.read_text(encoding="utf-8")
            )
            managed_artifact_paths = {
                str(entry["path"])
                for entry in artifact_manifest.get("files", [])
                if isinstance(entry, dict) and isinstance(entry.get("path"), str)
            }
        except Exception as exc:
            issues.append(f"locked publication artifacts failed validation: {exc}")
    file_count = 0
    total_bytes = 0
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        relative = path.relative_to(root)
        # A freshly built snapshot has no history, but maintainers should also be
        # able to validate the working tree after creating its new anonymous Git
        # repository or cloning it. Git's object database is audited separately
        # through the neutral root commit and is not publication payload content.
        if ".git" in relative.parts:
            continue
        file_count += 1
        if path.is_symlink():
            issues.append(f"symlink is not allowed: {relative}")
            continue
        if (
            relative.parts[0] in FORBIDDEN_TOP_LEVEL_PATHS
            and relative.as_posix() not in managed_artifact_paths
        ) or set(relative.parts) & FORBIDDEN_PATH_PARTS:
            issues.append(f"forbidden publication path: {relative}")
        if relative.name == ".env" or relative.name.startswith(".env.") and relative.name != ".env.example":
            issues.append(f"credential file is not allowed: {relative}")
        size = path.stat().st_size
        total_bytes += size
        if size > max_bytes:
            issues.append(f"file exceeds {max_bytes:,} bytes: {relative} ({size:,})")
        if not _looks_textual(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            issues.append(f"text-like file is not valid UTF-8: {relative}")
            continue
        for label, pattern in CONTENT_RULES.items():
            if pattern.search(text):
                issues.append(f"{label} found in {relative}")
        for match in EMAIL_RE.finditer(text):
            email = match.group(1)
            domain = email.rsplit("@", 1)[1].lower()
            if domain not in SAFE_EXAMPLE_DOMAINS:
                issues.append(f"non-placeholder email found in {relative}")
                break
        if path.suffix == ".ipynb":
            notebook = json.loads(text)
            if not isinstance(notebook, dict) or not isinstance(
                notebook.get("cells"), list
            ):
                issues.append(f"notebook has an invalid structure: {relative}")
                continue
            for cell in notebook.get("cells", []):
                if cell.get("cell_type") != "code":
                    continue
                cell_metadata = cell.get("metadata")
                has_execution_metadata = isinstance(cell_metadata, dict) and any(
                    key in cell_metadata
                    for key in ("execution", "ExecuteTime", "executionInfo")
                )
                if (
                    cell.get("outputs")
                    or cell.get("execution_count") is not None
                    or has_execution_metadata
                ):
                    issues.append(f"executed notebook state found in {relative}")
                    break
    if file_count > max_files:
        issues.append(
            f"release exceeds {max_files:,} files: found {file_count:,}"
        )
    if total_bytes > max_total_bytes:
        issues.append(
            "release exceeds "
            f"{max_total_bytes:,} bytes: found {total_bytes:,}"
        )
    return issues


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path, help="new directory to create")
    mode.add_argument("--check", type=Path, metavar="DIRECTORY", help="validate an existing snapshot")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        manifest = _load_manifest(args.manifest.resolve())
        if args.check is not None:
            issues = check_release(args.check, manifest)
            if issues:
                for issue in issues:
                    print(f"ERROR: {issue}", file=sys.stderr)
                return 1
            print(f"Publication scan passed: {args.check.resolve()}")
            return 0
        count = build_release(ROOT, args.output, manifest)
        print(f"Created publication snapshot with {count} files: {args.output.resolve()}")
        return 0
    except (OSError, ValueError, ReleaseError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
