from manager import RepoTextFile


def test_attribute_repo(repo_text_file: RepoTextFile) -> None:
    assert repo_text_file.repo


def test_render(repo_text_file: RepoTextFile) -> None:
    assert (
        repo_text_file.render()
        == """\
---
---__Reference__:
---
---* Corresponding C source code: [lua/limglib.c Lines 301-304](https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/f52b099f3e01d53dc03b315e1909245c3d5418d3/source/texk/web2c/luatexdir/lua/limglib.c#L301-304)
---
---😱 [Types](https://github.com/TeXLuaCATS/manager/blob/main/tests/files/template.lua) incomplete or incorrect? 🙏 [Please contribute!](https://github.com/TeXLuaCATS/manager/pulls)
local function test () end"""
    )
