# -*- coding: UTF-8 -*-

import sys
import os
import hashlib

def findAllDuplicates(path, chunkSize=1024*20):
    fileCounter = 0
    for dirpath, _, files in os.walk(path):
        # exclude "hidden" directories (dirs with . prefix, e.g. ~/.ssh)
        # todo: make that configureable!
        if "/." not in dirpath:
            fileCounter = fileCounter + len(files)
            print "Counting files ... %d\r" % fileCounter,
    print ""
    
    hashes = {}    
    fileCounter = 0
    dupeCount = 0
    for dirpath, _, filenames in os.walk(path):
        for filename in filenames:
            # exclude "hidden" directories (dirs with . prefix, e.g. ~/.ssh)
            # todo: make that configureable!
            if "/." not in dirpath:
                filepath = os.path.join(dirpath, filename)
                hashObject = hashlib.sha1()
                with open(filepath, 'rb') as f:
                    # todo: check performance idea: hash in chunks of 1024, and only hash more if a duplicate was found.
                    # todo: make the chunkSize configureable!
                    hashObject.update(f.read(chunkSize))
                hashDigest = hashObject.digest()
                if not hashes.has_key(hashDigest):
                    hashes[hashDigest] = [filepath]
                else:
                    if len(hashes[hashDigest]) == 1:
                        dupeCount += 1
                    hashes[hashDigest].append(filepath)
                fileCounter += 1
                print "Files checked: %d - Duplicates found: %d\r" % (fileCounter, dupeCount),
    return [filelist for filelist in hashes.values() if len(filelist) > 1]

if sys.argv[1:]:
    dupes = findAllDuplicates(sys.argv[1])
            
    conflictedFiles = []
    for filePaths in dupes:
        for filePath in filePaths:
            if "conflicted" in filePath.lower():
                conflictedFiles.append(filePaths)
                break              
    dupes = conflictedFiles
    
    print "\n\nDisplaying Top 10 of most duplicated files:"
    for pos, filePaths in enumerate(sorted(dupes, key=lambda filePaths: len(filePaths), reverse=True), start=1):
        commonPrefix = os.path.dirname(os.path.commonprefix(filePaths))
        print "\n(%d) Found %d duplicate files (size: %d Bytes) in %s/:" % (pos, len(filePaths), os.path.getsize(filePaths[0]), commonPrefix)
        for i, filePath in enumerate(filePaths, start=1):
            print "\t%d: %s" % (i, filePath[len(commonPrefix)+1:])
            
    print "\nFound %d Duplicates (%d duplicate files in total)" % (len(dupes), reduce(lambda sumValue, files: sumValue + len(files), dupes, 0))
else:
    print "usage:  duplicate-file-finder.py <directory_path>"
