from manager import Subproject, Repository


def test_merge(subproject: Subproject, meta_repo: Repository) -> None:
    assert subproject.merge_defintions.content == ""
    assert len(subproject.merge_defintions.content) == 0
    subproject.merge()
    assert len(subproject.merge_defintions.content) > 0
    assert "\nreturn " not in subproject.merge_defintions.content
    assert "@meta" in subproject.merge_defintions.content


def test_download_manuals(subproject: Subproject, meta_repo: Repository) -> None:
    subproject.manuals_folder.clear()
    assert len(list(subproject.manuals_folder.list_files(extension="tex"))) == 0
    subproject.download_manuals()
    assert len(list(subproject.manuals_folder.list_files(extension="tex"))) > 0
