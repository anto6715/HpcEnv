#!/usr/bin/env python


if __name__ == "__main__":
    import sys
    import glob
    import os
    
    input_dir = sys.argv[1]
    old_pattern = sys.argv[2]
    new_pattern = sys.argv[3]
    
    input_files = glob.glob(input_dir + '/*.nc')
    for file in input_files:
        old_filename = os.path.basename(file)
        new_filename = old_filename.replace(old_pattern, new_pattern)
        new_file = input_dir + '/' + new_filename
        os.rename(file, new_file)
