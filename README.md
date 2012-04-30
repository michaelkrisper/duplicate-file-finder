# duplicate-file-finder
This is a python script to find duplicate files in a directory structure. For optimal performance, files are checked in 3 iterations:
1. Group by file size
2. Group by adler32-CRC of the first 1024 Bytes
3. Group by md5-hash

After the whole directory structure is searched, duplicate files are displayed. With the default settings the top 10 duplicate values (those with the most duplicate files) are displayed.

## Usage:
	usage: duplicatefilefinder.py directory [-h] [-fast] [-a | -top X] [--hidden] [--empty]
	
	positional arguments:
	  directory   the directory which should be checked for duplicate FILES
	
	optional arguments:
	  -h, --help  show this help message and exit
	  -fast       Searches very fast for only for the top X duplicates. The fast
	              check may return less than the top X, even if they would exist.
	              Remarks: the -fast option is useless when -a is given.
	  -a          display all duplicate FILES. equal to -top 0
	  -top X      set the amount of displayed duplicates. If 0 is given, all
	              results will be displayed. default=10
	  --hidden    check hidden FILES and directories too
	  --empty     check empty FILES too

##EXAMPLES:
    (1) duplicatefilefinder.py ~/Downloads
        Description: Searches the Downloads directory for duplicate FILES and displays the top 3 duplicates (with the most files).
	
    (2) duplicatefilefinder.py ~/Downloads -top 3
        Description: Searches duplicates, but only displays the top 3 most duplicates
	
    (3) duplicatefilefinder.py ~/Downloads -top 3 --fast 
        Description: Searches for the top 3 duplicates. May eventually get less than 3 results, even if they would exist.
	
    (4) duplicatefilefinder.py ~/Downloads -a
        Description: Searches duplicates and displays ALL results
	
    (5) duplicatefilefinder.py ~/Downloads --hidden --empty
        Description: Searches duplicates and also include hidden or empty FILES
	
##Sample Output:
	duplicatefilefinder.py . -fast --empty
	(By Size) 24 Files checked, 1 duplicates found (2 files) 
	(By CRC ) 2 Files checked, 1 duplicates found (2 files)  
	(By Hash) 2 Files checked, 1 duplicates found (2 files) 
	
	(1) Found 2 duplicate files (size: 16 Bytes) in ./test/:
	 1: copy of testfile
	 2: testfile
	
	Found 1 duplicates at least (2 duplicate files total) -- More duplicates may exist.

