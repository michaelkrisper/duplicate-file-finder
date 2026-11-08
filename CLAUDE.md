# CLAUDE.md

Command-line tool that finds duplicate files in one or more directory trees by size and
SHA-256 content hash, optionally deleting older copies. Single file,
`duplicatefilefinder.py`, Python 3.9+, standard library only. No packaging, nothing
deployed.

## Commands

```bash
python3 duplicatefilefinder.py --help
python3 duplicatefilefinder.py DIR [DIR ...] [-a | -t X] [-f] [-s] [-H] [-e] [-m N] [-d]
pip install pytest ruff
pytest                     # test_duplicatefilefinder.py, < 1 s, uses tmp_path trees
ruff check .               # config in pyproject.toml (E, F, W, I; 140 cols)
```

CI (`.github/workflows/ci.yml`) runs ruff on 3.14 and pytest on 3.9 and 3.14.

## Architecture

- `main(argv)` -> `parse_arguments(argv)` -> `get_files()` (generator over `os.walk`,
  skips symlinks, files below `--min-file-size`, and hidden names unless `-H`) ->
  `filter_duplicate_files()` -> print -> optional `delete_duplicates()`.
- `filter_duplicate_files()` runs staged passes: size, then (only with `--fast`) SHA-256
  of the first 1024 bytes, then full SHA-256. Each pass only feeds the groups with more
  than one file into the next; with `--fast` it also keeps only the biggest groups,
  which is why fast mode may report fewer results.
- `-a` or `-top 0` sets `args.top = None` (show all). `--empty` sets the minimum size
  to 0.

## Rules and pitfalls

- Results go to stdout, progress and the summary to stderr; `-s` output is
  tab-separated for scripts. Keep that split.
- `--delete` removes every file but the newest (by mtime) in every group found, not
  only the displayed ones. Treat changes there as data-loss risks and cover them with
  tests on `tmp_path`.
- Hidden filtering applies only below the searched directory (scanning `~/.config/app`
  must work); hidden directories are pruned during the walk.
- Unreadable files and directories are reported on stderr and skipped, never fatal.
- The README's usage block mirrors the argparse help; update both together. Keep the
  legacy single-dash `-top` option.

## Workflow

- Every change starts with a GitHub issue. Branch `<issue>-<slug>` from `main`,
  open a PR with `Closes #<issue>`. Never push to `main` directly.
- PRs auto-merge (squash) once CI and the "Linked ticket" check pass; drafts are not merged.
- Versions exist only as git tags `vX.Y.Z`. Every merge to `main` tags the next patch;
  never edit version numbers in files. Minor/major releases: Actions -> Release.
- Nothing is deployed; a merge to `main` only creates the patch tag.
- Details: CONTRIBUTING.md.
