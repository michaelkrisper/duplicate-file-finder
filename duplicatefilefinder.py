# -*- coding: UTF-8 -*-
"""
Functions for traversing a directory structure and finding duplicate files.
This is done by hashing every single file and comparing the hashes.
"""

import sys
import os
import hashlib


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

def find_all_duplicates(path, chunk_size=1024 * 100):
    """ Finds alle duplicate files in the path. """
    file_counter = 0
    for dirpath, _, files in os.walk(path):
        # exclude "hidden" directories (dirs with . prefix, e.g. ~/.ssh)
        # todo: make that configureable!
        if "/." not in dirpath:
            file_counter = file_counter + len(files)
            print "Counting files ... %d\r" % file_counter,
    print ""
    
    hashes = {}    
    file_counter = 0
    dupe_count = 0
    for dirpath, _, filenames in os.walk(path):
        for filename in filenames:
            # exclude "hidden" directories (dirs with . prefix, e.g. ~/.ssh)
            # todo: make that configureable!
            if "/." not in dirpath:
                filepath = os.path.join(dirpath, filename)
                digest = get_hash(chunk_size, filepath)
                if not hashes.has_key(digest):
                    hashes[digest] = [filepath]
                else:
                    if len(hashes[digest]) == 1: 
                        dupe_count += 1
                    hashes[digest].append(filepath)
                file_counter += 1
                print "Files checked: %d - Duplicates found: %d\r" % (file_counter, dupe_count),
                sys.stdout.flush()
    return [filelist for filelist in hashes.values() if len(filelist) > 1]

def main(path):
    """ The main method """
    dupes = find_all_duplicates(path)
    
    # only show "dropbox" conflicted files            
    #conflicted_files = []
    #for paths in dupes:
    #    for path in paths:
    #        if "conflicted" in path.lower():
    #            conflicted_files.append(paths)
    #            break
    #dupes = conflicted_files
    
    if len(dupes) > 0:
        print "\n\nDisplaying Top 10 of most duplicated files:"
        for pos, paths in enumerate(sorted(dupes, key=len, reverse=True)[:10], start=1):
            prefix = os.path.dirname(os.path.commonprefix(paths))
            print "\n(%d) Found %d duplicate files (size: %d Bytes) in %s/:" % (pos,
                                                                                len(paths),
                                                                                os.path.getsize(paths[0]),
                                                                                prefix)
            for i, path in enumerate(paths, start=1):
                print "\t%d: %s" % (i, path[len(prefix) + 1:])
            
    print "\nFound %d duplicates (%d duplicate files in total)" % (len(dupes),
                                                                   reduce(lambda sumValue, files: sumValue + len(files), dupes, 0))



if __name__ == "__main__":
    if sys.argv[1:]:
        #todo: write unit test!
        #todo: document functions
        #todo: add better argument check (ArgumentParser)
        #todo: add -h, --help command
        #todo: add -v, --verbose for verbose mode (output all scanned files; when a duplicate was found; hashDigests too?)
        #todo: add -s, --size for manual chunksize setting
        #todo: add -a, --all for display of all duplicate files, not only the top10
        main(sys.argv[1])
        
    else:
        print "Searches for duplicate files and then shows the Top 10 of most duplicated files.\n"
        print "usage:  %s <directory>\n" % os.path.basename(sys.argv[0])
        print "Arguments:\n\t<directory>\t the directory which should be checked for duplicate files.\n"
        print "Example:\n\tduplicatefilefinder.py ~/Downloads\n"
