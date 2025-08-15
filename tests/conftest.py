from pathlib import Path

import pytest

from manager import Repository, TextFile, RepoTextFile, project_base_path


@pytest.fixture
def repo() -> Repository:
    return Repository(project_base_path)


@pytest.fixture
def real_repo() -> Repository:
    return Repository.clone(
        "https://github.com/TeXLuaCATS/LuaTeX.git", "/tmp/luatex-type-definitions"
    )


@pytest.fixture
def template_path() -> Path:
    return Path(__file__).resolve().parent / "files" / "template.lua"


@pytest.fixture
def file_path(repo: Repository) -> Path:
    return repo.basepath / "test" / "test.lua"


@pytest.fixture
def text_file(template_path: Path) -> TextFile:
    return TextFile(template_path)


@pytest.fixture
def repo_text_file(repo: Repository, template_path: Path) -> RepoTextFile:
    return RepoTextFile(template_path, repo)
