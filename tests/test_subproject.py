import pytest

from manager import Folder, Repository, Subproject


def test_name(subproject: Subproject, meta_repo: Repository) -> None:
    assert subproject.name == "LuaTeX"


def test_lowercase_name(subproject: Subproject, meta_repo: Repository) -> None:
    assert subproject.lowercase_name == "luatex"


def test_get(subproject: Subproject, meta_repo: Repository) -> None:
    text_file = subproject.get("library/node.lua")
    assert (
        str(text_file.path) == "/tmp/TeXLuaCATS_meta/TeXLuaCATS/LuaTeX/library/node.lua"
    )


def test_base(subproject: Subproject, meta_repo: Repository) -> None:
    assert str(subproject.base) == "/tmp/TeXLuaCATS_meta/TeXLuaCATS/LuaTeX"


def test_library(subproject: Subproject, meta_repo: Repository) -> None:
    assert str(subproject.library) == "/tmp/TeXLuaCATS_meta/TeXLuaCATS/LuaTeX/library"


def test_dist(subproject: Subproject, meta_repo: Repository) -> None:
    assert str(subproject.dist) == "/tmp/TeXLuaCATS_meta/dist/LuaTeX"


def test_dist_library(subproject: Subproject, meta_repo: Repository) -> None:
    assert str(subproject.dist_library) == "/tmp/TeXLuaCATS_meta/dist/LuaTeX/library"


def test_merged_defintions(subproject: Subproject, meta_repo: Repository) -> None:
    assert (
        str(subproject.merged_defintions)
        == "/tmp/TeXLuaCATS_meta/dist/LuaTeX/merged_defintions.lua"
    )


def test_merge(subproject: Subproject, meta_repo: Repository) -> None:
    assert subproject.merged_defintions.content == ""
    assert len(subproject.merged_defintions.content) == 0
    subproject.merge()
    assert len(subproject.merged_defintions.content) > 0
    assert "\nreturn " not in subproject.merged_defintions.content
    assert "@meta" in subproject.merged_defintions.content


@pytest.mark.slow
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

    assert dist.count() == 36

    assert "function callback.register" in dist.get("library/callback.lua").content
    assert library.count() == 34
    for file in library.list():
        assert "\n_N." not in file.content
