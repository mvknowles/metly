HASH_REPS = 50000
import random
import hashlib
from Crypto.Hash import SHA256

def new_salt():
    salt_seed = str(random.getrandbits(128))
    salt = hashlib.sha256(salt_seed).hexdigest()

    return salt

def hash_password(string, salt):
    sha256 = SHA256.new()
    sha256.update(string)
    sha256.update(salt)

    for x in xrange(HASH_REPS):
        sha256.update(sha256.digest())
        if x % 10: sha256.update(salt)

    return sha256.hexdigest()
