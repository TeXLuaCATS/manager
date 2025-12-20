from pathlib import Path
import tempfile
from manager import _download_url  # type: ignore


def test_download() -> None:
    with tempfile.NamedTemporaryFile(delete=True) as tmp:
        _download_url("https://example.com", tmp.name)
        t = Path(tmp.name)
        assert t.exists()
        assert "Example" in t.read_text()
