#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Module for traversing a directory structure, finding duplicate files and displaying them, but does NOT delete them."""

import os
import argparse
import md5
import sys

__author__ = "Michael Krisper"
__copyright__ = "Copyright 2012, Michael Krisper"
__credits__ = ["Michael Krisper"]
__license__ = "GPL"
__version__ = "1.1.0"
__maintainer__ = "Michael Krisper"
__email__ = "michael.krisper@gmail.com"
__status__ = "Production"

def parse_arguments():
    """ Parses the Arguments """
    
    epilog = """EXAMPLES:
    (1) %(prog)s ~/Downloads
        Description: Searches the Downloads directory for duplicate files and displays the top 10.

    (2) %(prog)s ~/Downloads -top 3
        Description: Searches duplicates, but only displays the top 3 most duplicates

    (3) %(prog)s ~/Downloads -a
        Description: Searches duplicates and displays ALL results

    (4) %(prog)s ~/Downloads --hidden --empty
        Description: Searches duplicates and also include hidden or empty files"""
    
    parser = argparse.ArgumentParser(description=__doc__, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument(dest="directory",
                        help="the directory which should be checked for duplicate files")

    group = parser.add_mutually_exclusive_group()
    
    group.add_argument("-a", dest="show_all", action="store_true",
                       help="display all duplicate files. equal to -top 0")
    
    group.add_argument("-top", dest="top", action="store", metavar="COUNT", type=int, default=10,
                       help="set the amount of displayed duplicates. If 0 is given, all results will be displayed. default=10")

    parser.add_argument("--hidden", dest="include_hidden", action="store_true",
                        help="check hidden files and directories too")
    
    parser.add_argument("--empty", dest="include_empty", action="store_true",
                        help="check empty files too")
    
    return parser.parse_args()

def main():
    """The main method"""
    args = parse_arguments()
    
    print "Preparing for search ... ",
    sys.stdout.flush()
    files = get_files(args.directory, args.include_hidden, args.include_empty)

    duplicate_list = filter_duplicate_files(files)
    
    if args.show_all or args.top == 0:
        args.top = None
    
    print_duplicates(duplicate_list, args.top)

def get_files(directory, include_hidden, include_empty):
    """Returns all files in the directory, which apply to the filter rules."""
    return (os.path.join(dirpath, filename) 
             for dirpath, _, filenames in os.walk(directory) 
             for filename in filenames
                if not os.path.islink(os.path.join(dirpath, filename))
                and (include_hidden or 
                     reduce(lambda r, d: r and not d.startswith("."), os.path.join(dirpath, filename).split(os.sep)[1:], True))
                and (include_empty or os.path.getsize(os.path.join(dirpath, filename)) > 0))

def filter_duplicate_files(files):
    """Finds all duplicate files in the directory."""
    filelist = ((filepath, generate_fileid(filepath), 0) for filepath in files)

    total_amount = 0
    counted = False

    files_checked = 0

    duplicates = {}
    while True:
        file_groups = {}
        for filepath, idgenerator, digest in filelist:
            files_checked += 1
            if not counted:
                total_amount += 1
            try:
                digest = idgenerator.next()
                file_groups.setdefault(digest, []).append((filepath, idgenerator, digest))
                if len(file_groups[digest]) > 1:
                    files_checked -= 1
                    if len(file_groups[digest]) == 2:
                        files_checked -= 1
            except StopIteration:
                duplicates.setdefault(digest, []).append(filepath)

            print "\rChecked %d / %d files" % (files_checked, total_amount),

        if len(file_groups) == 0:
            break
        counted = True
        filelist = (entry for files in file_groups.itervalues() if len(files) > 1 for entry in files)

    return duplicates.values()

def generate_fileid(filename, chunk_size=1024 * 8):
    """Generates an id for a file until the file is complete read."""
    yield os.path.getsize(filename)

    hash_object = md5.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda:f.read(chunk_size), ""):
            hash_object.update(chunk)
    yield hash_object.digest()

def print_duplicates(files, displaycount):
    for pos, paths in enumerate(sorted(files, key=len, reverse=True)[:displaycount], start=1):
        prefix = os.path.dirname(os.path.commonprefix(paths))
        print "\n(%d) Found %d duplicate files (size: %d Bytes) in %s/:" % \
            (pos, len(paths), os.path.getsize(paths[0]), prefix)
        for i, path in enumerate(sorted(paths), start=1):
            print "%2d: %s" % (i, path[len(prefix) + 1:])
            
    print "\nFound %d duplicates (%d duplicate files total)" % \
        (len(files), reduce(lambda sumValue, files: sumValue + len(files), files, 0))

if __name__ == "__main__":
    main()
