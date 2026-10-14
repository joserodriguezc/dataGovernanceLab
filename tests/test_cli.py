from typer.testing import CliRunner

from dglab.cli import app, chapter_modules


def test_chapter_modules_in_order():
    modules = chapter_modules()
    assert [n for n, _ in modules] == list(range(1, 18))
    assert modules[16][1] == "chapters.ch17_caso_estudio_novapay.run"


def test_run_all_stops_on_failure(monkeypatch):
    import importlib

    def boom(name):
        raise RuntimeError(f"fallo en {name}")

    monkeypatch.setattr(importlib, "import_module", boom)
    result = CliRunner().invoke(app, ["run-all", "--start", "17", "--no-build"])
    assert result.exit_code == 1
    assert "Falla el capítulo 17" in result.output
