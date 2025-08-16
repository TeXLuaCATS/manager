from manager import projects, set_subproject


def test_get() -> None:
    assert projects.get("luatex").name == "LuaTeX"
    assert projects.get("LuaTeX").name == "LuaTeX"


def test_iterator() -> None:
    counter = 0
    for project in projects:
        assert project.name.lower() == project.lowercase_name
        counter += 1
    assert counter == 13


def test_iterator_set_subproject() -> None:
    set_subproject("luatex")
    counter = 0
    for project in projects:
        assert project.name.lower() == project.lowercase_name
        counter += 1
    assert counter == 1
    set_subproject(None)
