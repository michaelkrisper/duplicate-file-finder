# -*- coding: UTF-8 -*-
"""
Module for traversing a directory structure and finding duplicate files.
"""

import sys
import os
import hashlib
import argparse

def get_hash(chunk_size, filepath):
    """ Calculates the hash of a file. """
    hash_object = hashlib.sha1()
    with open(filepath, 'rb') as f_input:
    # todo: better performance idea: hash in chunks of 1024, and only hash more if a duplicate was found.
    # todo: better performance idea: first only check filesize, and only hash if size is the same.
    # todo: make the chunk_size configureable!
        for chunk in iter(lambda:f_input.read(chunk_size), ""):
            hash_object.update(chunk)
    
    digest = hash_object.digest()
    return digest

def find_all_duplicates(directory, chunk_size=1024 * 100, verbose=False):
    """ Finds alle duplicate files in the directory. """
    file_counter = 0
    for dirpath, _, files in os.walk(directory):
        # exclude "hidden" directories (dirs with . prefix, e.g. ~/.ssh)
        # todo: make that configureable!
        if "/." not in dirpath:
            file_counter = file_counter + len(files)
            print "Counting files ... %d\r" % file_counter,
    print ""
    
    hashes = {}    
    file_counter = 0
    dupe_count = 0
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            # exclude "hidden" directories (dirs with . prefix, e.g. ~/.ssh)
            # todo: make that configureable!
            if "/." not in dirpath:
                filepath = os.path.join(dirpath, filename)
                if verbose: print "Checking file: %s" % filepath
                digest = get_hash(chunk_size, filepath)
                if not hashes.has_key(digest):
                    hashes[digest] = [filepath]
                else:
                    if len(hashes[digest]) == 1:
                        dupe_count += 1
                        if verbose: print "File was a duplicate."
                    hashes[digest].append(filepath)
                file_counter += 1
                print "Files checked: %d - Duplicates found: %d\r" % (file_counter, dupe_count),
                sys.stdout.flush()
            else:
                if verbose: print "Jumped over hidden directory: %s" % dirpath  
    return [filelist for filelist in hashes.values() if len(filelist) > 1]

def main():
    """ The main method """
    args = parseArguments()
    dupes = find_all_duplicates(directory=args.directory, verbose=args.verbose, chunk_size=args.chunksize)
    
    if (len(dupes) and args.top) > 0:
        print "\n\nDisplaying Top %d of most duplicated files:" % args.top
        for pos, paths in enumerate(sorted(dupes, key=len, reverse=True)[:args.top + 1], start=1):
            prefix = os.path.dirname(os.path.commonprefix(paths))
            print "\n(%d) Found %d duplicate files (size: %d Bytes) in %s/:" % (pos,
                                                                                len(paths),
                                                                                os.path.getsize(paths[0]),
                                                                                prefix)
            for i, path in enumerate(paths, start=1):
                print "\t%d: %s" % (i, path[len(prefix) + 1:])
            
    print "\nFound %d duplicates (%d duplicate files in total)" % (len(dupes),
                                                                   reduce(lambda sumValue, files: sumValue + len(files), dupes, 0))

def parseArguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(dest="directory", help="the directory which should be checked for duplicate files.")
    parser.add_argument("-v", dest="verbose", action="store_true", help="display verbose output.")
    parser.add_argument("-c", dest="chunksize", action="store_const", type=int, help="set the default chunk size in bytes for reading files", default=1024)
    parser.add_argument("-a", dest="top", action="store_const", type=int, help="display all duplicate files. equal to -top 0", const=0)
    parser.add_argument("-top", dest="top", action="store_const", type=int, help="set the amount of displayed duplicates. default: -top 10", default=10)
    return parser.parse_args()

if __name__ == "__main__":
    #todo: write unit test!
    #todo: document functions
    #todo: add better argument check (ArgumentParser)
    #todo: add -h, --help command
    #todo: add -v, --verbose for verbose mode (output all scanned files; when a duplicate was found; hashDigests too?)
    #todo: add -s, --size for manual chunksize setting
    #todo: add -a, --all for display of all duplicate files, not only the top10
    
    main()