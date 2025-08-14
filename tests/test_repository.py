from manager import Repository, project_base_path


repo = Repository(project_base_path)


def test_get_commit_id() -> None:
    assert len(repo.get_latest_commitid()) == 40


def test_is_commited() -> None:
    assert isinstance(repo.is_commited(), bool)


def test_get_remote() -> None:
    assert repo.get_remote() == "git@github.com:TeXLuaCATS/manager.git"


def test_get_latest_commit_url() -> None:
    assert repo.get_latest_commitid() in repo.get_latest_commit_url()
