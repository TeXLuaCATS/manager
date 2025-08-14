from manager import TextFile


def test_content(text_file: TextFile) -> None:
    assert "local function test () end" in text_file.content
