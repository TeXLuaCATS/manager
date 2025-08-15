from pathlib import Path

from manager import Repository


def test_basepath(repo: Repository) -> None:
    assert str(repo.basepath).startswith("/")


def test_get_relpath(repo: Repository, file_path: Path) -> None:
    assert repo.get_relpath(file_path) == "test/test.lua"


def test_get_github_blob_url(repo: Repository, file_path: Path) -> None:
    assert (
        repo.get_github_blob_url(file_path)
        == "https://github.com/TeXLuaCATS/manager/blob/main/test/test.lua"
    )


def test_github_owner_repo(repo: Repository) -> None:
    assert repo.github_owner_repo == "TeXLuaCATS/manager"


def test_github_pull_request_url(repo: Repository) -> None:
    assert repo.github_pull_request_url == "https://github.com/TeXLuaCATS/manager/pulls"


def test_is_commited(repo: Repository) -> None:
    assert isinstance(repo.is_commited, bool)


def test_get_latest_commitid(repo: Repository) -> None:
    assert len(repo.latest_commitid) == 40


def test_get_latest_commit_url(repo: Repository) -> None:
    assert repo.latest_commitid in repo.latest_commit_url


def test_get_remote(repo: Repository) -> None:
    assert repo.remote == "git@github.com:TeXLuaCATS/manager.git"


def test_files(repo: Repository) -> None:
    count = 0
    for _ in repo.files("tests/files"):
        count += 1
    assert count == 1


def test_copy_subdir(real_repo: Repository, tmp_path: Path) -> None:
    real_repo.copy_subdir("library", tmp_path)
    assert (tmp_path / "callback.lua").exists()


def test_real_repo(real_repo: Repository) -> None:
    assert real_repo.github_owner_repo == "TeXLuaCATS/LuaTeX"
