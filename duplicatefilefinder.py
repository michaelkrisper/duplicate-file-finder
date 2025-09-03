#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Module for traversing a directory structure, finding duplicate FILES and displaying them, but does NOT delete them."""

import os
import argparse
import hashlib
import zlib
import UpdatePrinter

__author__ = "Michael Krisper"
__copyright__ = "Copyright 2012, Michael Krisper"
__credits__ = ["Michael Krisper"]
__license__ = "GPL"
__version__ = "1.3.1"
__maintainer__ = "Michael Krisper"
__email__ = "michael.krisper@gmail.com"
__status__ = "Production"
__python_version__ = "2.7.3"

def parse_arguments():
    """ Parses the Arguments """

    epilog = """EXAMPLES:
    (1) %(prog)s ~/Downloads
        Description: Searches the Downloads directory for duplicate files and displays the top 3 duplicates (with the most files).

    (2) %(prog)s ~/Downloads -top 3
        Description: Searches duplicates, but only displays the top 3 most duplicates

    (3) %(prog)s ~/Downloads -top 3 --fast 
        Description: Searches for the top 3 duplicates. May eventually get less than 3 results, even if they would exist.

    (4) %(prog)s ~/Downloads -a
        Description: Searches duplicates and displays ALL results

    (5) %(prog)s ~/Downloads --hidden --empty
        Description: Searches duplicates and also include hidden or empty files
    """

    parser = argparse.ArgumentParser(description=__doc__, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(dest="directory", help="the directory which should be checked for duplicate files")
    parser.add_argument("-fast", dest="fast", action="store_true", 
                        help="Searches very fast for only for the top X duplicates. The fast check may return less than the \
                        top X, even if they would exist. Remarks: the fast option is useless when -a is given.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-a", dest="show_all", action="store_true", help="display all duplicate files. equal to -top 0")
    group.add_argument("-top", dest="top", action="store", metavar="X", default=3, type=int,  
                       help="set the amount of displayed duplicates. If 0 is given, all results will be displayed. default=10")
    parser.add_argument("--hidden", dest="include_hidden", action="store_true", help="check hidden files and hidden directories too")
    parser.add_argument("--empty", dest="include_empty", action="store_true", help="check empty files too")
    group.add_argument("--min-file-size", dest="min_file_size", action="store", default=1, type=int,
                       help="set the file filter so that file must be at least min-file-size to be examined, defaults to 1")
    args = parser.parse_args()
    if args.show_all or args.top == 0:
        args.top = None

    return args

def print_duplicates(files, displaycount=None):
    """Prints a list of duplicates."""
    sortedfiles = sorted(files, key=lambda x: (len(x[1]), os.path.getsize(x[1][0])), reverse=True)
    for pos, entry in enumerate(sortedfiles[:displaycount], start=1):
        checksum, paths = entry
        checksum = checksum.encode('hex')
        prefix = os.path.dirname(os.path.commonprefix(paths))
        print "\n(%d) Found %d duplicate files (size: %d Bytes, sha256 %r) in %s/:" % \
            (pos, len(paths), os.path.getsize(paths[0]), checksum, prefix)
        for i, path in enumerate(sorted(paths), start=1):
            print "%2d: %s" % (i, path[len(prefix) + 1:])

def get_hash_key(filename):
    """Calculates the hash value for a file."""
    hash_object = hashlib.sha256()
    with open(filename, 'rb') as inputfile:
        for chunk in iter(lambda:inputfile.read(1024 * 8), ""):
            hash_object.update(chunk)
    return hash_object.digest()

def get_crc_key(filename):
    """Calculates the crc value for a file."""
    with open(filename, 'rb') as inputfile:
        chunk = inputfile.read(1024)
    return zlib.adler32(chunk)

def filter_duplicate_files(files, top=None):
    """Finds all duplicate files in the directory."""
    duplicates = {}
    update = UpdatePrinter.UpdatePrinter().update
    iterations = ((os.path.getsize, "By Size", top**2 if top else None),  # top * top <-- this could be performance optimized further by top*3 or top*4
                  (get_crc_key, "By CRC ", top*2 if top else None),       # top * 2
                  (get_hash_key, "By Hash", None))
    
    for keyfunction, name, topcount in iterations:
        duplicates.clear()
        count = 0
        duplicate_count = 0
        i = 0
        for i, filepath in enumerate(files, start=1):
            key = keyfunction(filepath)
            duplicates.setdefault(key, []).append(filepath)
            if len(duplicates[key]) > 1:
                count += 1
                if len(duplicates[key]) == 2:
                    count += 1
                    duplicate_count += 1

            update("\r(%s) %d Files checked, %d duplicates found (%d files)" % (name, i, duplicate_count, count))
        else:
            update("\r(%s) %d Files checked, %d duplicates found (%d files)" % (name, i, duplicate_count, count), force=True)
        print ""
        sortedfiles = sorted(duplicates.itervalues(), key=len, reverse=True)
        files = [filepath for filepaths in sortedfiles[:topcount] if len(filepaths) > 1 for filepath in filepaths]    

    return [(checksum, duplicates[checksum]) for checksum in duplicates if len(duplicates[checksum]) > 1]

def get_files(directory, include_hidden, min_file_size=1):
    """Returns all FILES in the directory which apply to the filter rules."""
    return (os.path.join(dirpath, filename)
            for dirpath, _, filenames in os.walk(directory)
            for filename in filenames
                if not os.path.islink(os.path.join(dirpath, filename))
                and (include_hidden or
                     reduce(lambda r, d: r and not d.startswith("."), os.path.abspath(os.path.join(dirpath, filename)).split(os.sep), True))
                and (os.path.getsize(os.path.join(dirpath, filename)) >= min_file_size))

if __name__ == "__main__":
    ARGS = parse_arguments()
    FILES = get_files(ARGS.directory, ARGS.include_hidden, ARGS.include_empty)
    if ARGS.include_empty:
        ARGS.min_file_size = 0
    FILES = get_files(ARGS.directory, ARGS.include_hidden, ARGS.min_file_size)
    DUPLICATES = filter_duplicate_files(FILES, ARGS.top if ARGS.fast else None)
    print_duplicates(DUPLICATES, ARGS.top)
    
    if ARGS.fast:
        print "\nFound %d duplicates at least (%d duplicate files total) -- More duplicates may exist." % \
            (len(DUPLICATES), reduce(lambda sumValue, files: sumValue + len(files), DUPLICATES, 0))
    else:
        print "\nFound %d duplicates (%d duplicate files total)" % \
            (len(DUPLICATES), reduce(lambda sumValue, files: sumValue + len(files), DUPLICATES, 0))
