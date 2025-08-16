from pathlib import Path
from typing import Callable

from manager import Repository, TextFile


def test_content(text_file: TextFile) -> None:
    assert "local function test () end" in text_file.content


def test_render(text_file: TextFile, repo: Repository) -> None:
    assert (
        text_file.render(repo)
        == """\
---
---__Reference__:
---
---* Corresponding C source code: [lua/limglib.c Lines 301-304](https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/f52b099f3e01d53dc03b315e1909245c3d5418d3/source/texk/web2c/luatexdir/lua/limglib.c#L301-304)
---
---😱 [Types](https://github.com/TeXLuaCATS/manager/blob/main/tests/files/template.lua) incomplete or incorrect? 🙏 [Please contribute!](https://github.com/TeXLuaCATS/manager/pulls)
local function test () end"""
    )


def test_double_dash_comments(copy_to_tmp: Callable[[str | Path], Path]):
    path = copy_to_tmp("double-dash-comments.lua")
    file = TextFile(path)
    assert (
        file.remove_double_dash_comments()
        == "\n_N = {}\n\n---\n---@meta\n\n---\n---This is the TeX lib.\ntex = {}"
    )
