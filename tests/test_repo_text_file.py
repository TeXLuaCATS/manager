from manager import RepoTextFile


def test_attribute_repo(repo_text_file: RepoTextFile) -> None:
    assert repo_text_file.repo


def test_render(repo_text_file: RepoTextFile) -> None:
    assert (
        repo_text_file.render()
        == "---😱 [Types](https://github.com/TeXLuaCATS/manager/blob/main/tests/files/template.lua) incomplete or incorrect? 🙏 [Please contribute!](https://github.com/TeXLuaCATS/manager/pulls)\nlocal function test () end"
    )
