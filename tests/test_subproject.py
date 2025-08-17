from manager import Folder, Subproject, Repository


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
    dist = Folder(subproject.dist)
    dist.clear()
    assert dist.count() == 0
    downstream = subproject.downstream_repo
    if downstream is None:
        raise Exception("Downstream must be not null.")
    library = Folder(downstream.path / "library")
    library.clear()
    assert library.count() == 0

    # distribute
    subproject.distribute(sync_to_remote=False)

    assert dist.count() == 35

    assert "function callback.register" in dist.get("library/callback.lua").content
    assert library.count() == 34
    for file in library.list():
        assert "\n_N." not in file.content
