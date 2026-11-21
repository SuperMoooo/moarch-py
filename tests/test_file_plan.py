from pathlib import Path

import pytest

from moarch_py.file_plan import AnchorNotFoundError, FileConflictError, FilePlan, insert_at_anchor

SOURCE = (
    "import a\n\n# moarch:imports\n\n"
    "def build():\n    items = []\n    # moarch:items\n    return items\n"
)


def test_insert_goes_above_the_anchor_with_its_indentation() -> None:
    result = insert_at_anchor(SOURCE, "items", "items.append(1)", relative_path="x.py")

    assert "    items.append(1)\n    # moarch:items\n" in result


def test_inserting_the_same_snippet_twice_changes_nothing() -> None:
    once = insert_at_anchor(SOURCE, "imports", "import b", relative_path="x.py")
    twice = insert_at_anchor(once, "imports", "import b", relative_path="x.py")

    assert twice == once


def test_a_missing_anchor_says_what_to_paste() -> None:
    with pytest.raises(AnchorNotFoundError) as raised:
        insert_at_anchor("x = 1\n", "routers", "include(r)", relative_path="router.py")

    assert raised.value.snippet == "include(r)"
    assert "router.py" in str(raised.value)


def test_nothing_is_written_when_one_file_conflicts(tmp_path: Path) -> None:
    (tmp_path / "taken.py").write_text("mine\n", encoding="utf-8")
    plan = FilePlan(tmp_path)
    plan.add("new.py", "new\n")
    plan.add("taken.py", "generated\n")

    with pytest.raises(FileConflictError) as raised:
        plan.write()

    assert raised.value.paths == ["taken.py"]
    assert not (tmp_path / "new.py").exists()
    assert (tmp_path / "taken.py").read_text(encoding="utf-8") == "mine\n"


def test_planned_edits_of_existing_files_are_not_conflicts(tmp_path: Path) -> None:
    (tmp_path / "router.py").write_text("old\n", encoding="utf-8")
    plan = FilePlan(tmp_path)
    plan.edit("router.py", "old\nnew\n")

    plan.write()

    assert (tmp_path / "router.py").read_text(encoding="utf-8") == "old\nnew\n"


def test_files_are_written_with_lf_line_endings(tmp_path: Path) -> None:
    plan = FilePlan(tmp_path)
    plan.add("a.py", "one\ntwo\n")

    plan.write()

    assert (tmp_path / "a.py").read_bytes() == b"one\ntwo\n"
