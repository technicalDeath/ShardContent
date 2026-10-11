"""Reads the client's English text table (UOData/Cliloc.enu) into {number: text}. Port of ModernUO's BwtDecompress and Localization loader
(ModernUO/Projects/Server/Client/BwtDecompress.cs). Pure Python, about 5 seconds.

    from cliloc import load
    text = load()[1016093]        # "The Ironwood Inn"

Why: shop signs in the shard's sign data (signs.cfg) carry only a cliloc number; this names them.
"""
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.environ.get("CLILOC_PATH") or os.path.normpath(os.path.join(HERE, "..", "..", "..", "UOData", "Cliloc.enu"))


def _stage1(data):
    first = data[0]
    vals, fb, sb = [], first, 0
    for _ in range(65536):
        vals.append(fb + (sb << 8))
        fb = (fb + 1) & 0xFF
        if fb == 0:
            sb = (sb + 1) & 0xFF
    vals.sort()
    t = vals[:256]
    n = len(data)
    out = bytearray(n)
    for i in range(n - 1):          # the C# loop consumes n-1 symbols; the last byte is read but never used
        v = t.pop(data[i])
        t.insert(0, v)
        out[i] = v & 0xFF
    return out


def _stage2(inp):
    symbol = list(range(256))
    part = [0] * (256 * 3)
    part[:256] = list(struct.unpack_from("<256i", inp, 0))
    total = sum(part[:256])
    nonzero = 256 - part[:256].count(0)
    tmp = part[:256]
    freq = [0] * 256
    for i in range(256):
        value, index = 0, 0
        for j in range(256):
            if tmp[j] > value:
                index, value = j, tmp[j]
        if value == 0:
            break
        freq[i] = index
        tmp[index] = 0
    m = 0
    for i in range(nonzero):
        f = freq[i]
        symbol[inp[m + 1024]] = f
        part[f + 256] = m + 1
        m += part[f]
        part[f + 512] = m
    val = symbol[0]
    out = bytearray(total)
    count = 0
    while count < total:
        out[count] = val
        if part[val + 256] >= part[val + 512]:
            if nonzero > 0:
                nonzero -= 1
                for k in range(nonzero):
                    symbol[k] = symbol[k + 1]
                val = symbol[0]
            else:
                nonzero -= 1
        else:
            idx = inp[part[val + 256] + 1024]
            part[val + 256] += 1
            if idx != 0:
                for k in range(idx):
                    symbol[k] = symbol[k + 1]
                symbol[idx] = val
                val = symbol[0]
        count += 1
    return bytes(out)


def load(path=None):
    raw = open(path or PATH, "rb").read()
    if struct.unpack_from("<iH", raw, 0) == (2, 1):
        data = raw[6:]
    else:
        data = _stage2(_stage1(raw[4:]))
        assert struct.unpack_from("<iH", data, 0) == (2, 1), "bad cliloc header"
        data = data[6:]
    out, pos = {}, 0
    while pos + 7 <= len(data):
        num, _flag, ln = struct.unpack_from("<IBH", data, pos)
        pos += 7
        out[num] = data[pos:pos + ln].decode("utf-8", "replace")
        pos += ln
    return out


if __name__ == "__main__":
    import sys
    cl = load()
    for a in sys.argv[1:] or ["1016093"]:
        print(a, cl.get(int(a)))
