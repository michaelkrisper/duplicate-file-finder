# duplicate-file-finder
This is a python script to find duplicate files in a directory structure. For optimal performance, files are checked in 3 iterations:

1. Group by file size
2. Group by sha256-hash of the first 1024 Bytes
3. Group by sha256-hash of the whole file

After the whole directory structure is searched, duplicate files are displayed.

## Usage:
	usage: duplicatefilefinder.py [-h] [-fast] [--delete] [--script-friendly]
	                              [-a] [-top X] [--hidden] [--empty]
	                              [--min-file-size MIN_FILE_SIZE]
	                              one-or-more-directories

	positional arguments:
	  directory             the directory which should be checked for duplicate
	                        files

	options:
	  -h, --help            show this help message and exit
	  -fast                 Enables a faster but less thorough search by pruning
	                        files between comparison stages. May result in fewer
	                        duplicates being found than actually exist. Ineffective
	                        when used with -a. Note: the default is doing a hash 
                            of the entire file.
	  --delete              delete older duplicate files
	  --script-friendly     use machine-readable output
	  -a                    display all duplicate files. equal to -top 0
	  -top X                set the amount of displayed duplicates. If 0 is given,
	                        all results will be displayed. default=3
	  --hidden              check hidden files and hidden directories too
	  --empty               check empty files too
	  --min-file-size MIN_FILE_SIZE
	                        set the file filter so that file must be at least min-
	                        file-size to be examined, defaults to 1

## EXAMPLES:
    (1) duplicatefilefinder.py ~/Downloads
        Description: Searches the Downloads directory for duplicate files and displays the top 3 duplicates (with the most files).
	
    (2) duplicatefilefinder.py ~/Downloads -top 3
        Description: Searches duplicates, but only displays the top 3 most duplicates
	
    (3) duplicatefilefinder.py ~/Downloads -top 3 --fast 
        Description: Searches for the top 3 duplicates. May eventually get less than 3 results, even if they would exist.
	
    (4) duplicatefilefinder.py ~/Downloads -a
        Description: Searches duplicates and displays ALL results
	
    (5) duplicatefilefinder.py ~/Downloads --hidden --empty
        Description: Searches duplicates and also include hidden or empty files

    (6) duplicatefilefinder.py ~/Downloads --delete
        Description: Searches duplicates and deletes the older files, keeping the newest one.

    (7) duplicatefilefinder.py ~/Downloads --script-friendly
        Description: Searches duplicates and prints them in a machine-readable format.

    (9) duplicatefilefinder.py ~/Downloads --min-file-size 1024
        Description: Searches duplicates but only considers files that are at least 1024 bytes in size.
	
## Sample Output:
	duplicatefilefinder.py . --empty
	(By Size) 24 Files checked, 1 duplicates found (2 files) 
	(By Partial Hash) 2 Files checked, 1 duplicates found (2 files)
	(By Full Hash) 2 Files checked, 1 duplicates found (2 files)
	
	(1) Found 2 duplicate files (size: 16 Bytes, sha256 'a1b2c3d4...') in ./test/:
	 1: copy of testfile
	 2: testfile
	
	Found 1 duplicates (2 duplicate files total)

