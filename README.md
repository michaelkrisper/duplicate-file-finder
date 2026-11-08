# duplicate-file-finder

Command-line tool that finds duplicate files in one or more directory trees by content.

[![CI](https://github.com/michaelkrisper/duplicate-file-finder/actions/workflows/ci.yml/badge.svg)](https://github.com/michaelkrisper/duplicate-file-finder/actions/workflows/ci.yml)
[![Version](https://img.shields.io/github/v/tag/michaelkrisper/duplicate-file-finder?sort=semver&label=version)](https://github.com/michaelkrisper/duplicate-file-finder/releases)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Files are compared in stages so that most of them never have to be read completely:

1. Group by file size
2. Group by SHA-256 of the first 1024 bytes (only with `--fast`)
3. Group by SHA-256 of the whole file

## Features

- Searches several directories at once
- Skips symlinks, and by default hidden and empty files
- Shows the duplicate groups with the most files first (top 3 by default, `-a` for all)
- Tab-separated output for scripts (`-s`)
- Optional deletion of older copies, keeping the newest file of each group (`-d`)
- Single file, standard library only

## Installation

Requires Python 3.9 or newer.

```bash
git clone https://github.com/michaelkrisper/duplicate-file-finder.git
cd duplicate-file-finder
python3 duplicatefilefinder.py --help
```

## Usage

```
usage: duplicatefilefinder.py [-h] [-f] [-d] [-s] [-a | -t X] [-H] [-e]
                              [-m MIN_FILE_SIZE]
                              directories [directories ...]

positional arguments:
  directories           one or more directories which should be checked for
                        duplicate files

options:
  -h, --help            show this help message and exit
  -f, --fast            search only for the top X duplicates, which is much
                        faster. May return fewer than X results, even if they
                        exist. Ignored when -a is given.
  -d, --delete          delete older duplicate files, keeping the newest file
                        of each group
  -s, --script-friendly
                        use machine-readable output
  -a                    display all duplicate files. equal to -top 0
  -t, -top X            set the amount of displayed duplicates. If 0 is given,
                        all results will be displayed. default=3
  -H, --hidden          check hidden files and hidden directories too
  -e, --empty           check empty files too
  -m, --min-file-size MIN_FILE_SIZE
                        set the file filter so that file must be at least min-
                        file-size to be examined, defaults to 1
```

### Examples

```bash
python3 duplicatefilefinder.py ~/Downloads                          # top 3 duplicate groups
python3 duplicatefilefinder.py ~/Downloads ~/Documents -top 5       # top 5 across two directories
python3 duplicatefilefinder.py ~/Downloads ~/Documents -top 3 --fast
python3 duplicatefilefinder.py ~/Pictures -a --min-file-size 1048576  # all groups, files >= 1 MiB
python3 duplicatefilefinder.py ~/Downloads --hidden --empty
python3 duplicatefilefinder.py ~/Downloads -a -s > duplicates.tsv
```

`--delete` acts on every duplicate group that was found, not only on the groups
that are displayed. Run without it first and check the result.

### Sample output

```
$ python3 duplicatefilefinder.py sample
(By Size) 7 Files checked, 3 duplicates found (7 files)
(By Full Hash) 7 Files checked, 2 duplicates found (5 files)

(1) Found 3 duplicate files (size: 21 Bytes, sha256 'd0c2c85112468272dca514d5cb8732349e8986f50b56b409a8bf23e0b473d70d') in sample/:
 1: sample/backup/beach.jpg
 2: sample/photos/2023/beach.jpg
 3: sample/photos/beach (1).jpg

(2) Found 2 duplicate files (size: 6 Bytes, sha256 '845e91831319e89c4d656bdb80c278ac09a7230d61e5dfd2e1b1fbb436ac8917') in sample/:
 1: sample/backup/report.txt
 2: sample/report.txt

Found 2 duplicates (5 duplicate files total)
```

Progress lines and the summary are written to stderr, the results to stdout.

## Development

```bash
pip install pytest ruff
pytest
ruff check .
```

CI runs both on every pull request. Every merge to `main` is tagged with the
next patch version; bundled releases with release notes come from the Release
workflow.

## Contributing

Changes start with an issue and go through a pull request; see
[CONTRIBUTING](CONTRIBUTING.md).

## License

MIT - see [LICENSE](LICENSE).
