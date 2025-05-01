import socket
import struct
import threading
import zlib
from utils import make_packet, parse_packet, HEADER_SIZE

def run(args):
    print(f"[SR run] args={args}")
    if args.mode == 'sender':
        print("[SR run] Sender mode")
        _sr_sender(args)
    else:
        print("[SR run] Receiver mode")
        _sr_receiver(args)


def _sr_sender(args):
    print(f"[SR Sender] Sending to {args.host}:{args.port}, window={args.window}, chunk={args.chunk}, timeout={args.timeout}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.1)
    base = 0
    next_seq = 0
    window = {}  # seq -> (pkt, timer)
    lock = threading.Lock()

    def start_timer(seq):
        pkt, _ = window[seq]
        t = threading.Timer(args.timeout, lambda: timeout_handler(seq))
        window[seq] = (pkt, t)
        t.start()

    def timeout_handler(seq):
        with lock:
            pkt, _ = window[seq]
            sock.sendto(pkt, (args.host, args.port))
            print(f"[SR Sender] TIMEOUT seq={seq}, retransmitted")
            start_timer(seq)

    with open('input.dat', 'rb') as f:
        while True:
            with lock:
                if next_seq < base + args.window:
                    data = f.read(args.chunk)
                    if not data:
                        break
                    pkt = make_packet(next_seq, data)
                    window[next_seq] = (pkt, None)
                    sock.sendto(pkt, (args.host, args.port))
                    print(f"[SR Sender] Sent seq={next_seq}, {len(data)} bytes")
                    start_timer(next_seq)
                    next_seq += 1
            try:
                raw, _ = sock.recvfrom(4)
                ack = struct.unpack('!I', raw)[0]
                with lock:
                    print(f"[SR Sender] Received ACK={ack}")
                    if base <= ack < next_seq:
                        for s in range(base, ack + 1):
                            _, t = window.pop(s)
                            if t:
                                t.cancel()
                        base = ack + 1
            except socket.timeout:
                continue
    sock.close()


def _sr_receiver(args):
    print(f"[SR Receiver] Listening on {args.host}:{args.port}, chunk={args.chunk}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    expected = 0
    buffer = {}
    with open('output.dat', 'wb') as f:
        while True:
            packet, addr = sock.recvfrom(HEADER_SIZE + args.chunk)
            seq, chksum, payload = parse_packet(packet)
            ok = (zlib.crc32(payload) & 0xffffffff) == chksum
            print(f"[SR Receiver] Got seq={seq}, checksum_ok={ok}")
            if ok and expected <= seq < expected + args.window:
                buffer[seq] = payload
            while expected in buffer:
                f.write(buffer.pop(expected))
                expected += 1
                f.flush()
            ack = expected - 1
            sock.sendto(struct.pack('!I', ack), addr)
            print(f"[SR Receiver] Sent ACK={ack}")
    sock.close()
