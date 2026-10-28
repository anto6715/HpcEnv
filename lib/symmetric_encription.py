#!/usr/bin/env python


import os
import base64

import click

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet


@click.group('main')
def main():
    pass


def derive_key_from_password(password: str, salt: bytes) -> bytes:
    # You can use PBKDF2HMAC or Scrypt for key derivation
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())
    return base64.urlsafe_b64encode(key)


def generate_salt():
    return os.urandom(16)


@main.command()
@click.argument('input_file')
@click.argument('output_file')
@click.argument('password')
def encrypt_file(input_file, output_file, password):
    salt = generate_salt()
    key = derive_key_from_password(password, salt)
    fernet = Fernet(key)

    with open(input_file, 'rb') as f_in:
        file_data = f_in.read()

    encrypted_data = fernet.encrypt(file_data)

    with open(output_file, 'wb') as f_out:
        f_out.write(salt)  # Save the salt at the beginning of the file
        f_out.write(encrypted_data)


@main.command()
@click.argument('input_file')
@click.argument('output_file')
@click.argument('password')
# Decrypt a file
def decrypt_file(input_file, output_file, password):
    with open(input_file, 'rb') as f_in:
        salt = f_in.read(16)  # Read the salt from the beginning of the file
        encrypted_data = f_in.read()

    key = derive_key_from_password(password, salt)
    fernet = Fernet(key)

    decrypted_data = fernet.decrypt(encrypted_data)

    with open(output_file, 'wb') as f_out:
        f_out.write(decrypted_data)


if __name__ == '__main__':
    main()
