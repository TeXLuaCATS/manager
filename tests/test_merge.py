from manager import Repository, set_basepath, get_subproject


def test_merge(meta_repo: Repository) -> None:
    assert meta_repo.path.exists()
    set_basepath(meta_repo.path)
    luatex = get_subproject("luatex")
    luatex.merge()
    assert "\nreturn " not in luatex.merge_defintions.content
