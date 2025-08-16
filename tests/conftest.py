from pathlib import Path
import shutil
from typing import Callable, Union

import pytest

from manager import Repository, TextFile, project_base_path


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
    """files/template.lua"""
    return TextFile(template_path)


@pytest.fixture
def files_dir() -> Path:
    """
    Returns the path to the ``tests/files`` directory.

    Returns:
        Path: A Path object pointing to the ``tests/files`` directory.
    """
    return Path(__file__).parent / "files"


@pytest.fixture
def copy_to_tmp(tmp_path: Path, files_dir: Path) -> Callable[[Union[str, Path]], Path]:
    def _copy(src: Union[str, Path]) -> Path:
        """
        Copy a file from the specified source path within the ``tests/files`` to a temporary directory.

        Args:
            src (Union[str, Path]): The source file name or path relative to ``tests/files``.

        Returns:
            Path: The path to the copied file in the temporary directory.
        """
        src = files_dir / src
        dest: Path = tmp_path / src.name
        shutil.copy(files_dir / src, dest)
        return dest

    return _copy
