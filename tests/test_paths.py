from dglab import paths


def test_root_contains_project_files():
    assert (paths.ROOT / "pyproject.toml").exists()
    assert paths.CHAPTERS_DIR.is_dir()


def test_all_17_chapters_exist():
    for number in range(1, 18):
        chapter = paths.chapter_dir(number)
        assert (chapter / "README.md").exists()
