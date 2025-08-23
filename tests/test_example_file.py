from pathlib import Path
import pytest
from manager import ExampleFile


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

--tex: test
callback.register("post_linebreak_filter", function(head)
  for n, type, subtype in node.traverse(head.head) do
    assert.is_type(n, "userdata")
    assert.is_type(type, "number")
    assert.is_type(subtype, "number")
  end
  return head
end)
"""
    )


def test_orig_lines(example_file: ExampleFile) -> None:
    assert example_file.orig_lines == [
        "#! luatex --luaonly",
        "",
        'local assert = require("utils").assert',
        "",
        "--tex: test",
        'callback.register("post_linebreak_filter", function(head)',
        "  for n, type, subtype in node.traverse(head.head) do",
        '    assert.is_type(n, "userdata")',
        '    assert.is_type(type, "number")',
        '    assert.is_type(subtype, "number")',
        "  end",
        "  return head",
        "end)",
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


def test_tex_markup(example_file: ExampleFile) -> None:
    assert example_file.tex_markup == "test"


def test_shebang(example_file: ExampleFile) -> None:
    assert example_file.shebang == ["luatex", "--luaonly"]
