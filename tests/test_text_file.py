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
        template.render_templates(repo)
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


class TestConvertTexToLua:
    def test_preample(self, TmpTextFile: Callable[[str], TextFile]) -> None:
        file = TmpTextFile("luatex-manual_preamble.tex")
        assert (
            file.convert_tex_to_lua()
            == """---
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
---want to peek in “The *e-TeX* manual” and documentation about *pdfTeX*.
---
---But ... if you're here because of *Lua*, then all you need to know is that
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

    def test_lua(self, TmpTextFile: Callable[[str], TextFile]) -> None:
        file = TmpTextFile("luatex-manual_lua.tex")
        assert (
            file.convert_tex_to_lua()
            == """---
---# Using *LuaTeX*
---
---\\startsection[title={Initialization},reference=init]
---
---# *LuaTeX* as a *Lua* interpreter
---
---There are some situations that make *LuaTeX* behave like a standalone *Lua*
---interpreter:
---
---* if a `--luaonly` option is given on the commandline, or
---
---* if the executable is named `texlua` or `luatexlua`, or
---
---* if the only non-option argument (file) on the commandline has the extension
---    `lua` or `luc`.
---
---In this mode, it will set *Lua*'s `arg[0]` to the found script name, pushing
---preceding options in negative values and the rest of the command line in the
---positive values, just like the *Lua* interpreter.
---
---*LuaTeX* will exit immediately after executing the specified *Lua* script and is,
---in effect, a somewhat bulky stand alone *Lua* interpreter with a bunch of extra
---preloaded libraries.
---
---# *LuaTeX* as a *Lua* byte compiler
---
---There are two situations that make *LuaTeX* behave like the *Lua* byte compiler:
---
---* if a `--luaconly` option is given on the command line, or
---* if the executable is named `texluac`
---
---In this mode, *LuaTeX* is exactly like `luac` from the stand alone *Lua*
---distribution, except that it does not have the `-l` switch, and that it
---accepts (but ignores) the `--luaconly` switch. The current version of *Lua*
---can dump bytecode using `string.dump` so we might decide to drop this
---version of *LuaTeX*.
---
---# Other commandline processing
---
---When the *LuaTeX* executable starts, it looks for the `--lua` command line
---option. If there is no `--lua` option, the command line is interpreted in a
---similar fashion as the other *TeX* engines. Some options are accepted but have no
---consequence. The following command-line options are understood:
---
--- commandline argument                 explanation
---
--- `--credits`                     display credits and exit
--- `--debug-format`                enable format debugging
--- `--draftmode`                   switch on draft mode i.e.\\ generate no output in *PDF* mode
--- `--[no-]check-dvi-total-pages`  exit when DVI exceeds 65535 pages (default: check)
--- `--[no-]file-line-error`        disable/enable `file:line:error` style messages
--- `--[no-]file-line-error-style`  aliases of `--[no-]file-line-error`
--- `--fmt=FORMAT`                  load the format file `FORMAT`
--- `--halt-on-error`               stop processing at the first error
--- `--help`                        display help and exit
--- `--ini`                         be `iniluatex`, for dumping formats
--- `--interaction=STRING`          set interaction mode: `batchmode`, `nonstopmode`,
---                                            `scrollmode` or `errorstopmode`
--- `--jobname=STRING`              set the job name to `STRING`
--- `--kpathsea-debug=NUMBER`       set path searching debugging flags according to the bits of
---                                           `NUMBER`
--- `--lua=FILE`                    load and execute a *Lua* initialization script
--- `--luadebug`                    enable the `debug` library
--- `--[no-]mktex=FMT`              disable/enable `mktexFMT` generation with `FMT` is
---                                            `tex` or `tfm`
--- `--nosocket`                    disable the *Lua* socket library
--- `--no-socket`                   disable the *Lua* socket library
--- `--socket`                      enable the *Lua* socket library
--- `--output-comment=STRING`       use `STRING` for *DVI* file comment instead of date (no
---                                            effect for *PDF*)
--- `--output-directory=DIR`        use `DIR` as the directory to write files to
--- `--output-format=FORMAT`        use `FORMAT` for job output; `FORMAT` is `dvi`
---                                            or `pdf`
--- `--progname=STRING`             set the program name to `STRING`
--- `--recorder`                    enable filename recorder
--- `--safer`                       disable easily exploitable *Lua* commands
--- `--[no-]shell-escape`           disable/enable system calls
--- `--shell-restricted`            restrict system calls to a list of commands given in `texmf.cnf`
--- `--synctex=NUMBER`              enable `synctex`
--- `--utc`                         use utc times when applicable
--- `--version`                     display version and exit
---
---We don't support `write` 18 because `os.execute` can do the same. It
---simplifies the code and makes more write targets possible.
---
---The value to use for `jobname` is decided as follows:
---
---* If `--jobname` is given on the command line, its argument will be the
---    value for `jobname`, without any changes. The argument will not be
---    used for actual input so it need not exist. The `--jobname` switch only
---    controls the `jobname` setting.
---
---* Otherwise, `jobname` will be the name of the first file that is read
---    from the file system, with any path components and the last extension (the
---    part following the last `.`) stripped off.
---
---* There is an exception to the previous point: if the command line goes into
---    interactive mode (by starting with a command) and there are no files input
---    via `everyjob` either, then the `jobname` is set to `texput` as a last resort.
---
---The file names for output files that are generated automatically are created by
---attaching the proper extension (`log`, `pdf`, etc.) to the found
---`jobname`. These files are created in the directory pointed to by `--output-directory`, or in the current directory, if that switch is not present.
---If `--output-directory` is not empty, its value it's copied to the
---`TEXMF_OUTPUT_DIRECTORY` env. variable; if it's empty, the value of
---`TEXMF_OUTPUT_DIRECTORY` is the value of the output directory.
---"""
        )
