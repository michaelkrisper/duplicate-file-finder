duplicate-file-finder
=====================
This is a python script to find duplicate files in a directory structure.

Files are searched in 3 ways to get optimimum performance:
1) Compare by file size only
2) Compare by md5-hash value of the first 1024 bytes
3) Compare by md5-hash value of the whole file.

After the whole directory structure is searched, duplicate files are displayed. With the default settings the top 10 duplicate values (those with the most duplicate files) are displayed, but that can be changed by an argument (-top).

Usage:
=====================
usage: duplicatefilefinder.py [-h] [-a | -top TOP] [--hidden] [--empty]
                              directory

positional arguments:
  directory   the directory which should be checked for duplicate files

optional arguments:
  -h, --help  show this help message and exit
  -a          display all duplicate files. equal to -top 0
  -top TOP    set the amount of displayed duplicates. If 0 is given, all
              results will be displayed. default=10
  --hidden    check hidden files and directories too
  --empty     check empty files too

EXAMPLES:
    (1) duplicatefilefinder.py ~/Downloads
        Description: Searches the Downloads directory for duplicate files and displays the top 10.

    (2) duplicatefilefinder.py ~/Downloads -top 3
        Description: Searches duplicates, but only displays the top 3 most duplicates

    (3) duplicatefilefinder.py ~/Downloads -a
        Description: Searches duplicates and displays ALL results

    (4) duplicatefilefinder.py ~/Downloads --hidden --empty
        Description: Searches duplicates and also include hidden or empty files



Sample Output:
=====================
duplicatefilefinder.py . --hidden --empty

Filesize compare:
108 files checked - 13 duplicates found (44 duplicate files)

Quick content compare:
44 files checked - 5 duplicates found (17 duplicate files)

Intensive content compare:
17 files checked - 5 duplicates found (16 duplicate files)

(1) Found 5 duplicate files (size: 41 Bytes) in ./.git/:
	1: ORIG_HEAD
	2: refs/heads/master
	3: refs/remotes/origin/master
	4: refs/tags/1.0
	5: refs/tags/v1.0

(2) Found 4 duplicate files (size: 11341 Bytes) in ./:
	1: callgraph.dot
	2: test/callgraph.dot
	3: test/copy of callgraph.dot
	4: test/copy of copy of callgraph.dot

(3) Found 3 duplicate files (size: 15151 Bytes) in ./test/:
	1: another copy of copy of New Empty File
	2: copy of copy of New Empty File
	3: third copy of copy of New Empty File

(4) Found 2 duplicate files (size: 3831 Bytes) in ./.git/logs/:
	1: HEAD
	2: refs/heads/master

(5) Found 2 duplicate files (size: 0 Bytes) in ./test/:
	1: .samplehiddenfile
	2: New Empty File

Found 5 duplicates (16 duplicate files total)

