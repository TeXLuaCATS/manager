from manager import subprojects, set_subproject


class TestIterator:
    def test_all(self) -> None:
        counter = 0
        for project in subprojects:
            assert project.name.lower() == project.lowercase_name
            counter += 1
        assert counter == 13

    def test_set_subproject(self) -> None:
        set_subproject("luatex")
        counter = 0
        for project in subprojects:
            assert project.name.lower() == project.lowercase_name
            counter += 1
        assert counter == 1
        set_subproject(None)


class TestGet:
    def test_by_lowercase(self) -> None:
        assert subprojects.get("luatex").name == "LuaTeX"

    def test_by_camelcase(self) -> None:
        assert subprojects.get("LuaTeX").name == "LuaTeX"


def test_names() -> None:
    assert subprojects.names == [
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
