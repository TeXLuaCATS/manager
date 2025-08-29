from pathlib import Path
import pytest
from manager import ExampleFile, Repository


@pytest.fixture
def example_file(files_dir: Path) -> ExampleFile:
    return ExampleFile(files_dir / "example-file.lua")


def test_path(example_file: ExampleFile) -> None:
    assert example_file.path.exists()


def test_orig_content(example_file: ExampleFile) -> None:
    assert (
        example_file.orig_content
        == """#! luatex --luaonly

local assert = require("utils").assert

--tex: tex
--tex-before: before
callback.register("post_linebreak_filter", function(head)
  for n, type, subtype in node.traverse(head.head) do
    assert.is_type(n, "userdata")
    assert.is_type(type, "number")
    assert.is_type(subtype, "number")
  end
  return head
end)
--tex-after: after
"""
    )


def test_orig_lines(example_file: ExampleFile) -> None:
    assert example_file.orig_lines == [
        "#! luatex --luaonly",
        "",
        'local assert = require("utils").assert',
        "",
        "--tex: tex",
        "--tex-before: before",
        'callback.register("post_linebreak_filter", function(head)',
        "  for n, type, subtype in node.traverse(head.head) do",
        '    assert.is_type(n, "userdata")',
        '    assert.is_type(type, "number")',
        '    assert.is_type(subtype, "number")',
        "  end",
        "  return head",
        "end)",
        "--tex-after: after",
    ]


def test_first_line(example_file: ExampleFile) -> None:
    assert example_file.first_line == "#! luatex --luaonly"


def test_cleaned_lua_code(example_file: ExampleFile) -> None:
    assert (
        example_file.cleaned_lua_code
        == """local assert = require("utils").assert

callback.register("post_linebreak_filter", function(head)
  for n, type, subtype in node.traverse(head.head) do
    assert.is_type(n, "userdata")
    assert.is_type(type, "number")
    assert.is_type(subtype, "number")
  end
  return head
end)"""
    )


def test_pure_lua_code(example_file: ExampleFile) -> None:
    assert (
        example_file.pure_lua_code
        == """callback.register("post_linebreak_filter", function(head)
  for n, type, subtype in node.traverse(head.head) do
    assert.is_type(n, "userdata")
    assert.is_type(type, "number")
    assert.is_type(subtype, "number")
  end
  return head
end)"""
    )


def test_docstring(example_file: ExampleFile) -> None:
    assert (
        example_file.docstring
        == """
---__Example:__
---
---```lua
---callback.register("post_linebreak_filter", function(head)
---  for n, type, subtype in node.traverse(head.head) do
---    assert.is_type(n, "userdata")
---    assert.is_type(type, "number")
---    assert.is_type(subtype, "number")
---  end
---  return head
---end)
---```
---"""
    )


def test_tex_markup_before(example_file: ExampleFile) -> None:
    assert example_file.tex_markup_before == "tex\nbefore"


def test_tex_markup_after(example_file: ExampleFile) -> None:
    assert example_file.tex_markup_after == "after"


def test_tmp_lua() -> None:
    assert "tmp.lua" in str(ExampleFile.tmp_lua())


def test_tmp_tex() -> None:
    assert "tmp.tex" in str(ExampleFile.tmp_tex())


def test_file_to_run(example_file: ExampleFile) -> None:
    assert "tmp.lua" in str(example_file.file_to_run)


def test_shebang(example_file: ExampleFile) -> None:
    assert example_file.shebang == ["luatex", "--luaonly"]


def test_luaonly(example_file: ExampleFile) -> None:
    assert example_file.luaonly is True
    example_file.luaonly = True
    assert example_file.luaonly is True
    example_file.luaonly = False
    assert example_file.luaonly is False
    example_file.shebang = ["luatex"]
    assert example_file.luaonly is False
    example_file.shebang = ["luatex", "--luaonly"]
    assert example_file.luaonly is True


def test_write_tex_file(example_file: ExampleFile, meta_repo: Repository) -> None:
    example_file.write_tex_file()
    assert (
        meta_repo.get_text_file("tmp.tex").content
        == """tex
before
\\directlua{dofile('tmp.lua')}
after
\\bye
"""
    )


def test_write_lua_file(example_file: ExampleFile, meta_repo: Repository) -> None:
    example_file.write_lua_file()
    assert (
        meta_repo.get_text_file("tmp.lua").content
        == """print('---start---')
local assert = require("utils").assert

callback.register("post_linebreak_filter", function(head)
  for n, type, subtype in node.traverse(head.head) do
    assert.is_type(n, "userdata")
    assert.is_type(type, "number")
    assert.is_type(subtype, "number")
  end
  return head
end)
print('---stop---')"""
    )
