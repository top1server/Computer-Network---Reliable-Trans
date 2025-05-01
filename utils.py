import struct
import zlib

# Header: seq_num (4 bytes), checksum (4 bytes)
HEADER_FMT = '!II'
HEADER_SIZE = struct.calcsize(HEADER_FMT)

def make_packet(seq: int, data: bytes) -> bytes:
    """Create packet: [seq_num][checksum][payload]."""
    chksum = zlib.crc32(data) & 0xffffffff
    header = struct.pack(HEADER_FMT, seq, chksum)
    return header + data

def parse_packet(packet: bytes):
    """Unpack packet into (seq_num, checksum, payload)."""
    seq, chksum = struct.unpack(HEADER_FMT, packet[:HEADER_SIZE])
    payload = packet[HEADER_SIZE:]
    return seq, chksum, payload