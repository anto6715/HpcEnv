#!/usr/bin/env python

import os
import re
import xarray as xr
import numpy as np
from collections.abc import Sequence

OK_MESSAGE = "OK"
FAIL_MESSAGE = "FAIL"
DEFAULT_MAXDEPTH = 1  # negative value remove the limit on
DEBUG_ACTIVE = False
DEFAULT_FILENAME = ".nc"
DTYPE_NOT_CHECKED = ["S8", "S1", "O"]  # S8|S1:char, O: string


def get_args(raw_args=None):
    import argparse

    parse = argparse.ArgumentParser(description="netCDF Comparison Tool")
    # General args
    parse.add_argument('folder1', type=str, help="Path of first folder to compare")
    parse.add_argument('folder2', type=str, help="Path of second folder to compare")
    parse.add_argument('--name', type=str, default=DEFAULT_FILENAME,
                       help="Name of the files to compare."
                            "It can be a sub-set of the complete name or a regex expression")
    parse.add_argument('--maxdepth', type=int, default=DEFAULT_MAXDEPTH,
                       help="Descend at most levels levels of directories below the "
                            "starting-points. If set to -1 it scan all the subdirectories")
    parse.add_argument('--common_pattern', type=str, default=None,
                       help="Common file pattern in two files to compare. "
                            "Es mfsX_date.nc and expX_date.nc -> date.nc is the common part")
    parse.add_argument('--variables', nargs='+', help="Variable to compare")

    return parse.parse_args(raw_args)


def all_match_are_satisfied(matching_strings: tuple, file2: str):
    if len(matching_strings) == 0:
        raise ValueError("Matching string list is empty")
    for match in matching_strings:
        if match not in file2:
            return False
        else:
            debug(f"Found {match} in {file2}")

    return True


def debug(input_str):
    if DEBUG_ACTIVE:
        print(input_str)


def get_match(pattern, string):
    if pattern[0] != "(" or pattern[-1] != ")":
        pattern = f"({pattern})"  # force to use group refex as search
    match_object = re.search(pattern, string)
    if match_object is not None:
        return match_object.groups()
    else:
        return None


def get_file_list_to_compare_with_match(sequence1: Sequence, sequence2, match_pattern: str):
    """
    Given a regex match pattern, it finds a fileX in sequence1 that match the regex expression,
        then try to find in sequence2 a fileY that match the regex pattern with the same value of fileX.
        Example:
            match_pattern = \d{7}_\d{8}
            fileX = MO_PR_PF_*3901977_20221201*_p01_20221201_20221201.nc
            fileY = GL_LATEST_PR_PF_*3901977_20221201*.nc
        Between ** character has been highlighted the pattern that match with regex match_patten
    Args:
        sequence1: An iterable where find the files that match with match_pattern
        sequence2: An iterable where find the files that match match_pattern with the same values of the files
            from sequence1
        match_pattern: A regex expression

    Returns: A list of tuple. Each tuple contains two files that have the same value in correspondence of match_pattern
    """
    match_list = list()
    for file in sequence1:
        matching_strings = get_match(match_pattern, file)
        if matching_strings:
            match_found = False
            for file2 in sequence2:
                filename2 = os.path.basename(file2)
                if all_match_are_satisfied(matching_strings, filename2):
                    match_found = True
                    debug(f"Found two files that match")
                    debug(f"\t- {file}")
                    debug(f"\t- {file2}")
                    match_list.append((file, file2))
            if not match_found:
                debug(f"FAIL File to compare with {file} NOT FOUND")
        else:
            debug(f"The file {file} doesn't match with {match_pattern}")

    return match_list


def walklevel(input_dir, level=1):
    """Generator function, usage: for root, dirs, files in walklevel: # do something"""
    input_dir = input_dir.rstrip(os.path.sep)
    assert os.path.isdir(input_dir)
    num_sep = input_dir.count(os.path.sep)
    max_depth_level = num_sep + level - 1  # -1 used to have the same behavior of find bash command
    for root, dirs, files in os.walk(input_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        # level < 0 is a special case used to explore all the subdirs
        if num_sep_this >= max_depth_level and level > 0:
            del dirs[:]


def get_file_list_to_compare(nc_file_list1: list, nc_file_list2: list):
    file_list_to_compare = list()
    for file1 in nc_file_list1:
        filename1 = os.path.basename(file1)
        match_file2 = [file2 for file2 in nc_file_list2 if filename1 in file2]
        if len(match_file2) == 0:
            debug(f"FAIL File to compare with {file1} NOT FOUND")
        else:
            file_list_to_compare += [(file1, file2) for file2 in match_file2]

    return file_list_to_compare


def compare_datasets(file1, file2, variables_to_compare: list):
    debug("Compare:")
    debug(f"\t- {file1}")
    debug(f"\t- {file2}")
    with xr.open_dataset(file1, decode_cf=False) as dataset1:
        with xr.open_dataset(file2, decode_cf=False) as dataset2:

            # keep only float vars
            if variables_to_compare is None or len(variables_to_compare) == 0:
                vars_list = []
                extract_vars(dataset1, vars_list)
            else:
                vars_list = variables_to_compare
            debug(f"Var to check: {vars_list}")
            # iterate over vars
            for var in vars_list:
                debug(f"Checking {var}")
                if var not in dataset1.data_vars and var not in dataset1.dims:
                    print(f"FAIL {var} not found in {file1}")
                    continue
                else:
                    field1 = dataset1[var].to_masked_array()
                if var not in dataset2.data_vars and var not in dataset2.dims:
                    print(f"FAIL {var} not found in {file2}")
                    continue
                else:
                    field2 = dataset2[var].to_masked_array()
                if field1.shape == field2.shape:
                    try:
                        difference_field = field1 - field2
                    except np.core._exceptions.UFuncTypeError:
                        print(
                            f"FAIL Can't compare {var} in {file1} and in {file2} with different types")
                        continue
                else:
                    print(
                        f"FAIL Can't compare {var} in {file1} and in {file2} with shapes {field1.shape} {field2.shape}")
                    continue
                max_difference = difference_field.max()
                min_difference = difference_field.min()
                mask_is_equal = np.array_equal(field1.mask, field2.mask)

                if min_difference == 0 and max_difference == 0 and mask_is_equal:
                    result = OK_MESSAGE
                else:
                    result = FAIL_MESSAGE

                print(result, min_difference, max_difference, mask_is_equal, file1, var, file2, var)


def extract_vars(dataset: xr.Dataset, vars_list):
    for var_name in dataset.data_vars:
        var_dtype = dataset[var_name].dtype
        debug(f"Variable: {var_name}, dtype: {var_dtype}")
        if var_dtype not in DTYPE_NOT_CHECKED:
            vars_list.append(var_name)
    for var_name in dataset.dims:
        var_dtype = dataset[var_name].dtype
        debug(f"Variable: {var_name}, dtype: {var_dtype}")
        if var_dtype not in DTYPE_NOT_CHECKED:
            vars_list.append(var_name)


def main(raw_args=None):
    args = get_args(raw_args)
    folder1 = args.folder1
    folder2 = args.folder2
    filter_name = args.name
    common_pattern = args.common_pattern
    maxdepth = args.maxdepth
    variables_to_compare: list = args.variables

    nc_file_list1 = [os.path.join(root, f)
                     for root, dirs, files in walklevel(folder1, maxdepth)
                     for f in files
                     if get_match(filter_name, os.path.join(root, f))]
    nc_file_list2 = [os.path.join(root, f)
                     for root, dirs, files in walklevel(folder2, maxdepth)
                     for f in files
                     if get_match(filter_name, os.path.join(root, f))]

    if common_pattern is None:
        files_to_compare = get_file_list_to_compare(nc_file_list1, nc_file_list2)
    else:
        files_to_compare = get_file_list_to_compare_with_match(nc_file_list1, nc_file_list2, common_pattern)

    for file1, file2 in files_to_compare:
        compare_datasets(file1, file2, variables_to_compare)


if __name__ == "__main__":
    main()
