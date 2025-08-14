from pathlib import Path
from manager import render_template


tpl = Path(__file__).resolve().parent / "files" / "template.lua"


def test_template() -> None:
    assert render_template(tpl) == "---Please contribute\nlocal function test () end"
