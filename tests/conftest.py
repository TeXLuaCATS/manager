from pathlib import Path

import pytest

from manager import Repository, TextFile, project_base_path


@pytest.fixture
def repo() -> Repository:
    return Repository(project_base_path)


@pytest.fixture
def template_path() -> Path:
    return Path(__file__).resolve().parent / "files" / "template.lua"


@pytest.fixture
def file_path(repo: Repository) -> Path:
    return repo.basepath / "test" / "test.lua"


@pytest.fixture
def text_file(template_path: Path) -> TextFile:
    return TextFile(template_path)
