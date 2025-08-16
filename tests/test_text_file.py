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


def test_remove_double_dash_comments(TmpTextFile: Callable[[str], TextFile]) -> None:
    file = TmpTextFile("double-dash-comments.lua")
    assert (
        file.remove_double_dash_comments()
        == "\n_N = {}\n\n---\n---@meta\n\n---\n---This is the TeX lib.\ntex = {}"
    )

def test_manuals(TmpTextFile: Callable[[str], TextFile]) -> None:
    file = TmpTextFile("luatex-manual.tex")
    assert (
        file.convert_tex_to_lua()
        == """---% language=uk
---
---# Preamble
---
---This is a reference manual, not a tutorial. This means that we discuss changes
---relative to traditional *TeX* and also present new functionality. As a consequence
---we will refer to concepts that we assume to be known or that might be explained
---later.
---
---The average user doesn't need to know much about what is in this manual. For
---instance fonts and languages are normally dealt with in the macro package that
---you use. Messing around with node lists is also often not really needed at the
---user level. If you do mess around, you'd better know what you're dealing with.
---Reading “The *TeX* Book” by Donald Knuth is a good investment of time
---then also because it's good to know where it all started. A more summarizing
---overview is given by “*TeX* by Topic” by Victor Eijkhout. You might
---want to peek in “The *e-TeX* manual” and documentation about *PDF*TEX.
---
---But \\unknown\\ if you're here because of *Lua*, then all you need to know is that
---you can call it from within a run. The macro package that you use probably will
---provide a few wrapper mechanisms but the basic `directlua` command that
---does the job is:
---
---```
---\\directlua{tex.print("Hi there")}
---```
---
---You can put code between curly braces but if it's a lot you can also put it in a
---file and load that file with the usual *Lua* commands.
---"""
    )
