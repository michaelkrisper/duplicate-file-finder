#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Module for traversing a directory structure, finding duplicate FILES and displaying them, but does NOT delete them."""

import os
import argparse
import hashlib
import zlib

__author__ = "Michael Krisper"
__copyright__ = "Copyright 2012, Michael Krisper"
__credits__ = ["Michael Krisper"]
__license__ = "GPL"
__version__ = "1.2.1"
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
        Description: Searches duplicates and also include hidden or empty FILES

    (5) %(prog)s ~/Downloads -top 3 --fast 
        Description: Searches for the top 3 duplicates. May get less than 3 results, even if they exist."""

    parser = argparse.ArgumentParser(description=__doc__, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(dest="directory", help="the directory which should be checked for duplicate FILES")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-a", dest="show_all", action="store_true", help="display all duplicate FILES. equal to -top 0")
    group.add_argument("-top", dest="top", action="store", metavar="X", default=10, type=int,  
                       help="set the amount of displayed duplicates. If 0 is given, all results will be displayed. default=10")
    
    parser.add_argument("--hidden", dest="include_hidden", action="store_true", help="check hidden FILES and directories too")
    parser.add_argument("--empty", dest="include_empty", action="store_true", help="check empty FILES too")
    parser.add_argument("--fast", dest="fast", action="store_true", 
                        help="Searches very fast for only for the top X duplicates. The fast check may return less than the top X, even if they would exist. Remarks: the --fast option is useless when -a is given.")


    args = parser.parse_args()

    if args.show_all or args.top == 0:
        args.top = None

    return args

def print_duplicates(files, displaycount=None):
    """Prints a list of duplicates."""
    sortedfiles = sorted(files, key=lambda x: (len(x), os.path.getsize(x[0])), reverse=True)
    for pos, paths in enumerate(sortedfiles[:displaycount], start=1):
        prefix = os.path.dirname(os.path.commonprefix(paths))
        print "\n(%d) Found %d duplicate files (size: %d Bytes) in %s/:" % \
            (pos, len(paths), os.path.getsize(paths[0]), prefix)
        for i, path in enumerate(sorted(paths), start=1):
            print "%2d: %s" % (i, path[len(prefix) + 1:])

    print "\nFound %d duplicates (%d duplicate files total)" % \
        (len(files), reduce(lambda sumValue, files: sumValue + len(files), files, 0))

def get_hash_key(filename):
    """Calculates the hash value for a file."""
    hash_object = hashlib.md5()
    with open(filename, 'rb') as inputfile:
        for chunk in iter(lambda:inputfile.read(1024 * 8), ""):
            hash_object.update(chunk)
    return hash_object.digest()

def get_crc_key(filename):
    """Calculates the crc value for a file."""
    with open(filename, 'rb') as inputfile:
        chunk = inputfile.read(128)
    return zlib.adler32(chunk)

def filter_duplicate_files(files, top=None):
    """Finds all duplicate files in the directory."""
    duplicates = {}
    iterations = ((os.path.getsize, "By Size", top**3 if top else None),
                  (get_crc_key, "By CRC ", top**2 if top else None),
                  (get_hash_key, "By Hash", None))
    
    for keyfunction, name, topcount in iterations:
        duplicates.clear()
        count = 0
        duplicate_count = 0
        for i, filepath in enumerate(files, start=1):
            key = keyfunction(filepath)
            duplicates.setdefault(key, []).append(filepath)
            if len(duplicates[key]) > 1:
                count += 1
                if len(duplicates[key]) == 2:
                    count += 1
                    duplicate_count += 1
                    
            print "\r(%s) %d Files checked, %d duplicates found (%d files)" % (name, i, duplicate_count, count),
        print ""
        sortedfiles = sorted(duplicates.itervalues(), key=len, reverse=True)
        files = [filepath for filepaths in sortedfiles[:topcount] if len(filepaths) > 1 for filepath in filepaths]

    return [filelist for filelist in duplicates.itervalues() if len(filelist) > 1]

def get_files(directory, include_hidden, include_empty):
    """Returns all FILES in the directory which apply to the filter rules."""
    return (os.path.join(dirpath, filename)
            for dirpath, _, filenames in os.walk(directory)
            for filename in filenames
                if not os.path.islink(os.path.join(dirpath, filename))
                and (include_hidden or
                     reduce(lambda r, d: r and not d.startswith("."), os.path.abspath(os.path.join(dirpath, filename)).split(os.sep), True))
                and (include_empty or os.path.getsize(os.path.join(dirpath, filename)) > 0))

if __name__ == "__main__":
    ARGS = parse_arguments()
    FILES = get_files(ARGS.directory, ARGS.include_hidden, ARGS.include_empty)
    DUPLICATES = filter_duplicate_files(FILES, ARGS.top if ARGS.fast else None)
    print_duplicates(DUPLICATES, ARGS.top)
