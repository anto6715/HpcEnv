#!/usr/bin/env python

import click


@click.group('test')
def main():
    pass


@main.command()
@click.argument('myy_arg')
def cmd1():
    pass


if __name__ == '__main__':
    main()
