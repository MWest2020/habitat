# SPDX-License-Identifier: MIT
"""A minimal PNG reader and writer, standard library only (change add-designer-role).

The designer's gates must run in CI without Pillow, so they read PNGs here:
8-bit, non-interlaced, colour types 0 (grey), 2 (RGB), 4 (grey+alpha) and
6 (RGBA). Anything else is reported as unsupported, never guessed at.
"""
import struct
import zlib

SIG = b"\x89PNG\r\n\x1a\n"
CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}


class PngError(ValueError):
    pass


def _chunks(data):
    if data[:8] != SIG:
        raise PngError("not a PNG file")
    pos = 8
    while pos + 8 <= len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        yield kind, data[pos + 8:pos + 8 + length]
        pos += 12 + length


def header(path):
    """(width, height, bit_depth, colour_type, interlace) from IHDR."""
    with open(path, "rb") as fh:
        data = fh.read(64)
    for kind, body in _chunks(data):
        if kind == b"IHDR":
            w, h, depth, ctype, _c, _f, inter = struct.unpack(">IIBBBBB", body)
            return w, h, depth, ctype, inter
    raise PngError("no IHDR chunk")


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


class Image:
    """Decoded pixels as RGBA tuples; `px(x, y)` and `width`/`height`."""

    def __init__(self, width, height, ctype, rows):
        self.width, self.height, self.ctype, self.rows = width, height, ctype, rows
        self.n = CHANNELS[ctype]

    def px(self, x, y):
        r = self.rows[y]
        i = x * self.n
        if self.ctype == 6:
            return tuple(r[i:i + 4])
        if self.ctype == 2:
            return (r[i], r[i + 1], r[i + 2], 255)
        if self.ctype == 4:
            return (r[i], r[i], r[i], r[i + 1])
        return (r[i], r[i], r[i], 255)


def read(path):
    with open(path, "rb") as fh:
        data = fh.read()
    idat, ihdr = b"", None
    for kind, body in _chunks(data):
        if kind == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
    if ihdr is None:
        raise PngError("no IHDR chunk")
    w, h, depth, ctype, _c, _f, inter = ihdr
    if depth != 8 or ctype not in CHANNELS or inter:
        raise PngError(f"unsupported PNG (depth {depth}, colour type {ctype}, "
                       f"interlace {inter}); export it with design-kit render")
    n = CHANNELS[ctype]
    stride = w * n
    raw = zlib.decompress(idat)
    rows, prev = [], bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        cur = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = cur[i - n] if i >= n else 0
            b = prev[i]
            c = prev[i - n] if i >= n else 0
            if f == 1:
                cur[i] = (cur[i] + a) & 255
            elif f == 2:
                cur[i] = (cur[i] + b) & 255
            elif f == 3:
                cur[i] = (cur[i] + ((a + b) >> 1)) & 255
            elif f == 4:
                cur[i] = (cur[i] + _paeth(a, b, c)) & 255
        rows.append(cur)
        prev = cur
    return Image(w, h, ctype, rows)


def write(path, width, height, pixel, alpha=True):
    """Write an 8-bit PNG; `pixel(x, y)` returns an RGBA tuple. Used by tests."""
    ctype, n = (6, 4) if alpha else (2, 3)
    raw = bytearray()
    if isinstance(pixel, tuple):          # one colour: build the rows at once
        raw = (b"\x00" + bytes(pixel[:n]) * width) * height
    for y in range(0 if isinstance(pixel, tuple) else height):
        raw.append(0)
        for x in range(width):
            raw.extend(pixel(x, y)[:n])

    def chunk(kind, body):
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, ctype, 0, 0, 0)
    with open(path, "wb") as fh:
        fh.write(SIG + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw)))
                 + chunk(b"IEND", b""))
