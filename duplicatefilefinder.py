#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Module for traversing a directory structure, finding duplicate FILES and displaying them, but does NOT delete them."""

import os
import argparse
import md5

__author__ = "Michael Krisper"
__copyright__ = "Copyright 2012, Michael Krisper"
__credits__ = ["Michael Krisper"]
__license__ = "GPL"
__version__ = "1.2.0"
__maintainer__ = "Michael Krisper"
__email__ = "michael.krisper@gmail.com"
__status__ = "Production"

def parse_arguments():
    """ Parses the Arguments """

    epilog = """EXAMPLES:
    (1) %(prog)s ~/Downloads
        Description: Searches the Downloads directory for duplicate FILES and displays the top 10.

    (2) %(prog)s ~/Downloads -top 3
        Description: Searches duplicates, but only displays the top 3 most duplicates

    (3) %(prog)s ~/Downloads -a
        Description: Searches duplicates and displays ALL results

    (4) %(prog)s ~/Downloads --hidden --empty
        Description: Searches duplicates and also include hidden or empty FILES"""

    parser = argparse.ArgumentParser(description=__doc__, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(dest="directory",
                        help="the directory which should be checked for duplicate FILES")

    group = parser.add_mutually_exclusive_group()

    group.add_argument("-a", dest="show_all", action="store_true",
                       help="display all duplicate FILES. equal to -top 0")

    group.add_argument("-top", dest="top", action="store", metavar="COUNT", type=int, default=10,
                       help="set the amount of displayed duplicates. If 0 is given, all results will be displayed. default=10")

    parser.add_argument("--hidden", dest="include_hidden", action="store_true",
                        help="check hidden FILES and directories too")

    parser.add_argument("--empty", dest="include_empty", action="store_true",
                        help="check empty FILES too")

    return parser.parse_args()

def print_duplicates(files, displaycount=None):
    """Prints a list of duplicates."""
    for pos, paths in enumerate(sorted(files, key=len, reverse=True)[:displaycount], start=1):
        prefix = os.path.dirname(os.path.commonprefix(paths))
        print "\n(%d) Found %d duplicate files (size: %d Bytes) in %s/:" % \
            (pos, len(paths), os.path.getsize(paths[0]), prefix)
        for i, path in enumerate(sorted(paths), start=1):
            print "%2d: %s" % (i, path[len(prefix) + 1:])

    print "\nFound %d duplicates (%d duplicate files total)" % \
        (len(files), reduce(lambda sumValue, files: sumValue + len(files), files, 0))

def filter_duplicate_files(fileList):
    """Finds all duplicate files in the directory."""
    duplicates = {}
    count = 0
    for i, filepath in enumerate(fileList, start=1):
        key = os.path.getsize(filepath)
        duplicates.setdefault(key, []).append(filepath)
        if len(duplicates[key]) > 1:
            count += 1
            if len(duplicates[key]) == 2:
                count += 1
        print "\r(By File Size) %d Files checked, %d duplicates found  (%d duplicate files)" % (i, len(duplicates), count),
    print ""
    
    fileList = (filepath for filepaths in duplicates.itervalues() if len(filepaths) > 1 for filepath in filepaths)
    
    duplicates = {}
    count = 0
    for i, filepath in enumerate(fileList, start=1):
        hash_object = md5.md5()
        with open(filepath, 'rb') as inputfile:
            for chunk in iter(lambda:inputfile.read(1024 * 4), ""):
                hash_object.update(chunk)
        key = hash_object.digest()
        duplicates.setdefault(key, []).append(filepath)
        if len(duplicates[key]) > 1:
            count += 1
            if len(duplicates[key]) == 2:
                count += 1
        print "\r(By File Hash) %d Files checked, %d duplicates found  (%d duplicate files)" % (i, len(duplicates), count),
    print ""

    return [filelist for filelist in duplicates.itervalues() if len(filelist) > 1]

def get_files(directory, include_hidden, include_empty):
    """Returns all FILES in the directory which apply to the filter rules."""
    return (os.path.join(dirpath, filename)
             for dirpath, _, filenames in os.walk(directory)
             for filename in filenames
                if not os.path.islink(os.path.join(dirpath, filename))
                and (include_hidden or
                     reduce(lambda r, d: r and not d.startswith("."), os.path.join(dirpath, filename).split(os.sep)[1:], True))
                and (include_empty or os.path.getsize(os.path.join(dirpath, filename)) > 0))
    

if __name__ == "__main__":
    ARGS = parse_arguments()
    FILES = get_files(ARGS.directory, ARGS.include_hidden, ARGS.include_empty)
    DUPLICATES = filter_duplicate_files(FILES)

    if ARGS.show_all or ARGS.top == 0:
        print_duplicates(DUPLICATES)
    else:
        print_duplicates(DUPLICATES, ARGS.top)
