#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Script to search for all stack.env files in the backup folder recursively,
    encrypt them and store them in the database.
"""
import argparse
__author__ = "github.com/bearlike"

from utils import get_current_module_path
from tinydb import TinyDB, Query
from dotenv import load_dotenv
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import cryptography
from tqdm import tqdm
import base64
import os


load_dotenv()  # take environment variables from .env.

DB_PASSWORD = os.getenv("DB_PASSWORD", None)
DB_KEY = None

current_module_path = get_current_module_path()

# Initialize tinyDB
db = TinyDB(f'{current_module_path}/stack.encrypted.json')


def create_arg_parser():
    parser = argparse.ArgumentParser(
        description='Script to search for all stack.env files in the backup folder recursively, encrypt them and store them in the database.')

    parser.add_argument('--backup',
                        action='store_true',
                        default=True,
                        help='Back up all the files in the backup folder')

    parser.add_argument('--restore-all',
                        action='store_true',
                        help='Restore all files from the backup')

    parser.add_argument('--restore',
                        type=str,
                        help='Restore a single file from the backup. Requires a key as an argument.')

    parser.add_argument('--db-password',
                        type=str,
                        required=False,
                        help='Password for the database')
    return parser


def get_key_from_pass(password_provided=DB_PASSWORD) -> bytes:
    """Function to generate a key from the password
    Args:
        password_provided (str, optional): password to generate the key.
                                            Defaults to DB_PASSWORD.
    Returns:
        bytes: key generated from the password
    """
    # password must be a byte object to be used with this function
    password = password_provided.encode()
    salt = b'salt_compose_backup'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )

    key = base64.urlsafe_b64encode(kdf.derive(password))
    global DB_KEY
    # DB_KEY = key
    return key


def retrieve_all_backup_keys() -> list:
    """Function to retrieve all backup keys
    Returns:
        list: list of all backup keys
    """
    Backups = Query()
    dicts = db.search(Backups.date_id.matches("backups/*"))
    keys = [d["date_id"] for d in dicts]
    return keys


def store_encrypted(date_id, env_file):
    """Function to store the encrypted env file to the database
    Args:
        date_id (str): date_id of the backup
                        (eg: backups/2023/10/16/Hurricane/nextcloud/stack.env)
        env_file (str): env file content
    """
    all_keys = retrieve_all_backup_keys()
    # Create a cipher object and encrypt the env values
    cipher_suite = Fernet(get_key_from_pass())
    cipher_text = cipher_suite.encrypt(env_file.encode())
    if date_id in all_keys:
        # Remove the old entry
        db.remove(Query().date_id == date_id)
    # Store it in tinyDB
    db.insert({
        "date_id": date_id,
        "variables": cipher_text.decode()
    })


def retrieve_decrypted(date_id) -> str:
    """Function to retrieve the decrypted env file from the database
    Args:
        date_id (str): date_id of the backup
                        (eg: backups/2023/10/16/Hurricane/nextcloud/stack.env)
    Returns:
        str: decrypted env file content
    """
    # Query the DB for the key
    User = Query()
    encrypted_data = db.search(User.date_id == date_id)[0]["variables"]

    # Create a cipher object and decrypt the data
    cipher_suite = Fernet(get_key_from_pass())
    try:
        plain_text = cipher_suite.decrypt(encrypted_data.encode())
    except (
        cryptography.fernet.InvalidToken,
        cryptography.exceptions.InvalidSignature
    ):
        print("Invalid password. Please check the password and try again.")
        return False
    return plain_text.decode()


def search_stack_env_files() -> list:
    """ Function to search for all stack.env files in
        the backup folder recursively
    Returns:
        list: relative path of all stack.env files found
    """
    stack_env_files = []
    backup_path = f'{current_module_path}/backups'
    backup_path = os.path.abspath(backup_path)
    for root, dirs, files in os.walk(backup_path):
        for file in files:
            if file.endswith(".env"):
                path = os.path.join(root, file)[len(backup_path)+1:]
                # path = path.replace("\\", "/")
                stack_env_files.append(path)
    return sorted(list(set(stack_env_files)))


def filepath_to_str(filepath):
    """ Function to read the file content and return it as a string
    Args:
        filepath (str): path of the file
    Returns:
        str: file content
    """
    with open(filepath, 'r') as f:
        return f.read()


def backup():
    """ Function to perform the first time setup
    """
    # Backs up the all the stack.env file found
    keys = search_stack_env_files()
    print("Backing up the .env files:")
    for key in tqdm(keys):
        _path = f"backups/{key}"
        key = _path.replace("\\", "/")
        value = filepath_to_str(filepath=_path)
        store_encrypted(date_id=key, env_file=value)
        # remove file
        os.remove(_path)


def restore_one(key, write_to_file=True):
    """ Function to restore one stack.env file from the database
    Restores to the same path as the backup
    """
    path_list = key.split("/")
    path = os.path.join(*path_list)
    path = os.path.abspath(path)
    file_content = retrieve_decrypted(key)
    # Store file content to the path
    if write_to_file:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(file_content)
    else:
        print(file_content)


def restore_all():
    """ Function to restore all the stack.env files from the database
    Restores to the same path as the backup
    """
    Backups = Query()
    dicts = db.search(Backups.date_id.matches("backups/*"))
    print("Restoring the .env files:")
    for d in tqdm(dicts):
        key = d["date_id"]
        restore_one(key)


if __name__ == "__main__":
    parser = create_arg_parser()
    args = parser.parse_args()
    if args.db_password:
        DB_PASSWORD = args.db_password
    if DB_PASSWORD is None:
        raise Exception("DB_PASSWORD environment variable is not set.")
    if args.backup:
        backup()
    elif args.restore:
        restore_one(args.restore)
    elif args.restore_all:
        restore_all()
