#!/usr/bin/env python

# Source - https://stackoverflow.com/a/66065430
# Posted by dmmfll
# Retrieved 2026-03-17, License - CC BY-SA 4.0

"""Parameters
----------
passphrase : str
    Password to hash.  If unspecified, the user is asked to input
    and verify a password.
algorithm : str
    Hashing algorithm to use (e.g, 'sha1' or any argument supported
    by :func:`hashlib.new`, or 'argon2').

Returns
-------
hashed_passphrase : str
    Hashed password, in the format 'hash_algorithm:salt:passphrase_hash'."""

import getpass

from jupyter_server.auth import passwd

my_password = getpass.getpass()

hashed_password = passwd(passphrase=my_password, algorithm="argon2")

print(hashed_password)
