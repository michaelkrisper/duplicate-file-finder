#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Module for traversing a directory structure, finding duplicate FILES and displaying them, but does NOT delete them."""

import os
import sys
import argparse
import hashlib
import zlib
from functools import reduce
import UpdatePrinter



def print_duplicates(files, displaycount=None):
    """Prints a list of duplicates."""
    sortedfiles = sorted(files, key=lambda x: (len(x), os.path.getsize(x[0])), reverse=True)
    for pos, paths in enumerate(sortedfiles[:displaycount], start=1):
        prefix = os.path.dirname(os.path.commonprefix(paths))
        print("\n(%d) Found %d duplicate files (size: %d Bytes) in %s/:" % \
            (pos, len(paths), os.path.getsize(paths[0]), prefix))
        for i, path in enumerate(sorted(paths), start=1):
            print("%2d: %s" % (i, path[len(prefix) + 1:]))

def get_hash_key(filename):
    """Calculates the hash value for a file."""
    hash_object = hashlib.sha256()
    i = 0
    with open(filename, 'rb') as inputfile:
        for chunk in iter(lambda:inputfile.read(1024 * 8), b''):
            i+=1
            #print(sys.getsizeof(chunk)) 
            print(i)
            #hash_object.update(chunk)
    print(i)
    return hash_object.digest()

def get_crc_key(filename):
    """Calculates the crc value for a file."""
    with open(filename, 'rb') as inputfile:
        chunk = inputfile.read(1024)
    return zlib.adler32(chunk)
'''
def filter_duplicate_files(files, top=None):
    """Finds all duplicate files in the directory."""
    duplicates = {}
    update = UpdatePrinter.UpdatePrinter().update
    iterations = ((os.path.getsize, "By Size", top**2 if top else None),  # top * top <-- this could be performance optimized further by top*3 or top*4
                  (get_crc_key, "By CRC ", top*2 if top else None))       # top * 2
                  #(get_hash_key, "By Hash", None))
    
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
        print("")
        sortedfiles = sorted(duplicates.values(), key=len, reverse=True)
        files = [filepath for filepaths in sortedfiles[:topcount] if len(filepaths) > 1 for filepath in filepaths]    

    return [filelist for filelist in duplicates.values() if len(filelist) > 1]
'''

def get_files(directory, include_hidden, include_empty):
    """Returns all FILES in the directory which apply to the filter rules."""
    return (os.path.join(dirpath, filename)
            for dirpath, _, filenames in os.walk(directory)
            for filename in filenames
                if not os.path.islink(os.path.join(dirpath, filename))
                and filename.endswith('.pdf')   
                and (include_hidden or
                     reduce(lambda r, d: r and not d.startswith("."), os.path.abspath(os.path.join(dirpath, filename)).split(os.sep), True))
                and (include_empty or os.path.getsize(os.path.join(dirpath, filename)) > 0))

if __name__ == "__main__":
    file = sys.argv[1]
    key = get_hash_key(file)

