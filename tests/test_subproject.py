from manager import Subproject, Repository, set_basepath


def test_merge(subproject: Subproject, meta_repo: Repository) -> None:
    assert meta_repo.path.exists()
    meta_repo.clean()
    set_basepath(meta_repo.path)
    assert subproject.merge_defintions.content == ""
    assert len(subproject.merge_defintions.content) == 0
    subproject.merge()
    assert len(subproject.merge_defintions.content) > 0
    assert "\nreturn " not in subproject.merge_defintions.content
    assert "@meta" in subproject.merge_defintions.content
