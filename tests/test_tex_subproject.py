from manager import Repository, Subproject, TeXSubproject


def test_base(subproject: Subproject, meta_repo: Repository) -> None:
    assert str(subproject.base) == "/tmp/TeXLuaCATS_meta/TeXLuaCATS/LuaTeX"


def test_downstream_repo(subproject: Subproject, meta_repo: Repository) -> None:
    assert subproject.downstream_repo
    assert (
        str(subproject.downstream_repo.basepath)
        == "/tmp/TeXLuaCATS_meta/LuaCATS/downstream/tex-luatex"
    )


def test_readme_tex(tex_subproject: TeXSubproject, meta_repo: Repository) -> None:
    assert tex_subproject.readme_tex
    assert (
        str(tex_subproject.readme_tex)
        == "/tmp/TeXLuaCATS_meta/TeXLuaCATS/LuaTeX/README.tex"
    )


def test_compile_tex_doc(tex_subproject: TeXSubproject, meta_repo: Repository) -> None:
    tex_subproject.compile_tex_doc()
    assert tex_subproject.readme_pdf
    assert tex_subproject.readme_pdf.exists()
