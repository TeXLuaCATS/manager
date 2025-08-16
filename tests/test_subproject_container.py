from manager import projects, set_subproject


class TestIterator:
    def test_all(self) -> None:
        counter = 0
        for project in projects:
            assert project.name.lower() == project.lowercase_name
            counter += 1
        assert counter == 13

    def test_set_subproject(self) -> None:
        set_subproject("luatex")
        counter = 0
        for project in projects:
            assert project.name.lower() == project.lowercase_name
            counter += 1
        assert counter == 1
        set_subproject(None)


def test_get() -> None:
    assert projects.get("luatex").name == "LuaTeX"
    assert projects.get("LuaTeX").name == "LuaTeX"


def test_names() -> None:
    assert projects.names == [
        "lmathx",
        "lpeg",
        "luaharfbuzz",
        "luasocket",
        "luazip",
        "lzlib",
        "md5",
        "slnunicode",
        "lualatex",
        "lualibs",
        "luametatex",
        "luaotfload",
        "luatex",
    ]
