import hashlib


def hashsong(song):
    m = hashlib.sha512()
    m.update(song.link.encode("utf-8"))
    return m
