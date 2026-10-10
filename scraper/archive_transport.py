"""Streaming authenticated encryption for archives crossing public CI artifacts."""
import argparse
import os
import struct
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b'SCOUTARC1'
CHUNK = 1024 * 1024
OAEP = padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=MAGIC)


def encrypt(source, destination, public_key):
    key = serialization.load_pem_public_key(Path(public_key).read_bytes())
    secret = AESGCM.generate_key(bit_length=256)
    wrapped = key.encrypt(secret, OAEP)
    nonce = os.urandom(8)
    cipher = AESGCM(secret)
    temporary = Path(str(destination) + '.partial')
    try:
        with open(source, 'rb') as incoming, temporary.open('wb') as outgoing:
            outgoing.write(MAGIC + struct.pack('!H', len(wrapped)) + wrapped + nonce)
            index = 0
            while True:
                data = incoming.read(CHUNK)
                sequence = struct.pack('!I', index)
                encrypted = cipher.encrypt(nonce + sequence, data, MAGIC + sequence)
                outgoing.write(struct.pack('!I', len(encrypted)) + encrypted)
                if not data:
                    break
                index += 1
            outgoing.flush()
            os.fsync(outgoing.fileno())
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def decrypt(source, destination, private_key):
    key = serialization.load_pem_private_key(Path(private_key).read_bytes(), password=None)
    temporary = Path(str(destination) + '.partial')
    try:
        with open(source, 'rb') as incoming, temporary.open('wb') as outgoing:
            if incoming.read(len(MAGIC)) != MAGIC:
                raise ValueError('Invalid archive header')
            length = struct.unpack('!H', incoming.read(2))[0]
            secret = key.decrypt(incoming.read(length), OAEP)
            nonce = incoming.read(8)
            cipher = AESGCM(secret)
            index = 0
            while True:
                length = struct.unpack('!I', incoming.read(4))[0]
                if length < 16 or length > CHUNK + 16:
                    raise ValueError('Invalid archive frame')
                sequence = struct.pack('!I', index)
                data = cipher.decrypt(nonce + sequence, incoming.read(length), MAGIC + sequence)
                if not data:
                    if incoming.read(1):
                        raise ValueError('Unexpected trailing archive data')
                    break
                outgoing.write(data)
                index += 1
            outgoing.flush()
            os.fsync(outgoing.fileno())
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['encrypt', 'decrypt'])
    parser.add_argument('source')
    parser.add_argument('destination')
    parser.add_argument('key')
    args = parser.parse_args()
    (encrypt if args.mode == 'encrypt' else decrypt)(args.source, args.destination, args.key)
