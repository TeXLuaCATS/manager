from typing import Callable

import pytest

from manager import Repository, TextFile


@pytest.fixture
def template(TmpTextFile: Callable[[str], TextFile]) -> TextFile:
    return TmpTextFile("template.lua")


def test_filename(template: TextFile) -> None:
    assert template.filename == "template.lua"


def test_content(template: TextFile) -> None:
    assert "local function test () end" in template.content


def test_render(template: TextFile, repo: Repository) -> None:
    assert (
        template.render(repo)
        == """\
---
---__Reference__:
---
---* Corresponding C source code: [lua/limglib.c Lines 301-304](https://gitlab.lisn.upsaclay.fr/texlive/luatex/-/blob/f52b099f3e01d53dc03b315e1909245c3d5418d3/source/texk/web2c/luatexdir/lua/limglib.c#L301-304)
---
---😱 [Types](https://github.com/TeXLuaCATS/manager/blob/main/library/template.lua) incomplete or incorrect? 🙏 [Please contribute!](https://github.com/TeXLuaCATS/manager/pulls)
local function test () end"""
    )


def test_double_dash_comments(TmpTextFile: Callable[[str], TextFile]) -> None:
    file = TmpTextFile("double-dash-comments.lua")
    assert (
        file.remove_double_dash_comments()
        == "\n_N = {}\n\n---\n---@meta\n\n---\n---This is the TeX lib.\ntex = {}"
    )
