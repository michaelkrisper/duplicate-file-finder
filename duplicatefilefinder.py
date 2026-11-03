#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Traverses directory structures, finds duplicate files and displays them. Files are only deleted when --delete is given."""

import argparse
import hashlib
import os
import sys
import time
from functools import partial, reduce


def parse_arguments(argv=None):
    """ Parses the Arguments """

    epilog = """examples:
  %(prog)s ~/Downloads
      search Downloads and display the 3 duplicates with the most files

  %(prog)s ~/Downloads ~/Documents -top 5
      search both directories and display the 5 duplicates with the most files

  %(prog)s ~/Downloads ~/Documents -top 3 --fast
      quickly search for the top 3 duplicates (may return fewer than 3)

  %(prog)s ~/Downloads ~/Documents ~/Pictures -a
      search all three directories and display all duplicates

  %(prog)s ~/Downloads --hidden --empty
      also include hidden and empty files
"""

    parser = argparse.ArgumentParser(description=__doc__, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(dest="directories", nargs='+', help="one or more directories which should be checked for duplicate files")
    parser.add_argument("-f","--fast", dest="fast", action="store_true",
                        help="search only for the top X duplicates, which is much faster. May return fewer than X results, "
                        "even if they exist. Ignored when -a is given.")
    parser.add_argument("-d", "--delete", dest="delete_old", action="store_true",
                        help="delete older duplicate files, keeping the newest file of each group")
    parser.add_argument("-s", "--script-friendly", dest="script_friendly", action="store_true", help="use machine-readable output")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-a", dest="show_all", action="store_true", help="display all duplicate files. equal to -top 0")
    group.add_argument("-t", "-top", dest="top", action="store", metavar="X", default=3, type=int,
                       help="set the amount of displayed duplicates. If 0 is given, all results will be displayed. default=3")
    parser.add_argument("-H", "--hidden", dest="include_hidden", action="store_true", help="check hidden files and hidden directories too")
    parser.add_argument("-e", "--empty", dest="include_empty", action="store_true", help="check empty files too")
    parser.add_argument("-m", "--min-file-size", dest="min_file_size", action="store", default=1, type=int,
                       help="set the file filter so that file must be at least min-file-size to be examined, defaults to 1")
    args = parser.parse_args(argv)

    if args.show_all or args.top == 0:
        args.top = None

    return args

class UpdatePrinter(object):
    """Class for printing nice status output on the console."""
    def __init__(self, refreshrate=0.05, stream=sys.stdout):
        self.__last = 0
        self.__last_text_length = 0
        self.refreshrate = refreshrate
        self.stream = stream

    def update(self, value, force=False, flush=True):
        """Updates the last line on the console. Overwrites previous output made with
        this method. Has a mechanism which prevents flickering. Use the force parameter to enforce output."""
        if ((time.time() - self.__last) >= self.refreshrate) or force:
            print("\r%s%s" % (value, " " * (self.__last_text_length - len(value))), end=' ', file=self.stream)
            self.__last_text_length = len(value)
            if flush:
                self.stream.flush()
            self.__last = time.time()

def print_duplicates_human_readable(files, displaycount=None):
    """Prints a list of duplicates in a human-readable format."""
    try:
        sortedfiles = sorted(files, key=lambda x: (len(x[1]), os.path.getsize(x[1][0])), reverse=True)
    except OSError:
        sortedfiles = sorted(files, key=lambda x: len(x[1]), reverse=True)

    for pos, entry in enumerate(sortedfiles[:displaycount], start=1):
        try:
            checksum, paths = entry
            checksum = checksum.hex()
            prefix = os.path.dirname(os.path.commonprefix(paths))
            print("\n(%d) Found %d duplicate files (size: %d Bytes, sha256 %r) in %s/:" % \
                (pos, len(paths), os.path.getsize(paths[0]), checksum, prefix))
            for i, path in enumerate(sorted(paths), start=1):
                print("%2d: %s" % (i, path))
        except OSError as e:
            print("\nCould not display duplicate entry, file might have been deleted: %s" % e, file=sys.stderr)

def print_duplicates_script_friendly(files, displaycount=None):
    """Prints a list of duplicates in a machine-readable format."""
    try:
        sortedfiles = sorted(files, key=lambda x: (len(x[1]), os.path.getsize(x[1][0])), reverse=True)
    except OSError:
        sortedfiles = sorted(files, key=lambda x: len(x[1]), reverse=True)
    for i, entry in enumerate(sortedfiles[:displaycount]):
        _, paths = entry
        for path in sorted(paths):
            print("%d\t%s" % (i, path))

def delete_duplicates(files):
    """Deletes older duplicate files."""
    for checksum, paths in files:
        try:
            sortedpaths = sorted(paths, key=lambda x: os.path.getmtime(x), reverse=True)
            for path in sortedpaths[1:]:
                try:
                    print("deleting: %s" % path, file=sys.stderr)
                    os.remove(path)
                except OSError as e:
                    print("could not delete file: %s" % e, file=sys.stderr)
        except OSError as e:
            print("could not access file for deletion: %s" % e, file=sys.stderr)

def get_hash_key(filename, partial=False):
    """Calculates the hash value for a file."""
    try:
        hash_object = hashlib.sha256()
        with open(filename, 'rb') as inputfile:
            if partial:
                hash_object.update(inputfile.read(1024))
            else:
                for chunk in iter(lambda:inputfile.read(1024 * 8), b""):
                    hash_object.update(chunk)
        return hash_object.digest()
    except OSError as e:
        print("permission denied for file: %s" % e.filename, file=sys.stderr)
        return None

def filter_duplicate_files(files, fast, top=None):
    """Finds all duplicate files in the directory."""
    duplicates = {}
    update = UpdatePrinter(stream=sys.stderr).update

    iterations = [(os.path.getsize, "By Size", top**2 if top else None)]
    if fast:
        iterations.append((partial(get_hash_key, partial=True), "By Partial Hash", top*2 if top else None))
    iterations.append((get_hash_key, "By Full Hash", None))

    for keyfunction, name, topcount in iterations:
        duplicates.clear()
        count = 0
        duplicate_count = 0
        i = 0
        for i, filepath in enumerate(files, start=1):
            key = keyfunction(filepath)
            if key is None:
                continue
            duplicates.setdefault(key, []).append(filepath)
            if len(duplicates[key]) > 1:
                count += 1
                if len(duplicates[key]) == 2:
                    count += 1
                    duplicate_count += 1

            update("\r(%s) %d Files checked, %d duplicates found (%d files)" % (name, i, duplicate_count, count))
        else:
            update("\r(%s) %d Files checked, %d duplicates found (%d files)" % (name, i, duplicate_count, count), force=True)
        print("", file=sys.stderr)
        sortedfiles = sorted(duplicates.values(), key=len, reverse=True)
        files = [filepath for filepaths in sortedfiles[:topcount] if len(filepaths) > 1 for filepath in filepaths]

    return [(checksum, duplicates[checksum]) for checksum in duplicates if len(duplicates[checksum]) > 1]

def on_walk_error(err):
    """Error handler for os.walk."""
    print("Cannot access directory '%s'. Permission denied." % err.filename, file=sys.stderr)


def get_files(directories, include_hidden, min_file_size=1):
    """Returns all files in the directories which apply to the filter rules."""
    for directory in directories:
        for dirpath, dirnames, filenames in os.walk(directory, onerror=on_walk_error):
            if not include_hidden:
                # Only names below the given directory count as hidden, not the directory's own ancestors.
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
                filenames = [f for f in filenames if not f.startswith(".")]
            for filename in filenames:
                try:
                    filepath = os.path.join(dirpath, filename)
                    if not os.path.islink(filepath) and os.path.getsize(filepath) >= min_file_size:
                        yield filepath
                except OSError:
                    # e.g. permission denied
                    print("Cannot access file '%s'. Permission denied." % filepath, file=sys.stderr)
                    continue

def main(argv=None):
    """Runs the command line interface."""
    args = parse_arguments(argv)
    if args.include_empty:
        args.min_file_size = 0
    files = get_files(args.directories, args.include_hidden, args.min_file_size)
    duplicates = filter_duplicate_files(files, args.fast, args.top if args.fast else None)

    if args.script_friendly:
        print_duplicates_script_friendly(duplicates, args.top)
    else:
        print_duplicates_human_readable(duplicates, args.top)

    if args.delete_old:
        delete_duplicates(duplicates)

    if args.fast:
        print("\nFound %d duplicates at least (%d duplicate files total) -- More duplicates may exist." % \
            (len(duplicates), reduce(lambda sum_value, files: sum_value + len(files[1]), duplicates, 0)), file=sys.stderr)
    else:
        print("\nFound %d duplicates (%d duplicate files total)" % \
            (len(duplicates), reduce(lambda sum_value, files: sum_value + len(files[1]), duplicates, 0)), file=sys.stderr)


if __name__ == "__main__":
    main()
