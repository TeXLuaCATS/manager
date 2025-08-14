from manager import Repository, project_base_path


repo = Repository(project_base_path)


def test_get_basepath() -> None:
    assert str(repo.get_basepath()).startswith("/")


def test_get_relpath() -> None:
    assert (
        repo.get_relpath(repo.get_basepath() / "test" / "test.lua") == "test/test.lua"
    )


def test_get_github_owner_repo() -> None:
    assert repo.get_github_owner_repo() == "TeXLuaCATS/manager"


def test_is_commited() -> None:
    assert isinstance(repo.is_commited(), bool)


def test_get_latest_commitid() -> None:
    assert len(repo.get_latest_commitid()) == 40


def test_get_latest_commit_url() -> None:
    assert repo.get_latest_commitid() in repo.get_latest_commit_url()


def test_get_remote() -> None:
    assert repo.get_remote() == "git@github.com:TeXLuaCATS/manager.git"
