from manager import Folder, TextFile


def test_list(folder: Folder) -> None:
    counter = 0
    for _ in folder.list():
        counter += 1
    assert counter == 0

    folder.get("tmp.lua")
    counter = 0
    for _ in folder.list():
        counter += 1
    assert counter == 1


def test_get(folder: Folder) -> None:
    file_new = TextFile(folder.path / "some-file.txt")
    file_new.write("Some text ...")
    file_get = folder.get("some-file.txt")
    assert file_new.content == file_get.content


class TestClear:
    def test_root(self, folder: Folder) -> None:
        (folder.path / "new.txt").touch()
        assert folder.count() == 1
        folder.clear()
        assert folder.count() == 0

    def test_subfolder(self, folder: Folder) -> None:
        subfolder = folder.path / "sub"
        subfolder.mkdir()
        (subfolder / "file1.txt").touch()
        assert folder.count() == 2
        folder.clear("sub")
        assert folder.count() == 1


class TestCount:
    def test_root(self, folder: Folder) -> None:
        assert folder.count() == 0
        new = folder.path / "new.txt"
        new.touch()
        assert folder.count() == 1

    def test_subfolder(self, folder: Folder) -> None:
        assert folder.count() == 0
        subfolder = folder.path / "sub"
        subfolder.mkdir()
        file1 = subfolder / "file1.txt"
        file1.touch()
        assert folder.count("sub") == 1
        assert folder.count() == 2
