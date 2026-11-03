import os

import pytest

import duplicatefilefinder as dff


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return str(path)


def groups(duplicates):
    return sorted(sorted(os.path.basename(p) for p in paths) for _, paths in duplicates)


@pytest.fixture
def tree(tmp_path):
    write(tmp_path / "a.txt", b"same content")
    write(tmp_path / "sub" / "b.txt", b"same content")
    write(tmp_path / "c.txt", b"other conten")  # same size, different content
    write(tmp_path / "d.bin", b"x" * 2048 + b"1")
    write(tmp_path / "e.bin", b"x" * 2048 + b"2")  # same size and first 1024 bytes
    write(tmp_path / "f.bin", b"x" * 2048 + b"1")
    write(tmp_path / "empty1", b"")
    write(tmp_path / "empty2", b"")
    write(tmp_path / ".hidden.txt", b"same content")
    write(tmp_path / ".git" / "g.txt", b"same content")
    return tmp_path


def find(directory, fast=False, top=None, **kwargs):
    files = dff.get_files([str(directory)], kwargs.get("include_hidden", False), kwargs.get("min_file_size", 1))
    return dff.filter_duplicate_files(files, fast, top)


def test_finds_duplicates_by_content(tree):
    assert groups(find(tree)) == [["a.txt", "b.txt"], ["d.bin", "f.bin"]]


def test_fast_mode_finds_same_groups(tree):
    assert groups(find(tree, fast=True, top=3)) == [["a.txt", "b.txt"], ["d.bin", "f.bin"]]


def test_hidden_files_included_on_request(tree):
    result = groups(find(tree, include_hidden=True))
    assert [".hidden.txt", "a.txt", "b.txt", "g.txt"] in result


def test_empty_files_with_min_size_zero(tree):
    assert ["empty1", "empty2"] in groups(find(tree, min_file_size=0))


def test_min_file_size(tree):
    assert groups(find(tree, min_file_size=100)) == [["d.bin", "f.bin"]]


def test_hidden_ancestor_directory_is_searched(tmp_path):
    root = tmp_path / ".config" / "app"
    write(root / "a", b"data")
    write(root / "b", b"data")
    assert groups(find(root)) == [["a", "b"]]


def test_symlinks_are_ignored(tmp_path):
    target = write(tmp_path / "a", b"data")
    os.symlink(target, tmp_path / "link")
    assert list(dff.get_files([str(tmp_path)], False)) == [target]


def test_get_hash_key(tmp_path):
    path = write(tmp_path / "f", b"a" * 1024 + b"b")
    other = write(tmp_path / "g", b"a" * 1024 + b"c")
    assert dff.get_hash_key(path) != dff.get_hash_key(other)
    assert dff.get_hash_key(path, partial=True) == dff.get_hash_key(other, partial=True)


def test_get_hash_key_missing_file(tmp_path, capsys):
    assert dff.get_hash_key(str(tmp_path / "missing")) is None
    assert "missing" in capsys.readouterr().err


def test_delete_keeps_newest(tmp_path):
    old = write(tmp_path / "old", b"data")
    new = write(tmp_path / "new", b"data")
    os.utime(old, (1_000_000, 1_000_000))
    os.utime(new, (2_000_000, 2_000_000))
    dff.delete_duplicates([(b"key", [old, new])])
    assert not os.path.exists(old)
    assert os.path.exists(new)


def test_human_readable_output(tree, capsys):
    dff.print_duplicates_human_readable(find(tree), displaycount=1)
    out = capsys.readouterr().out
    assert "(1) Found 2 duplicate files (size: 2049 Bytes" in out
    assert "d.bin" in out and "f.bin" in out
    assert "a.txt" not in out


def test_script_friendly_output(tree, capsys):
    dff.print_duplicates_script_friendly(find(tree))
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 4
    assert [line.split("\t")[0] for line in lines] == ["0", "0", "1", "1"]
    assert lines[0].endswith("d.bin")


def test_parse_arguments_defaults():
    args = dff.parse_arguments(["dir"])
    assert args.directories == ["dir"]
    assert args.top == 3
    assert not args.fast


@pytest.mark.parametrize("argv", [["dir", "-a"], ["dir", "-top", "0"]])
def test_parse_arguments_show_all(argv):
    assert dff.parse_arguments(argv).top is None


def test_min_file_size_combines_with_show_all():
    args = dff.parse_arguments(["dir", "-a", "--min-file-size", "1024"])
    assert args.top is None
    assert args.min_file_size == 1024


def test_main_end_to_end(tree, capsys):
    dff.main([str(tree), "-s", "-a", "--empty"])
    out = capsys.readouterr().out
    assert len(out.splitlines()) == 6


def test_main_delete(tree):
    dff.main([str(tree), "-a", "--delete"])
    remaining = sorted(p.name for p in tree.rglob("*") if p.is_file())
    assert len([n for n in remaining if n in ("a.txt", "b.txt")]) == 1
    assert len([n for n in remaining if n in ("d.bin", "f.bin")]) == 1
    assert ".hidden.txt" in remaining and "c.txt" in remaining and "e.bin" in remaining
