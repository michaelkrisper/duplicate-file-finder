# -*- coding: UTF-8 -*-
"""Module for traversing a directory structure, finding duplicate files and displaying them, but does NOT delete them."""

import sys
import os
import hashlib
import argparse

def parse_arguments():
    """ Parses the Arguments """
    epilog = """EXAMPLES:
    (1) %(prog)s ~/Downloads
        Description: Searches the Download directory for duplicate files

    (2) %(prog)s ~/Downloads -top 3
        Description: Searches duplicates, but only displays the top 3 most duplicates

    (3) %(prog)s ~/Downloads -a
        Description: Searches duplicates and displays ALL results

    (4) %(prog)s ~/Downloads -v -a
        Description: Searches duplicates, displays ALL results and displays all files checked

    (5) %(prog)s ~/Downloads -c 512
        Description: Searches duplicates, reads files with the a chunksize 512 bytes"""
    
    parser = argparse.ArgumentParser(description=__doc__, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument(dest="directory", help="the directory which should be checked for duplicate files")
    parser.add_argument("-v", dest="verbose", action="store_true", help="display verbose output")
    parser.add_argument("-c", dest="chunksize", action="store", type=int, help="set the default chunk size in bytes for reading files", default=1024*10)
    parser.add_argument("--hidden", dest="check_hidden", action="store_true", help="check hidden files and directories too")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-a", dest="show_all", action="store_true", help="display all duplicate files. equal to -top 0")
    group.add_argument("-top", dest="top", action="store", type=int, help="set the amount of displayed duplicates. If 0 is given, all results will be displayed. default=10", default=10)
    
    return parser.parse_args()


def main():
    """ The main method """
    args = parse_arguments()
    dupes = get_duplicate_files_by_filesize(directory=args.directory, check_hidden=args.check_hidden, verbose=args.verbose)
    dupes = get_duplicate_files_by_hash(dupes, chunk_size=args.chunksize, verbose=args.verbose)
    
    if args.show_all or args.top == 0:
        args.top = len(dupes)
    
    if len(dupes) > 0:
        print "\n\nDisplaying Top %d of most duplicated files:" % args.top
        for pos, paths in enumerate(sorted(dupes, key=len, reverse=True)[:args.top], start=1):
            prefix = os.path.dirname(os.path.commonprefix(paths))
            print "\n(%d) Found %d duplicate files (size: %d Bytes) in %s/:" % \
                (pos, len(paths), os.path.getsize(paths[0]), prefix)
            for i, path in enumerate(sorted(paths), start=1):
                print "\t%d: %s" % (i, path[len(prefix) + 1:])
    else:
        print "\n\nNo duplicate files to display."
            
    print "\nFound %d duplicates (%d duplicate files)" % \
        (len(dupes), reduce(lambda sumValue, files: sumValue + len(files), dupes, 0))


def get_duplicate_files_by_filesize(directory, check_hidden, verbose):
    """Searches duplicate files by filesize only."""
    files_dict = {}
    file_counter = 0
    for dirpath, _, filenames in os.walk(directory):
        # exclude "hidden" directories (dirs with . prefix, e.g. ~/.ssh)
        # todo: make that configureable!
        for file_name in filenames:
            path = os.path.join(dirpath, file_name)
            if os.path.islink(path) or check_hidden or "/." not in dirpath:
                if verbose:
                    print "Jumped over hidden directory/file:", path
                continue
            
            if verbose:
                print "Checking file:", path
            size = os.path.getsize(path)
            if files_dict.has_key(size):
                files_dict[size].append(path)
                if verbose:
                    print "Found duplicate file size."
            else:
                files_dict[size] = [path]
            file_counter += 1
            print "Counting files ... %d\r" % file_counter,
                
    dupes = [files for files in files_dict.values() if len(files) > 1]
    print "\nFound %d duplicates by files size (%d duplicate files)" % \
        (len(dupes), reduce(lambda sumValue, files: sumValue + len(files), dupes, 0))
    return dupes


def get_duplicate_files_by_hash(duplicate_files, chunk_size, verbose):
    """ Finds all duplicate files in the directory. """
    
    hashes = {}
    file_counter = 0
    dupe_count = 0
    for filenames in duplicate_files:
        for filepath in filenames:
            if verbose:
                print "Checking file: %s" % filepath
            digest = get_hash_for_file(filepath, chunk_size)
            if not hashes.has_key(digest):
                hashes[digest] = [filepath]
            else:
                if len(hashes[digest]) == 1:
                    dupe_count += 1
                    if verbose:
                        print "File was a duplicate."
                hashes[digest].append(filepath)
            file_counter += 1
            print "Files checked: %d - Duplicates found: %d\r" % (file_counter, dupe_count),
            sys.stdout.flush()
            
    return [filelist for filelist in hashes.values() if len(filelist) > 1]


def get_hash_for_file(filepath, chunk_size):
    """ Calculates the hash of a file. """
    # todo: better performance idea: hash in chunks of 1024, and only hash more if a duplicate was found.
    hash_object = hashlib.sha1()
    with open(filepath, 'rb') as f_input:
        for chunk in iter(lambda:f_input.read(chunk_size), ""):
            hash_object.update(chunk)
    digest = hash_object.digest()
    return digest
        

if __name__ == "__main__":
    #todo: write unit test!
    main()
