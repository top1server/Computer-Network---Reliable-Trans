import socket
import struct
import threading
import zlib
from utils import make_packet, parse_packet, HEADER_SIZE
import os
import math

def run(args):
    print(f"[GBN run] args={args}")
    if args.mode == 'sender':
        print("[GBN run] Sender mode")
        _gbn_sender(args)
    else:
        print("[GBN run] Receiver mode")
        _gbn_receiver(args)


def _gbn_sender(args):
    print(f"[GBN Sender] Sending to {args.host}:{args.port}, window={args.window}, chunk={args.chunk}, timeout={args.timeout}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.1)
    base = 0
    next_seq = 0
    window = {}
    lock = threading.Lock()
    timer = None

    def start_timer():
        nonlocal timer
        if timer:
            timer.cancel()
        timer = threading.Timer(args.timeout, timeout_handler)
        timer.start()

    def timeout_handler():
        with lock:
            print(f"[GBN Sender] TIMEOUT, retransmitting window {base}→{next_seq-1}")
            for s in range(base, next_seq):
                sock.sendto(window[s], (args.host, args.port))
        start_timer()

    with open('input.dat', 'rb') as f:
        while True:
            with lock:
                if next_seq < base + args.window:
                    data = f.read(args.chunk)
                    if not data:
                        break
                    pkt = make_packet(next_seq, data)
                    window[next_seq] = pkt
                    sock.sendto(pkt, (args.host, args.port))
                    print(f"[GBN Sender] Sent seq={next_seq}, {len(data)} bytes")
                    if base == next_seq:
                        start_timer()
                    next_seq += 1
            try:
                raw, _ = sock.recvfrom(4)
                ack = struct.unpack('!I', raw)[0]
                with lock:
                    print(f"[GBN Sender] Received ACK={ack}")
                    if base <= ack < next_seq:
                        base = ack + 1
                        if base == next_seq:
                            timer.cancel()
                        else:
                            start_timer()
            except socket.timeout:
                continue
    if timer:
        timer.cancel()
    sock.close()


def _gbn_receiver(args):
    print(f"[GBN Receiver] Listening on {args.host}:{args.port}, chunk={args.chunk}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    expected = 0
    with open('output.dat', 'wb') as f:
        while True:
            packet, addr = sock.recvfrom(HEADER_SIZE + args.chunk)
            seq, chksum, payload = parse_packet(packet)
            ok = (zlib.crc32(payload) & 0xffffffff) == chksum
            print(f"[GBN Receiver] Got seq={seq}, checksum_ok={ok}")
            if seq == expected and ok:
                f.write(payload)
                f.flush()
                expected += 1
            ack = expected - 1
            sock.sendto(struct.pack('!I', ack), addr)
            print(f"[GBN Receiver] Sent ACK={ack}")
    sock.close()