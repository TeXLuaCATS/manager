from manager import Color


def test_red() -> None:
    assert Color.red("red") == "\x1b[0;31mred\x1b[0m"


def test_green() -> None:
    assert Color.green("green") == "\x1b[0;32mgreen\x1b[0m"
