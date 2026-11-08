from __future__ import annotations

from scripts.build_public_release import (
    _sanitize_release_gitignore,
    check_release,
)


def _manifest() -> dict[str, object]:
    return {
        "include": ["README.md"],
        "max_file_bytes": 1_000_000,
        "max_release_files": 100,
        "max_release_bytes": 1_000_000,
    }


def test_release_gitignore_keeps_locked_artifacts_commit_visible(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text(".env\n/data/\n/results/\n/runs/\n", encoding="utf-8")

    _sanitize_release_gitignore(gitignore)

    text = gitignore.read_text(encoding="utf-8")
    assert "/data/" not in text.splitlines()
    assert "/results/" not in text.splitlines()
    assert "/runs/" in text.splitlines()
    assert "commit-visible" in text


def test_release_scan_rejects_gitignore_that_hides_artifacts(tmp_path):
    (tmp_path / ".gitignore").write_text("/data/\n/results/\n", encoding="utf-8")

    issues = check_release(tmp_path, _manifest())

    assert any("hides publication artifacts" in issue for issue in issues)


def test_release_scan_ignores_new_anonymous_git_database(tmp_path):
    git_object = tmp_path / ".git" / "objects" / "aa" / "object"
    git_object.parent.mkdir(parents=True)
    git_object.write_bytes(b"\x00\xffnot-text")

    issues = check_release(tmp_path, _manifest())

    assert not issues
