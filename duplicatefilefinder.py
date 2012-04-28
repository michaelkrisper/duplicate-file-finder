# -*- coding: UTF-8 -*-
"""Module for traversing a directory structure, finding duplicate files and displaying them, but does NOT delete them."""

import os
import argparse
import md5

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
    
    parser.add_argument(dest="directory", help="the directory which should be checked for duplicate files")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-a", dest="show_all", action="store_true", help="display all duplicate files. equal to -top 0")
    group.add_argument("-top", dest="top", action="store", type=int, help="set the amount of displayed duplicates. If 0 is given, all results will be displayed. default=10", default=10)

    parser.add_argument("--hidden", dest="include_hidden", action="store_true", help="check hidden files and directories too")
    parser.add_argument("--empty", dest="include_empty", action="store_true", help="check empty files too")
    
    return parser.parse_args()


def get_files(directory, include_hidden, include_empty):
    """Returns all files in the directory, which apply to the filter rules."""
    return [(os.path.join(dirpath, filename) 
             for dirpath, _, filenames in os.walk(directory) 
             for filename in filenames
                if not os.path.islink(os.path.join(dirpath, filename)) 
                and (include_hidden or not "/." in dirpath) 
                and (include_empty or os.path.getsize(os.path.join(dirpath, filename)) > 0))]

def main():
    """The main method"""
    args = parse_arguments()
    files = get_files(args.directory, args.include_hidden, args.include_empty)
    
    print "Filesizes compare:"
    files = filter_duplicate_files(files, os.path.getsize)
    
    print "\nQuick compare:"
    files = filter_duplicate_files(files, lambda filename: get_hash_for_file(filename, chunk_size=1024, partial=True))
    
    print "\nIntensive compare:"
    files = filter_duplicate_files(files, get_hash_for_file)
    
    if args.show_all or args.top == 0:
        args.top = None
    
    files = list(files)

    for pos, paths in enumerate(sorted(files, key=len, reverse=True)[:args.top], start=1):
        prefix = os.path.dirname(os.path.commonprefix(paths))
        print "\n(%d) Found %d duplicate files (size: %d Bytes) in %s/:" % \
            (pos, len(paths), os.path.getsize(paths[0]), prefix)
        for i, path in enumerate(sorted(paths), start=1):
            print "\t%d: %s" % (i, path[len(prefix) + 1:])
            
    print "\nFound %d duplicates (%d duplicate files total)" % \
        (len(files), reduce(lambda sumValue, files: sumValue + len(files), files, 0))

def filter_duplicate_files(files, hashFunction):
    """ Finds all duplicate files in the directory. """
    file_groups = {}
    file_counter = 0
    dupe_count = 0
    dupe_file_count = 0
    
    for fileList in files:
        for filepath in fileList:
            file_counter += 1
            digest = hashFunction(filepath)
            if not file_groups.has_key(digest):
                file_groups[digest] = [filepath]
            else:
                file_groups[digest].append(filepath)
                dupe_file_count += 1
                if len(file_groups[digest]) == 2:
                    dupe_count += 1
                    dupe_file_count += 1
            print "%d files checked - %d duplicates found (%d duplicate files)\r" % (file_counter, dupe_count, dupe_file_count),
    
    print ""
    return (sublist for sublist in file_groups.values() if len(sublist) > 1)

def get_hash_for_file(filename, chunk_size=1024 * 8, partial=False):
    """Calculates the hash of a file."""
    hash_object = md5.md5()
    with open(filename, 'rb') as f_input:
        for chunk in iter(lambda:f_input.read(chunk_size), ""):
            hash_object.update(chunk)
            if partial:
                return hash_object.digest()
    return hash_object.digest()

if __name__ == "__main__":
    main()
