from manager import Folder


class TestClear:

    def test_root(self, folder: Folder) -> None:
        new = folder.path / "new.txt"
        new.touch()
        assert folder.count() == 1
        folder.clear()
        assert folder.count() == 0

    def test_subfolder(self, folder: Folder) -> None:
        subfolder = folder.path / "sub"
        subfolder.mkdir()
        file1 = subfolder / "file1.txt"
        file1.touch()
        assert folder.count() == 2
        folder.clear("sub")
        assert folder.count() == 1


def test_number(folder: Folder) -> None:
    assert folder.count() == 0
    new = folder.path / "new.txt"
    new.touch()
    assert folder.count() == 1
