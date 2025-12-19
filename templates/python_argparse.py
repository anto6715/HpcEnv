#!/usr/bin/env python

from typing import List
from argparse import Namespace


def get_args(raw_args=None) -> Namespace:
    import argparse

    parse = argparse.ArgumentParser(description="Restart cleaning")
    # General args
    parse.add_argument('arg', type=str, help="First arg")
    parse.add_argument('-d', '--ref_date', type=str, default='default', help="Default arg")

    return parse.parse_args(raw_args)


def main(raw_args: List['str']):
    args = get_args(raw_args)


if __name__ == '__main__':
    main()
