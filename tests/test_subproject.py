from manager import Subproject, Repository


def test_merge(subproject: Subproject, meta_repo: Repository) -> None:
    assert subproject.merge_defintions.content == ""
    assert len(subproject.merge_defintions.content) == 0
    subproject.merge()
    assert len(subproject.merge_defintions.content) > 0
    assert "\nreturn " not in subproject.merge_defintions.content
    assert "@meta" in subproject.merge_defintions.content


def test_download_manuals(subproject: Subproject, meta_repo: Repository) -> None:
    folder = subproject.manuals_folder
    folder.clear()
    assert folder.count() == 0
    subproject.download_manuals()
    assert folder.count() > 0


def test_distribute(subproject: Subproject, meta_repo: Repository) -> None:
    if subproject.downstream_repo:
        subproject.downstream_repo.folder.clear()
    subproject.distribute(sync_to_remote=False)
