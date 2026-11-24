"""Linuxのtrash関数がXDG Trashを使うことを検証する。"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TRASH_SCRIPT = ROOT / "shell" / "trash.sh"


@pytest.fixture
def isolated_trash(tmp_path):
    home = tmp_path / "home"
    data_home = tmp_path / "data"
    home.mkdir()
    data_home.mkdir()
    env = os.environ.copy()
    env.update({"HOME": str(home), "XDG_DATA_HOME": str(data_home)})

    def run(*args):
        return subprocess.run(
            [
                "bash",
                "-c",
                'source "$1"; shift; trash "$@"',
                "test-trash",
                str(TRASH_SCRIPT),
                *map(str, args),
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    return run, home, data_home


@pytest.mark.skipif(shutil.which("gio") is None, reason="gio is required")
def test_trash_uses_xdg_layout_and_records_original_path(isolated_trash):
    run, home, data_home = isolated_trash
    source = home / "a file.txt"
    source.write_text("content", encoding="utf-8")

    result = run("--", source)

    assert result.returncode == 0, result.stderr
    assert not source.exists()
    files = data_home / "Trash" / "files"
    info = data_home / "Trash" / "info"
    trashed = list(files.iterdir())
    assert len(trashed) == 1
    assert trashed[0].read_text(encoding="utf-8") == "content"
    metadata = (info / f"{trashed[0].name}.trashinfo").read_text(encoding="utf-8")
    assert "[Trash Info]" in metadata
    assert "Path=" in metadata and "%20" in metadata
    assert "DeletionDate=20" in metadata


@pytest.mark.skipif(shutil.which("gio") is None, reason="gio is required")
def test_trash_keeps_same_named_files_without_overwriting(isolated_trash):
    run, home, data_home = isolated_trash
    first = home / "first" / "same.txt"
    second = home / "second" / "same.txt"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")

    result = run(first, second)

    assert result.returncode == 0, result.stderr
    files = sorted((data_home / "Trash" / "files").iterdir())
    assert len(files) == 2
    assert sorted(file.read_text(encoding="utf-8") for file in files) == [
        "first",
        "second",
    ]


@pytest.mark.skipif(shutil.which("gio") is None, reason="gio is required")
def test_trash_preserves_rm_directory_and_missing_file_behavior(isolated_trash):
    run, home, _ = isolated_trash
    directory = home / "nested"
    directory.mkdir()
    missing = home / "missing"

    rejected_directory = run(directory)
    forced_missing = run("-f", missing)
    rejected_missing = run(missing)
    accepted_directory = run("-r", directory)

    assert rejected_directory.returncode != 0
    assert forced_missing.returncode == 0
    assert rejected_missing.returncode != 0
    assert accepted_directory.returncode == 0, accepted_directory.stderr
    assert not directory.exists()


def test_trash_reports_missing_gio(isolated_trash, tmp_path):
    _, home, data_home = isolated_trash
    source = home / "file"
    source.write_text("content", encoding="utf-8")
    empty_path = tmp_path / "empty-path"
    empty_path.mkdir()
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "XDG_DATA_HOME": str(data_home),
            "PATH": str(empty_path),
        }
    )

    result = subprocess.run(
        [
            shutil.which("bash") or "/bin/bash",
            "-c",
            'source "$1"; shift; trash "$@"',
            "test-trash",
            str(TRASH_SCRIPT),
            str(source),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode != 0
    assert "gio" in result.stderr.lower()
    assert source.exists()


def test_trash_keeps_source_when_gio_fails(isolated_trash, tmp_path):
    _, home, data_home = isolated_trash
    source = home / "file"
    source.write_text("content", encoding="utf-8")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_gio = fake_bin / "gio"
    fake_gio.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    fake_gio.chmod(0o755)
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "XDG_DATA_HOME": str(data_home),
            "PATH": f"{fake_bin}:/usr/bin:/bin",
        }
    )

    result = subprocess.run(
        [
            shutil.which("bash") or "/bin/bash",
            "-c",
            'source "$1"; shift; trash "$@"',
            "test-trash",
            str(TRASH_SCRIPT),
            str(source),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode != 0
    assert source.read_text(encoding="utf-8") == "content"
