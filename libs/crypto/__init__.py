# -*- coding: utf-8 -*-
"""Cryptographic module used for secure LinuFy"""

from flask import current_app
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto import Random
from hashlib import sha256


def encrypt(raw):
    private_key = sha256(current_app.config['SECRET_KEY'].encode("utf-8")).digest()
    nonce = Random.get_random_bytes(12)
    cipher = AES.new(private_key, AES.MODE_GCM, nonce)
    data, signature = cipher.encrypt_and_digest(raw.encode('utf8'))
    return b64encode(nonce + signature + data)


def decrypt(enc):
    private_key = sha256(current_app.config['SECRET_KEY'].encode("utf-8")).digest()
    enc = b64decode(enc)
    nonce = enc[:12]
    signature = enc[12:28]
    data = enc[28:]
    cipher = AES.new(private_key, AES.MODE_GCM, nonce)
    try:
        return cipher.decrypt_and_verify(data, signature).decode("utf-8")
    except ValueError:
        return None