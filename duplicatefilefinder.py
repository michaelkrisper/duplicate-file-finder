#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Module for traversing a directory structure, finding duplicate FILES and displaying them, but does NOT delete them."""

import os
import argparse
import hashlib
import sys
import time
from functools import partial, reduce
from multiprocessing import Pool

def parse_arguments():
    """ Parses the Arguments """

    epilog = """EXAMPLES:
    (1) %(prog)s ~/Downloads
        Description: Searches the Downloads directory for duplicate files and displays the top 3 duplicates (with the most files).

    (2) %(prog)s ~/Downloads ~/Documents -top 3
        Description: Searches duplicates in Downloads and Documents directories, but only displays the top 3 most duplicates

    (3) %(prog)s ~/Downloads ~/Documents -top 3 --fast
        Description: Searches for the top 3 duplicates across multiple directories. May eventually get less than 3 results, even if they would exist.

    (4) %(prog)s ~/Downloads ~/Documents ~/Pictures -a
        Description: Searches duplicates across multiple directories and displays ALL results

    (5) %(prog)s ~/Downloads --hidden --empty
        Description: Searches duplicates and also include hidden or empty files
    """

    parser = argparse.ArgumentParser(description=__doc__, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(dest="directories", nargs='+', help="one or more directories which should be checked for duplicate files")
    parser.add_argument("-f","--fast", dest="fast", action="store_true",
                        help="Searches very fast for only for the top X duplicates. The fast check may return less than the \
                        top X, even if they would exist. Remarks: the fast option is ignored when -a is given.")
    parser.add_argument("-d", "--delete", dest="delete_old", action="store_true", help="delete older duplicate files")
    parser.add_argument("-s", "--script-friendly", dest="script_friendly", action="store_true", help="use machine-readable output")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-a", dest="show_all", action="store_true", help="display all duplicate files. equal to -top 0")
    group.add_argument("-t", "-top", dest="top", action="store", metavar="X", default=3, type=int,
                       help="set the amount of displayed duplicates. If 0 is given, all results will be displayed. default=10")
    parser.add_argument("-H", "--hidden", dest="include_hidden", action="store_true", help="check hidden files and hidden directories too")
    parser.add_argument("-e", "--empty", dest="include_empty", action="store_true", help="check empty files too")
    group.add_argument("-m", "--min-file-size", dest="min_file_size", action="store", default=1, type=int,
                       help="set the file filter so that file must be at least min-file-size to be examined, defaults to 1")
    args = parser.parse_args()

    if args.fast:
        args.fast = True
    else:
        args.fast = False

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
    sortedfiles = sorted(files, key=lambda x: (len(x[1]), os.path.getsize(x[1][0])), reverse=True)
    for pos, entry in enumerate(sortedfiles[:displaycount], start=1):
        checksum, paths = entry
        checksum = checksum.hex()
        prefix = os.path.dirname(os.path.commonprefix(paths))
        print("\n(%d) Found %d duplicate files (size: %d Bytes, sha256 %r) in %s/:" % \
            (pos, len(paths), os.path.getsize(paths[0]), checksum, prefix))
        for i, path in enumerate(sorted(paths), start=1):
            print("%2d: %s" % (i, path))

def print_duplicates_script_friendly(files, displaycount=None):
    """Prints a list of duplicates in a machine-readable format."""
    sortedfiles = sorted(files, key=lambda x: (len(x[1]), os.path.getsize(x[1][0])), reverse=True)
    for i, entry in enumerate(sortedfiles[:displaycount]):
        _, paths = entry
        for path in sorted(paths):
            print("%d\t%s" % (i, path))

def delete_duplicates(files):
    """Deletes older duplicate files."""
    for checksum, paths in files:
        sortedpaths = sorted(paths, key=lambda x: os.path.getmtime(x), reverse=True)
        for path in sortedpaths[1:]:
            print("deleting: %s" % path, file=sys.stderr)
            os.remove(path)

def get_hash_key(filename, partial=False):
    """Calculates the hash value for a file."""
    hash_object = hashlib.sha256()
    try:
        blocksize = os.stat(filename).st_blksize
    except FileNotFoundError:
        return hash_object.digest()
    with open(filename, 'rb') as inputfile:
        if partial:
            hash_object.update(inputfile.read(blocksize))
        else:
            for chunk in iter(lambda:inputfile.read(blocksize), b""):
                hash_object.update(chunk)
    return hash_object.digest()

def get_partial_hash_key(filename):
    """Helper function to call get_hash_key with partial=True."""
    return get_hash_key(filename, partial=True)

def filter_duplicate_files(files, fast, top=None):
    """Finds all duplicate files in the directory."""
    duplicates = {}
    update = UpdatePrinter(stream=sys.stderr).update
    
    iterations = [(os.path.getsize, "By Size", False, top**2 if top else None)]
    if fast:
        iterations.append((get_partial_hash_key, "By Partial Hash", True, top*2 if top else None))
    iterations.append((get_hash_key, "By Full Hash", True, None))

    pool = Pool()
    try:
        for keyfunction, name, parallelize, topcount in iterations:
            duplicates.clear()
            count = 0
            duplicate_count = 0
            i = 0

            if parallelize:
                keys = pool.map(keyfunction, files)
                for i, (filepath, key) in enumerate(zip(files, keys), start=1):
                    duplicates.setdefault(key, []).append(filepath)
                    if len(duplicates[key]) > 1:
                        count += 1
                        if len(duplicates[key]) == 2:
                            count += 1
                            duplicate_count += 1
                    update("\r(%s) %d Files checked, %d duplicates found (%d files)" % (name, i, duplicate_count, count))
            else:
                for i, filepath in enumerate(files, start=1):
                    key = keyfunction(filepath)
                    duplicates.setdefault(key, []).append(filepath)
                    if len(duplicates[key]) > 1:
                        count += 1
                        if len(duplicates[key]) == 2:
                            count += 1
                            duplicate_count += 1
                    update("\r(%s) %d Files checked, %d duplicates found (%d files)" % (name, i, duplicate_count, count))

            update("\r(%s) %d Files checked, %d duplicates found (%d files)" % (name, i, duplicate_count, count), force=True)
            print("", file=sys.stderr)
            sortedfiles = sorted(duplicates.values(), key=len, reverse=True)
            files = [filepath for filepaths in sortedfiles[:topcount] if len(filepaths) > 1 for filepath in filepaths]
    finally:
        pool.close()
        pool.join()

    return [(checksum, duplicates[checksum]) for checksum in duplicates if len(duplicates[checksum]) > 1]

def get_files(directories, include_hidden, min_file_size=1):
    """Returns all FILES in the directories which apply to the filter rules."""
    for directory in directories:
        for dirpath, _, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if (not os.path.islink(filepath)
                    and (include_hidden or
                         reduce(lambda r, d: r and not d.startswith("."), os.path.abspath(filepath).split(os.sep), True))
                    and (os.path.getsize(filepath) >= min_file_size)):
                    yield filepath

if __name__ == "__main__":
    ARGS = parse_arguments()
    if ARGS.include_empty:
        ARGS.min_file_size = 0
    FILES = get_files(ARGS.directories, ARGS.include_hidden, ARGS.min_file_size)
    DUPLICATES = filter_duplicate_files(FILES, ARGS.fast, ARGS.top if ARGS.fast else None)
    
    if ARGS.script_friendly:
        print_duplicates_script_friendly(DUPLICATES, ARGS.top)
    else:
        print_duplicates_human_readable(DUPLICATES, ARGS.top)

    if ARGS.delete_old:
        delete_duplicates(DUPLICATES)

    if ARGS.fast:
        print("\nFound %d duplicates at least (%d duplicate files total) -- More duplicates may exist." % \
            (len(DUPLICATES), reduce(lambda sum_value, files: sum_value + len(files[1]), DUPLICATES, 0)), file=sys.stderr)
    else:
        print("\nFound %d duplicates (%d duplicate files total)" % \
            (len(DUPLICATES), reduce(lambda sum_value, files: sum_value + len(files[1]), DUPLICATES, 0)), file=sys.stderr)

